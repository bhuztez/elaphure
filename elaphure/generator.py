import os
from fnmatch import fnmatch
from glob import has_magic, _isrecursive, _ishidden
from werkzeug._internal import _log


def match(filename, pathname):
    if not has_magic(pathname):
        return filename == pathname
    dirname, basename = os.path.split(pathname)
    if _isrecursive(basename):
        if not dirname:
            return True
        while filename:
            if match(filename, dirname):
                return True
            filename = os.path.dirname(filename)
        return False

    if dirname:
        if not match(os.path.dirname(filename), dirname):
            return False
    elif os.path.dirname(filename):
        return False
    filename = os.path.basename(filename)
    if _ishidden(filename):
        return False
    return fnmatch(filename, basename)


class Generator:

    def __init__(self, config, source):
        self.files = config.SOURCE_FILES
        self.readers = config.READERS
        self.registry = config.registry
        self.source = source

    def add(self, filename):
        for pattern, reader_name, meta_func in self.files:
            if match(filename, pattern):
                reader = self.readers[reader_name]
                with self.source.open(filename) as f:
                    data = reader.metadata(f)
                self.registry.add(filename, reader_name, meta_func(filename, data))
                return True

    def remove(self, filename):
        return self.registry.remove(filename)

    def scan(self):
        with self.registry:
            for filename in self.source.walk():
                if self.add(filename):
                    _log("info", " * File found %r" % (filename,))

    def watch(self):
        for event, src_path, *dest_path in self.source.watch():
            with self.registry:
                if event == 'created':
                    if self.add(src_path):
                        _log("info", " * File found %r" % (src_path,))
                elif event == 'modified':
                    if self.add(src_path):
                        _log("info", " * File modified %r" % (src_path,))
                elif event == 'deleted':
                    if self.remove(src_path):
                        _log("info", " * File deleted %r" % (src_path,))
                elif event == 'moved':
                    remove = self.remove(src_path)
                    add = self.add(dest_path[0])
                    if remove or add:
                        _log("info", " * File moved from %r to %r" % (src_path, dest_path))

def scan(config, src):
    Generator(config, src).scan()

def watch(config, src):
    from threading import Thread
    Thread(target=Generator(config, src).watch, daemon=True).start()
