from threading import Lock
from operator import itemgetter
from itertools import groupby
from . import Entry

class DummyRegistry:

    def __init__(self):
        self._entries = {}
        self._lock = Lock()

    def __enter__(self):
        self._lock.acquire()

    def __exit__(self, exc_type, exc_value, traceback):
        self._lock.release()

    def iter(self, values):
        for entry in self._entries.values():
            if not all(
                    (k in entry) and (entry[k] == v)
                    for k, v in values.items()):
                continue
            yield entry

    def select(self, values, order_by=None):
        data = list(self.iter(values))
        if order_by is not None:
            for key in reversed(order_by.split(',')):
                data.sort(key=itemgetter(key[1:]), reverse=key.startswith('-'))
        return data

    def find_all(self, values, args, page_size=None):
        if page_size is None:
            for v in set(tuple(entry[a] for a in args) for entry in self.iter(values)):
                yield dict(zip(args, v))
        else:
            for k, g in groupby(
                    sorted(tuple(entry[a] for a in args) for entry in self.iter(values)),
                    lambda x: x):
                d = dict(zip(args, k))
                for i, _ in enumerate(g):
                    d['__page'] = i + 1
                    yield d

    def add(self, filename, reader, metadata):
        self._entries[filename] = Entry(metadata, filename=filename, reader=reader)

    def remove(self, filename):
        try:
            del self._entries[filename]
            return True
        except KeyError:
            pass
