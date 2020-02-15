import numpy as np
import pandas as pd

from bokeh.models import ColumnDataSource
from bokeh.layouts import column, row
from bokeh.models import Select
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

    statistics_table_html = """<table>
                    <tr>
                        <th>Monthly</th>
                        <th>All</th>
                        <th>{category}</th>
                    </tr>
                    <tr>
                        <td>Average</td>
                        <td>{avg_all:.2f}</td>
                        <td>{avg_category:.2f}</td>
                    </tr>
                </table>"""

    def __init__(self, category_colname, monthyear_colname, price_colname):
        self.category = category_colname
        self.monthyear = monthyear_colname
        self.price = price_colname

    def get_gridplot(self, dataframe):
        """Main function of the Category Object, that returns created gridplot for all Visualizations and Divs.

            Function creates a list of unique categories from provided dataframe and generates:
                - multi line plot with total values vs chosen category values
                - Select dropdown Widget, which allows user to choose category
                - Statistics Table Div, that provides info on some Category statistics from the dataframe.

            Callback is chained to Select Widget - upon change, multi line plot and all Divs are updated with the
            data of the new category.

            Returns Bokeh layout, which can be embedded into Web Application.
        """

        # unique categories used in Category View
        unique_categories = get_unique_values_from_column(dataframe, self.category)
        first_chosen_category = unique_categories[0]

        # multi line plot
        aggregated = get_aggregated_dataframe_sum(dataframe, [self.monthyear, self.category])
        source_data = self.__get_source_data_for_multi_line_plot(aggregated, first_chosen_category)
        line_plot, line_plot_source = self.create_line_plot(source_data)

        # statistics table Div
        line_values = source_data["ys"]
        statistics_data = self.__get_statistics_data(line_values, first_chosen_category)
        table_div = Div(text=self.statistics_table_html.format(**statistics_data))

        # Category dropdown widget
        dropdown = Select(title='Category:', value=first_chosen_category, options=unique_categories)

        # callback for dropdown, which will trigger changes in the view upon change of the category
        def callback(attr, old, new):
            if new != old:
                # updating lines in the plot - total stays the same, whereas category line changes
                new_ys = self.__get_source_data_for_multi_line_plot(aggregated, new)["ys"]
                line_plot_source.data["ys"] = new_ys

                # statistics table div gets updated with the new category data
                new_data = self.__get_statistics_data(new_ys, new)
                table_div.text = self.statistics_table_html.format(**new_data)

        dropdown.on_change("value", callback)

        return row(table_div, column(dropdown, line_plot))

    def create_line_plot(self, source_data, **kwargs):

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

        data = {
            "category": cat_name,
            "avg_all": avg["All"],
            "avg_category": avg["Cat"],
            "median_all": median["All"],
            "median_category": median["Cat"],
        }
        return data
