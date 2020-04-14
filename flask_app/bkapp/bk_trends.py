import pandas as pd
import numpy as np

from bokeh.models import ColumnDataSource, Circle
from bokeh.models.widgets import Div
from bokeh.plotting import figure
from bokeh.layouts import row, column

class Trends(object):

    info_title = "Expenses Info"
    info_stats = """
    <div>Average: <span>{avg}</span></div>
    <div>Median: <span>{median}</span></div>
    <div>Minimum: <span>{min}</span></div>
    <div>Maximum: <span>{max}</span></div>
    <div>Standard Deviation <span>std</span></div>
    """

    heatmap_title = "Heatmap"

    def __init__(self, category_colname, monthyear_colname, price_colname, product_colname,
                 date_colname, currency_colname, shop_colname, month_format, color_mapping):

        # Column Names
        self.category = category_colname
        self.monthyear = monthyear_colname
        self.price = price_colname
        self.product = product_colname
        self.date = date_colname
        self.currency = currency_colname
        self.shop = shop_colname

        # MonthYear Formatting
        self.monthyear_format = month_format  # formatting of date in MonthYear column

        # ColorMap
        self.color_map = color_mapping  # ColorMap object exposing attributes with specific colors

        # DataFrames
        self.original_expense_df = None  # original expense dataframe passed to the gridplot function

        # State Variables
        self.months = None

        self.g_info_title = "Info Title"
        self.g_info_statistics = "Expenses Stats"
        self.g_line_plot = "Line Plot"
        self.g_heatmap_title = "Heatmap Title"
        self.g_heatmap_buttons = "Heatmap Buttons"
        self.g_heatmap = "Heatmap"

        # Grid Elements Dicts
        self.grid_elem_dict = None
        self.grid_source_dict = None

    def gridplot(self, expense_dataframe):

        # Trends ########################
        # Info                  # Hover Tool                    # Line Plot Title
        # Average Expenses      # Expenses                      # Line Plot with 2 lines (raw and % change)
        # Median                # Higher/Lower % than Average   # Line Plot with 2 lines (raw and % change)
        # Minimum               # Transactions Number           # Line Plot with 2 lines (raw and % change)
        # Maximum               #                               # Line Plot with 2 lines (raw and % change)
        # Standard Deviation    #                               # Line Plot with 2 lines (raw and % change)
        ###########################
        # HeatMap Title
        # Heatmap Options (Transactions # or Price Sum)
        # # # # # # # # #
        # Heatmap
        # Heatmap
        # Heatmap

        self.original_expense_df = expense_dataframe

        self.initialize_gridplot()
        self.update_gridplot()

        grid = row(
            column(
                self.grid_elem_dict[self.g_info_title],
                self.grid_elem_dict[self.g_info_statistics]
            ),
            column(
                self.grid_elem_dict[self.g_line_plot]
            )
        )

        return grid

    def initialize_gridplot(self):

        elem_dict = {}
        source_dict = {}

        elem_dict[self.g_info_title] = Div(text=self.info_title)
        elem_dict[self.g_info_statistics] = Div(text=self.info_stats)

        source_dict[self.g_line_plot] = self.__create_line_plot_source()
        elem_dict[self.g_line_plot] = self.__create_line_plot(source_dict[self.g_line_plot])

        elem_dict[self.g_heatmap_title] = Div(text=self.heatmap_title)


        self.grid_elem_dict = elem_dict
        self.grid_source_dict = source_dict

    def update_gridplot(self):
        pass

    # ========== Creation of Grid Elements ========== #

    def __create_line_plot_source(self):

        data = {
            "x": ["a"],
            "y": [1]
        }

        source = ColumnDataSource(
            data=data
        )

        return source

    def __create_line_plot(self, source):

        p = figure(width=580, height=460, x_range=source.data["x"], toolbar_location=None)

        p.line(x="x", y="y", source=source, line_width=5, color="blue")
        scatter = p.scatter(x="x", y="y", source=source)

        selected_circle = Circle(fill_alpha=1)
        nonselected_circle = Circle(fill_alpha=0.2)

        scatter.selection_glyph = selected_circle
        scatter.nonselection_glyph = nonselected_circle

        return p

