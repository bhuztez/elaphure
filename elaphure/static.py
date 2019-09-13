import os
from fnmatch import fnmatch
from pathlib import PurePath
from werkzeug.wsgi import SharedDataMiddleware


class Static:

    def __init__(self, config, source):
        self.dirs = config.STATICFILES_DIRS
        self.exclude = config.STATICFILES_EXCLUDE
        self.source = source

    def is_allowed(self, path):
        return not any(
            fnmatch(s, p)
            for s in PurePath(path).parts
            for p in self.exclude)

    def __iter__(self):
        for prefix, base in self.dirs.items():
            for filename in self.source.walk(base):
                if self.is_allowed(filename):
                    name = os.path.relpath(filename, base)
                    yield f'{prefix}/{name}'

    def __call__(self, application):
        application = SharedDataMiddleware(application, self.dirs, cache=False)
        application.is_allowed = self.is_allowed
        application._opener = lambda filename: lambda: self.source._open(filename)
        return application
