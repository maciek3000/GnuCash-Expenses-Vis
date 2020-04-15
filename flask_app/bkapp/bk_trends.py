import pandas as pd
import numpy as np
from datetime import datetime

from bokeh.models import ColumnDataSource, Circle, RadioGroup, FactorRange, LinearColorMapper
from bokeh.models.widgets import Div
from bokeh.plotting import figure
from bokeh.layouts import row, column

from .pandas_functions import unique_values_from_column

class Trends(object):

    info_title = "Expenses Info"
    info_stats = """
    <div>Average: <span>{mean:.2f}</span></div>
    <div>Median: <span>{median:.2f}</span></div>
    <div>Minimum: <span>{min:.2f}</span></div>
    <div>Maximum: <span>{max:.2f}</span></div>
    <div>Standard Deviation <span>{std:.2f}</span></div>
    """

    heatmap_title = "Heatmap"
    heatmap_radio_buttons = ["Transactions", "Price"]

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
        self.current_expense_df = None

        # State Variables
        self.months = None
        self.heatmap_color_map = None

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
        self.current_expense_df = expense_dataframe
        self.months = unique_values_from_column(expense_dataframe, self.monthyear)

        self.initialize_gridplot()
        self.update_gridplot()

        grid = column(
            row(
                column(
                    self.grid_elem_dict[self.g_info_title],
                    self.grid_elem_dict[self.g_info_statistics]
                ),
                column(
                    self.grid_elem_dict[self.g_line_plot]
                )
            ),
            row(
                column(
                    self.grid_elem_dict[self.g_heatmap_title],
                    self.grid_elem_dict[self.g_heatmap_buttons],
                    self.grid_elem_dict[self.g_heatmap]
                )
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
        elem_dict[self.g_heatmap_buttons] = RadioGroup(labels=self.heatmap_radio_buttons, active=0)

        source_dict[self.g_heatmap] = self.__create_heatmap_source()
        elem_dict[self.g_heatmap] = self.__create_heatmap(source_dict[self.g_heatmap])

        self.grid_elem_dict = elem_dict
        self.grid_source_dict = source_dict

    def update_gridplot(self):
        self.__update_info_stats()
        self.__update_line_plot()
        self.__update_heatmap()

    # ========== Creation of Grid Elements ========== #

    def __create_line_plot_source(self):

        new_format = "%b-%Y"
        formatted_months = [datetime.strptime(month, self.monthyear_format).strftime(new_format) for month in self.months]

        data = {
            "x": formatted_months,
            "y": [1]*len(self.months)  # ensuring same length of data values
        }

        source = ColumnDataSource(
            data=data
        )

        return source

    def __create_line_plot(self, source):

        base_color = self.color_map.base_color

        p = figure(width=620, height=340, x_range=source.data["x"], toolbar_location="right", tools=["box_select"])

        p.line(x="x", y="y", source=source, line_width=5, color=base_color)
        scatter = p.circle(x="x", y="y", source=source, color=base_color)

        selected_circle = Circle(fill_alpha=1, line_color=base_color, fill_color=base_color)
        nonselected_circle = Circle(fill_alpha=0.2, line_alpha=0.2, line_color=base_color, fill_color=base_color)

        scatter.selection_glyph = selected_circle
        scatter.nonselection_glyph = nonselected_circle

        p.axis.minor_tick_line_color = None
        p.axis.major_tick_line_color = None
        p.axis.axis_line_color = self.color_map.background_gray
        p.axis.major_label_text_color = self.color_map.label_text_color
        p.axis.major_label_text_font_size = "13px"
        p.xaxis.major_label_orientation = 0.785  # 45 degrees in radians

        return p

    def __create_heatmap_source(self):

        data = {
            "week": [0],
            "weekday": [0],
            "value": [0],
            "date": [0]
        }

        source = ColumnDataSource(
            data=data
        )

        return source

    def __create_heatmap(self, source):



        grouped = [(x.split("-")[0], x.split("-")[1]) for x in self.months]


        y_weekdays = [str(x) for x in range(6, -1, -1)]
        x_weeks = list(map(lambda x: str(x), range(1, 53)))

        rgb = self.color_map.base_color_rgb
        palette = [(rgb[0], rgb[1], rgb[2], x) for x in np.linspace(0.5, 1.0, 5)]
        print(palette)
        palette = [(100, 100, 100), (200, 200, 200)]
        # palette = ["#75968f", "#a5bab7", "#c9d9d3", "#e2e2e2", "#dfccce", "#ddb7b1", "#cc7878", "#933b41", "#550b1d"]
        cmap = LinearColorMapper(palette=palette, low=0, high=1)

        p = figure(
            height=280, width=1080,
            x_range=x_weeks, y_range=y_weekdays,
            x_axis_location="above",
            tooltips=[("date", "@date"), ("price", "@value")]
        )

        p.rect(
            x="week", y="weekday", width=1, height=1,
            source=source,  fill_color={
                "field": "value", "transform": cmap
            },
            line_color=None
        )

        self.heatmap_color_map = cmap
        return p

    # ========== Updating Grid Elements ========== #

    def __update_info_stats(self):

        stats = self.current_expense_df.groupby(by=[self.monthyear]).sum()[self.price].describe()
        stats["median"] = stats["50%"]

        new_text = self.info_stats.format(**stats)

        self.grid_elem_dict[self.g_info_statistics].text = new_text

    def __update_line_plot(self):

        new_values = self.current_expense_df.groupby(by=[self.monthyear]).sum()[self.price].tolist()

        source = self.grid_source_dict[self.g_line_plot]
        source.data["y"] = new_values

        fig = self.grid_elem_dict[self.g_line_plot]
        fig.y_range.start = 0
        fig.y_range.end = np.nanmax(new_values) + 0.01 * np.nanmax(new_values)

    def __update_heatmap(self):

        data = self.grid_source_dict[self.g_heatmap].data
        fig = self.grid_elem_dict[self.g_heatmap]

        grouped = self.current_expense_df.groupby(by=[self.date]).sum().reset_index()
        grouped["weekday"] = grouped[self.date].dt.weekday
        grouped["month"] = grouped[self.date].dt.month.apply(lambda x: "{x:02d}".format(x=x))
        grouped["year"] = grouped[self.date].dt.year.astype(str)
        grouped["week"] = grouped[self.date].dt.weekofyear.apply(lambda x: "{x:02d}".format(x=x))

        zipped = list(zip(grouped["year"].tolist(), grouped["week"].tolist()))

        self.heatmap_color_map.high = grouped[self.price].max()
        self.heatmap_color_map.low = 0

        zipped_range = sorted(list(set(zipped)))

        fig.x_range = FactorRange(*zipped_range)

        # df = self.current_expense_df.copy()
        # df["weekday"] = df[self.date].dt.weekday
        # df["Month"] = df[self.date].dt.month.apply(lambda x: "{x:02d}".format(x=x))
        # df["Year"] = df[self.date].dt.year.astype("str")

        data["year"] = grouped["year"]
        data["date"] = grouped[self.date].dt.strftime("%d-%b-%Y")
        data["week"] = zipped
        data["weekday"] = grouped["weekday"]
        data["value"] = grouped[self.price]


        # grouped = df.groupby(by=["Year", "Month"])