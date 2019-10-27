from werkzeug.wrappers import Response
from werkzeug.exceptions import HTTPException, NotFound


class Reader:

    def __init__(self, source, filename, reader):
        self.source = source
        self.filename = filename
        self.reader = reader

    def html(self):
        with self.source.open(self.filename) as f:
            return self.reader.html(f)

class Page:

    def __init__(self, data, page_size, page):
        self.page_size = page_size
        self.page = page
        self.count = len(data)
        self.num_pages = self.count // page_size
        if self.count % page_size:
            self.num_pages += 1
        if not (0 < page <= self.num_pages):
            raise NotFound()

        self.has_next = page < self.num_pages
        self.has_previous = page > 1
        self.has_other_pages = page != 1
        self.start_index = 1 + (page - 1) * page_size
        self.end_index = page * page_size

        self.data = data[self.start_index-1: self.end_index]

    def __iter__(self):
        return iter(self.data)

class Site:

    def __init__(self, config, source):
        self.readers = config.readers
        self.views = config.views
        self.urls = config.urls
        self.registry = config.registry
        self.source = source

    def __iter__(self):
        for rule in self.urls.iter_rules():
            defaults = rule.defaults or {}
            args = rule.arguments or ()
            page_size = defaults.get('__page_size', None)

            if '__page' not in args:
                page_size = None

            defaults = {k:v for k,v in defaults.items() if not k.startswith("__")}
            args = tuple(a
                         for a in rule.arguments
                         if a not in defaults and not a.startswith("__"))

            if args or page_size:
                for kwds in self.registry.find_all(defaults or {}, args, page_size):
                    url = self.urls.build(rule.endpoint, kwds)
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
                    if values:
                        args = {k:v for k,v in values.items() if k.startswith("__")}
                        for k in args:
                            del values[k]

                        entries = self.registry.select(values, args.get('__order_by', None))
                        if '__page_size' in args:
                            entries = Page(entries, args['__page_size'], args['__page'])
                    else:
                        entries = []

                    response = self.views[endpoint](self.registry, self.urls, self.read, values, entries)
            except HTTPException as e:
                response = e
            return response(environ, start_response)
