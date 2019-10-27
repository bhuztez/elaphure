import os
from types import ModuleType
from warnings import warn
from werkzeug.routing import Rule
from pkg_resources import load_entry_point, get_entry_info
from .urls import Urls


class cached_property:
    def __init__(self, func):
        self.func = func
        self.name = None

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        value = self.func(instance)
        setattr(instance, self.name, value)
        return value

class LazyDescriptor:

    def __init__(self, func):
        self.func = func
        self.name = None

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        value = self.func(owner)
        setattr(owner, self.name, value)
        return value

class LazyMeta(type):

    def __new__(self, name, bases, kwds, *, info=None):
        if not bases:
            return type.__new__(self, name, bases, {"info": info})

        return type(
            name,
            tuple(base.wrapped if isinstance(base, LazyMeta) else base
                  for base in bases),
            kwds)

    @cached_property
    def wrapped(self):
        return self.info.load()

    def __call__(self, *args, **kwargs):
        return LazyDescriptor(lambda _: self.wrapped(*args, **kwargs))


class Builtins(dict):

    def __getitem__(self, key):
        if key not in self:
            info = get_entry_info(__package__, f'{__package__}_extensions', key)
            if info is not None:
                class LazyClass(metaclass=LazyMeta, info=info):
                    pass
                self[key] = LazyClass
        return super().__getitem__(key)

class Meta(type):

    def __getattr__(self, key):
        try:
            return load_entry_point(__package__, f'{__package__}_{self.__name__}', key)()
        except ImportError:
            raise AttributeError(key)

    def __getitem__(self, key):
        try:
            return getattr(self, key.replace('-', '_'))
        except AttributeError:
            raise KeyError(key)

class ConfigDict(metaclass=Meta):
    pass

class registries(ConfigDict):
    pass

class sources(ConfigDict):
    pass

class readers(ConfigDict):
    pass

class writers(ConfigDict):
    pass


def load_config(filename, registry='default'):
    filename = os.path.abspath(filename)
    mod = ModuleType("__config__")
    mod.__builtins__ = Builtins(__builtins__)
    mod.__file__ = filename
    mod.Rule = Rule
    mod.warn = warn
    mod.config = ConfigDict

    with open(filename, 'r') as f:
        code = compile(f.read(), filename, 'exec')

    exec(code, mod.__dict__)
    config = mod.__dict__

    config.setdefault('registries', registries)
    config.setdefault('sources', sources)
    config.setdefault('readers', readers)
    config.setdefault('writers', writers)

    config.setdefault('SOURCE_FILES', [])
    config.setdefault('STATICFILES_DIRS', {})
    config.setdefault('STATICFILES_EXCLUDE', [])
    config.setdefault("URLS", [])

    mod.registry = mod.registries[registry]
    mod.urls = Urls(mod.URLS)
    return mod
