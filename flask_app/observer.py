# https://stackoverflow.com/questions/48336820/using-decorators-to-implement-observer-pattern-in-python3


class Observer(object):
    def __init__(self):
        self.callbacks = []

    def notify(self, *args, **kwargs):
        for callback in self.callbacks:
            callback(*args, **kwargs)

    def register(self, callback):
        self.callbacks.append(callback)
        return callback

    @classmethod
    def watched_property(cls, observer, key):
        actual_key = "_{}".format(key)

        def getter(obj):
            return getattr(obj, actual_key)

        def setter(obj, value):
            obs = getattr(obj, observer)
            setattr(obj, actual_key, value)
            obs.notify(obj, key, value)

        return property(fget=getter, fset=setter)
