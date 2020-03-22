import numpy as np
import pandas as pd
from datetime import datetime

from bokeh.models import ColumnDataSource, Select, DataTable, TableColumn, DateFormatter, \
    BoxSelectTool, BoxZoomTool, PanTool, DatetimeTickFormatter, HoverTool, ResetTool, Circle, CustomJS
from bokeh.layouts import column, row, grid
from bokeh.plotting import figure
from bokeh.models.widgets import Div


def unique_values_from_column(df, column):
    """Returns sorted and unique values from a column from a DataFrame df.

        If there are any NaN values, they are replaced to string "nan".
     """
    return sorted(df[column].replace({np.nan: "nan"}).unique().tolist())


def aggregated_dataframe_sum(df, columns):
    """Returns new DataFrame from a df, aggregated by column names provided in columns.

        Indexes are reset and values are sorted by the columns that were provided in list_of_cols.
    """
    agg = df.groupby(columns).sum().reset_index().sort_values(by=columns)
    return agg


class Category(object):
    """Category Object that provides wrapping and methods to generate gridplot used in Category View in flask_app.

        Main method is .create_gridplot, that returns the whole responsive Visualizations and Div's with descriptions.
        When initializing the object, appropriate column names of expense DataFrame should be provided.
    """

    category_title = "{category}"

    category_fraction = "<span>{category_fraction:.2%}</span> of all Expenses!"
    category_products_fraction = "<span>{category_products_fraction:.2%}</span> of all Products!"

    statistics_table = """<table>
                    <thead>
                        <tr>
                            <th scope="col"> </th>
                            <th scope="col">[{curr}]</th>
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
                            <th scope="row">Min</th>
                            <td>{min:.2f}</td>
                        </tr>
                        <tr>
                            <th scope="row">Max</th>
                            <td>{max:.2f}</td>
                        </tr>
                        <tr>
                            <th scope="row">Standard Deviation</th>
                            <td>{std:.2f}</td>
                        </tr>
                        <tr>
                            <th scope="row">Products bought</th>
                            <td>{count}</td>
                        </tr>
                    </tbody>
                </table>"""

    line_plot_tooltip = """
        <div class="line_tooltip">
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
                 date_colname, currency_colname, shop_colname):
        self.category = category_colname
        self.monthyear = monthyear_colname
        self.price = price_colname
        self.product = product_colname
        self.date = date_colname
        self.currency = currency_colname
        self.shop = shop_colname

        self.current_df = None
        self.categories = None
        self.categories_df = None
        self.single_category_df = None
        self.months = None

        self.g_category_title = "Category Title"
        self.g_dropdown = "Dropdown"
        self.g_statistics_table = "Statistics Table"
        self.g_category_fraction = "Category Fraction"
        self.g_category_products_fraction = "Category Products Fraction"
        self.g_line_plot = "Line Plot"
        self.g_product_histogram = "Product Histogram"
        self.g_transactions = "Transactions"

        self.grid_elem_dict = None
        self.grid_source_dict = None

    def gridplot(self, dataframe):

        self.current_df = dataframe
        self.categories = unique_values_from_column(dataframe, self.category)
        self.months = unique_values_from_column(dataframe, self.monthyear)
        self.categories_df = aggregated_dataframe_sum(dataframe, [self.monthyear, self.category])

        initial_category = self.categories[0]
        self.grid_elem_dict, self.grid_source_dict = self.initialize_grid_elements(initial_category)
        self.update_grid(initial_category)

        def callback(attr, old, new):
            if new != old:
                self.update_grid(new)

        self.grid_elem_dict[self.g_dropdown].on_change("value", callback)

        output = column(
             row(self.grid_elem_dict[self.g_category_title], css_classes=["title_row"]),
             row(
                 column(self.grid_elem_dict[self.g_statistics_table],),
                 column(self.grid_elem_dict[self.g_category_fraction], self.grid_elem_dict[self.g_category_products_fraction],),
                 column(self.grid_elem_dict[self.g_dropdown], self.grid_elem_dict[self.g_line_plot]),
                 css_classes=["first_row"]),
             row(self.grid_elem_dict[self.g_product_histogram], self.grid_elem_dict[self.g_transactions]),
            sizing_mode="stretch_width"
        )

        return output

    def initialize_grid_elements(self, initial_category):

        elem_dict = {}
        source_dict = {}

        #TODO: rename css classes

        elem_dict[self.g_category_title] = Div(text="", css_classes=["category_title"],)
        elem_dict[self.g_statistics_table] = Div(text="", css_classes=["statistics_div"], )
        elem_dict[self.g_category_fraction] = Div(text="", css_classes=["category_fraction"], )
        elem_dict[self.g_category_products_fraction] = Div(text="", css_classes=["category_products_fraction"], )

        source_dict[self.g_line_plot] = self.__create_line_plot_source()
        elem_dict[self.g_line_plot] = self.__create_line_plot(source_dict[self.g_line_plot])

        source_dict[self.g_product_histogram] = self.__create_product_histogram_source()
        elem_dict[self.g_product_histogram] = self.__create_product_histogram_table(source_dict[self.g_product_histogram])

        source_dict[self.g_transactions] = self.__create_transactions_source()
        elem_dict[self.g_transactions] = self.__create_transactions_table(source_dict[self.g_transactions])

        elem_dict[self.g_dropdown] = Select(value=initial_category, options=self.categories,
                          css_classes=["category_dropdown"])

        return elem_dict, source_dict

    def update_grid(self, category):

        self.__update_category_title(category)
        self.__update_statistics_table(category)
        self.__update_category_fraction(category)
        self.__update_category_products_fraction(category)

        self.__update_line_plot(category)
        self.__update_product_histogram_table(category)
        self.__update_transactions_table(category)

    # ========== Creation of Grid Elements ========== #

    def __create_line_plot_source(self):

        temp_values = [1 for month in self.months]
        formatted_months = [datetime.strftime(datetime.strptime(month, "%m-%Y"), "%b-%y") for month in self.months]
        source = ColumnDataSource(
            data={
                "x": formatted_months,
                "y": temp_values
            }
        )
        return source

    def __create_line_plot(self, cds):

        # BoxZoomTool is not added due to the issue with ResetTool; when changing the range via SelectDropdown,
        # the range is being reset to the 'initial_category' range

        base_color = "#19529c"

        p = figure(width=360, height=360, x_range=cds.data["x"], y_range=[0, 10], tooltips=self.line_plot_tooltip,
                   toolbar_location=None)
        p.line(x="x", y="y", source=cds, color=base_color, line_width=5,)


        # TODO: write JS Callback to implement selecting part of a plot which will propagate JS events for DataTables below
        # This might require rethinking of how DataFrames are stored in the Object, how aggregations are calculated, etc.

        # scatter = p.circle(x="x", y="y", source=cds, color=base_color, size=4)
        #
        # selected_circle = Circle(fill_alpha=1.0, fill_color=base_color, line_color=base_color)
        # nonselected_circle = Circle(fill_alpha=0.2, line_a   lpha=0.2, fill_color=base_color, line_color=base_color)
        #
        # scatter.selection_glyph = selected_circle
        # scatter.nonselection_glyph = nonselected_circle

        p.axis.minor_tick_line_color = None
        p.axis.major_tick_line_color = None
        p.axis.axis_line_color = "#DCDCDC"
        p.axis.major_label_text_color = "#C5C5C5"
        p.axis.major_label_text_font_size = "13px"
        p.xaxis.major_label_orientation = 0.785 # 45 degrees in radians

        return p

    def __create_product_histogram_source(self):

        source = ColumnDataSource(
            data={
                "index": [0],
                "Product": [0]
            }
        )

        return source

    def __create_product_histogram_table(self, source):

        columns = [
            TableColumn(field="index", title="Product"),
            TableColumn(field="Product", title="Buy Count")
        ]

        dt = DataTable(source=source, columns=columns, header_row=True, index_position=None)

        return dt

    def __create_transactions_source(self):

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

        columns = [
            TableColumn(field=self.date, title="Date", formatter=DateFormatter(format="%d-%m-%Y")),
            TableColumn(field=self.product, title="Product"),
            TableColumn(field=self.price, title="Price"),
            TableColumn(field=self.shop, title="Shop")
        ]

        dt = DataTable(source=source, columns=columns, header_row=True, index_position=None)
        return dt

    # ========== Updating Grid Elements ========== #

    def __update_category_title(self, category):
        self.grid_elem_dict[self.g_category_title].text = self.category_title.format(category=category)

    def __update_statistics_table(self, category):
        format_dict = {}

        new_category_df = self.categories_df[self.categories_df[self.category] == category]
        last = new_category_df[self.price].iloc[-1]
        count = self.current_df[self.current_df[self.category] == category].shape[0]

        describe_dict = new_category_df.describe()[self.price].to_dict()
        format_dict.update(describe_dict)
        format_dict["median"] = format_dict["50%"] # percentage signs are unsupported as keyword arguments
        format_dict["last"] = last
        format_dict["count"] = count
        format_dict["curr"] = self.current_df[self.currency].unique()[0] #TODO: implement currency properly

        self.grid_elem_dict[self.g_statistics_table].text = self.statistics_table.format(**format_dict)

    def __update_category_fraction(self, category):
        category_sum = self.categories_df[self.categories_df[self.category] == category][self.price].sum()
        total_sum = self.categories_df[self.price].sum()
        category_fraction = category_sum / total_sum

        self.grid_elem_dict[self.g_category_fraction].text = self.category_fraction.format(category_fraction=category_fraction)

    def __update_category_products_fraction(self, category):
        category_products = self.current_df[self.current_df[self.category] == category].shape[0]
        all_products = self.current_df.shape[0]
        category_products_fraction = category_products / all_products

        self.grid_elem_dict[self.g_category_products_fraction].text = self.category_products_fraction.format(
            category_products_fraction=category_products_fraction
        )

    def __update_line_plot(self, category):

        values = self.__values_from_category(category)
        self.grid_source_dict[self.g_line_plot].data["y"] = values
        self.grid_elem_dict[self.g_line_plot].y_range.start = 0
        self.grid_elem_dict[self.g_line_plot].y_range.end = np.nanmax(values) + (0.01 * np.nanmax(values))

    def __update_product_histogram_table(self, category):

        filtered_df = self.current_df[self.current_df[self.category] == category]
        product_counts = pd.DataFrame(filtered_df[self.product].value_counts())
        self.grid_source_dict[self.g_product_histogram].data = product_counts

    def __update_transactions_table(self, category):
        new_df = self.current_df[self.current_df[self.category] == category]
        new_df = new_df.fillna("-")
        self.grid_source_dict[self.g_transactions].data = new_df

    def __values_from_category(self, category):

        category_dict = self.categories_df[self.categories_df[self.category] == category].set_index(
                        self.monthyear)[self.price].to_dict()
        values = [category_dict[month] if month in category_dict else np.nan for month in self.months]

        return values
