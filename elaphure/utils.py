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
