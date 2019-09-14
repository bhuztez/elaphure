from werkzeug.wrappers import Response
from werkzeug.exceptions import HTTPException, NotFound

class Site:

    def __init__(self, config, source):
        self.readers = config.READERS
        self.templates = config.TEMPLATES
        self.urls = config.URLS
        self.registry = config.registry
        self.source = source

    def render(self, filename, context):
        return self.templates.get_template(filename).render(**context)

    def __iter__(self):
        urls = self.urls.bind("localhost", "/")
        for rule in self.urls.iter_rules():
            if rule.arguments:
                for entry in self.registry.find_all(rule.defaults or {}, rule.arguments or ()):
                    yield urls.build(
                        rule.endpoint,
                        {a: rule.defaults.get(a, entry.get(a, None))
                         for a in rule.arguments})
            else:
                yield urls.build(rule.endpoint)

    def __call__(self, environ, start_response):
        urls = self.urls.bind_to_environ(environ)
        try:
            endpoint, values = urls.match()
            with self.registry as registry:
                context = {'registry': registry, 'urls': urls}

                if values:
                    entry = self.registry.find(values)
                    if not entry:
                        raise NotFound()

                    context['filename'] = entry.filename
                    context['entry'] = entry
                    with self.source.open(entry.filename) as f:
                        context['content'] = self.readers[entry.reader].html(f)

                response = Response(self.render(endpoint, context), mimetype='text/html')
        except HTTPException as e:
            response = e
        return response(environ, start_response)
