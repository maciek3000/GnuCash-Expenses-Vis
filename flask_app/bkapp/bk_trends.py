import pandas as pd
import numpy as np
import random
import string
from datetime import datetime

from bokeh.models import ColumnDataSource, Circle, RadioGroup, LinearColorMapper, FuncTickFormatter
from bokeh.models import NumeralTickFormatter, ColorBar, PrintfTickFormatter, BasicTicker, Label

from bokeh.models.widgets import Div
from bokeh.plotting import figure
from bokeh.layouts import row, column

from .pandas_functions import unique_values_from_column


class Trends(object):
    """Trends Object that provides methods to generate gridplot used in Trends View in flask_app.

                Object expects:
                    - appropriate column names for the expense DataFrame that will be provided to other methods;
                    - month_format string, which represents in what string format date in monthyear column was saved;
                    - color_map ColorMap object, which exposes attributes for specific colors.

                Main methods are:
                    - gridplot() : workhorse of the Object, creates elements gridplot, creates callbacks and updates
                        appropriate elements of the grid. Returns grid that can be served in the Bokeh Server.
                    - initalize_grid_elements() : creates all elements and data sources of gridplot and assigns them
                        appropriately to self.grid_elem_dict and self.grid_source_dict
                    - update_gridplot function, called when the whole gridplot needs to be updated;
                    - update_gridplot_on_month_selection_change, called when the selection of months on the line plot
                        is changed.

                Attributes of the instance Object are described as single-line comments in __init__() method;
                Other attributes of the class are HTML templates or other text used in Div or other Web Elements
                creation; they are described in corresponding functions that update those Elements.
            """

    monthly_title = "Monthly"
    daily_title = "Daily"
    stats_template = """
    <div>Average: <span>{mean:,.2f}</span></div>
    <div>Median: <span>{median:,.2f}</span></div>
    <div>Minimum: <span>{min:,.2f}</span></div>
    <div>Maximum: <span>{max:,.2f}</span></div>
    <div>Standard Deviation: <span>{std:,.2f}</span></div>
    """

    line_plot_title = "Monthly Expenses"
    histogram_title = "Daily Expenses Histogram"

    heatmap_title = "Heatmap"
    heatmap_radio_buttons = ["Price", "# of Products"]

    line_plot_tooltip = """
        <div class="hover_tooltip" id="hover_line_plot">
            <div>
                <span>Month: </span>
                <span>@x</span>
            </div>
            <div>
                <span>Value: </span>
                <span>@y{0.00}</span>
            </div>
        </div>
    """

    heatmap_plot_tooltip = """
        <div class="hover_tooltip" id="hover_heatmap">
            <div>
                <span>Date: </span>
                <span>@date</span>
            </div>
            <div>
                <span>Price: </span>
                <span>@price{0,0.00}</span>
            </div>
            <div>
                <span># of Products: </span>
                <span>@count</span>
            </div>
        </div>
    """

    interaction_message = "Select MonthPoints on the Plot to interact with the Dashboard"

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
        self.chosen_months = None

        # Heatmap Variables
        self.heatmap_color_mapper = None
        self.heatmap_df_column_dict = None

        # Identifiers for Grid Elements and DataSources
        self.g_monthly_title = "Monthly Title"
        self.g_monthly_statistics = "Monthly Stats"
        self.g_daily_title = "Daily Title"
        self.g_daily_statistics = "Daily Stats"
        self.g_line_plot = "Line Plot"
        self.g_histogram = "Density Plot"
        self.g_heatmap_title = "Heatmap Title"
        self.g_heatmap_buttons = "Heatmap Buttons"
        self.g_heatmap = "Heatmap"

        # Grid Elements Dicts
        self.grid_elem_dict = None
        self.grid_source_dict = None

    def gridplot(self, expense_dataframe):
        """Main function of Trends Object. Creates Gridplot with appropriate Visualizations and Elements and
                    returns it.

                    Accepts expense_dataframe argument that should be a Dataframe representing Expenses.

                    The function does several things:
                        - initializes the gridplot,
                        - sets Month property to be a collection of all months present in expense_dataframe,
                        - set .chosen_months property to .months (as during initialization, all months are selected)
                        - chooses initial Heatmap Radio Button selection
                        - sets callback on chosen grid elements, so that changes made by the user are then reflected
                            to other grid elements
                        - returns created grid as a bokeh layout, that can be later used in a Bokeh Server
                """

        self.original_expense_df = expense_dataframe
        self.current_expense_df = expense_dataframe
        self.months = unique_values_from_column(expense_dataframe, self.monthyear)
        self.chosen_months = self.months  # initially all months are selected

        initial_heatmap_button_selected = 0

        self.initialize_gridplot(initial_heatmap_button_selected)
        self.update_gridplot(initial_heatmap_button_selected)

        def heatmap_aggregation_callback(attr, old, new):
            if new != old:
                self.__update_heatmap_values(new)

        self.grid_elem_dict[self.g_heatmap_buttons].on_change("active", heatmap_aggregation_callback)

        def line_plot_selection_callback(attr, old, new):
            new_indices = set(new)
            old_indices = set(old)

            if new_indices != old_indices:
                self.__update_chosen_months(new_indices)
                self.update_gridplot_on_month_selection_change()

        self.grid_source_dict[self.g_line_plot].selected.on_change("indices", line_plot_selection_callback)

        # Gridplot
        grid = column(
            row(
                column(
                    self.grid_elem_dict[self.g_monthly_title],
                    self.grid_elem_dict[self.g_monthly_statistics],
                    self.grid_elem_dict[self.g_daily_title],
                    self.grid_elem_dict[self.g_daily_statistics],
                    css_classes=["info_column"]
                ),
                column(
                    row(
                        self.grid_elem_dict[self.g_line_plot],
                        self.grid_elem_dict[self.g_histogram]
                    )
                ),
                css_classes=["first_row"]
            ),
            row(
                column(
                    self.grid_elem_dict[self.g_heatmap_title],
                    self.grid_elem_dict[self.g_heatmap_buttons],
                    self.grid_elem_dict[self.g_heatmap],
                ),
                css_classes=["second_row"]
            )
        )

        return grid

    def initialize_gridplot(self, initial_heatmap_choice):
        """Initializes all Elements and DataSources of the Gridplot.

            Function creates several Elements of a Gridplot:
                - Monthly Title and Monthly Statistic Expenses Divs
                - Daily Title and Daily Statistic Expenses Divs
                - Monthly Expenses Line Plot
                - Daily Expenses Histogram
                - Heatmap Title Div
                - Heatmap Radio Button Group
                - Heatmap

            Additionally, Separate DataSources (ColumnDataSources) are created for:
                - Line Plot
                - Histogram
                - Heatmap

            This is made as updates to some Elements are based only on property changes of those Elements
            (e.g. Div.text), whereas other Elements are automatically changed when their ColumnDataSource data
            is changed (e.g. Category Barplot).

            In the end, all Elements go into one dictionary, whereas DataSources go into other dictionary which are
            then placed into .grid_elem_dict and .grid_source_dict attributes, respectively.

            Purposes of Elements are described either in the functions that create them or in the functions that
            update the content of the Element.
        """

        elem_dict = {}
        source_dict = {}

        info_title_elem_css = "info_title"
        info_elem_css = "info_element"
        monthly_css = "monthly_class"

        # Statistics Divs
        elem_dict[self.g_monthly_title] = Div(text=self.monthly_title, css_classes=[
            info_title_elem_css, info_elem_css, monthly_css])
        elem_dict[self.g_monthly_statistics] = Div(text=self.stats_template, css_classes=[
            info_elem_css, monthly_css])

        elem_dict[self.g_daily_title] = Div(text=self.daily_title, css_classes=[info_title_elem_css, info_elem_css])
        elem_dict[self.g_daily_statistics] = Div(text=self.stats_template, css_classes=[info_elem_css])

        # Line Plot and Histogram
        source_dict[self.g_line_plot] = self.__create_line_plot_source()
        elem_dict[self.g_line_plot] = self.__create_line_plot(source_dict[self.g_line_plot])

        source_dict[self.g_histogram] = self.__create_histogram_source()
        elem_dict[self.g_histogram] = self.__create_histogram(source_dict[self.g_histogram])

        # Heatmap
        elem_dict[self.g_heatmap_title] = Div(text=self.heatmap_title, css_classes=["heatmap_title"])
        elem_dict[self.g_heatmap_buttons] = RadioGroup(
            labels=self.heatmap_radio_buttons, active=initial_heatmap_choice,
            css_classes=["heatmap_radio_buttons"], inline=True
        )

        source_dict[self.g_heatmap] = self.__create_heatmap_source()
        elem_dict[self.g_heatmap] = self.__create_heatmap(source_dict[self.g_heatmap])

        self.grid_elem_dict = elem_dict
        self.grid_source_dict = source_dict

    def update_gridplot(self, heatmap_choice):
        """Helper function that calls specific updates for specified elements of the grid.

            Requires heatmap_choice argument that represents chosen index of Heatmap Radio Button Group.
        """

        self.__update_current_expense_df()
        self.__update_info()
        self.__update_line_plot()
        self.__update_histogram()
        self.__update_heatmap(heatmap_choice)

    def update_gridplot_on_month_selection_change(self):
        """Helper function that calls specific updates for specified elements of the grid."""

        self.__update_current_expense_df()
        self.__update_info()
        self.__update_histogram()

    # ========== Creation of Grid Elements ========== #

    def __create_line_plot_source(self):
        """Creation of Line Plot DataSource for Gridplot.

            ColumnDataSource consist of two keys:
                - x : contains months for the X-axis, formatted in "%b-%y" format (e.g. Jan-19)
                - y : temp values of the same length as x; they will be replaced when the update function for the
                    line plot is called

            Returns created ColumnDataSource.
        """
        new_format = "%b-%Y"
        formatted_months = [datetime.strptime(month, self.monthyear_format).strftime(new_format)
                            for month in self.months]

        data = {
            "x": formatted_months,
            "y": [1]*len(self.months)  # ensuring same length of data values
        }

        source = ColumnDataSource(
            data=data
        )

        return source

    def __create_line_plot(self, source):
        """Creates Line Plot showing trends of monthly expenses.

            Function accept argument:
                - source
            which should be ColumnDataSource with "x" and "y" keys and corresponding collections of values associated
            with them. It will be then used as a source for a created Plot.

            Created figure will have only "box_select" and "hover_tool" toolbox options enabled;
            hover tooltip is defined as HTML in .line_plot_tooltip property.

            Figure will plot two models: Line and Scatter (Circles). This is done so that user can freely select
            points on the graph and have visual cues (decreased alpha) that the selection works.

            Figure itself will plot "x" values from source on X-axis and "y" values from source on Y-axis.

            Additionally, message is added at the top of the plot, informing user about possibility of
            selecting points on the graph.

            Returns created Plot p.
        """
        base_color = self.color_map.contrary_color

        p = figure(width=540, height=340, x_range=source.data["x"], toolbar_location=None, tools=["box_select"],
                   title=self.line_plot_title, tooltips=self.line_plot_tooltip)

        p.line(x="x", y="y", source=source, line_width=5, color=base_color)
        scatter = p.circle(x="x", y="y", source=source, color=base_color)

        selected_circle = Circle(fill_alpha=1, line_color=base_color, fill_color=base_color)
        nonselected_circle = Circle(fill_alpha=0.2, line_alpha=0.2, line_color=base_color, fill_color=base_color)

        scatter.selection_glyph = selected_circle
        scatter.nonselection_glyph = nonselected_circle

        p.title.text_color = self.color_map.label_text_color
        p.title.text_font_size = "16px"

        info_label = Label(x=180, y=260, x_units="screen", y_units="screen",
                           text=self.interaction_message,
                           render_mode="css",
                           text_color=self.color_map.background_gray, text_font_size="12px",
                           text_font_style="italic")

        p.add_layout(info_label)

        p.axis.minor_tick_line_color = None
        p.axis.major_tick_line_color = None
        p.axis.axis_line_color = self.color_map.background_gray
        p.axis.major_label_text_color = self.color_map.label_text_color
        p.axis.major_label_text_font_size = "13px"
        p.xaxis.major_label_orientation = 0.785  # 45 degrees in radians

        p.yaxis.formatter = NumeralTickFormatter(format="0,0.00")

        return p

    def __create_histogram_source(self):
        """Creation of Histogram Barplot DataSource for Gridplot.

            ColumnDataSource consist of three keys:
                - hist: defines bins present on the y-axis of the histogram,
                - top_edges: defines top edges of rectangles in the histogram,
                - bottom_edges: defines bottom edges of rectangles in the histogram.

            Returns created ColumnDataSource.
        """

        data = {
            "hist": [0],
            "top_edges": [0],
            "bottom_edges": [0],
        }

        source = ColumnDataSource(data=data)

        return source

    def __create_histogram(self, source):
        """Creates Histogram Barplot showing Distribution of Daily Expenses.

            Figure plots quadrilateral representing histogram data of daily expenses. Whole figure is rotated
            90 degrees, so that quadrilaterals are plotted in a vertical fashion.

            Values of quads are:
                - left: 0, to start directly at y-axis
                - right: "hist" column, representing probability (histogram) data,
                - top & bottom: "top_edges" and "bottom_edges", edges of quads which should be plotted

            Returns created Plot p.
        """
        p = figure(width=300, height=340, title=self.histogram_title, toolbar_location=None,
                   tools=[""])

        p.quad(left=0, right="hist", top="top_edges", bottom="bottom_edges",
               source=source, fill_color=self.color_map.link_text_color,
               line_color=self.color_map.link_text_color)

        p.title.text_color = self.color_map.label_text_color
        p.title.text_font_size = "16px"

        p.axis.major_tick_line_color = None
        p.axis.minor_tick_line_color = None
        p.xaxis.visible = False
        p.axis.axis_line_color = self.color_map.background_gray
        p.axis.major_label_text_color = self.color_map.label_text_color
        p.axis.major_label_text_font_size = "13px"

        p.yaxis.formatter = NumeralTickFormatter(format="0,0.00")

        return p

    def __create_heatmap_source(self):
        """Creation of Heatmap Barplot DataSource for Gridplot.

            ColumnDataSource consist of several keys:
                - week: weeks of year (e.g. 1, 2, 52, 67)
                - weekday: day of the week (from 0 to 6)
                - value: column which will be plotted in the heatmap
                - date: date of a single point
                - price: price paid in a day
                - count: number of products bought in a day

            Returns created ColumnDataSource.
        """

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
        """Creates Heatmap Plot of Expenses.

            "Heatmap" Plot is a Figure plotting rectangles side by side, with every rectangle colored according
            to the defined color palette and the value associated with a given rectangle.

            Heatmap Plot in this case plots Week numbers on the X axis (week numbers from a year, e.g. 1, 13, 52)
            and days of the week (Monday, Tuesday, etc.) on the Y axis. This way, there are maximum 7 rectangles
            in a column and as many rows as weeks in the data.

            X axis is a Categorical Range of Week Numbers. Y axis is a Categorical Range of Strings representing
            numbers of days of the week (Monday - "0", Sunday - "6"). Y axis has also formatter attached to it,
            to format ticks into English 3-letter short acronyms for every day (e.g. Mon, Tue, etc.).

            ColorPalette is defined from ColorMap object which defines tints from a base color. Every second color
            from the palette is used for a bigger contrast. Additionally, ColorBar is attached to the Plot on the
            right side to provide color legend for a user.

            Returns created Plot p.
        """

        y_weekdays = [str(x) for x in range(6, -1, -1)]  # there is always 7 days in a week
        x_weeks = list(map(lambda x: str(x), range(1, 53)))

        palette = list(reversed([self.color_map.base_color_tints[i] for i in range(0, 10, 2)]))
        cmap = LinearColorMapper(palette=palette, low=0, high=1)
        cmap.low_color = "white"

        p = figure(
            height=180, width=1200,
            x_range=x_weeks, y_range=y_weekdays,
            x_axis_location="above",
            tooltips=self.heatmap_plot_tooltip,
            toolbar_location=None
        )

        p.rect(
            x="week", y="weekday", width=1, height=1,
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

        color_bar = ColorBar(color_mapper=cmap, ticker=BasicTicker(desired_num_ticks=len(palette)),
                             formatter=PrintfTickFormatter(), label_standoff=10, border_line_color=None,
                             location=(0, 0), major_label_text_font_size="12px",
                             major_label_text_color=self.color_map.text_color)

        p.add_layout(color_bar, "right")

        return p

    # ========== Updating Grid Elements ========== #

    def __update_chosen_months(self, indices):
        """Function updates .chosen_months attribute based on provided indices.

            Depending on indices passed to the function, corresponding months from .months attribute will be chosen.
            Order of indices doesn't matter.

            If the list is empty, it means that there are no specific months chosen and the attribute should return
            to it's initial state - all months in the DataFrame.
            If indices contain any elements, corresponding elements from .months are chosen and loaded into
            .chosen_months attribute.

            Attribute .chosen_months is updated.
        """

        if len(indices) == 0:
            self.chosen_months = self.months
        else:
            self.chosen_months = [self.months[i] for i in indices]

    def __update_current_expense_df(self):
        """Updates .current_expense_df attribute with data filtered by chosen months.

            Original DataFrame (from .original_expense_df) is filtered to include only months present in
            .chosen_months attribute.

            Attribute .current_expense_df is updated.
        """

        self.current_expense_df = self.original_expense_df[self.original_expense_df[
            self.monthyear].isin(self.chosen_months)]

    def __update_info(self):
        """Helper function that calls updating both monthly and daily statistics Divs, as both of those
        Elements should be updated at the same time."""

        self.__update_monthly_info()
        self.__update_daily_info()

    def __update_monthly_info(self):
        """Updates text in "Monthly Statistics" Div.

            "Monthly Statistics" Div defines several descriptory statistics value (e.g. mean, median, etc.) that are
            calculated from .current_expense_df dataframe. Df is first grouped by "monthyear" column to aggregate
            values on a monthly basis and then values are inserted into pre-defined HTML template.

            Several values for formatting are extracted from "price" column:
                - mean
                - median
                - min
                - max
                - std

            .stats_template HTML template is used, with values described above replacing their appropriate {format}
            arguments counterparts.

            Grid Element .g_monthly_statistics[.text] is updated
        """

        stats = self.current_expense_df.groupby(by=[self.monthyear]).sum()[self.price].describe()
        stats["median"] = stats["50%"]

        new_text = self.stats_template.format(**stats)

        self.grid_elem_dict[self.g_monthly_statistics].text = new_text

    def __update_daily_info(self):
        """Updates text in "Daily Statistics" Div.

            "Daily Statistics" Div defines several descriptory statistics value (e.g. mean, median, etc.) that are
            calculated from .current_expense_df dataframe. Df is first grouped by "date" column to aggregate
            values on a daily basis and then values are inserted into pre-defined HTML template.

            Several values for formatting are extracted from "price" column:
                - mean
                - median
                - min
                - max
                - std

            .stats_template HTML template is used, with values described above replacing their appropriate {format}
            arguments counterparts.

            Grid Element .g_daily_statistics[.text] is updated
        """

        stats = self.current_expense_df.groupby(by=[self.date]).sum()[self.price].describe()
        stats["median"] = stats["50%"]

        new_text = self.stats_template.format(**stats)

        self.grid_elem_dict[self.g_daily_statistics].text = new_text

    def __update_line_plot(self):
        """Updates Line Plot showing expenses aggregated on a monthly level.

            Function calculates monthly expenses from .original_expense_df DataFrame by grouping data by "monthyear"
            column and then extracting values from "price" column. Those values are then inserted into ColumnDataSource
            corresponding to Line Plot as new "y" values.

            Additionally, y_range of the Plot is updated: start is 0, whereas end is calculated to 101% of the
            highest value present in the corresponding "price" column of the aggregated DataFrame.

            Grid Element .g_line_plot and Grid Source Element .g_line_plot are updated.
        """

        # original_expense_df as line plot shouldn't be changed after month selection update
        new_values = self.original_expense_df.groupby(by=[self.monthyear]).sum()[self.price].tolist()

        source = self.grid_source_dict[self.g_line_plot]
        source.data["y"] = new_values

        fig = self.grid_elem_dict[self.g_line_plot]
        fig.y_range.start = 0
        fig.y_range.end = np.nanmax(new_values) + 0.01 * np.nanmax(new_values)

    def __update_histogram(self):
        """Updates histogram (BarPlot) data with calculated values.

            Function calculates new values by first aggregating .current_expense_df by "date" column (to calculate
            daily expenses), extracting sum() from "price" column and then applying np.histogram function to it.

            Hist and edges arrays are obtained:
                - hist defines probability value of each bin,
                - edges define edges for each bin.

            Top edge should exclude the last value, whereas bottom edge should exclude the first value.

            Those arrays are then used as new data for Histogram ColumnDataSource columns, "hist", "top_edges" and
            "bottom_edges".

            Grid Element .g_histogram and Grid Source Element .g_histogram are updated.
        """

        hist, edges = np.histogram(
            self.current_expense_df.groupby(by=[self.date]).sum()[self.price],
            density=True,
            bins=50
        )

        source = self.grid_source_dict[self.g_histogram]

        new_values = {
            "hist": hist,
            "top_edges": edges[:-1],
            "bottom_edges": edges[1:]
        }

        source.data.update(new_values)

    def __update_heatmap(self, selected_index):
        """Updates Heatmap Plot with Daily data from expense DataFrame.

            Accepts selected_index argument, which represents selection in the Heatmap Radio Group Button. Refer to
            __update_heatmap_values function, as it isn't used in the body of this function per se.

            Function first creates new aggregated DataFrame- .original_expense_df is aggregated by "date" column
            to create "Daily" aggregation. Specific transformations are described in __aggregated_expense_df function.

            From this newly created df several values are extracted and inserted into ColumnDataSource of the Heatmap:
                - "date": array of Strings of dates in "%d-%b-%Y" format,
                - "week": array of Strings of numbers of weeks padded to 4 digits (e.g. "0001")
                - "weekday" array of Strings of numbers of days of the week (e.g. "1", "5")
                - "price": array of Float numbers representing Daily expenses
                - "count": array of Numbers representing number of transactions in a single day
                - "value": values of either "price" or "count" that are displayed in the Heatmap (refer to
                        __update_heatmap_values for description).

            .heatmap_df_column_dict is updated with the dictionary from __create_new_column_names function - it
            provides mapping between column names aliases and "real" column names in the Dataframe.

            Range of X axis is also updated - new Range of weeks is calculated: start = min week number
            of the aggregated df; stop = max week number of the aggregated df; interval - 1. This range
            is also padded to 4 digits, similiar to "weekday" column and then inserted into the Plot as the new
            X axis range. This is done to properly visualize any breaks or time gaps if they are present in the data.

            There is also a FuncTickFormatter applied to X axis - week number ticks are matched to those in the
            provided dictionary (described in __create_first_week_to_month_dict function) and replaced with their
            respective items. If there is no match for the week, null tick ("") is placed.

            Such action is performed to declutter X axis - if it was left with week numbers, there would be a lot of
            ticks and their labels would overflow one another. By replacing only some of the week numbers with
            their respective items (month names), we not only give more space to the X axis range, but also provide
            user with the more intuitive figures (month names that everyone is familiar with instead of week numbers).

            Grid Element .g_heatmap and Grid Source Element .g_heatmap are updated.
        """

        # Heatmap isn't responsive to Month Selection
        df = self.original_expense_df

        # column names dict and aggregated df
        self.heatmap_df_column_dict = self.__create_new_column_names(df.reset_index().columns)
        aggregated = self.__aggregated_expense_df(df)
        column_names = self.heatmap_df_column_dict

        data = self.grid_source_dict[self.g_heatmap].data
        fig = self.grid_elem_dict[self.g_heatmap]

        # new Range generated to include any possible time gaps
        new_min = aggregated["week"].min()
        new_max = aggregated["week"].max()

        # new_max + 1 as range function is exclusive for the end parameter
        x_range = pd.Series(range(new_min, new_max+1, 1)).apply(lambda x: "{x:04d}".format(x=x)).tolist()

        fig.x_range.factors = x_range

        temp_values = [0] * len(aggregated[self.price])

        new_values = {
            "date": aggregated[column_names["date_str"]],
            "week": aggregated[column_names["week_str"]],
            "weekday": aggregated[column_names["weekday_str"]],
            "price": aggregated[self.price],
            "count": aggregated[column_names["count"]],
            "value": temp_values  # performed to not trigger ColumnDataSource warning over unmatched columns
        }

        data.update(new_values)

        # updating "value" Column in ColumnDataSource based on the index
        self.__update_heatmap_values(selected_index)

        # Formatter of X axis
        func_tick_dict = self.__create_first_week_to_month_dict(aggregated)

        formatter = FuncTickFormatter(args={"d": func_tick_dict}, code="""
                    var return_tick;
                    return_tick = "";
                    if (tick in d) {
                        return_tick = d[tick];
                    }
                    return return_tick;
                """)

        fig.xaxis.formatter = formatter

    def __update_heatmap_values(self, selected_index):
        """Updates "value" Column in Heatmap ColumnDataSource based on provided selected_index argument.

            Selected_index represents current selection of the Heatmap Radio Group buttons chosen by the user.
            The index shows the choice from .heatmap_radio_buttons Class property list:
                0 - Price
                1 - # of Products.

            Given that choice, either "price" Column or "count" Column is inserted as into "value" Column and is
            then displayed on the Heatmap Plot.

            Additionally, new minimum and maximum is calculated, with which ColorBar Legend of the heatmap is updated
            to reflect changes.
            If # of Products is selected, then regular min() and max() values are calculated.

            When Price is selected, then min() serves as a new low for the ColorBar, but new high is calculated as
            mean + (3 * std). This assumption is based on a fact that in a normal distribution, points above 3 SDs
            can be considered as outliers. Distribution of values is unknown here - it isn't calculated anywhere
            and we can only assume that it might be similar to log-normal as home budgets might consist mostly of
            small transactions and only a handful of them can be considered "big". This way, to solve the problem of
            most of transactions being shown on the lower spectrum of the color palette, we can treat the distribution
            of prices as normal and treat values above 3 SDs as outliers. This way differences in colors are preserved
            and the whole Plot is more informative this way.

            Grid Source Element .g_heatmap and ColorMapper .heatmap_color_mapper are updated.
        """

        # 0 - Price, 1 - Products
        data = self.grid_source_dict[self.g_heatmap].data

        if selected_index == 0:
            values = data["price"]
            high = values.mean() + (3 * values.std())  # see docstring
        elif selected_index == 1:
            values = data["count"]
            high = values.max()
        else:
            raise Exception("How did I get here?")

        low = values.min()
        data["value"] = values

        self.heatmap_color_mapper.high = high
        self.heatmap_color_mapper.low = low

    def __create_new_column_names(self, columns, n=8, seed=None):
        """Creates new dictionary of column alias: real column name pairs, given columns argument.

            Accepts:
                - column: collection with column names already in use
                - n: length of newly created name
                - seed: seed of random module.

            As the .original_expense_df comes from the user, names of the columns do not always have to follow
            regular naming patterns. As object has to create new columns and then refer to them later in the runtime,
            it cannot be assumed that the new names that the functions assign to columns won't be the names already
            in use in the original DataFrame. Therefore, function to make sure that the names aren't duplicates is
            needed.

            Function takes embedded default_col_names variable and assigns new column names as items of corresponding
            keys. Every key defines a default version of the name - if there is no such name in columns parameter, then
            default names are used.

            However, if any name is already present, then the new random value of length n (from ascii upper and
            lowercase letters) is created and checked again. New random string is being created as long as it isn't
            present in the columns or in the already created column names values.

            Returns dictionary of column aliases: new, real column names.
        """

        random.seed(seed)

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
            "count": "count",
            "monthyear_str": "monthyear_str"
        }

        new_values = []
        for key, item in default_col_names.items():

            new_value = item
            while (new_value in columns) or (new_value in new_values):
                new_value = "".join(random.choices(string.ascii_uppercase + string.ascii_lowercase, k=n))

            new_values.append(new_value)
            default_col_names[key] = new_value

        return default_col_names

    def __aggregated_expense_df(self, dataframe):
        """Creates new dataframe aggregated by "date" column from dataframe passed as the argument.

            dataframe argument should be Pandas Dataframe defining the same columns as .original_expense_df.

            Column names are taken from the dictionary defined in .heatmap_df_column_dict.

            Function aggregates the dataframe by "date" column (.date attribute), calculates both sum() and count()
            aggregating functions and joins dataframes together such as "count" becomes a column in the dataframe
            that had sum() applied to it.

            Columns (referred via their aliases) are created:
                - "year" - year of the transaction
                - "month" - month of the transaction
                - "weekday" - day of the week of the transaction
                - "week" - calculated as the difference between the date in .date Series and min() date in the Df,
                            floor divided by 7 (creating TimeDelta object) and then extracting number of days.
                - "year_str" - year of the transaction as String
                - "month_str" - month of the transaction as String in format "%b"
                - "weekday_str" - day of the week of the transaction as String
                - "date_str" - date of the transaction as String in format "%d-%b-%Y", extracted from .date column
                - "monthyear_str" - concatenated String column as "Year-Month" format, where year has 4 digits and
                                    month has 2 digits
                - "week_str" - week number of the transaction as String, padded to 4 digits (e.g. 0001).

            Returns created dataframe.
        """

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
        aggregated[column_dict["monthyear_str"]] = aggregated[column_dict["year_str"]] \
            + "-" \
            + aggregated[self.date].dt.strftime("%m")

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
        """Creates mapping between the number of the first week of the month and the month itself.

            agg should be an aggregated dataframe (created in __aggregated_expense_df function).

            Additional transformations are applied to the agg Dataframe to extract dictionary mapping key, value pairs
            of: Week number - Month String.

            The assumption made here is that only Mondays can start a Month. After filtering agg dataframe only to
            those days, grouping by "year_str" is performed to extract first month of a given year (as the provided
            data does not always have to start in January). This is done to concatenate Year String with it's first
            Month String into one.

            Agg dataframe is then grouped by "monthyear" and only first week numbers are left. Aggregation is done
            by "monthyear" column to avoid removing data of same months from different years (December '19 and '20).

            After that, month_str values are concatenated with year values if the given month was the first month
            in this year. In the end, week_str : month_str dictionary is created.

            week_to_month_dict dictionary is returned.
        """

        column_dict = self.heatmap_df_column_dict

        monday_agg = agg[agg[column_dict["weekday"]] == 0]
        year_month_agg = monday_agg.groupby(column_dict["year_str"]).first()[
            column_dict["monthyear_str"]].reset_index().set_index(column_dict["monthyear_str"])

        # grouped by monthyear_str to include duplicate months from different years in case of a time gap
        month_agg = monday_agg.groupby(column_dict["monthyear_str"]).first()[
            [column_dict["week_str"], column_dict["month_str"]]]

        month_agg[column_dict["year_str"]] = year_month_agg

        func = lambda x: x[column_dict["month_str"]] if pd.isna(x[column_dict["year_str"]]) else "({}) {}".format(
                x[column_dict["year_str"]], x[column_dict["month_str"]])

        month_agg[column_dict["month_str"]] = month_agg.apply(func, axis=1)

        month_to_week_dict = month_agg.set_index(column_dict["month_str"])[column_dict["week_str"]].to_dict()
        week_to_month_dict = {item: key for key, item in month_to_week_dict.items()}

        return week_to_month_dict
