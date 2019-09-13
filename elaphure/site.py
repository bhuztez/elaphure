from werkzeug.wrappers import Response
from werkzeug.exceptions import HTTPException, NotFound

class Site:

    def __init__(self, config, source):
        self.readers = config.READERS
        self.templates = config.TEMPLATES
        self.urls = config.URLS
        self.database = config.database
        self.source = source

    def render(self, filename, context):
        return self.templates.get_template(filename).render(**context)

    def __iter__(self):
        urls = self.urls.bind("localhost", "/")
        for rule in self.urls.iter_rules():
            if rule.arguments:
                for _, _, _, metadata in self.database.find_all(rule.defaults or {}, rule.arguments or ()):
                    yield urls.build(
                        rule.endpoint,
                        {a: rule.defaults.get(a, metadata.get(a, None))
                         for a in rule.arguments})
            else:
                yield urls.build(rule.endpoint)

    def __call__(self, environ, start_response):
        urls = self.urls.bind_to_environ(environ)
        try:
            endpoint, values = urls.match()
            with self.database as db:
                context = {'db': db, 'urls': urls}

                if values:
                    result = self.database.find(values)
                    if not result:
                        raise NotFound()

                    oid, filename, reader, metadata = result
                    context['oid'] = oid
                    context['filename'] = filename
                    context['metadata'] = metadata
                    with self.source.open(filename) as f:
                        context['content'] = self.readers[reader].html(f)

                response = Response(self.render(endpoint, context), mimetype='text/html')
        except HTTPException as e:
            response = e
        return response(environ, start_response)
