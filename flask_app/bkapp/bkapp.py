from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from bokeh.server.server import Server
from bokeh.themes import Theme
from ..gnucash.gnucash_db_parser import GnuCashDBParser
from tornado.ioloop import IOLoop
import os

class BokehApp(object):

    def __init__(self, file_path, port, names):
        self.datasource = GnuCashDBParser(file_path, names=names).get_df()
        self.port = port

    def provide_viz(self, doc):

        agg = self.datasource.groupby(['MonthYear']).sum().reset_index().sort_values(by='MonthYear')
        source = ColumnDataSource(agg)

        p = figure(width=480, height=480, x_range=agg['MonthYear'])
        p.vbar(x='MonthYear', width=0.9, top='Price', source=source)

        doc.add_root(p)
        doc.theme = Theme(filename=os.path.join(os.path.dirname(os.path.realpath(__file__)), "theme.yaml"))

    def bkworker(self):
        server = Server({'/provide': self.provide_viz}, io_loop=IOLoop(), allow_websocket_origin=['127.0.0.1:5000'],
                        port=self.port)
        server.start()
        server.io_loop.start()
