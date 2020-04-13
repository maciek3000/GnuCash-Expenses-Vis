import numpy as np
import pandas as pd
from datetime import datetime

from .pandas_functions import unique_values_from_column

from bokeh.models import ColumnDataSource, Select, DataTable, TableColumn, DateFormatter, Circle
from bokeh.layouts import column, row
from bokeh.plotting import figure
from bokeh.models.widgets import Div


class Category(object):
    """Category Object that provides methods to generate gridplot used in Category View in flask_app.

        Object expects:
            - appropriate column names for the dataframe that will be provided to other methods;
            - month_format string, which represents in what string format date in monthyear column was saved;
            - color_map ColorMap object, which exposes attributes for specific colors.

        Main methods are:
            - gridplot() : workhorse of the Object, creates elements gridplot, creates callbacks and updates
                appropriate elements of the grid. Returns grid that can be served in the Bokeh Server.
            - initalize_grid_elements() : creates all elements and data sources of gridplot and assigns them
                appropriately to self.grid_elem_dict and self.grid_source_dict
            - update_grid_on_chosen_category_change() and update_grid_on_month_selection_change() : functions that are
                called when user changes selected category or selected months on a gridplot; they are responsible for
                appropriate updating gridplot elements.

        Attributes of the instance Object are described as single-line comments in __init__() method;
        Attributes of the class are HTML templates used in Div Elements creation; they are described in corresponding
            functions that update those Divs.
    """

    category_title = "{category}"

    total_from_category = "<span>{total_from_category:.2f}</span> - total Money spent"
    category_fraction = "It makes <span>{category_fraction:.2%}</span> of all Expenses"
    total_products_from_category = "<span>{total_products_from_category:.0f}</span> - number of Products bought"
    category_products_fraction = "This is <span>{category_products_fraction:.2%}</span> of all Products"

    statistics_table = """<table>
                    <caption>Details</caption>
                    <thead>
                        <tr>
                            <th scope="col"></th>
                            <th scope="col"></th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <th scope="row">Last Month</th>
                            <td>{last:.2f}</td>
                        </tr>
                        <tr>
                            <th scope="row">Average</th>
                            <td>{mean:.2f}</td>
                        </tr>
                        <tr>
                            <th scope="row">Median</th>
                            <td>{median:.2f}</td>
                        </tr>
                        <tr>
                            <th scope="row">Minimum</th>
                            <td>{min:.2f}</td>
                        </tr>
                        <tr>
                            <th scope="row">Maximum</th>
                            <td>{max:.2f}</td>
                        </tr>
                        <tr>
                            <th scope="row">Standard Deviation</th>
                            <td>{std:.2f}</td>
                        </tr>
                    </tbody>
                    <tfoot>
                        <tr>
                            <th scope="row"></th>
                            <td>[{curr}]</td>
                        </tr>
                    </tfoot>
                </table>"""

    line_plot_tooltip = """
        <div class="hover_tooltip">
            <div>
                <span>Month: </span>
                <span>@x</span>
            </div>
            <div>
                <span>Value: </span>
                <span>@y{0.00}</y>
            </div>
        </div>
    """

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
        self.original_df = None  # original dataframe passed to the gridplot function
        self.chosen_category_df = None  # original dataframe filtered only to the chosen category
        self.chosen_months_and_category_df = None  # original dataframe filtered only to the chosen category and months

        # State Variables
        self.categories = None
        self.months = None
        self.chosen_category = None
        self.chosen_months = None

        # Identificators for Grid Elements and DataSources
        self.g_category_title = "Category Title"
        self.g_dropdown = "Dropdown"
        self.g_statistics_table = "Statistics Table"
        self.g_total_from_category = "Total Category"
        self.g_category_fraction = "Category Fraction"
        self.g_total_products_from_category = "Total Products From Category"
        self.g_category_products_fraction = "Category Products Fraction"
        self.g_line_plot = "Line Plot"
        self.g_product_histogram = "Product Histogram"
        self.g_transactions = "Transactions"

        # Dicts of Elements and DataSources
        self.grid_elem_dict = None
        self.grid_source_dict = None

    def gridplot(self, dataframe):
        """Main function of Category Object. Creates Gridplot with appropriate Visualizations and Elements and
            returns it.

            Accepts dataframe argument that should be a Dataframe representing Expenses.

            The function does several things:
                - initializes the gridplot,
                - chooses the first category that will be displayed (first item of all categories
                - sorted in alphabetical order),
                - updates the elements of the gridplot to reflect change to this category
                - sets callback on chosen grid elements, so that changes made by the user are then reflected
                    to other grid elements
                - returns created grid as a bokeh layout, that can be later used in a Bokeh Server

            Function extracts all categories present in the dataframe and loads them into the Select Element.
            However, this behavior might be changed in the future when creation of category list is delegated
            to another object.
        """

        self.original_df = dataframe
        self.chosen_category_df = dataframe
        self.chosen_months_and_category_df = dataframe

        # TODO: categories will be extracted depending on settings
        self.categories = unique_values_from_column(dataframe, self.category)
        self.months = unique_values_from_column(dataframe, self.monthyear)
        self.chosen_months = self.months  # during initialization, all months are selected

        self.__update_chosen_category(self.categories[0])
        self.initialize_grid_elements()
        self.update_grid_on_chosen_category_change()

        # Setting up the Callbacks
        def dropdown_callback(attr, old, new):
            if new != old:
                self.__update_chosen_category(new)
                self.update_grid_on_chosen_category_change()

        self.grid_elem_dict[self.g_dropdown].on_change("value", dropdown_callback)

        def selection_callback(attr, old, new):
            new_indices = set(new)
            old_indices = set(old)

            if new_indices != old_indices:
                self.update_grid_on_month_selection_change(new_indices)

        self.grid_source_dict[self.g_line_plot].selected.on_change("indices", selection_callback)

        # Gridplot
        output = column(
            row(self.grid_elem_dict[self.g_category_title], css_classes=["first_row"]),
            row(
                column(
                    self.grid_elem_dict[self.g_total_from_category],
                    self.grid_elem_dict[self.g_category_fraction],
                    self.grid_elem_dict[self.g_total_products_from_category],
                    self.grid_elem_dict[self.g_category_products_fraction],
                    css_classes=["info_column"]),
                column(self.grid_elem_dict[self.g_statistics_table]),
                column(
                    self.grid_elem_dict[self.g_dropdown],
                    self.grid_elem_dict[self.g_line_plot]),
                css_classes=["second_row"]),
            row(
                self.grid_elem_dict[self.g_product_histogram],
                self.grid_elem_dict[self.g_transactions],
                css_classes=["third_row"]),
            sizing_mode="stretch_width"
        )

        return output

    def initialize_grid_elements(self):
        """Initializes all Elements and DataSources of the Gridplot.

            Function creates several Elements of a Gridplot:
                - Category Title Div
                - "Statistics" Table Div
                - 4 "Headline" Divs
                - Category Dropdown Select Widget
                - Line Plot
                - 2 DataTables

            Additionally, Separate DataSources (ColumnDataSources) are created for:
                - Line Plot
                - 2 DataTables

            This is made as updates to some Elements are based only on property changes of those Elements
            (e.g. Div.text), whereas other Elements are automatically changed when their ColumnDataSource data is
            changed (e.g. Line Plot).

            In the end, all elements go into one dictionary, whereas DataSources go into other dictionary which are
            then placed into .grid_elem_dict and .grid_source_dict attributes, respectively.

            Purposes of Elements are described either in the functions that create them or in the functions that
            update the content of the Element.
        """

        elem_dict = {}
        source_dict = {}

        # Category Title and Statistics Table
        elem_dict[self.g_category_title] = Div(text="", css_classes=["category_title"], )
        elem_dict[self.g_statistics_table] = Div(text="", css_classes=["statistics_table"], )

        # 4 Headline Divs
        info_element_class = "info_element"
        elem_dict[self.g_total_from_category] = Div(text="", css_classes=[info_element_class])
        elem_dict[self.g_category_fraction] = Div(text="", css_classes=[info_element_class])
        elem_dict[self.g_total_products_from_category] = Div(text="", css_classes=[info_element_class])
        elem_dict[self.g_category_products_fraction] = Div(text="", css_classes=[info_element_class])

        # Line Plot
        source_dict[self.g_line_plot] = self.__create_line_plot_source()
        elem_dict[self.g_line_plot] = self.__create_line_plot(source_dict[self.g_line_plot])

        # DataTables
        source_dict[self.g_product_histogram] = self.__create_product_histogram_source()
        elem_dict[self.g_product_histogram] = self.__create_product_histogram_table(
            source_dict[self.g_product_histogram])

        source_dict[self.g_transactions] = self.__create_transactions_source()
        elem_dict[self.g_transactions] = self.__create_transactions_table(source_dict[self.g_transactions])

        # Select Dropdown
        elem_dict[self.g_dropdown] = Select(value=self.chosen_category, options=self.categories,
                                            css_classes=["category_dropdown"])

        self.grid_elem_dict = elem_dict
        self.grid_source_dict = source_dict

    def update_grid_on_chosen_category_change(self):
        """Helper function that calls specific updates for specified elements of the grid."""

        self.__update_chosen_category_dataframe()
        self.__update_chosen_months_and_category_dataframe()

        self.__update_category_title()
        self.__update_statistics_table()
        self.__update_total_from_category()
        self.__update_category_fraction()
        self.__update_total_products_from_category()
        self.__update_category_products_fraction()

        self.__update_line_plot()
        self.__update_product_histogram_table()
        self.__update_transactions_table()

    def update_grid_on_month_selection_change(self, new_indices):
        """Helper function that calls specific updates for specified elements of the grid."""

        self.__update_chosen_months(new_indices)
        self.__update_chosen_months_and_category_dataframe()

        self.__update_transactions_table()
        self.__update_product_histogram_table()

    # ========== Creation of Grid Elements ========== #

    def __create_line_plot_source(self):
        """Creation of Line Plot DataSource for Gridplot.

            ColumnDataSource consist of two keys:
                - x : contains months for the X-axis, formatted in "%b-%y" format (e.g. Jan-19)
                - y : temp values of the same length as x; they will be replaced when the update function for the
                    line plot is called

            Returns created ColumnDataSource.
        """

        temp_values = [1] * len(self.months)  # done to ensure that the shape of y values is the same as x
        formatted_months = [datetime.strftime(datetime.strptime(month, self.monthyear_format), "%b-%y") for month in self.months]
        source = ColumnDataSource(
            data={
                "x": formatted_months,
                "y": temp_values
            }
        )
        return source

    def __create_line_plot(self, cds):
        """Creates Line Plot showing trends of different amounts of money spent on chosen category.

            Function accept argument:
                - cds
            which should be ColumnDataSource with "x" and "y" keys and corresponding collections of values associated
            with them. Cds will be then used as a source for a created Plot.

            Created figure will have bokeh toolbar with only "box_select" and "hover_tool" options enabled;
            hover tooltip is defined as HTML in .line_plot_tooltip property.

            Figure will plot two models: Line and Scatter (Circles). This is done so that user can freely select
            points on the graph and have visual cues (decreased alpha) that the selection works.

            Figure itself will plot "x" values from CDS on X-axis and "y" values from CDS on Y-axis.
            Visual changes applied are defined directly in the function and there is no API for that as of now.

            Returns created Plot p.
        """

        # BoxZoom Tool is not added due to the issue with ResetTool; when changing the range via SelectDropdown,
        # the range is being reset to the initialization category range. Therefore, neither Reset nor BoxZoom are
        # added to limit the options for the user to "play" with the graph.

        base_color = self.color_map.base_color

        p = figure(width=550, height=400, x_range=cds.data["x"], y_range=[0, 10], tooltips=self.line_plot_tooltip,
                   toolbar_location="right", tools=['box_select'])
        p.line(x="x", y="y", source=cds, color=base_color, line_width=5, )

        scatter = p.circle(x="x", y="y", source=cds, color=base_color, size=4)

        selected_circle = Circle(fill_alpha=1.0, fill_color=base_color, line_color=base_color)
        nonselected_circle = Circle(fill_alpha=0.2, line_alpha=0.2, fill_color=base_color, line_color=base_color)

        scatter.selection_glyph = selected_circle
        scatter.nonselection_glyph = nonselected_circle

        p.axis.minor_tick_line_color = None
        p.axis.major_tick_line_color = None
        p.axis.axis_line_color = self.color_map.background_gray
        p.axis.major_label_text_color = self.color_map.label_text_color
        p.axis.major_label_text_font_size = "13px"
        p.xaxis.major_label_orientation = 0.785  # 45 degrees in radians

        return p

    def __create_product_histogram_source(self):
        """Creates DataSource for Product Histogram (Value Counts) DataTable.

            ColumnDataSource defines two keys: "index" and .product string taken from the attribute of the Object.
            They are used later during creation of the DataTable.

            Returns created ColumnDataSource.
        """
        source = ColumnDataSource(
            data={
                "index": [0],
                self.product: [0]
            }
        )

        return source

    def __create_product_histogram_table(self, source):
        """Function creates and returns DataTable based on provided DataSource source.

            Provided source should be a ColumnDataSource including two parameters in it's .data dictionary:
                - index
                - .product attribute
            DataTable is created and this data is incorporated into it as "Product" and "Buy Count" columns
            appropriately. This Table generally shows how many

            DataTable has it's index column (counter) removed for clarity.

            Returns DataTable.
        """

        columns = [
            TableColumn(field="index", title="Product"),
            TableColumn(field=self.product, title="Buy Count")
        ]

        dt = DataTable(source=source, columns=columns, header_row=True, index_position=None)

        return dt

    def __create_transactions_source(self):
        """Function creates DataSource for Transactions DataTable.

            ColumnDataSource defines 4 variables in it's data, based on provided column names during initialization of
            Category object:
                - .date
                - .product
                - .price
                - .shop

            Returns created ColumnDataSource.
        """

        source = ColumnDataSource(
            data={
                self.date: [0],
                self.product: [0],
                self.price: [0],
                self.shop: [0]
            }
        )

        return source

    def __create_transactions_table(self, source):
        """Creates Transactions DataTable with DataSource source passed as it's ColumnData Source.

            DataTable defines 4 fields that need to be passed in the source ColumnDataSource .data attribute:
                - .date
                - .product
                - .price
                - .shop
            Those attributes correspond to column names in .original_df and it's derivatives. Created DataTable will
            show details of those 4 columns for every transaction necessary. Additionally, .date field will be
            formatted to %d-%m-%Y format (31-01-2019).

            DataTable has it's index (counter) column removed for clarity.

            Returns created DataTable.
        """
        columns = [
            TableColumn(field=self.date, title="Date", formatter=DateFormatter(format="%d-%m-%Y")),
            TableColumn(field=self.product, title="Product"),
            TableColumn(field=self.price, title="Price"),
            TableColumn(field=self.shop, title="Shop")
        ]

        dt = DataTable(source=source, columns=columns, header_row=True, index_position=None)
        return dt

    # ========== Updating Grid Elements ========== #

    def __update_chosen_category(self, category):
        """Function updates .chosen_category attribute with passed category String.

            Attribute .chosen_category is updated.
        """

        self.chosen_category = category

    def __update_chosen_months(self, indices):
        """Function updates .chosen_months attribute based on provided indices.

            The role of the function is to update .chosen_months attribute based on indices, that represent which
            months did the user choose in the grid Line Plot.
            If the list is empty, it means that there are no specific months chosen and the attribute should return
            to it's initial state - all months in the DataFrame.
            If indices contain any elements, corresponding elements from .months are chosen and loaded into
            .chosen_months attribute.

            It doesn't matter in what order .chosen_months are provided.

            Attribute .chosen_months is updated.
        """

        if len(indices) == 0:
            self.chosen_months = self.months
        else:
            self.chosen_months = [self.months[i] for i in indices]

    def __update_chosen_category_dataframe(self):
        """Function updates .chosen_category_df attribute with DataFrame filtered to .chosen_category.

            DataFrame in .original_df attribute is filtered to produce a view that includes rows where
            .category column contains .chosen_category String.

            Filtering is done via .str.contains method - filtering DataFrame this way allows greater flexibility:
                - full String can be passed which will reduce "rows" of the DataFrame greatly, or
                - only a part of String can be passed - this way partial filtering and less granularity can be
                    achieved.

            Attribute .chosen_category_dataframe is updated.
        """

        self.chosen_category_df = self.original_df[self.original_df[self.category].str.contains(self.chosen_category)]

    def __update_chosen_months_and_category_dataframe(self):
        """Function updates .chosen_month_and_category_df attribute with data filtered by category and months.

            Function takes .original_df DataFrame, applies the same filtering in regard to .category column as
            ___update_chosen_category_df function and additionally filters rows only to those, where .monthyear
            column value is present in collection of .chosen_months attribute.
            This way, DataFrame (View) filtered to specific category and months is created.

            Attribute .chosen_months_and_category_df is updated.
        """

        all_months_df = self.original_df[
            self.original_df[self.category].str.contains(self.chosen_category)]
        self.chosen_months_and_category_df = all_months_df[all_months_df[self.monthyear].isin(self.chosen_months)]

    def __update_category_title(self):
        """Function updates text in Category Title Div.

            Particular Div is identified by .g_category_title attribute. Text in this Div is located in .category_title
            attribute and it defines {category} keyword, which is replaced by .chosen_category String.
            The whole text is then replaced in the Div.

            Grid Element .g_category_title[.text] is updated.
        """
        self.grid_elem_dict[self.g_category_title].text = self.category_title.format(category=self.chosen_category)

    def __update_statistics_table(self):
        """Function updates text in "Statistics" Table Div.

            Statistics Table Div is the most complex Div in the Gridplot. It defines several descriptive statistic
            values corresponding to .chosen_category Category Expenses. Template for this text is located in
            .statistics_table attribute and it should define all format keywords described below.


            Several values for formatting are extracted:
                - count : how many transactions from a .chosen_category were made
            .chosen_category_df is grouped by .monthyear column and the sum is calculated, from which next values
            are calculated:
                - last : sum of expenses from the last month (based on .months attribute). If a given category didn't
                    have any expenses last month, np.nan is used
                - mean
                - min
                - max
                - std
                - median
            Additionally, currency curr is defined as the currency used in transactions. However, this is only a naive
            implementation as it doesn't take into account different currencies that might have been used in
            transactions.

            .statistics_table HTML template is used, with values described above replacing their appropriate {format}
            arguments counterparts.

            Grid Element .g_statistics_table[.text] is updated
        """

        format_dict = {}

        category_df = self.chosen_category_df.groupby(self.monthyear).sum()
        if self.months[-1] in category_df.index:
            last = category_df[self.price].iloc[-1]
        else:
            last = np.nan
        count = self.chosen_category_df.shape[0]

        describe_dict = category_df.describe()[self.price].to_dict()
        format_dict.update(describe_dict)
        format_dict["median"] = format_dict["50%"]  # percentage signs are unsupported as keyword arguments
        format_dict["last"] = last
        format_dict["count"] = count
        format_dict["curr"] = self.original_df[self.currency].unique()[0]  # TODO: implement currency properly

        self.grid_elem_dict[self.g_statistics_table].text = self.statistics_table.format(**format_dict)

    def __update_total_from_category(self):
        """Function updates text in total_from_category Div (one of the "Headlines" Div).

            Div shows total sum of expenses calculated from .chosen_category_df DataFrame. Sum of .price column is
            inserted into the HTML template located in .total_from_category by {total_from_category} format argument.

            Grid Element .g_total_from_category[.text] is updated.
        """

        total_from_category = self.chosen_category_df[self.price].sum()
        self.grid_elem_dict[self.g_total_from_category].text = self.total_from_category.format(
            total_from_category=total_from_category)

    def __update_category_fraction(self):
        """Function updates text in category_fraction Div (one of the "Headlines" Div).

            Div shows fraction of percentage of .chosen_category in comparison to total Expenses provided in the
            .original_df. Fraction is calculated as sum of .chosen_category_df[.price] value divided by the sum of
            .original_df[.price].
            The value is then inserted into .category_fraction HTML template, with {category_fraction} format
            argument being replaced with the percentage value.

            Grid Element .g_category_fraction[.text] is updated.
        """

        category_sum = self.chosen_category_df[self.price].sum()
        total_sum = self.original_df[self.price].sum()
        category_fraction = category_sum / total_sum

        self.grid_elem_dict[self.g_category_fraction].text = self.category_fraction.format(
            category_fraction=category_fraction)

    def __update_total_products_from_category(self):
        """Function updates total_products_from_category Div text (one of the 4 "Headlines" Divs).

            Div shows how many Products were bought from a category (in .chosen_category_df DataFrame). Simple shape
            of .chosen_category_df is retrieved, which is then inserted into .total_products_from_category HTML
            template as a {total_products_from_category} format argument.

            Grid Element .g_total_products_from_category[.text] is updated.
        """

        total_products_from_category = self.chosen_category_df.shape[0]

        self.grid_elem_dict[self.g_total_products_from_category].text = self.total_products_from_category.format(
            total_products_from_category=total_products_from_category
        )

    def __update_category_products_fraction(self):
        """Function updates category_products_fraction Div text (one of the 4 "Headlines" Divs).

            Div shows what is a fraction of Products bought from a .chosen_category as a percentage of all
            Products bought. Numbers are obtained as DataFrame shapes from .chosen_category_df and .original_df,
            respectively and then first value is divided by the second value.
            .category_products_fraction HTML template is then updated as {category_products_fraction} format
            argument is replaced by the result of the division.

            Grid Element .g_category_products_fraction[.text] is updated.
        """

        category_products = self.chosen_category_df.shape[0]
        all_products = self.original_df.shape[0]
        category_products_fraction = category_products / all_products

        self.grid_elem_dict[self.g_category_products_fraction].text = self.category_products_fraction.format(
            category_products_fraction=category_products_fraction
        )

    def __update_line_plot(self):
        """Function updates Line Plot and it's corresponding ColumnDataSource.

            Values are calculated from .chosen_category_df DataFrame - DataFrame is grouped by .monthyear and then
            Pandas Series is extracted to dictionary, with .monthyear column as index and .price as values. Series
            is compared to .months - to maintain the length of values of all months used in .original_df, any month not
            present in Series is given np.nan value.

            With collection of values extracted, it is replaced in .g_line_plot ColumnDataSource "y" keyword, which
            automatically updates the data on the plot.

            Additionally, Y-axis range is updated to reflect new values:
                - start is always set as 0
                - end is calculated as the 101% of maximum value present in extracted Series.

            Grid Element .g_line_plot and Grid Source Element .g_line_plot are updated.
        """

        category_dict = self.chosen_category_df.groupby([self.monthyear]).sum()[self.price].to_dict()
        values = [category_dict[month] if month in category_dict else np.nan for month in self.months]

        self.grid_source_dict[self.g_line_plot].data["y"] = values
        self.grid_elem_dict[self.g_line_plot].y_range.start = 0
        self.grid_elem_dict[self.g_line_plot].y_range.end = np.nanmax(values) + (0.01 * np.nanmax(values))

    def __update_product_histogram_table(self):
        """Function updates Product Histogram (Value Counts) DataTable.

            The purpose of the DataTable is to show how many different Products were bought from a .chosen_category,
            but also from .chosen_months (as Selected on the Line Plot). Therefore, DataFrame
            .chosen_months_and_category is used as a basis for calculation.
            Generally speaking, a Histogram is created by using .value_counts() method - .product counts are then
            used as a replacement for Grid Source Element .g_product_histogram[.data] - there is no need to modify
            the DataTable itself.

            Grid Source Element .g_product_histogram[.data] is updated.
        """

        product_counts = pd.DataFrame(self.chosen_months_and_category_df[self.product].value_counts(dropna=True))
        self.grid_source_dict[self.g_product_histogram].data = product_counts

    def __update_transactions_table(self):
        """Function updates All Transactions DataTable.

            The purpose of this DataTable is to show all Transactions that involved .chosen_category and were done
            somewhere along .chosen_months months. Therefore, .chosen_months_and_category_df is used as a basis for
            this function.
            DataTable only shows transactions in a format specified while creating the DataTable, so no calculations
            are necessary. For visual clarity, np.nan values are replaced with single hyphen "-" and values are
            sorted by .date column.
            Only Grid Source Element is modified - no need to modify the DataTable itself.

            Grid Source Element .g_transactions[.data] is updated.
        """

        df = self.chosen_months_and_category_df.fillna("-")
        df = df.sort_values(by=[self.date], ascending=True)
        self.grid_source_dict[self.g_transactions].data = df
