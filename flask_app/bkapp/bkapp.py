from bokeh.models import ColumnDataSource, NumeralTickFormatter
from bokeh.models.widgets import Dropdown, Select, Div
from bokeh.plotting import figure, curdoc
from bokeh.server.server import Server
from bokeh.themes import Theme
from bokeh.layouts import column, row
from ..gnucash.gnucash_db_parser import GnuCashDBParser
from tornado.ioloop import IOLoop
import os

class BokehApp(object):

    def __init__(self, file_path, port, names):
        self.datasource = GnuCashDBParser(file_path, names=names).get_df()
        self.port = port
        self.views = {
            '/trends': self.trends,
            '/category': self.category,
            '/some_data': self.some_data,
        }
        self.theme = Theme(filename=os.path.join(os.path.dirname(os.path.realpath(__file__)), "theme.yaml"))

    def trends(self, doc):

        agg = self.datasource.groupby(['MonthYear']).sum().reset_index().sort_values(by='MonthYear')
        source = ColumnDataSource(agg)

        p = figure(width=480, height=480, x_range=agg['MonthYear'])
        p.vbar(x='MonthYear', width=0.9, top='Price', source=source, color='#8CA8CD')

        p.xaxis.major_tick_line_color = None
        p.xaxis.minor_tick_line_color = None
        p.yaxis.major_tick_line_color = None
        p.yaxis.minor_tick_line_color = None

        p.yaxis[0].formatter = NumeralTickFormatter(format="0.0a")

        p.xaxis.axis_line_color = "#C7C3C3"
        p.yaxis.axis_line_color = "#C7C3C3"

        p.xaxis.major_label_text_color = "#8C8C8C"
        p.yaxis.major_label_text_color = "#8C8C8C"

        doc.add_root(p)
        doc.theme = self.theme

    def category(self, doc):

        unique_categories = self.datasource['Category'].unique().tolist()
        unique_categories.sort()

        months = self.datasource['MonthYear'].unique().tolist()
        months.sort()

        df = self.datasource[self.datasource['Category'] == unique_categories[0]]
        agg = df.groupby(['MonthYear']).sum().reset_index().sort_values(by='MonthYear')
        source = ColumnDataSource(data=agg)

        p = figure(width=360, height=360, x_range=months)
        p.vbar(x='MonthYear', top='Price', width=0.9, source=source, color='#8CA8CD')

        p.xaxis.major_tick_line_color = None
        p.xaxis.minor_tick_line_color = None
        p.yaxis.major_tick_line_color = None
        p.yaxis.minor_tick_line_color = None

        p.yaxis[0].formatter = NumeralTickFormatter(format="0.0a")

        p.xaxis.axis_line_color = "#C7C3C3"
        p.yaxis.axis_line_color = "#C7C3C3"

        p.xaxis.major_label_text_color = "#8C8C8C"
        p.yaxis.major_label_text_color = "#8C8C8C"

        def callback(attr, old, new):
            if new != old:
                df = self.datasource[self.datasource['Category'] == new]
                agg = df.groupby(['MonthYear']).sum().reset_index().sort_values(by='MonthYear')
                source.data = ColumnDataSource(agg).data

        #menu = list(zip(unique_categories, unique_categories))
        dropdown = Select(title='Category:', value=unique_categories[0], options=unique_categories)
        dropdown.on_change('value', callback)

        doc.add_root(column(dropdown, p))
        doc.theme = self.theme

    def some_data(self, doc):
        agg = self.datasource.groupby(['MonthYear']).sum().reset_index()

        val = agg['Price'].mean()
        text = 'Average expenses are: <p style="color:#9c2b19"> {} </p>'.format(val)
        t = Div(text=text, id="some_data_text")

        doc.add_root(t)
        doc.theme = self.theme

    def bkworker(self):
        server = Server(self.views, io_loop=IOLoop(),
                        allow_websocket_origin=['127.0.0.1:5000', 'localhost:5000',
                                                '127.0.0.1:9090', 'localhost:9090'],
                        port=self.port)
        server.start()
        server.io_loop.start()
