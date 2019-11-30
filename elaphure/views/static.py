import os
import mimetypes
from fnmatch import fnmatch
from pathlib import PurePath
from werkzeug.wrappers import Response
from werkzeug.wsgi import FileWrapper

class StaticFileView:

    def __init__(self, basedir, exclude=()):
        self.basedir = basedir
        self.exclude = exclude

    def is_allowed(self, path):
        return not any(
            fnmatch(s, p)
            for s in PurePath(path).parts
            for p in self.exclude)

    def find_all(self, config, values, args):
        assert tuple(args) == ('path',)

        for filename in config.source.walk(self.basedir):
            if not self.is_allowed(filename):
                continue
            yield {'path': os.path.relpath(filename, self.basedir)}

    def __call__(self, config, endpoint, values):
        assert len(values) == 1
        filename = os.path.join(self.basedir, values['path'])
        return Response(
            FileWrapper(config.source.open(filename, 'rb')),
            mimetype=mimetypes.guess_type(filename)[0] or 'text/plain'
        )
