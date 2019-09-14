from threading import Lock
from . import Entry

class DummyRegistry:

    def __init__(self, config):
        self._entries = {}
        self._lock = Lock()

    def __enter__(self):
        self._lock.acquire()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._lock.release()

    def iter(self, values, args=()):
        for entry in self._entries.values():
            if not all(
                    (k in entry) and (entry[k] == v)
                    for k, v in values.items()):
                continue
            if not all((k in entry) for k in args):
                continue
            yield entry

    def find(self, values):
        try:
            return next(self.iter(values))
        except StopIteration:
            pass

    def find_all(self, values, args=()):
        return list(self.iter(values, args))

    def add(self, filename, reader, metadata):
        self._entries[filename] = Entry(metadata, filename=filename, reader=reader)

    def remove(self, filename):
        try:
            del self._entries[filename]
            return True
        except KeyError:
            pass
