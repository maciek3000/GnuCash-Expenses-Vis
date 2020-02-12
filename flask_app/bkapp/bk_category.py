import numpy as np
import statistics

from bokeh.models import ColumnDataSource, CustomJS
from bokeh.layouts import column, row
from bokeh.models import Select
from bokeh.plotting import figure
from bokeh.models.widgets import Div


class Category(object):

    table_text = """<table>
                    <tr>
                        <th></th>
                        <th>All</th>
                        <th>{category}</th>
                    </tr>
                    <tr>
                        <td>Average</td>
                        <td>{avg_all}</td>
                        <td>{avg_category}</td>
                    </tr>
                </table>"""

    def __init__(self):
        pass

    def get_gridplot(self, dataframe, category_name, month_name, price_name):
        line_plot = self.get_category_line_plot(dataframe, category_name, month_name, price_name)
        # info_table = self.get_info_table(dataframe)
        return line_plot

    def get_category_line_plot(self, dataframe, category_name, month_name, price_name):
        cats = dataframe[category_name].unique().tolist()
        cats.sort()

        months = dataframe[month_name].unique().tolist()
        months.sort()

        # getting values for the ColumnDataSource
        aggregated_df = dataframe.groupby([month_name, category_name]).sum().reset_index().sort_values(
            by=[month_name, category_name])
        total_values = aggregated_df.groupby([month_name]).sum()[price_name].unique().tolist()
        cat_dict = aggregated_df[aggregated_df[category_name] == cats[0]].set_index(month_name)[price_name].to_dict()
        cat_values = [cat_dict[month] if month in cat_dict else np.nan for month in months]

        avg_all = str(round(aggregated_df[price_name].mean(), 2))
        avg_category = str(round(aggregated_df[aggregated_df[category_name] == cats[0]][price_name].mean(), 2))

        source = ColumnDataSource({
            "xs": [months, months],
            "ys": [total_values, cat_values],
            "width": [3, 2],
            "color": ["blue", "red"]
        })

        # creating the figure
        p = figure(width=360, height=360, x_range=months, y_range=[0, max(total_values)])
        p.multi_line("xs", "ys", source=source, line_width="width", color="color")

        div = self.get_div(category=cats[0], avg_all=avg_all, avg_category=avg_category)

        def callback(attr, old, new):
            if new != old:
                new_dict = aggregated_df[aggregated_df[category_name] == new].set_index(month_name)[
                    price_name].to_dict()
                new_values = [new_dict[month] if month in new_dict else np.nan for month in months]
                source.data["ys"] = [total_values, new_values]

                div.text = self.table_text.format(avg_all=avg_all, category=new,
                                                  avg_category=np.nanmean(new_values))


        dropdown = Select(title='Category:', value=cats[0], options=cats)
        dropdown.on_change('value', callback)

        return row(div, column(dropdown, p))

    def get_info_table(self, dataframe, category_name, avg_all, avg_category):

        avg_all = str(round(dataframe['Price'].mean(), 2))

        div = self.get_div(category="Bread", avg_all=avg_all, avg_category="250")
        return div

    def get_div(self, **kwargs):
        text = self.table_text.format(**kwargs)

        div = Div(text=text)
        return div