import json
import sqlite3

def convert_json(s):
    return json.loads(s)

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


class Database:

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
        return self.conn.__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        return self.conn.__exit__(exc_type, exc_value, traceback)

    def find(self, values):
        condition = ' AND '.join(('json_extract(metadata, ?) = ?' for _ in values))
        return self.conn.execute(
            f'''SELECT oid, filename, reader, metadata FROM source WHERE {condition}''',
            tuple(p
                  for k, v in values.items()
                  for p in [f'$.{k}', v])).fetchone()

    def find_all(self, values, args):
        args = [arg for arg in args if arg not in values]
        condition = ' AND '.join(
            ['json_extract(metadata, ?) = ?' for _ in values] +
            ['json_extract(metadata, ?) IS NOT NULL' for _ in args])

        return self.conn.execute(
            f'''SELECT oid, filename, reader, metadata FROM source WHERE {condition}''',
            tuple(p
                  for k, v in values.items()
                  for p in [f'$.{k}', v])
            + tuple(f'$.{k}' for k in args)).fetchall()

    def add(self, filename, reader, metadata):
        self.conn.execute(
            '''INSERT OR REPLACE INTO source VALUES (?,?,json(?))''',
            (filename, reader, json.dumps(metadata)))

    def remove(self, filename):
        return self.conn.execute(
            '''DELETE FROM source WHERE filename = ?''',
            (filename,)).rowcount > 0
