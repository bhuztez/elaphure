import json
import sqlite3
import datetime
from . import Entry

def json_encode(o):
    if isinstance(o, datetime.date):
        return {"date": o.isoformat()}
    raise TypeError

def json_object_hook(o):
    if len(o) == 1:
        if 'date' in o:
            return datetime.date.fromisoformat(o["date"])
    return o

def convert_json(s):
    return json.loads(s, object_hook=json_object_hook)

sqlite3.register_converter("JSON", convert_json)

class JsonGroupArray:
    def __init__(self):
        self.data = []

    def step(self, value):
        if value is None:
            return
        self.data.append(value)

    def finalize(self):
        return "[" + ",".join(self.data) + "]"

DATE_FMT = {
    'year': '%Y',
    'month': '%m',
    'day': '%d',
}

def column_expr(k):
    if '__' not in k:
        return 'json_extract(metadata, ?)'
    n, a = k.split('__')
    if a in DATE_FMT:
        return "CAST(strftime(?, json_extract(metadata, ?)) AS INTEGER)"
    assert False

def column_args(k):
    if '__' not in k:
        return [f'$.{k}']
    n, a = k.split('__')
    if a in DATE_FMT:
        return [DATE_FMT[a], f'$.{n}.date']

def condition(values):
    return (
        ' AND '.join(f"{column_expr(k)} = ?" for k in values),
        tuple(p
              for k, v in values.items()
              for p in column_args(k) + [v]))

def column(keys):
    return (', '.join(column_expr(k) for k in keys),
            tuple(p
                  for k in keys
                  for p in column_args(k)))

class SqliteRegistry:

    def __init__(self):
        conn = sqlite3.connect(
            ':memory:',
            check_same_thread=False,
            detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)

        conn.create_aggregate("json_group_array", 1, JsonGroupArray)

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

    def select(self, values, order_by=None):
        cond = condition(values)
        sql = f'''SELECT oid, filename, reader, metadata FROM source WHERE {cond[0]}'''
        params = cond[1]
        if order_by is not None:
            keys = order_by.split(',')
            sql += ''' ORDER BY ''' + ', '.join(
                f'''{column_expr(key[1:])} {"DESC" if key.startswith('-') else "ASC"}'''
                for key in keys)
            params += tuple(p
                            for k in keys
                            for p in column_args(k[1:]))

        return [
            Entry(metadata, oid=oid, filename=filename, reader=reader)
            for oid, filename, reader, metadata in self.conn.execute(sql, params)]

    def find_all(self, values, args, page_size=None):
        cond = condition(values)
        col = column(args)
        if page_size is None:
            sql = f'''SELECT {col[0]} FROM source WHERE {cond[0]} GROUP BY {col[0]}'''
            params = col[1] + cond[1] + col[1]
            return [dict(zip(args, t))
                    for t in self.conn.execute(sql, params).fetchall()]

        columns = 'count(1)'
        if col[0]:
            columns += ', ' + col[0]

        sql = f'''SELECT {columns} FROM source WHERE {cond[0]}'''
        if col[0]:
            sql += ' GROUP BY {col[0]}'

        params = col[1] + cond[1] + col[1]
        return [dict(zip(('__page',) + args, [i,] + t))
                for p, *t in self.conn.execute(sql, params).fetchall()
                for i in range(1, p // page_size + bool(p % page_size) + 1)]


    def add(self, filename, reader, metadata):
        self.conn.execute(
            '''INSERT OR REPLACE INTO source VALUES (?,?,json(?))''',
            (filename, reader, json.dumps(metadata, default=json_encode)))

    def remove(self, filename):
        return self.conn.execute(
            '''DELETE FROM source WHERE filename = ?''',
            (filename,)).rowcount > 0
