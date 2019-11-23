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

from string import Formatter
from collections.abc import Mapping
from datetime import datetime
from functools import reduce
from werkzeug.exceptions import NotFound

from .utils import cached_property

DATE_FMT = {
    'year': '%Y',
    'month': '%m',
    'day': '%d',
}

class Entry(Mapping):

    def __init__(self, metadata, **kwargs):
        self.__dict__.update(kwargs)
        self.__data = metadata

    def __getitem__(self, key):
        if '__' not in key:
            return self.__data[key]
        v, a = key.split('__')
        if a not in DATE_FMT:
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
        with self.open() as f:
            return self.reader.content(f)

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

def column(k):
    if '__' not in k:
        return F('json_extract(metadata, {})', f'$.{k}')
    n, a = k.split('__')
    if a in DATE_FMT:
        return F("CAST(strftime({}, json_extract(metadata, {})) AS INTEGER)", DATE_FMT[a], f'$.{n}')
    assert False

def condition(values):
    return F('AND').join(
        F('{} = {}', column(k), v) for k, v in values.items())


class Page(list):

    def __init__(self, count, page_size, page):
        self.page_size = page_size
        self.page = page
        self.count = count
        self.num_pages = self.count // page_size
        if self.count % page_size:
            self.num_pages += 1
        if not (0 < page <= self.num_pages):
            raise NotFound()

        self.has_next = page < self.num_pages
        self.has_previous = page > 1
        self.has_other_pages = page != 1

        self.start_index = (page - 1) * page_size + 1
        self.end_index = count if self.page == self.num_pages else self.start_index - 1 + page_size


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

    def raw(self, sql, *args):
        return [
            Entry(
                metadata,
                filename=filename,
                reader=self.config.readers[reader],
                source=self.config.source)
            for filename, reader, metadata in self.execute(sql, *args)
        ]

    def select(self, values, *, order_by=None, page_size=None, page=None, **_):
        frag = F('FROM source WHERE {}', condition(values))
        sql = F('SELECT filename, reader, metadata {}', frag)

        if order_by is not None:
            keys = order_by.split(',')
            sql = F(
                "{} ORDER BY {}", sql,
                F(',').join(
                    F("{} DESC" if key.startswith('-') else "{} ASC", column(key[1:]))
                    for key in order_by.split(',')))

        if page_size is None:
            return self.raw(sql)

        count = self.execute('''SELECT count(1) {}''', frag).fetchone()[0]
        page = Page(count, page_size, page)

        list.__init__(page, self.raw("{} LIMIT {}, {}", sql, page.start_index - 1, page_size))
        return page

    def find_all(self, values, args, *, page_size=None, **_):
        cond = condition(values)
        columns = F(',').join(column(arg) for arg in args)

        if page_size is None:
            return [
                dict(zip(args, row))
                for row in self.execute("SELECT DISTINCT {} FROM source WHERE {}", columns, cond)]

        if columns:
            sql = F("SELECT count(1), {} FROM source WHERE {} GROUP BY {}", columns, cond, columns)
        else:
            sql = F("SELECT count(1) FROM source WHERE {}", cond)

        return [dict(zip(('__page',) + args, [i,] + row))
                for p, *row in self.execute(sql)
                for i in range(1, p // page_size + bool(p % page_size) + 1)]
