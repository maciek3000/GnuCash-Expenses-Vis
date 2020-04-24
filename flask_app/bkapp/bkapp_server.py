from tornado.ioloop import IOLoop
import os

from bokeh.server.server import Server
from bokeh.themes import Theme

from .bkapp import BokehApp


class BokehServer(object):
    """
    Bokeh Server Wrapper for Expenses Visualizations.

    Wrapped inside is BokehApp, which creates main Visualizations that later are embedded into
    Flask Views. All of Bokeh Views follow simple pattern of calling BokehApp with appropriate parameters
    (which later could be dynamically obtained, e.g. column names) and then adding roots to the document.

    To add a visualization (view), the function has to be defined and then added into self.views dictionary.
    """

    def __init__(self, port, col_mapping, expense_dataframe, income_dataframe, server_date,
                 monthyear_format, category_sep):

        self.bkapp = BokehApp(expense_dataframe, income_dataframe,
                              col_mapping, monthyear_format, server_date, category_sep)
        self.port = port
        self.views = {
            '/trends': self.trends,
            '/category': self.category,
            '/overview': self.overview,
            '/settings_categories': self.settings_categories,
            '/settings_month_range': self.settings_month_range,
        }

        self.theme = Theme(filename=os.path.join(os.path.dirname(os.path.realpath(__file__)), "theme.yaml"))

    def settings_month_range(self, doc):

        fig = self.bkapp.settings_month_range()
        doc.add_root(fig)
        doc.theme = self.theme

    def settings_categories(self, doc):

        fig = self.bkapp.settings_categories()
        doc.add_root(fig)
        doc.theme = self.theme

    def trends(self, doc):

        fig = self.bkapp.trends_gridplot()
        doc.add_root(fig)
        doc.theme = self.theme

    def category(self, doc):

        fig = self.bkapp.category_gridplot()
        doc.add_root(fig)
        doc.theme = self.theme

    def overview(self, doc):
        fig = self.bkapp.overview_gridplot()
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
