import pandas as pd
import numpy as np
from datetime import datetime
import random
import string

import bokeh
from bokeh.models import ColumnDataSource, Circle, RadioGroup, FactorRange, LinearColorMapper, FuncTickFormatter
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

    line_plot_title = "Average Expenses"
    histogram_title ="Daily Expenses Histogram"

    heatmap_title = "Heatmap"
    heatmap_radio_buttons = ["Price", "Transactions"]

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

        # Heatmap Variables
        self.heatmap_color_mapper = None
        self.heatmap_df_column_dict = None

        self.g_info_title = "Info Title"
        self.g_info_statistics = "Expenses Stats"
        self.g_line_plot = "Line Plot"
        self.g_histogram = "Density Plot"
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
        initial_heatmap_button_selected = 0

        self.initialize_gridplot(initial_heatmap_button_selected)
        self.update_gridplot(initial_heatmap_button_selected)

        def callback(attr, old, new):
            if new != old:
                self.__update_heatmap_values(new)

        self.grid_elem_dict[self.g_heatmap_buttons].on_change("active", callback)

        grid = column(
            row(
                column(
                    self.grid_elem_dict[self.g_info_title],
                    self.grid_elem_dict[self.g_info_statistics]
                ),
                column(
                    row(
                        self.grid_elem_dict[self.g_line_plot],
                        self.grid_elem_dict[self.g_histogram]
                    )
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

    def initialize_gridplot(self, initial_heatmap_choice):

        elem_dict = {}
        source_dict = {}

        elem_dict[self.g_info_title] = Div(text=self.info_title)
        elem_dict[self.g_info_statistics] = Div(text=self.info_stats)

        source_dict[self.g_line_plot] = self.__create_line_plot_source()
        elem_dict[self.g_line_plot] = self.__create_line_plot(source_dict[self.g_line_plot])

        source_dict[self.g_histogram] = self.__create_histogram_source()
        elem_dict[self.g_histogram] = self.__create_histogram(source_dict[self.g_histogram])

        elem_dict[self.g_heatmap_title] = Div(text=self.heatmap_title)
        elem_dict[self.g_heatmap_buttons] = RadioGroup(labels=self.heatmap_radio_buttons, active=initial_heatmap_choice)

        source_dict[self.g_heatmap] = self.__create_heatmap_source()
        elem_dict[self.g_heatmap] = self.__create_heatmap(source_dict[self.g_heatmap])

        self.grid_elem_dict = elem_dict
        self.grid_source_dict = source_dict

    def update_gridplot(self, heatmap_choice):
        self.__update_info_stats()
        self.__update_line_plot()
        self.__update_histogram()
        self.__update_heatmap(heatmap_choice)

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

        base_color = self.color_map.contrary_color

        p = figure(width=620, height=340, x_range=source.data["x"], toolbar_location=None, tools=["box_select"])

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

    def __create_histogram_source(self):

        data = {
            "hist": [0],
            "top_edges": [0],
            "bottom_edges": [0],
        }

        source = ColumnDataSource(data=data)

        return source

    def __create_histogram(self, source):

        p = figure(width=340, height=340)

        p.quad(left=0, right="hist", top="top_edges", bottom="bottom_edges",
               source=source, fill_color=self.color_map.link_text_color, line_color=self.color_map.base_color)

        p.axis.major_tick_line_color = None
        p.axis.minor_tick_line_color = None
        p.xaxis.visible = False
        p.axis.axis_line_color = self.color_map.background_gray
        p.axis.major_label_text_color = self.color_map.label_text_color
        p.axis.major_label_text_font_size = "13px"

        return p

    def __create_heatmap_source(self):

        data = {
            "week": [0],
            "weekday": [0],
            "value": [0],
            "date": [0],
            "price": [0],
            "count": [0]
        }

        source = ColumnDataSource(
            data=data
        )

        return source

    def __create_heatmap(self, source):


        y_weekdays = [str(x) for x in range(6, -1, -1)]  # there is always 7 days in a week
        x_weeks = list(map(lambda x: str(x), range(1, 53)))

        palette = list(reversed([self.color_map.base_color_tints[i] for i in range(0, 10, 2)]))
        cmap = LinearColorMapper(palette=palette, low=0, high=1)
        cmap.low_color = "white"

        p = figure(
            height=280, width=1080,
            x_range=x_weeks, y_range=y_weekdays,
            x_axis_location="above",
            tooltips=[("date", "@date"), ("price", "@price{0,0.00}"), ("count", "@count")],
            toolbar_location=None
        )

        p.rect(
            x="week", y="weekday", width=1.01, height=0.55,
            source=source,  fill_color={
                "field": "value", "transform": cmap
            },
            line_color=None
        )

        p.axis.minor_tick_line_color = None
        p.axis.major_tick_line_color = None
        p.axis.axis_line_color = "white"
        p.axis.major_label_text_color = self.color_map.label_text_color
        p.axis.major_label_text_font_size = "13px"

        p.axis.group_text_color = self.color_map.label_text_color
        p.axis.group_text_font_size = "13px"

        p.yaxis.major_label_standoff = 25

        weekday_mapper = {
            0: "Mon",
            1: "Tue",
            2: "Wed",
            3: "Thu",
            4: "Fri",
            5: "Sat",
            6: "Sun"
        }

        weekday_formatter = FuncTickFormatter(args={"weekday_mapper": weekday_mapper}, code="""
            return weekday_mapper[tick];
        """)

        p.yaxis.formatter = weekday_formatter
        self.heatmap_color_mapper = cmap

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

    def __update_histogram(self):
        hist, edges = np.histogram(self.current_expense_df[self.price], density=True, bins=50)

        source = self.grid_source_dict[self.g_histogram]

        source.data["hist"] = hist
        source.data["top_edges"] = edges[:-1]
        source.data["bottom_edges"] = edges[1:]


    def __update_heatmap(self, selected_index):

        self.heatmap_df_column_dict = self.__create_new_column_names(self.current_expense_df.reset_index().columns)
        aggregated = self.__aggregated_expense_df(self.current_expense_df)
        week_to_month = self.__create_first_week_to_month_dict(aggregated)

        column_names = self.heatmap_df_column_dict
        data = self.grid_source_dict[self.g_heatmap].data
        fig = self.grid_elem_dict[self.g_heatmap]

        # pd.Series as .unique() returns ndarray
        x_range = pd.Series(aggregated[column_names["week_str"]].unique()).sort_values().tolist()
        fig.x_range.factors = x_range

        data["date"] = aggregated[column_names["date_str"]]
        data["week"] = aggregated[column_names["week_str"]]
        data["weekday"] = aggregated[column_names["weekday_str"]]
        data["price"] = aggregated[self.price]
        data["count"] = aggregated[column_names["count"]]

        self.__update_heatmap_values(selected_index)

        func_tick_dict = self.__create_first_week_to_month_dict(aggregated)

        formatter = FuncTickFormatter(args={"d": func_tick_dict}, code="""
                    var return_tick;
                    return_tick = "";
                    if (tick in d) {
                        console.log(tick);
                        return_tick = d[tick];
                    }
                    return return_tick;
                """)

        fig.xaxis.formatter = formatter

    def __update_heatmap_values(self, selected_index):
        # 0 - Price, 1 - Products
        data = self.grid_source_dict[self.g_heatmap].data

        if selected_index == 0:
            values = data["price"]
        elif selected_index == 1:
            values = data["count"]
        else:
            raise Exception("How did I get here?")

        high = values.max()
        low = values.min()
        data["value"] = values

        self.heatmap_color_mapper.high = high
        self.heatmap_color_mapper.low = low

    def __create_new_column_names(self, columns, n=8):

        default_col_names = {
            "year": "year",
            "year_str": "year_str",
            "month": "month",
            "month_str": "month_str",
            "weekday": "weekday",
            "weekday_str": "weekday_str",
            "week": "week",
            "week_str": "week_str",
            "date_str": "date_str",
            "count": "count"
        }

        for key, item in default_col_names.items():

            new_value = item
            while new_value in columns:
                new_value = "".join(random.choices(string.ascii_uppercase + string.ascii_lowercase, k=n))

            default_col_names[key] = new_value

        return default_col_names

    def __aggregated_expense_df(self, dataframe):

        column_dict = self.heatmap_df_column_dict

        agg = dataframe.groupby(by=[self.date])
        agg_sum = agg.sum()
        agg_count = agg.count()
        agg_sum[column_dict["count"]] = agg_count[self.price]

        aggregated = agg_sum.reset_index().sort_values(by=self.date, ascending=True)

        aggregated[column_dict["year"]] = aggregated[self.date].dt.year
        aggregated[column_dict["month"]] = aggregated[self.date].dt.month
        aggregated[column_dict["weekday"]] = aggregated[self.date].dt.weekday

        # string columns
        aggregated[column_dict["year_str"]] = aggregated[column_dict["year"]].astype(str)
        aggregated[column_dict["month_str"]] = aggregated[self.date].dt.strftime("%b")
        aggregated[column_dict["weekday_str"]] = aggregated[column_dict["weekday"]].astype(str)
        aggregated[column_dict["date_str"]] = aggregated[self.date].dt.strftime("%d-%b-%Y")

        # first day is counted as the first Monday in the dataframe
        start_date = aggregated[aggregated[column_dict["weekday"]] == 0][self.date].min()

        # weeks are defined as the difference between first Monday and the date and then floor divided by 7
        # there may be a week counted as -1, but it is not a problem
        aggregated[column_dict["week"]] = ((aggregated[self.date] - start_date) // 7).dt.days

        # padded to 4 digits to avoid sorting issues
        # assuming regular year to have 52 weeks, df would have to have ~192 years of data to break sorting
        aggregated[column_dict["week_str"]] = aggregated[column_dict["week"]].apply(lambda x: "{x:04d}".format(x=x))

        return aggregated

    def __create_first_week_to_month_dict(self, agg):
        column_dict = self.heatmap_df_column_dict

        monday_agg = agg[agg[column_dict["weekday"]] == 0]
        year_month_agg = monday_agg.groupby(column_dict["year_str"]).first()[
            column_dict["month"]].reset_index().set_index(column_dict["month"])

        month_agg = monday_agg.groupby(column_dict["month"]).first()[
            [column_dict["week_str"], column_dict["month_str"]]]

        month_agg[column_dict["year_str"]] = year_month_agg

        func = lambda x: x[column_dict["month_str"]] if pd.isna(x[column_dict["year_str"]]) else "({}) {}".format(
                x[column_dict["year_str"]], x[column_dict["month_str"]])

        month_agg[column_dict["month_str"]] = month_agg.apply(func, axis=1)

        month_to_week_dict = month_agg.set_index(column_dict["month_str"])[column_dict["week_str"]].to_dict()
        week_to_month_dict = {item: key for key, item in month_to_week_dict.items()}

        return week_to_month_dict
