from wheezy.template.engine import Engine
from wheezy.template.ext.core import CoreExtension, extends_tokens
from wheezy.template.ext.code import CodeExtension
from warnings import warn

if 'code' not in extends_tokens:
    extends_tokens.append('code')

class Loader:
    def __init__(self, source):
        self.source = source

    def load(self, name):
        with self.source.open(name) as f:
            return f.read()

class WheezyReader:

    def metadata(self, source, filename):
        return {}

    def content(self, source, filename):
        engine = Engine(
            loader=Loader(source),
            extensions=[
                CoreExtension(token_start='\\$'),
                CodeExtension(token_start='\\$'),
            ])
        engine.global_vars.update({'warn': warn})
        return engine.get_template(filename).render({})
