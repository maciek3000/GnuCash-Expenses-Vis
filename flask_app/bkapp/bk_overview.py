import pandas as pd
import numpy as np

from datetime import datetime
from math import pi

from bokeh.models import ColumnDataSource
from bokeh.models.widgets import Div, Select
from bokeh.models.formatters import FuncTickFormatter
from bokeh.models.tools import HoverTool
from bokeh.layouts import column, row
from bokeh.plotting import figure

from .pandas_functions import unique_values_from_column


class Overview(object):
    """Overview Object that provides methods to generate gridplot used in Overview View in flask_app.

            Object expects:
                - appropriate column names for the dataframes (expense/income) that will be provided to other methods;
                - server_date datetime object, representing time at which server initialized Overview Object
                - month_format string, which represents in what string format date in monthyear column was saved;
                - color_map ColorMap object, which exposes attributes for specific colors.

            Main methods are:
                - gridplot() : workhorse of the Object, creates elements gridplot, creates callbacks and updates
                    appropriate elements of the grid. Returns grid that can be served in the Bokeh Server.
                - initalize_grid_elements() : creates all elements and data sources of gridplot and assigns them
                    appropriately to self.grid_elem_dict and self.grid_source_dict
                - update_gridplot function, that is called either during initialization or when user changes the
                    selection of the Month; updates gridplot with data corresponding to new Month.

            Attributes of the instance Object are described as single-line comments in __init__() method;
            piechart_start_angle defines the start offset for the piechart plotting; refer to piechart methods for
                more explanation.
            Other attributes of the class are HTML templates used in Div Elements creation; they are described in
                corresponding functions that update those Divs.
        """

    piechart_start_angle = (pi / 2)

    month_title = " Overview"

    expenses_chosen_month = "<span>{expenses_chosen_month:,.2f}</span>"
    expenses_chosen_month_subtitle = "Total Expenses This Month"

    trivia_title = "Trivia"
    total_products_chosen_month = "Products Bought: <span>{total_products_chosen_month}</span>"
    different_shops_chosen_month = "Unique Shops visited: <span>{different_shops_chosen_month}</span>"
    savings_positive = "Congratulations! You saved <span id='positive_savings'>{savings:.2%}</span> of your income " \
                       "this month! "
    savings_negative = "Uh oh.. You overpaid <span id='negative_savings'>{savings:.2%}</span> of your income."

    income_expenses_text = """
    <p>Income: <span>{income:,.2f}</span></p>
    <p>Expenses: <span id={savings_id}>{expenses:,.2f}</span></p>
    """

    category_expenses_title = "Expenses from Categories"

    category_barplot_tooltip = """
        <div class="hover_tooltip">
            <div>
                <span>Category: </span>
                <span>@x</span>
            </div>
            <div>
                <span>Value: </span>
                <span>@top{0.00}</y>
            </div>
        </div>
    """

    def __init__(self, category_colname, monthyear_colname, price_colname, product_colname,
                 date_colname, currency_colname, shop_colname, month_format, server_date, color_mapping):

        # Column Names
        self.category = category_colname
        self.monthyear = monthyear_colname
        self.price = price_colname
        self.product = product_colname
        self.date = date_colname
        self.currency = currency_colname
        self.shop = shop_colname

        # date provided by the server, representing time at which server initialized Overview Object
        self.server_date = server_date

        # MonthYear formatting
        self.monthyear_format = month_format  # formatting of date in MonthYear column

        # ColorMap
        self.color_map = color_mapping  # ColorMap object exposing attributes with specific colors

        # DataFrames
        # Next Month Dataframes are provided as they will be needed to create Budget Predictions

        self.original_expense_df = None  # original Expense DataFrame passed to Overview Object
        self.original_income_df = None  # original Income DataFrame passed to Overview Object
        self.chosen_month_expense_df = None  # original Expense DataFrame filtered only to chosen month
        self.next_month_expense_df = None  # original Expense DataFrame filtered only to next month
        self.chosen_month_income_df = None  # original Income DataFrame filtered only to chosen month
        self.next_month_income_df = None  # original Income DataFrame filtered only to next month

        # State Variables
        self.months = None
        self.chosen_month = None
        self.next_month = None

        # Identifiers for Grid Elements and DataSources
        self.g_month_dropdown = "Month Dropdown"
        self.g_month_title = "Month Title"
        self.g_expenses_chosen_month = "Expenses Last Month"
        self.g_expenses_chosen_month_subtitle = "Expenses Last Month Subtitle"
        self.g_trivia_title = "Trivia Title"
        self.g_total_products_chosen_month = "Products Last Month"
        self.g_different_shops_chosen_month = "Unique Shops"
        self.g_savings_info = "Savings Information"
        self.g_savings_piechart = "Savings Piechart"
        self.g_category_expenses_title = "Category Expenses Title"
        self.g_category_expenses = "Category Expenses"

        # Dicts of Elements and DataSources
        self.grid_elem_dict = None
        self.grid_source_dict = None

    def gridplot(self, expense_dataframe, income_dataframe):
        """Main function of Overview Object. Creates Gridplot with appropriate Visualizations and Elements and
            returns it.

            Accepts expense_dataframe argument that should be a Dataframe representing Expenses and
                income_dataframe argument, that should be a Dataframe representing Incomes.

            The function does several things:
                - initializes the gridplot,
                - sets Month property to be a collection of all months present in expense_dataframe,
                - chooses first month that will be displayed, based on provided server_date attribute
                - updates the elements of the gridplot with chosen month,
                - sets callback on chosen grid elements, so that changes made by the user are then reflected
                    to other grid elements
                - returns created grid as a bokeh layout, that can be later used in a Bokeh Server
        """

        self.original_expense_df = expense_dataframe
        self.original_income_df = income_dataframe
        self.months = unique_values_from_column(self.original_expense_df, self.monthyear)

        first_month = self.__choose_month_based_on_server_date()

        self.initialize_grid_elements(first_month)
        self.update_gridplot(first_month)

        # Setting up the Callbacks
        def dropdown_callback(attr, old, new):
            if new != old:
                self.update_gridplot(new)

        self.grid_elem_dict[self.g_month_dropdown].on_change("value", dropdown_callback)

        # Gridplot
        output = column(
            row(
                self.grid_elem_dict[self.g_month_dropdown],
                self.grid_elem_dict[self.g_month_title],
                css_classes=["title_row"],
            ),
            row(
                column(
                    self.grid_elem_dict[self.g_expenses_chosen_month],
                    self.grid_elem_dict[self.g_expenses_chosen_month_subtitle],
                    self.grid_elem_dict[self.g_trivia_title],
                    self.grid_elem_dict[self.g_total_products_chosen_month],
                    self.grid_elem_dict[self.g_different_shops_chosen_month],
                    css_classes=["info_column"]
                ),
                column(
                    self.grid_elem_dict[self.g_savings_info],
                    self.grid_elem_dict[self.g_savings_piechart],
                    css_classes=["piechart_column"]
                ),
                column(
                    self.grid_elem_dict[self.g_category_expenses_title],
                    self.grid_elem_dict[self.g_category_expenses],
                    css_classes=["barchart_column"]
                ),
                css_classes=["chosen_month_row"]
            ),
            row(
                column(
                    Div(text="Budget", css_classes=["title_row"]),
                    Div(text="Work in Progress", style={"font-size": "2em", "font-weight": "bold"})
                ),
            )
        )

        return output

    def initialize_grid_elements(self, first_month):
        """Initializes all Elements and DataSources of the Gridplot.

            Function creates several Elements of a Gridplot:
                - Month Dropdown and Month Title
                - 4 Info Elements Divs
                - Div with Savings information and Text
                - Piechart with Savings information
                - Category Barplot Title Div
                - Category Barplot

            Additionally, Separate DataSources (ColumnDataSources) are created for:
                - Piechart
                - Barplot

            This is made as updates to some Elements are based only on property changes of those Elements
            (e.g. Div.text), whereas other Elements are automatically changed when their ColumnDataSource data is
            changed (e.g. Category Barplot).

            In the end, all Elements go into one dictionary, whereas DataSources go into other dictionary which are
            then placed into .grid_elem_dict and .grid_source_dict attributes, respectively.

            Purposes of Elements are described either in the functions that create them or in the functions that
            update the content of the Element.
        """
        elem_dict = {}
        source_dict = {}

        elem_dict[self.g_month_dropdown] = Select(options=self.months, value=first_month,
                                                  css_classes=["month_dropdown"])
        elem_dict[self.g_month_title] = Div(text=self.month_title, css_classes=["month_title"])

        info_element_class = "info_element"

        elem_dict[self.g_expenses_chosen_month] = Div(
            text="", css_classes=[info_element_class]
        )
        elem_dict[self.g_expenses_chosen_month_subtitle] = Div(
            text=self.expenses_chosen_month_subtitle, css_classes=[info_element_class])

        elem_dict[self.g_trivia_title] = Div(text=self.trivia_title, css_classes=[info_element_class])
        elem_dict[self.g_total_products_chosen_month] = Div(text="", css_classes=[info_element_class])
        elem_dict[self.g_different_shops_chosen_month] = Div(text="", css_classes=[info_element_class])

        elem_dict[self.g_savings_info] = Div(text="", css_classes=["savings_information"])

        source_dict[self.g_savings_piechart] = self.__create_savings_piechart_source()
        elem_dict[self.g_savings_piechart] = self.__create_savings_piechart(source_dict[self.g_savings_piechart])

        elem_dict[self.g_category_expenses_title] = Div(text=self.category_expenses_title, css_classes=[
            "category_expenses_title"
        ])
        source_dict[self.g_category_expenses] = self.__create_category_barplot_source()
        elem_dict[self.g_category_expenses] = self.__create_category_barplot(source_dict[self.g_category_expenses])

        self.grid_elem_dict = elem_dict
        self.grid_source_dict = source_dict

    def update_gridplot(self, month):
        """Helper function that calls specific updates for specified elements of the grid.

            Requires month argument that represents new month value that was chosen.
        """

        self.__update_chosen_and_next_months(month)
        self.__update_dataframes()

