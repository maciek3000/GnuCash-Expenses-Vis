import numpy as np
import pandas as pd

from bokeh.models import ColumnDataSource, Select, RadioGroup, DataTable, TableColumn, DateFormatter
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

    category_title = "<h1>{category}</h1>"

    statistics_table_html = """<table>
                    <thead>
                        <tr>
                            <th scope="col"> </th>
                            <th scope="col">[Currency]</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <th scope="row">Last Month</th>
                            <td>{last_category:.2f}</td>
                        </tr>
                        <tr>
                            <th scope="row">Average</th>
                            <td>{avg_category:.2f}</td>
                        </tr>
                        <tr>
                            <th scope="row">Median</th>
                            <td>{median_category:.2f}</td>
                        </tr>
                        <tr>
                            <th scope="row">Min</th>
                            <td>{min_category:.2f}</td>
                        </tr>
                        <tr>
                            <th scope="row">Max</th>
                            <td>{max_category:.2f}</td>
                        </tr>
                        <tr>
                            <th scope="row">Standard Deviation</th>
                            <td>{std_category:.2f}</td>
                        </tr>
                    </tbody>
                </table>"""
                #TODO: add number of items bought


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
        self.g_line_plot = "Line Plot"
        self.g_product_histogram = "Product Histogram"
        self.g_transactions = "Transactions"

        self.grid_elem_dict = None
        self.grid_source_dict = None


    def new_gridplot(self, dataframe):

        self.current_df = dataframe
        self.categories = unique_values_from_column(dataframe, self.category)
        self.months = unique_values_from_column(dataframe, self.monthyear)
        self.categories_df = aggregated_dataframe_sum(dataframe, [self.monthyear, self.category])
        self.grid_elem_dict, self.grid_source_dict = self.initialize_grid_elements()

        def callback(attr, new, old):
            if new != old:
                self.update_grid(new)

        self.grid_elem_dict[self.g_dropdown].on_change("value", callback)

        grid = column(
             row(self.grid_elem_dict[self.g_category_title]),
             row(self.grid_elem_dict[self.g_statistics_table], column(
                            self.grid_elem_dict[self.g_dropdown], self.grid_elem_dict[self.g_line_plot])),
             row(self.grid_elem_dict[self.g_product_histogram], self.grid_elem_dict[self.g_transactions]),
            sizing_mode="stretch_both"
        )

        return grid

    def update_grid(self, category):

        self.grid_elem_dict[self.g_category_title].text = self.category_title.format(category=category)
        self.grid_elem_dict[self.g_statistics_table].text = self.__update_statistics_table(category)

        self.__update_line_plot(category)
        self.__update_product_histogram_table(category)

        # new_y = self.__dict_for_line_plot(categories_df, new)["y"]
        # print(new, new_y)
        # line_plot.y_range.end = np.nanmax(new_y)
        # line_plot.line.source.data["y"] = new_y
        #
        # # statistics table div gets updated with the new category data
        # #new_data = self.__get_statistics_data(new_ys, new)
        # category_title_div.text = self.category_title.format(category=new)
        # #table_div.text = self.statistics_table_html.format(**new_data)
        # # description_div.text = self.description_html.format(**new_data) # TODO: get separate dict
        #
        # # product frequency table gets updated
        # new_data = self.__get_product_frequency_data(
        #     dataframe[dataframe[self.category] == new]
        # ).data
        # product_frequency_source.data = new_data
        #
        # # update two tables
        # new_df = dataframe[dataframe[self.category] == new]
        # all_transactions_source.data = ColumnDataSource(new_df).data
        # # top_price_source.data = ColumnDataSource(
        # #     new_df.sort_values(by=[self.price], ascending=False).head(5)
        # # ).data


    def initialize_grid_elements(self):

        elem_dict = {}
        source_dict = {}

        elem_dict[self.g_category_title] = Div(text="", css_classes=["category_title"]) #stretch_width
        elem_dict[self.g_statistics_table] = Div(text="", css_classes=["statistics_div"])

        source_dict[self.g_line_plot] = self.__create_line_plot_source()
        elem_dict[self.g_line_plot] = self.__create_line_plot(source_dict[self.g_line_plot])

        source_dict[self.g_product_histogram] = self.__create_product_histogram_source()
        elem_dict[self.g_product_histogram] = self.__create_product_histogram_table(source_dict[self.g_product_histogram])

        source_dict[self.g_transactions] = self.__create_transactions_source()
        elem_dict[self.g_transactions] = self.__create_transactions_table(source_dict[self.g_transactions])

        initial_category = self.categories[0]
        elem_dict[self.g_dropdown] = Select(value=initial_category, options=self.categories,
                          css_classes=["category_dropdown"])

        self.update_grid(initial_category)

        return elem_dict, source_dict

    def __create_line_plot_source(self):

        temp_values = [1 for month in self.months]

        source = ColumnDataSource(
            data={
                "x": self.months,
                "y": temp_values
            }
        )
        return source

    def __create_line_plot(self, cds):

        p = figure(width=360, height=360, x_range=cds.data["x"])
        p.line(x="x", y="y", source=cds, color="blue", line_width=4)

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

        dt = DataTable(source=source, columns=columns, header_row=True)

        return dt

    def __create_transactions_source(self):

        source = ColumnDataSource(
            data={
                self.date: 0,
                self.product: 0,
                self.price: 0,
                self.shop: 0
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

        dt = DataTable(source=source, columns=columns, header_row=True)
        return dt

    def __update_statistics_table(self, category):
        #TODO:
        self.grid_elem_dict[self.g_statistics_table].text = self.statistics_table_html

    def __update_line_plot(self, category):

        values = self.__values_from_category(category)
        self.grid_elem_dict[self.g_line_plot].y_range.end = np.nanmax(values)
        self.grid_source_dict[self.g_line_plot].data["y"] = values

    def __update_product_histogram_table(self, category):




    def __values_from_category(self, category):

        category_dict = self.categories_df[self.categories_df[self.category] == category].set_index(
                        self.monthyear)[self.price].to_dict()
        values = [category_dict[month] if month in category_dict else np.nan for month in self.months]

        return values















    def gridplot(self, dataframe):
        """Main function of the Category Object, that returns created gridplot for all Visualizations and Divs.

            Function creates a list of unique categories from provided dataframe and generates:
                - multi line plot with total values vs chosen category values
                - Select dropdown Widget, which allows user to choose category
                - Statistics Table Div, that provides info on some Category statistics from the dataframe.

            Callback is chained to Select Widget - upon change, multi line plot and all Divs are updated with the
            data of the new category.

            Returns Bokeh layout, which can be embedded into Web Application.
        """

        # TODO: reorder variables, introduce new variables
        # TODO: rethink how sources for widgets and for text should be created
        # TODO: add capability to change category filtering (Extended)

        # unique categories used in Category View
        categories = unique_values_from_column(dataframe, self.category)
        categories_df = aggregated_dataframe_sum(dataframe, [self.monthyear, self.category])

        initial_category = categories[0]

        # category title Div
        category_title_div = Div(text=self.category_title.format(category=initial_category),
                                css_classes=["category_title"], sizing_mode="stretch_width")

        # Category dropdown widget
        dropdown = Select(value=initial_category, options=categories,
                          css_classes=["category_dropdown"])


        category_data_dict = self.__dict_for_line_plot(categories_df, initial_category)
        line_plot, line_plot_source = self.__create_line_plot(category_data_dict)

        # text data
        #line_values = line_plot_dict["y"]
        statistics_data = self.__get_statistics_data(category_data_dict["y"], initial_category)

        # TODO: Limit both tables below to 5 or 10 rows by one variable

        # Frequency Table
        product_frequency_source = self.__get_product_frequency_data(
            dataframe[dataframe[self.category] == initial_category])
        product_frequency_table = self.__create_product_frequency_table(product_frequency_source)

        # Transactions for Category ColumnDataSource TODO: change comment
        transactions_category_df = dataframe[dataframe[self.category] == initial_category]
        all_transactions_source = ColumnDataSource(transactions_category_df)
        # top_price_source = ColumnDataSource(
        #     transactions_category_df.sort_values(by=[self.price], ascending=False).head(5)
        # )


        # All Transactions DataTable
        transactions_datatable = self.__create_top_price_datatable(all_transactions_source) #TODO: add separate method

        # statistics table Div
        table_div = Div(text=self.statistics_table_html.format(**statistics_data), css_classes=["statistics_div"])

        # description Div
        # description_div = Div(text=self.description_html.format(**statistics_data), css_classes=["description_div"])



        # callback for dropdown, which will trigger changes in the view upon change of the category
        def callback(attr, old, new):
            if new != old:
                # updating lines in the plot - total stays the same, whereas category line changes
                new_y = self.__dict_for_line_plot(categories_df, new)["y"]
                print(new, new_y)
                line_plot.y_range.end = np.nanmax(new_y)
                line_plot.line.source.data["y"] = new_y

                # statistics table div gets updated with the new category data
                #new_data = self.__get_statistics_data(new_ys, new)
                category_title_div.text = self.category_title.format(category=new)
                #table_div.text = self.statistics_table_html.format(**new_data)
                # description_div.text = self.description_html.format(**new_data) # TODO: get separate dict

                # product frequency table gets updated
                new_data = self.__get_product_frequency_data(
                    dataframe[dataframe[self.category] == new]
                ).data
                product_frequency_source.data = new_data

                # update two tables
                new_df = dataframe[dataframe[self.category] == new]
                all_transactions_source.data = ColumnDataSource(new_df).data
                # top_price_source.data = ColumnDataSource(
                #     new_df.sort_values(by=[self.price], ascending=False).head(5)
                # ).data

        dropdown.on_change("value", callback)

        grd = grid(column(
            row(category_title_div),
            row(table_div, column(dropdown, line_plot)), #table_div,
            row(product_frequency_table, transactions_datatable),
        ))

        for elem in grd.children:
            print(elem)

        return grd

    def __dict_for_line_plot(self, df, category):
        months = unique_values_from_column(df, self.monthyear)
        category_dict = df[df[self.category] == category].set_index(self.monthyear)[self.price].to_dict()
        category_values = [category_dict[month] if month in category_dict else np.nan for month in months]

        data = {
            "x": months,
            "y": category_values,
        }
        return data

    def __create_line_plot_old(self, source_data, **kwargs):

        plot_feat_dict = {
            "width": 4,
            "color": "blue",
        }

        source = ColumnDataSource(data={
            **source_data,
            **kwargs,
        })

        p = figure(width=360, height=360, x_range=source.data["x"], y_range=[0, max(source.data["y"])])
        p.line(x="x", y="y", source=source, color="blue", line_width=4)

        return p, source

    def __get_statistics_data(self, values, cat_name):
        describe_df = pd.DataFrame({
            #"All":  lines[0],
            "Cat": values
        }).describe()

        avg = describe_df.loc["mean"]
        median = describe_df.loc["50%"]
        min = describe_df.loc["min"]
        max = describe_df.loc["max"]
        std = describe_df.loc["std"]

        data = {
            "category": cat_name,
            #"last_all": lines[0][-1],
            "last_category": values[-1],
            #"avg_all": avg["All"],
            "avg_category": avg["Cat"],
            #"median_all": median["All"],
            "median_category": median["Cat"],
            #"min_all": min["All"],
            "min_category": min["Cat"],
            #"max_all": max["All"],
            "max_category": max["Cat"],
            #"std_all": std["All"],
            "std_category": std["Cat"],
        }
        return data

    def __get_product_frequency_data(self, dataframe):

        d = pd.DataFrame(dataframe[self.product].value_counts())
        source = ColumnDataSource(d)

        return source

    def __create_product_frequency_table(self, source):

        columns = [
            TableColumn(field="index", title="Product"),
            TableColumn(field="Product", title="Buy Count")
        ]

        dt = DataTable(source=source, columns=columns, header_row=True)

        return dt

    def __create_top_price_datatable(self, source):

        columns = [
            TableColumn(field=self.date, title="Date", formatter=DateFormatter(format="%d-%m-%Y")),
            TableColumn(field=self.product, title="Product"),
            TableColumn(field=self.price, title="Price"),
            TableColumn(field=self.category, title="Category")
        ]

        dt = DataTable(source=source, columns=columns, header_row=True)
        return dt

    # ========== old code ========== #
    def __source_data_for_multi_line_plot(self, agg, cat):
        months = unique_values_from_column(agg, self.monthyear)
        total_values = agg.groupby([self.monthyear]).sum()[self.price].tolist()

        category_dict = agg[agg[self.category] == cat].set_index(self.monthyear)[self.price].to_dict()
        category_values = [category_dict[month] if month in category_dict else np.nan for month in months]
        data = {
            "xs": [months, months],
            "ys": [total_values, category_values]
        }
        return data