import numpy as np

from bokeh.models import ColumnDataSource
from bokeh.layouts import column
from bokeh.models import Select
from bokeh.plotting import figure


class Category(object):

    def __init__(self):
        pass

    def get_gridplot(self, dataframe, category_name, month_name, price_name):
        g = self.get_category_line_plot(dataframe, category_name, month_name, price_name)
        return g

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

        source = ColumnDataSource({
            "xs": [months, months],
            "ys": [total_values, cat_values],
            "width": [3, 2],
            "color": ["blue", "red"]
        })

        # creating the figure
        p = figure(width=360, height=360, x_range=months, y_range=[0, max(total_values)])
        p.multi_line("xs", "ys", source=source, line_width="width", color="color")

        def callback(attr, old, new):
            if new != old:
                new_dict = aggregated_df[aggregated_df[category_name] == new].set_index(month_name)[
                    price_name].to_dict()
                new_values = [new_dict[month] if month in new_dict else np.nan for month in months]
                source.data["ys"] = [total_values, new_values]

        dropdown = Select(title='Category:', value=cats[0], options=cats)
        dropdown.on_change('value', callback)

        return column(dropdown, p)