from collections.abc import Mapping

class Entry(Mapping):

    def __init__(self, metadata, **kwargs):
        self.__dict__.update(kwargs)
        self.__data = metadata

    def __contains__(self, key):
        if '__' not in key:
            return key in self.__data

        v, a = key.split('__')
        if v not in self.__data:
            return False
        return hasattr(self.__data[v], a)

    def __getitem__(self, key):
        if '__' not in key:
            return self.__data[key]
        v, a = key.split('__')
        return getattr(self.__data[v], a)

    def __iter__(self):
        return iter(self.__data)

    def __len__(self):
        return len(self.__data)
