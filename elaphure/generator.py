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

def add(config, filename):
    for pattern, reader_name, meta_func in config.SOURCE_FILES:
        if match(filename, pattern):
            reader = config.readers[reader_name]
            data = reader.metadata(config.source, filename)
            config.db.add(filename, reader_name, meta_func(filename, data))
            return True

def scan(config):
    with config.db:
        for filename in config.source.walk():
            if add(config, filename):
                _log("info", f" * File found {filename!r}")

def watch(config):
    for event, src_path, *dest_path in config.source.watch():
        with config.db:
            if event == 'created':
                if add(config, src_path):
                    _log("info", f" * File found {src_path!r}")
            elif event == 'modified':
                if add(config, src_path):
                    _log("info", f" * File modified {src_path!r}")
            elif event == 'deleted':
                if config.db.remove(src_path):
                    _log("info", f" * File deleted {src_path!r}")
            elif event == 'moved':
                removed = config.db.remove(src_path)
                added = add(config, dest_path[0])
                if removed or added:
                    _log("info", f" * File moved from {src_path!r} to {dest_path!r}")
