from werkzeug.wrappers import Response
from werkzeug.exceptions import HTTPException


class Reader:

    def __init__(self, source, filename, reader):
        self.source = source
        self.filename = filename
        self.reader = reader

    def html(self):
        with self.source.open(self.filename) as f:
            return self.reader.html(f)

class Site:

    def __init__(self, config, source):
        self.readers = config.readers
        self.views = config.views
        self.urls = config.urls
        self.registry = config.registry
        self.source = source

    def __iter__(self):
        for rule in self.urls.iter_rules():
            if rule.arguments:
                for entry in self.registry.find_all(rule.defaults or {}, rule.arguments or ()):
                    url = self.urls.build(
                        rule.endpoint,
                        {a: rule.defaults.get(a, entry.get(a, None))
                         for a in rule.arguments})

                    if self.urls.match(url, return_rule=True)[0] is rule:
                        yield url
            else:
                yield self.urls.build(rule.endpoint)

    def read(self, entry):
        return Reader(self.source, entry.filename, self.readers[entry.reader])

    def __call__(self, environ, start_response):
        with self.urls.bind_to_environ(environ):
            try:
                endpoint, values = self.urls.match()
                with self.registry:
                    response = self.views[endpoint](self.registry, self.urls, self.read, values)
            except HTTPException as e:
                response = e
            return response(environ, start_response)
