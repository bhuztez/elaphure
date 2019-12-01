import json
import sqlite3
try:
    sqlite3.connect(":memory:").execute("select json(1)")
except sqlite3.OperationalError:
    try:
        import sqlite3ct as sqlite3
    except ImportError:
        raise Exception("""
the sqlite3 bundled with Python compiled without JSON1 extension enabled

If you are running on Windows, try
choco install sqlite
pip3 install sqlite3ct
""")

sqlite3.register_converter("JSON", json.loads)

from warnings import warn
from string import Formatter
from functools import reduce
from collections.abc import Mapping
from datetime import datetime

from werkzeug.utils import cached_property

DATE_ATTRS = ('year', 'month', 'day')

class Entry(Mapping):

    def __init__(self, metadata, **kwargs):
        self.__dict__.update(kwargs)
        self.__data = metadata

    def __getitem__(self, key):
        if '__' not in key:
            return self.__data[key]
        v, a = key.split('__')
        if a not in DATE_ATTRS:
            raise KeyError(key)
        try:
            d = datetime.fromisoformat(self.__data.get(v, None))
        except (TypeError, ValueError):
            raise KeyError(key)
        return getattr(d, a)

    def __iter__(self):
        return iter(self.__data)

    def __len__(self):
        return len(self.__data)

    def open(self):
        return self.source.open(self.filename)

    @cached_property
    def content(self):
        return self.reader.content(self.source, self.filename)

class F:

    def __init__(self, sql, *args):
        fmt = Formatter()
        result = []
        params = []

        for (text, field_name, _, _), arg in zip(fmt.parse(sql), args + (None,)):
            result.append(text)
            if field_name is None:
                continue
            assert field_name == ''
            if isinstance(arg, F):
                result.append(arg.sql)
                params.extend(arg.params)
            else:
                result.append('?')
                params.append(arg)

        self.sql = ''.join(result).strip()
        self.params = tuple(params)

    def __bool__(self):
        return bool(self.sql)

    def join(self, fragments):
        fragments = list(fragments)
        if not fragments:
            return F("")
        return reduce(lambda a,b: F("{} {} {}", a, self, b), fragments)


class MultipleEntriesReturned(Exception):
    pass


class Database:

    def __init__(self, config):
        self.config = config

        conn = sqlite3.connect(
            ':memory:',
            check_same_thread=False,
            detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)

        with conn:
            conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS source(
                filename TEXT UNIQUE,
                reader TEXT,
                metadata JSON
                )''')

        self.conn = conn

    def __enter__(self):
        self.conn.__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        return self.conn.__exit__(exc_type, exc_value, traceback)

    def add(self, filename, reader, metadata):
        self.execute(
            '''INSERT OR REPLACE INTO source VALUES ({},{},json({}))''',
            filename, reader, json.dumps(metadata))

    def remove(self, filename):
        return self.execute(
            '''DELETE FROM source WHERE filename = {}''',
            filename).rowcount > 0

    def execute(self, sql, *args):
        if not isinstance(sql, F):
            sql = F(sql, *args)
        else:
            assert not args
        return self.conn.execute(sql.sql, sql.params)

    def select(self, sql, *args):
        return [
            Entry(
                metadata,
                filename=filename,
                reader=self.config.readers[reader],
                source=self.config.source)
            for filename, reader, metadata in self.execute(sql, *args)
        ]

    def get(self, sql, *args):
        entries = self.select(sql, *args)

        if not entries:
            return None

        if len(entries) > 1:
            raise MultipleEntriesReturned()

        return entries[0]
