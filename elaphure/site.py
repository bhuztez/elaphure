from werkzeug.wrappers import Response
from werkzeug.exceptions import HTTPException, NotFound

class Site:

    def __init__(self, config):
        self.views = config.views
        self.urls = config.urls
        self.db = config.db
        self.source = config.source

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
                for kwds in self.db.find_all(defaults or {}, args, page_size=page_size):
                    url = self.urls.build(rule.endpoint, kwds)
                    if self.urls.match(url, return_rule=True)[0] is rule:
                        yield url
            else:
                yield self.urls.build(rule.endpoint)

    def __call__(self, environ, start_response):
        with self.urls.bind_to_environ(environ):
            try:
                endpoint, values = self.urls.match()
                with self.db:
                    if values:
                        args = {k[2:]:v for k,v in values.items() if k.startswith("__")}
                        for k in args:
                            del values['__'+k]

                        entries = self.db.select(values, **args)
                    else:
                        entries = []

                    response = self.views[endpoint](self.db, self.urls, endpoint, values, entries)
            except HTTPException as e:
                response = e
            return response(environ, start_response)