#         self.__update_chosen_month_title()
        self.__update_expenses_chosen_month()
        self.__update_total_products_chosen_month()
        self.__update_different_shops_chosen_month()

        self.__update_piechart()
        self.__update_category_barplot()

    def change_category_column(self, col):
        """Changes .category attribute to col argument."""
        self.category = col

    # ========== Creation of Grid Elements ========== #

    def __create_savings_piechart_source(self):
        """Creation of Piechart DataSource for Gridplot.

            ColumnDataSource consist of several keys:
                - start_angle: defines where the colored wedge of the piechart will start
                - end_angle: defines where the colored wedge of the piechart will end
                - color: defines what color will the colored wedge of the piechart have
                - income: 1 element list containing Income value
                - expenses: 1 element list containing Expense value

            Returns created ColumnDataSource.
        """

        data = {
            "end_angle": [0.5 * pi],
            "color": ["red"],
            "start_angle": [self.piechart_start_angle],
            "income": [1000],
            "expenses": [1000]
        }

        source = ColumnDataSource(
            data=data
        )

        return source

    def __create_savings_piechart(self, source):
        """Creates Piechart showing how much income was saved or overpaid as a part of a whole circle.
            For detailed information on how it is calculated refer to functions updating this Piechart.

            Function accept argument:
                - source
            which should be ColumnDataSource with keys as specified in __create_savings_piechart_source function
            and corresponding collections of values associated with them. Source argument will be then used
            as a source for a created Piechart.

            Piecharts in bokeh are created by calling .wedge method on a plot.

            This plot is created by calling .wedge method two times:
                - first time is to create fully filled, background circle,
                - second time creates proper wedge that takes provided ColumnDataSource source to extract arguments.
                    This is also a wedge that will be dynamically changed upon changes to the source.

            This was done in such a way, as "usual" way (calculating start angles and end angles for both gray and
            colored wedges) was posing problems and errors (especially with the custom start angle).

            Returns created Plot p.
        """

        # Repeated arguments for both wedges
        wedge_kwargs = {
            "x": 0,
            "y": 1,
            "radius": 0.2,
            "direction": "clock",
        }

        p = figure(height=250, width=250, x_range=(-wedge_kwargs["radius"], wedge_kwargs["radius"]),
                   toolbar_location=None, tools=["tap"])

        p.wedge(
            start_angle=0, end_angle=2 * pi,
            fill_color=self.color_map.background_gray, line_color=self.color_map.background_gray,
            **wedge_kwargs
        )

        p.wedge(
            start_angle="start_angle", end_angle='end_angle',
            fill_color="color", line_color="color",
            source=source,
            **wedge_kwargs
        )

        p.axis.visible = False
        p.axis.axis_label = None

        return p

    def __create_category_barplot_source(self):
        """Creation of Category Barplot DataSource for Gridplot.

            ColumnDataSource consist of two keys:
                - x: defines categories present on the x-axis of the barplot,
                - top: defines heights (values) of bars in the barplot.

            Returns created ColumnDataSource.
        """

        data = {
            "x": ["a"],
            "top": [1]
        }

        source = ColumnDataSource(
            data=data
        )

        return source

    def __create_category_barplot(self, source):
        """Creates Categorical Barplot showing Expenses from different categories (Histogram).

           Function accept argument:
               - source
           which should be ColumnDataSource with "x" and "top" keys and corresponding collections of values
           associated with them. Source argument will be then used as a source for a created Barplot.

            This is a standard histogram, presenting Expenses from different categories. Bars are sorted in
            a descending order.

            HoverTool with vertical hovering is added, as "small" categories might be hard to hover over - therefore,
            hovering over the whole vertical line of the bar will trigger the HoverBox to appear.

           Returns created Plot p.
       """

        p = figure(width=550, height=400, x_range=source.data["x"], toolbar_location=None,
                   tools=["tap"])
        p.vbar("x", top="top", width=0.9, color=self.color_map.link_background_color, source=source)

        hover = HoverTool(
            tooltips=self.category_barplot_tooltip,
            mode="vline"
        )

        p.add_tools(hover)

        p.xaxis.major_label_orientation = 0.9
        p.axis.major_tick_in = None
        p.axis.minor_tick_in = None
        p.axis.major_tick_line_color = self.color_map.background_gray
        p.axis.minor_tick_out = None
        p.axis.axis_line_color = "white"
        p.axis.major_label_text_font_size = "13px"
        p.axis.major_label_text_color = self.color_map.label_text_color

        return p

    # ========== Updating Grid Elements ========== #

    def __update_chosen_and_next_months(self, month, date_format=None):
        """Updates chosen and next months attributes based on a month value that was provided.

            Accepts 2 arguments:
                - month: month String value from monthyear column which was chosen.
                - date_format: date format for the string in which month argument was encoded. If no date_format
                    is provided, function defaults it to .monthyear_format Instance attribute.

            next_month value is calculated as the 1 month offset from provided month (to the future) and encoded
            into string in date_format.

            Attributes .chosen_month and .next_month are updated with respective calculated values.
        """

        # instance attributes cannot be passed to the function as default argument values
        if date_format is None:
            date_format = self.monthyear_format

        next_month = (pd.Timestamp(datetime.strptime(month, date_format)) + pd.DateOffset(months=1)).strftime(
            date_format)
        self.chosen_month = month
        self.next_month = next_month

    def __update_dataframes(self):
        """Helper function that calls updates for Expense and Income Dataframes."""

        self.__update_expense_dataframes()
        self.__update_income_dataframes()

    def __update_expense_dataframes(self):
        """Function updates .chosen_month_expense_df and .next_month_expense_df attribute with data filtered
            by .monthyear column.

            Function takes .original_expense_df DataFrame, applies the filtering to .monthyear column to match values
            in .chosen_month value and .next_month attributes and assigns them accordingly.

            Attributes .chosen_months_expense_df and next_month_expense_df are updated.
        """

        self.chosen_month_expense_df = self.original_expense_df[
            self.original_expense_df[self.monthyear] == self.chosen_month]
        self.next_month_expense_df = self.original_expense_df[
            self.original_expense_df[self.monthyear] == self.next_month]

    def __update_income_dataframes(self):
        """Function updates .chosen_month_income_df and .next_month_income_df attribute with data filtered
            by .monthyear column.

            Function takes .original_income_df DataFrame, applies the filtering to .monthyear column to match values
            in .chosen_month value and .next_month attributes and assigns them accordingly.

            Attributes .chosen_months_income_df and next_month_income_df are updated.
        """

        self.chosen_month_income_df = self.original_income_df[
            self.original_income_df[self.monthyear] == self.chosen_month]
        self.next_month_income_df = self.original_income_df[self.original_income_df[self.monthyear] == self.next_month]

    def __update_expenses_chosen_month(self):
        """Function updates text in expenses_chosen_month Div (one of the "Info Elements" Div).

            Div shows total sum of expenses from a single chosen month, calculated from .chosen_month_expense_df
            DataFrame, sum of .price column. Calculated value is then inserted into the HTML template located in
            .expenses_chosen_month by {expenses_chosen_month} format argument.

            Grid Element .g_expenses_chosen_month[.text] is updated.
        """

        expenses_chosen_month = self.chosen_month_expense_df[self.price].sum()
        self.grid_elem_dict[self.g_expenses_chosen_month].text = self.expenses_chosen_month.format(
            expenses_chosen_month=expenses_chosen_month)

    def __update_total_products_chosen_month(self):
        """Function updates text in total_products_chosen_month Div (one of the "Info Elements" Div).

            Div shows total number of transactions from a single chosen month, calculated from .chosen_month_expense_df
            DataFrame (shape of a DataFrame). Calculated value is then inserted into the HTML template located in
            .total_products_chosen_month by {total_products_chosen_month} format argument.

            Grid Element .g_total_products_chosen_month[.text] is updated.
        """

        total_products_chosen_month = self.chosen_month_expense_df.shape[0]
        self.grid_elem_dict[self.g_total_products_chosen_month].text = self.total_products_chosen_month.format(
            total_products_chosen_month=total_products_chosen_month)

    def __update_different_shops_chosen_month(self):
        """Function updates text in different_shops_chosen_month Div (one of the "Info Elements" Div).

            Div shows unique number of shops from a single chosen month, calculated from .chosen_month_expense_df
            DataFrame, length of unique values from .shops column. Calculated value is then inserted into the HTML
            template located in .different_shops_chosen_month by {different_shops_chosen_month} format argument.

            Grid Element .g_different_shops_chosen_month[.text] is updated.
        """

        different_shops_chosen_month = len(unique_values_from_column(self.chosen_month_expense_df, self.shop))
        self.grid_elem_dict[self.g_different_shops_chosen_month].text = self.different_shops_chosen_month.format(
            different_shops_chosen_month=different_shops_chosen_month)

    def __update_piechart(self):
        """Helper function that calls all functions necessary to update Piechart Plot and Piechart Savings Div"""

        savings, income, expenses = self.__calculate_expense_percentage()

        self.__update_savings_info(savings, income, expenses)
        self.__update_savings_piechart(savings)

    def __update_savings_info(self, savings, income, expenses):
        """Function updates text in savings_info Div (Div for Piechart).

            Function accepts arguments:
                - savings: float number representing how much income was saved or overpaid,
                - income: sum of income from a chosen month,
                - expenses: sum of expenses from a chosen month.

            Function assesses if savings is positive or negative number and then prepares new text that will be
            inserted into savings_info Div - either .savings_postiive or .savings_negative (HTML Templates as
            Class attributes) and concatenates it with .income_expenses_text (another HTML template).
            Additionally, id for an HTML element is set depending on the positive/negative value of savings argument.

            HTML templates define in total 4 elements that can be configured by .format function:
                - {savings}
                - {income}
                - {expenses}
                - {savings_id}

            Grid Element .g_savings_info[.text] is updated.
        """

        # id is needed for income/expense values to have aligned formatting
        if savings >= 0:
            savings_text = self.savings_positive
            savings_id = "positive_savings"

        else:
            savings = -savings
            savings_text = self.savings_negative
            savings_id = "negative_savings"

        text = savings_text + self.income_expenses_text

        self.grid_elem_dict[self.g_savings_info].text = text.format(
            savings=savings, income=income, expenses=expenses, savings_id=savings_id)

    def __update_savings_piechart(self, savings):
        """Function updates Piechart and it's corresponding ColumnDataSource.

            Function accepts savings argument, which represent the fraction of income that was saved or overpaid.
            If the value is bigger than 0 then the color of the piechart is set to .color_map.positive_color color;
            otherwise, it is set to .color_map.negative_color.

            New end_angle is calculated for the colored wedge in the piechart (start angle stays
            the same as when it was defined during initialization of Piechart). As the whole circle is 2*pi, then the
            fraction provided in "savings" argument can represent how much of the circle should be colored.

            Additionally, clockwise direction implies that the values of angles should be negative. This value is then
            summed up with .piechart_start_angle and the correct end_angle is calculated and inserted into corresponding
            ColumnDataSource.

            If the angle is bigger than 2*pi (-2*pi), then it is always set to 2*pi to avoid any mistakes in coloring
            the wedge.

            Grid Element .g_savings_piechart and Grid Source Element .g_savings_piechart are updated.
        """

        if savings >= 0:
            part = savings
            color = self.color_map.positive_color
        else:
            part = -savings
            color = self.color_map.negative_color

        # negative values move angle clockwise
        angle_value = -(part * 2 * pi) + self.piechart_start_angle

        # if the value overreaches 100%, then the end angle is always set to -(2*pi) - whole circle will be colored
        limit = -(2 * pi)
        if angle_value <= limit:
            angle_value = limit

        angles = [angle_value]

        source = self.grid_source_dict[self.g_savings_piechart]
        source.data["end_angle"] = angles
        source.data["color"] = [color]

    def __update_category_barplot(self):
        """Function updates Category Barplot and it's corresponding ColumnDataSource.

            Function first calculates aggregated DataFrame, grouped by .monthyear column and then sorts it by
            .price column in a descending order. Data from this df is then pulled to update both ColumnDataSource
            and a Plot:
                - "x" and "top" values in ColumnDataSource are updated with Category/Price values, appropriately,
                - Plot x_range.factors is updated with new Category values

            Additionally, X axis JavaScript formatter is pinned to the Plot - if the length of categories exceeds
            25, then every second entry in the X axis is changed to ''. This is done to prevent overcrowding of
            labels in the X axis when there are too many Elements present.

            Grid Element .g_category_expenses and Grid Source Element .g_category_expenses are updated.
        """

        agg_df = self.chosen_month_expense_df.groupby([self.category]).sum().reset_index().sort_values(
                    by=[self.price], ascending=False)

        fig = self.grid_elem_dict[self.g_category_expenses]
        source = self.grid_source_dict[self.g_category_expenses]

        fig.x_range.factors = agg_df[self.category].tolist()

        new_data = {
            "x": agg_df[self.category],
            "top": agg_df[self.price]
        }

        source.data.update(new_data)


        if len(agg_df[self.category]) >= 25:
            formatter = FuncTickFormatter(code="""
                var return_tick;
                return_tick = tick;
                if (((index + 1) % 2) == 0) {
                    return_tick = '';
                }
                return return_tick;
            """)

            fig.xaxis.formatter = formatter

    # ========== Miscellaneous========== #

    def __choose_month_based_on_server_date(self, date_format=None):
        """Returns month string based on a time provided in .server_date attribute.

            The function aims to provide first chosen_month value, when there is no input from the user yet
            (e.g. in the beginning when the Gridplot is initialized).

            Accepts date_format argument String, which represents the format method of datetime in .monthyear column.
            If no argument is provided, it defaults to .monthyear_format attribute.

            The function first calculates the minus offset from the month present in .server_date (past offset) -
            e.g. today is 12-APR-2019, so the chosen month should be March 2019. However, the function also checks if
            the calculated month is present in .months collection (all months present in the Expense Dataframe).
            If yes, then chosen month is returned. If not, then the last month from .months collection is returned.

            Returns Datetime String in a date_format format.
        """

        if date_format is None:
            date_format = self.monthyear_format

        chosen_month = (pd.Timestamp(self.server_date) - pd.DateOffset(months=1)).strftime(date_format)
        if chosen_month not in self.months:
            chosen_month = self.months[-1]

        return chosen_month

    def __calculate_expense_percentage(self):
        """Function calculates difference between income and expense sums from a chosen month and presents it
            as a fraction of income sum.

            Function calculates difference of sum of .price column from chosen_month_income_df and
            chosen_month_expense_df. Then this difference is divided by income sum and is assigned to part variable.
            If the income is 0, np.nan is chosen instead.

            Returns part, income and expense numbers.
        """

        # negative as income is expressed as negative transaction
        income_month = -(self.chosen_month_income_df[self.price].sum())
        expense_month = self.chosen_month_expense_df[self.price].sum()

        difference = income_month - expense_month

        if income_month == 0:
            part = np.nan
        else:
            part = difference / income_month

        return part, income_month, expense_month
