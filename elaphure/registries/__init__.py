from collections.abc import Mapping

class Entry(Mapping):

    def __init__(self, metadata, **kwargs):
        self.__dict__.update(kwargs)
        self.__data = metadata

    def __getitem__(self, key):
        return self.__data[key]

    def __iter__(self):
        return iter(self.__data)

    def __len__(self):
        return len(self.__data)
