import pytest

def test_register(observer):
    """Testing if registering functions in the observer works correctly."""

    @observer.register
    def new_func():
        pass
    f = new_func

    assert f in observer.callbacks


def test_notify(observer):
    """Testing if notify function of observer object works correctly."""

    i = 0

    @observer.register
    def new_func():
        nonlocal i
        i = 1
    observer.notify()

    assert i == 1


def test_watched_property(observer):
    """Testing if changes to watched property trigger notifications to registered callbacks."""

    # Observing class with register "notify" function
    class Do(object):
        obs = observer

        def __init__(self):
            self.result = 0

        @obs.register
        def new_func(self, key, value):
            self.result = 1

    # class with property being observed
    class Observed(object):
        x = observer.watched_property("observer", "x", "parent")

        def __init__(self, obs, par):
            self.observer = obs
            self.parent = par

    parent = Do()
    observed = Observed(observer, parent)
    observed.x = 10

    assert parent.result == 1
