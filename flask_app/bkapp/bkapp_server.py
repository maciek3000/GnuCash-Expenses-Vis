from tornado.ioloop import IOLoop
import os

from bokeh.server.server import Server
from bokeh.themes import Theme

from ..gnucash.gnucash_db_parser import GnuCashDBParser
from .bkapp import BokehApp


class BokehServer(object):
    """
    Bokeh Server Wrapper for Expenses Visualizations.

    Wrapped inside is BokehApp, which creates main Visualizations that later are embedded into
    Flask Views. All of Bokeh Views follow simple pattern of calling BokehApp with appropriate parameters
    (which later could be dynamically obtained, e.g. column names) and then adding roots to the document.

    To add a visualization (view), the function has to defined and then added into self.views dictionary.
    """

    def __init__(self, file_path, port):
        self.bkapp = BokehApp(GnuCashDBParser(file_path).get_df())
        self.port = port
        self.views = {
            '/trends': self.trends,
            '/category': self.category,
            '/some_data': self.some_data,
            '/settings': self.settings,
            '/test_table': self.test_table,
        }

        self.theme = Theme(filename=os.path.join(os.path.dirname(os.path.realpath(__file__)), "theme.yaml"))

    def settings(self, doc):

        fig = self.bkapp.settings("ALL_CATEGORIES")
        doc.add_root(fig)
        doc.theme = self.theme

    def some_data(self, doc):

        fig = self.bkapp.some_data()
        doc.add_root(fig)
        doc.theme = self.theme

    def trends(self, doc):

        fig = self.bkapp.trends("MonthYear")
        doc.add_root(fig)
        doc.theme = self.theme

    def category(self, doc):

        fig = self.bkapp.category("Category", "MonthYear", "Price")
        doc.add_root(fig)
        doc.theme = self.theme

    def test_table(self, doc):

        fig = self.bkapp.test_table()
        doc.add_root(fig)
        doc.theme = self.theme

    def bkworker(self):
        """Called in a separate Thread by flask_app to serve Bokeh Visualizations."""

        server = Server(self.views, io_loop=IOLoop(),
                        allow_websocket_origin=['127.0.0.1:5000', 'localhost:5000',
                                                '127.0.0.1:9090', 'localhost:9090'],
                        port=self.port)
        server.start()
        server.io_loop.start()
