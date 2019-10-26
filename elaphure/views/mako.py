from mako.lookup import TemplateLookup
from werkzeug.wrappers import Response

class MakoView:
    template_dirs = []
    mimetype = 'text/html'

    def __init__(self, template_name):
        self.templates = TemplateLookup(
            self.template_dirs,
            input_encoding='utf-8',
            format_exceptions=True,
            cache_enabled=False,
            imports=['from warnings import warn'])
        self.template_name = template_name

    def render(self, **context):
        return self.templates.get_template(self.template_name).render(**context)

    def __call__(self, registry, urls, read, values):
        return Response(
            self.render(registry=registry, urls=urls, read=read, values=values),
            mimetype=self.mimetype)
