import numpy as np
import pandas as pd

from bokeh.models import ColumnDataSource, Select, RadioGroup, DataTable, TableColumn, DateFormatter
from bokeh.layouts import column, row
from bokeh.plotting import figure
from bokeh.models.widgets import Div


def get_unique_values_from_column(df, col_name):
    """Returns sorted and unique values from a column of col_name from a DataFrame df.

        If there are any NaN values, they are replaced to string "nan".
     """
    return sorted(df[col_name].replace({np.nan: "nan"}).unique().tolist())


def get_aggregated_dataframe_sum(df, list_of_cols):
    """Returns new DataFrame from a df, aggregated by column names provided in list_of_cols.

        Indexes are reset and values are sorted by the columns that were provided in list_of_cols.
    """
    agg = df.groupby(list_of_cols).sum().reset_index().sort_values(by=list_of_cols)
    return agg


class Category(object):
    """Category Object that provides wrapping and methods to generate gridplot used in Category View in flask_app.

        Main method is .create_gridplot, that returns the whole responsive Visualizations and Div's with descriptions.
        When initializing the object, appropriate column names of expense DataFrame should be provided.
    """
    description_html = """
        <p>Your average montly expenses from {category} are: {avg_category:.2f}</p>
    """
    # <p>Those expenses make on average <p id="category_percentage">{category_percentage:.2%}%</p> of all expenses!<br>
    # <p>Mostly bought product from this category is {product_often}</p>

    statistics_table_html = """<table>
                    <thead>
                        <tr>
                            <th scope="col">Monthly</th>
                            <th scope="col">All</th>
                            <th scope="col">{category}</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <th scope="row">Last Month:</th>
                            <td>{last_all:.2f}</td>
                            <td>{last_category:.2f}</td>
                        </tr>
                        <tr>
                            <th scope="row">Average</th>
                            <td>{avg_all:.2f}</td>
                            <td>{avg_category:.2f}</td>
                        </tr>
                        <tr>
                            <th scope="row">Median</th>
                            <td>{median_all:.2f}</td>
                            <td>{median_category:.2f}</td>
                        </tr>
                        <tr>
                            <th scope="row">Min</th>
                            <td>{min_all:.2f}</td>
                            <td>{min_category:.2f}</td>
                        </tr>
                        <tr>
                            <th scope="row">Max</th>
                            <td>{max_all:.2f}</td>
                            <td>{max_category:.2f}</td>
                        </tr>
                        <tr>
                            <th scope="row">Standard Deviation</th>
                            <td>{std_all:.2f}</td>
                            <td>{std_category:.2f}</td>
                        </tr>
                    </tbody>
                </table>"""
                #TODO: add number of items bought

    category_types = ["Simple", "Extended"]

    def __init__(self, category_colname, monthyear_colname, price_colname, product_colname, date_colname):
        self.category = category_colname
        self.monthyear = monthyear_colname
        self.price = price_colname
        self.product = product_colname
        self.date = date_colname

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
        unique_categories = get_unique_values_from_column(dataframe, self.category)
        first_chosen_category = unique_categories[0]

        # multi line plot
        aggregated = get_aggregated_dataframe_sum(dataframe, [self.monthyear, self.category])
        source_data = self.__get_source_data_for_multi_line_plot(aggregated, first_chosen_category)
        line_plot, line_plot_source = self.__create_line_plot(source_data)

        # text data
        line_values = source_data["ys"]
        statistics_data = self.__get_statistics_data(line_values, first_chosen_category)

        # TODO: Limit both tables below to 5 or 10 rows by one variable

        # Frequency Table
        product_frequency_source = self.__get_product_frequency_data(
            dataframe[dataframe[self.category] == first_chosen_category])
        product_frequency_table = self.__create_frequency_table(product_frequency_source)

        # Transactions for Category ColumnDataSource TODO: change comment
        transactions_category_df = dataframe[dataframe[self.category] == first_chosen_category]
        all_transactions_source = ColumnDataSource(transactions_category_df)
        # top_price_source = ColumnDataSource(
        #     transactions_category_df.sort_values(by=[self.price], ascending=False).head(5)
        # )


        # All Transactions DataTable
        transactions_datatable = self.__create_top_price_datatable(all_transactions_source) #TODO: add separate method

        # category name Div
        category_name_div = Div(text="<h1>{category}</h1>".format(category=first_chosen_category),
                                css_classes=["category_name"], sizing_mode="stretch_width")

        # statistics table Div
        table_div = Div(text=self.statistics_table_html.format(**statistics_data), css_classes=["statistics_div"])

        # description Div
        description_div = Div(text=self.description_html.format(**statistics_data), css_classes=["description_div"])

        # Category dropdown widget
        dropdown = Select(title='Category:', value=first_chosen_category, options=unique_categories,
                          css_classes=["category_dropdown"])

        # callback for dropdown, which will trigger changes in the view upon change of the category
        def callback(attr, old, new):
            if new != old:
                # updating lines in the plot - total stays the same, whereas category line changes
                new_ys = self.__get_source_data_for_multi_line_plot(aggregated, new)["ys"]
                line_plot_source.data["ys"] = new_ys

                # statistics table div gets updated with the new category data
                new_data = self.__get_statistics_data(new_ys, new)
                category_name_div.text = "<h1>{category}</h1>".format(category=new)
                table_div.text = self.statistics_table_html.format(**new_data)
                description_div.text = self.description_html.format(**new_data) # TODO: get separate dict

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

        # Category Type radio buttons
        # TODO: functionality of Category Type
        category_type_buttons = RadioGroup(labels=self.category_types,
                                           active=0)

        grid = column(
            row(category_name_div),
            row(description_div, table_div, column(row(dropdown, category_type_buttons), line_plot)),
            row(product_frequency_table, transactions_datatable)
        )

        return grid

    def __create_line_plot(self, source_data, **kwargs):

        plot_feat_dict = {
            "width": [4, 4],
            "color": ["blue", "red"]
        }

        source = ColumnDataSource({
            **source_data,
            **plot_feat_dict,
            **kwargs
        })

        p = figure(width=360, height=360, x_range=source.data["xs"][0], y_range=[0, max(source.data["ys"][0])])
        p.multi_line("xs", "ys", source=source, color="color", line_width="width")

        return p, source

    def __get_source_data_for_multi_line_plot(self, agg, cat):
        months = get_unique_values_from_column(agg, self.monthyear)
        total_values = agg.groupby([self.monthyear]).sum()[self.price].tolist()

        category_dict = agg[agg[self.category] == cat].set_index(self.monthyear)[self.price].to_dict()
        category_values = [category_dict[month] if month in category_dict else np.nan for month in months]
        data = {
            "xs": [months, months],
            "ys": [total_values, category_values]
        }
        return data

    def __get_statistics_data(self, lines, cat_name):
        values = pd.DataFrame({
            "All":  lines[0],
            "Cat": lines[1]
        }).describe()

        avg = values.loc["mean"]
        median = values.loc["50%"]
        min = values.loc["min"]
        max = values.loc["max"]
        std = values.loc["std"]

        data = {
            "category": cat_name,
            "last_all": lines[0][-1],
            "last_category": lines[1][-1],
            "avg_all": avg["All"],
            "avg_category": avg["Cat"],
            "median_all": median["All"],
            "median_category": median["Cat"],
            "min_all": min["All"],
            "min_category": min["Cat"],
            "max_all": max["All"],
            "max_category": max["Cat"],
            "std_all": std["All"],
            "std_category": std["Cat"]
        }
        return data

    def __get_product_frequency_data(self, dataframe):

        d = pd.DataFrame(dataframe[self.product].value_counts())
        source = ColumnDataSource(d)

        return source

    def __create_frequency_table(self, source):

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
