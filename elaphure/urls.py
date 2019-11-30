import os
from contextvars import ContextVar
from contextlib import contextmanager
from werkzeug.routing import Map

class Urls:

    def __init__(self, rules):
        self.map = Map(rules)
        self.urls = ContextVar("urls", default=self.map.bind(''))

    def iter_rules(self):
        return self.map.iter_rules()

    @contextmanager
    def _bind(self, urls):
        token = self.urls.set(urls)
        try:
            yield
        finally:
            self.urls.reset(token)

    def bind(self, *args, **kwargs):
        return self._bind(self.map.bind(*args, **kwargs))

    def bind_to_environ(self, *args, **kwargs):
        return self._bind(self.map.bind_to_environ(*args, **kwargs))

    def build(self, endpoint, values=None, method=None, force_external=False, append_unknown=True):
        urls = self.urls.get()
        path = urls.build(endpoint, values, method, force_external, append_unknown)
        if urls.url_scheme == 'file' and urls.server_name == '.':
            assert not force_external
            if path.endswith('/'):
                path = path + 'index.html'
            return os.path.relpath(path, os.path.dirname(urls.path_info))
        return path

    def match(self, path=None, return_rule=False):
        urls = self.urls.get()
        if path is None:
            return urls.match(return_rule=return_rule)
        if urls.url_scheme == 'file' and urls.server_name == '.':
            path = os.path.normpath(os.path.join(os.path.dirname(urls.path_info), path))
            if path.endswith("/index.html"):
                path = path[:-11]
        else:
            script_name = urls.script_name.rstrip("/")
            assert path.startswith(script_name)
            path = path[len(script_name):]

        return urls.match(path, return_rule=return_rule)

    def dispatch(self, *args, **kwargs):
        return self.urls.get().dispatch(*args, **kwargs)

    def current_url(self):
        return self.dispatch(lambda e, v: self.build(e,v))
