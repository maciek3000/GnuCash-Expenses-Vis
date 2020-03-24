import numpy as np
import pandas as pd
from datetime import datetime

from bokeh.models import ColumnDataSource, Select, DataTable, TableColumn, DateFormatter, Circle
from bokeh.layouts import column, row
from bokeh.plotting import figure
from bokeh.models.widgets import Div


def unique_values_from_column(df, column):
    """Returns sorted and unique values from a column from a DataFrame df.

        If there are any NaN values, they are replaced to string "nan".
     """
    return sorted(df[column].replace({np.nan: "nan"}).unique().tolist())


class Category(object):
    """Category Object that provides wrapping and methods to generate gridplot used in Category View in flask_app.

        Main method is .create_gridplot, that returns the whole responsive Visualizations and Div's with descriptions.
        When initializing the object, appropriate column names of expense DataFrame should be provided.
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

        self.original_df = None  # original dataframe passed to the gridplot function
        self.chosen_category_df = None
        self.chosen_months_and_category_df = None

        self.categories = None
        self.months = None
        self.chosen_category = None
        self.chosen_months = None

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

        self.grid_elem_dict = None
        self.grid_source_dict = None

    def gridplot(self, dataframe):

        self.original_df = dataframe
        self.chosen_category_df = dataframe
        self.chosen_months_and_category_df = dataframe

        # TODO: categories will be extracted depending on settings
        self.categories = unique_values_from_column(dataframe, self.category)
        self.months = unique_values_from_column(dataframe, self.monthyear)
        self.chosen_months = self.months

        self.__update_chosen_category(self.categories[0])
        self.initialize_grid_elements()
        self.update_grid_on_category_change()

        def dropdown_callback(attr, old, new):
            if new != old:
                self.__update_chosen_category(new)
                self.update_grid_on_category_change()

        self.grid_elem_dict[self.g_dropdown].on_change("value", dropdown_callback)

        def selection_callback(attr, old, new):
            new_indices = set(new)
            old_indices = set(old)

            if new_indices != old_indices:
                self.update_grid_on_month_selection_change(new_indices)

        self.grid_source_dict[self.g_line_plot].selected.on_change("indices", selection_callback)

        output = column(
            row(self.grid_elem_dict[self.g_category_title], css_classes=["first_row"]),
            row(
                column(
                    self.grid_elem_dict[self.g_total_from_category],
                    self.grid_elem_dict[self.g_category_fraction],
                    self.grid_elem_dict[self.g_total_products_from_category],
                    self.grid_elem_dict[self.g_category_products_fraction],
                    css_classes=["headline_column"]),
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

        elem_dict = {}
        source_dict = {}

        elem_dict[self.g_category_title] = Div(text="", css_classes=["category_title"], )
        elem_dict[self.g_statistics_table] = Div(text="", css_classes=["statistics_table"], )

        headline_class = "info_headline"
        elem_dict[self.g_total_from_category] = Div(text="", css_classes=[headline_class])
        elem_dict[self.g_category_fraction] = Div(text="", css_classes=[headline_class])
        elem_dict[self.g_total_products_from_category] = Div(text="", css_classes=[headline_class])
        elem_dict[self.g_category_products_fraction] = Div(text="", css_classes=[headline_class])

        source_dict[self.g_line_plot] = self.__create_line_plot_source()
        elem_dict[self.g_line_plot] = self.__create_line_plot(source_dict[self.g_line_plot])

        source_dict[self.g_product_histogram] = self.__create_product_histogram_source()
        elem_dict[self.g_product_histogram] = self.__create_product_histogram_table(
            source_dict[self.g_product_histogram])

        source_dict[self.g_transactions] = self.__create_transactions_source()
        elem_dict[self.g_transactions] = self.__create_transactions_table(source_dict[self.g_transactions])

        elem_dict[self.g_dropdown] = Select(value=self.chosen_category, options=self.categories,
                                            css_classes=["category_dropdown"])

        self.grid_elem_dict = elem_dict
        self.grid_source_dict = source_dict

    def update_grid_on_category_change(self):

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

        self.__update_chosen_months(new_indices)
        self.__update_chosen_months_and_category_dataframe()

        self.__update_transactions_table()
        self.__update_product_histogram_table()

    # ========== Creation of Grid Elements ========== #

    def __create_line_plot_source(self):
        temp_values = [1] * len(self.months)  # [1 for month in self.months]
        formatted_months = [datetime.strftime(datetime.strptime(month, "%m-%Y"), "%b-%y") for month in self.months]
        source = ColumnDataSource(
            data={
                "x": formatted_months,
                "y": temp_values
            }
        )
        return source

    def __create_line_plot(self, cds):

        # BoxZoom Tool is not added due to the issue with ResetTool; when changing the range via SelectDropdown,
        # the range is being reset to the initialization category range

        base_color = "#19529c"

        p = figure(width=360, height=360, x_range=cds.data["x"], y_range=[0, 10], tooltips=self.line_plot_tooltip,
                   toolbar_location="right", tools=['box_select'])
        p.line(x="x", y="y", source=cds, color=base_color, line_width=5, )

        scatter = p.circle(x="x", y="y", source=cds, color=base_color, size=4)

        selected_circle = Circle(fill_alpha=1.0, fill_color=base_color, line_color=base_color)
        nonselected_circle = Circle(fill_alpha=0.2, line_alpha=0.2, fill_color=base_color, line_color=base_color)

        scatter.selection_glyph = selected_circle
        scatter.nonselection_glyph = nonselected_circle

        p.axis.minor_tick_line_color = None
        p.axis.major_tick_line_color = None
        p.axis.axis_line_color = "#DCDCDC"
        p.axis.major_label_text_color = "#C5C5C5"
        p.axis.major_label_text_font_size = "13px"
        p.xaxis.major_label_orientation = 0.785  # 45 degrees in radians

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

    def __update_chosen_category(self, category):
        self.chosen_category = category

    def __update_chosen_months(self, indices):
        if len(indices) == 0:
            self.chosen_months = self.months
        else:
            self.chosen_months = [self.months[i] for i in indices]

    def __update_chosen_category_dataframe(self):
        self.chosen_category_df = self.original_df[self.original_df[self.category].str.contains(self.chosen_category)]

    def __update_chosen_months_and_category_dataframe(self):
        all_months_df = self.original_df[
            self.original_df[self.category].str.contains(self.chosen_category)]
        self.chosen_months_and_category_df = all_months_df[all_months_df[self.monthyear].isin(self.chosen_months)]

    def __update_category_title(self):
        self.grid_elem_dict[self.g_category_title].text = self.category_title.format(category=self.chosen_category)

    def __update_statistics_table(self):
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
        total_from_category = self.chosen_category_df.groupby([self.monthyear]).sum()[self.price].sum()

        self.grid_elem_dict[self.g_total_from_category].text = self.total_from_category.format(
            total_from_category=total_from_category)

    def __update_category_fraction(self):
        category_sum = self.chosen_category_df.groupby([self.monthyear]).sum()[self.price].sum()
        total_sum = self.original_df[self.price].sum()
        category_fraction = category_sum / total_sum

        self.grid_elem_dict[self.g_category_fraction].text = self.category_fraction.format(
            category_fraction=category_fraction)

    def __update_total_products_from_category(self):
        total_products_from_category = self.chosen_category_df.shape[0]

        self.grid_elem_dict[self.g_total_products_from_category].text = self.total_products_from_category.format(
            total_products_from_category=total_products_from_category
        )

    def __update_category_products_fraction(self):
        category_products = self.chosen_category_df.shape[0]
        all_products = self.original_df.shape[0]
        category_products_fraction = category_products / all_products

        self.grid_elem_dict[self.g_category_products_fraction].text = self.category_products_fraction.format(
            category_products_fraction=category_products_fraction
        )

    def __update_line_plot(self):

        category_dict = self.chosen_category_df.groupby([self.monthyear]).sum()[self.price].to_dict()
        values = [category_dict[month] if month in category_dict else np.nan for month in self.months]

        self.grid_source_dict[self.g_line_plot].data["y"] = values
        self.grid_elem_dict[self.g_line_plot].y_range.start = 0
        self.grid_elem_dict[self.g_line_plot].y_range.end = np.nanmax(values) + (0.01 * np.nanmax(values))

    def __update_product_histogram_table(self):

        product_counts = pd.DataFrame(self.chosen_months_and_category_df[self.product].value_counts(dropna=True))
        self.grid_source_dict[self.g_product_histogram].data = product_counts

    def __update_transactions_table(self):
        df = self.chosen_months_and_category_df.fillna("-")
        self.grid_source_dict[self.g_transactions].data = df
