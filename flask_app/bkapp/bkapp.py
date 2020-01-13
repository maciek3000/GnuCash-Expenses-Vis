from bokeh.models import ColumnDataSource, Slider
from bokeh.plotting import figure
from bokeh.server.server import Server
from bokeh.themes import Theme
from bokeh.layouts import column
from ..gnucash.gnucash_db_parser import GnuCashDBParser
from tornado.ioloop import IOLoop
import os

class BokehApp(object):

    def __init__(self, file_path):
        self.datasource = GnuCashDBParser(file_path, names=['Maciek', 'Justyna']).get_df()

    def provide_viz(self, doc):
        agg = self.datasource.groupby(['MonthYear']).sum().reset_index().sort_values()
        source = ColumnDataSource(agg)

        p = figure(width=480, height=480, x_range=agg['MonthYear'])
        p.vbar(x='MonthYear', width=0.9, top='Price', source=source)

def provide_viz(doc):

    from bokeh.sampledata.sea_surface_temperature import sea_surface_temperature

    df = sea_surface_temperature.copy()
    source = ColumnDataSource(data=df)

    plot = figure(x_axis_type='datetime', y_range=(0, 25), y_axis_label='Temperature (Celsius)',
                  title="Sea Surface Temperature at 43.18, -70.43")
    plot.line('time', 'temperature', source=source)

    def callback(attr, old, new):
        if new == 0:
            data = df
        else:
            data = df.rolling('{0}D'.format(new)).mean()
        source.data = ColumnDataSource(data=data).data

    slider = Slider(start=0, end=30, value=0, step=1, title="Smoothing by N Days")
    slider.on_change('value', callback)

    doc.add_root(column(slider, plot))

    doc.theme = Theme(filename=os.path.join(os.path.dirname(os.path.realpath(__file__)), "theme.yaml"))

def bkworker():
    server = Server({'/provide': provide_viz}, io_loop=IOLoop(), allow_websocket_origin=['127.0.0.1:5000', '127.0.0.1:9090'],
                    port=9090)
    server.start()
    server.io_loop.start()

