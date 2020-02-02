from flask_app import create_app


def test_create_app():
    """Basic testing if factory function of creating Flask app works"""

    assert not create_app().testing
    assert create_app({"TESTING":True}).testing
