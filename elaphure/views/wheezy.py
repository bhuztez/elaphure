from wheezy.template.engine import Engine
from wheezy.template.loader import FileLoader, autoreload
from wheezy.template.ext.core import CoreExtension, extends_tokens
from wheezy.template.ext.code import CodeExtension
from werkzeug.wrappers import Response
from warnings import warn, catch_warnings

extends_tokens.append('code')

class AutoRequireExtension:
    def __init__(self, *names):
        self.names = names

    @property
    def postprocessors(self):
        yield self.add_require

    def add_require(self, tokens):
        tokens.insert(0, (0, 'require', f"require({','.join(self.names)})"))

class WheezyView:
    token_start = '%'
    template_dirs = ['.']
    mimetype = 'text/html'

    def __init__(self, template_name):
        engine = Engine(
            loader=FileLoader(self.template_dirs),
            extensions=[
                CoreExtension(token_start=self.token_start),
                CodeExtension(token_start=self.token_start),
                AutoRequireExtension('urls', 'db', 'endpoint', 'values', 'entries')
            ])

        with catch_warnings(record=True):
            self.engine = autoreload(engine)

        engine.global_vars.update(
            {'_r': self.engine.render,
             'warn': warn})
        self.template_name = template_name

    def render(self, **context):
        return self.engine.get_template(self.template_name).render(context)

    def __call__(self, db, urls, endpoint, values, entries):
        return Response(
            self.render(db=db, urls=urls, endpoint=endpoint, values=values, entries=entries),
            mimetype=self.mimetype)
