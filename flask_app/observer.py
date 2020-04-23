# https://stackoverflow.com/questions/48336820/using-decorators-to-implement-observer-pattern-in-python3


class Observer(object):
    """Implementation of Listener pattern.

        Object exposes methods:
            - register - used to register given function as a callback
            - notify - upon calling, calls all callbacks that were registered.

        Additionally, Object has classmethod: watched_property. This is an implementation of @property decorator,
        that calls .notify function of the observer upon change of the property (setting new values).
    """

    def __init__(self):
        self.callbacks = []

    def notify(self, *args, **kwargs):
        """Function that is called upon being triggered by the Event."""
        for callback in self.callbacks:
            callback(*args, **kwargs)

    def register(self, callback):
        """Decorator used to register functions as callbacks."""
        self.callbacks.append(callback)
        return callback

    @classmethod
    def watched_property(cls, observer, key, obj_to_notify):
        """Function that bounds given property (attribute) to an observer.

            Accepts 3 String arguments:
                - observer name - attribute where the observer is stored;
                - key - name of the property being changed;
                - obj_to_notify - object that will be calling notify function.

            Function creates new key: _key and uses it to set actual attributes.
            Getter is a standard getattr.

            Setter sets new value to the actual_key attribute and additionally, triggers notify function
            of the observer. However, notify function isn't called by the object that has the observable properties,
            but rather some other object to which exists reference in the Observable object.
            As long as Object that will call notify function is referenced anywhere in the Observable object, it
            should work fine.
        """
        actual_key = "_{}".format(key)

        def getter(obj):
            return getattr(obj, actual_key)

        def setter(obj, value):
            obs = getattr(obj, observer)
            setattr(obj, actual_key, value)
            obj_notify = getattr(obj, obj_to_notify)
            obs.notify(obj_notify, key, value)

        return property(fget=getter, fset=setter)
