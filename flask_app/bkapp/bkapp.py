from bokeh.models import ColumnDataSource
from bokeh.plotting import figure, curdoc
from bokeh.server.server import Server
from bokeh.themes import Theme
from ..gnucash.gnucash_db_parser import GnuCashDBParser
from tornado.ioloop import IOLoop
import os

class BokehApp(object):

    def __init__(self, file_path, port, names):
        self.datasource = GnuCashDBParser(file_path, names=names).get_df()
        self.port = port
        self.views = {
            '/trends': self.trends,
            '/some_data': self.some_data
        }
        self.theme = Theme(filename=os.path.join(os.path.dirname(os.path.realpath(__file__)), "theme.yaml"))

    def trends(self, doc):

        agg = self.datasource.groupby(['MonthYear']).sum().reset_index().sort_values(by='MonthYear')
        source = ColumnDataSource(agg)

        p = figure(width=480, height=480, x_range=agg['MonthYear'])
        p.vbar(x='MonthYear', width=0.9, top='Price', source=source)

        doc.add_root(p)
        doc.theme = self.theme

    def some_data(self, doc):
        agg = self.datasource.groupby(['MonthYear']).sum().reset_index().sort_values(by='MonthYear')

        val = agg['Price'].mean()
        print(val)
        doc.template_variables['val'] = val

    def bkworker(self):
        server = Server(self.views, io_loop=IOLoop(),
                        allow_websocket_origin=['127.0.0.1:5000', 'localhost:5000',
                                                '127.0.0.1:9090', 'localhost:9090'],
                        port=self.port)
        server.start()
        server.io_loop.start()
