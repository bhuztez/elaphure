import os
from types import ModuleType
from warnings import warn
from werkzeug.routing import Map, Rule
from mako.lookup import TemplateLookup
from pkg_resources import load_entry_point
from .database import Database

class LazyDict:

    def __init__(self, func):
        self.data = {}
        self.func = func

    def __getitem__(self, key):
        if key not in self.data:
            self.data[key] = self.func(key)
        return self.data[key]


class Config:

    def __init__(self, filename):
        filename = os.path.abspath(filename)
        mod = ModuleType("__config__")
        mod.__file__ = filename
        mod.database = Database()
        mod.Map = Map
        mod.Rule = Rule
        mod.warn = warn

        self.database = mod.database

        with open(filename, 'r') as f:
            code = compile(f.read(), filename, 'exec')
        exec(code, mod.__dict__)
        config = mod.__dict__

        self._config = {
            'sources': config.get('SOURCES', {}),
            'readers': config.get('READERS', {}),
            'writers': config.get('WRITERS', {}),
        }

        self.SOURCES = LazyDict(lambda x: self.load_plugin('sources', x))
        self.READERS = LazyDict(lambda x: self.load_plugin('readers', x))
        self.WRITERS = LazyDict(lambda x: self.load_plugin('writers', x))

        self.SOURCE_FILES = config.get('SOURCE_FILES', [])

        self.STATICFILES_DIRS = config.get('STATICFILES_DIRS', {})
        self.STATICFILES_EXCLUDE = config.get('STATICFILES_EXCLUDE', [])

        self.TEMPLATES = TemplateLookup(
            config.get('TEMPLATE_DIRS', []),
            input_encoding='utf-8',
            format_exceptions=True,
            cache_enabled=False,
            imports=['from warnings import warn'])
        self.URLS = config.get('URLS', Map([]))

    def load_plugin(self, type, name):
        config = self._config[type].get(name, {})
        klass = load_entry_point(
            __package__, f'{__package__}_{type}', config.get('name', name))
        return klass(config)
