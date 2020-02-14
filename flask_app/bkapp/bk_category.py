import numpy as np
import pandas as pd

from bokeh.models import ColumnDataSource
from bokeh.layouts import column, row
from bokeh.models import Select
from bokeh.plotting import figure
from bokeh.models.widgets import Div


def get_unique_values_from_column(df, col_name):
    return sorted(df[col_name].replace({np.nan: "nan"}).unique().tolist())


def get_aggregated_dataframe_sum(df, list_of_cols):
    agg = df.groupby(list_of_cols).sum().reset_index().sort_values(by=list_of_cols)
    return agg


class Category(object):

    table_html = """<table>
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
        unique_categories = get_unique_values_from_column(dataframe, self.category)

        first_chosen_category = unique_categories[0]
        aggregated = get_aggregated_dataframe_sum(dataframe, [self.monthyear, self.category])

        source_data = self.__get_source_data_for_multi_line_plot(aggregated, first_chosen_category)
        line_plot, line_plot_source = self.create_line_plot(source_data)
        line_values = source_data["ys"]
        table_div = Div(text=self.__get_table_div_text(line_values, first_chosen_category))
        dropdown = Select(title='Category:', value=first_chosen_category, options=unique_categories)

        def callback(attr, old, new):
            if new != old:
                new_ys = self.__get_source_data_for_multi_line_plot(aggregated, new)["ys"]
                line_plot_source.data["ys"] = new_ys
                table_div.text = self.__get_table_div_text(new_ys, new)

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

    def __get_table_div_text(self, lines, cat_name):
        values = pd.DataFrame({
            "All":  lines[0],
            "Cat": lines[1]
        }).describe()
        avg = values.loc["mean"]
        median = values.loc["50%"]

        kwargs = {
            "category": cat_name,
            "avg_all": avg["All"],
            "avg_category": avg["Cat"],
            "median_all": median["All"],
            "median_category": median["Cat"],
        }
        text = self.table_html.format(**kwargs)
        return text
