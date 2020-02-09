import numpy as np
import pandas as pd

from bokeh.models.widgets import CheckboxGroup, Div, Select
from bokeh.models import ColumnDataSource, CDSView, NumeralTickFormatter, GroupFilter, DataTable, TableColumn
from bokeh.plotting import figure
from bokeh.layouts import column


class BokehApp(object):

    def __init__(self, dataframe):
        self.org_datasource = dataframe
        self.current_datasource = dataframe

    def settings(self, cat_name):
        all_cats = sorted(self.org_datasource[cat_name].unique().tolist())
        current_cats = self.current_datasource[cat_name].unique().tolist()

        def callback(new):
            chosen_filters = [all_cats[i] for i in new]
            cond = np.isin(self.org_datasource[cat_name], chosen_filters)
            self.current_datasource = self.org_datasource[cond]

        checkbox_group = CheckboxGroup(
            labels=all_cats,
            active=[all_cats.index(x) for x in current_cats]
        )

        checkbox_group.on_click(callback)

        return checkbox_group

    def trends(self, month_name):

        agg = self.current_datasource.groupby([month_name]).sum().reset_index().sort_values(by=month_name)
        source = ColumnDataSource(agg)

        p = figure(width=480, height=480, x_range=agg[month_name])
        p.vbar(x=month_name, width=0.9, top='Price', source=source, color='#8CA8CD')

        p.xaxis.major_tick_line_color = None
        p.xaxis.minor_tick_line_color = None
        p.yaxis.major_tick_line_color = None
        p.yaxis.minor_tick_line_color = None

        p.yaxis[0].formatter = NumeralTickFormatter(format="0.0a")

        p.xaxis.axis_line_color = "#C7C3C3"
        p.yaxis.axis_line_color = "#C7C3C3"

        p.xaxis.major_label_text_color = "#8C8C8C"
        p.yaxis.major_label_text_color = "#8C8C8C"

        return p

    def category(self, category_name, month_name, price_name):
        cats = self.current_datasource[category_name].unique().tolist()
        cats.sort()

        months = self.current_datasource[month_name].unique().tolist()
        months.sort()

        # getting values for the ColumnDataSource
        aggregated_df = self.current_datasource.groupby([month_name, category_name]).sum().reset_index().sort_values(by=[month_name, category_name])
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
                new_dict = aggregated_df[aggregated_df[category_name] == new].set_index(month_name)[price_name].to_dict()
                new_values = [new_dict[month] if month in new_dict else np.nan for month in months]
                source.data["ys"] = [total_values, new_values]

        dropdown = Select(title='Category:', value=cats[0], options=cats)
        dropdown.on_change('value', callback)

        return column(dropdown, p)


    def old_category(self):
        unique_categories = self.current_datasource['Category'].unique().tolist()
        unique_categories.sort()

        months = self.current_datasource['MonthYear'].unique().tolist()
        months.sort()

        df = self.current_datasource[self.current_datasource['Category'] == unique_categories[0]]
        agg = df.groupby(['MonthYear']).sum().reset_index().sort_values(by='MonthYear')
        source = ColumnDataSource(data=agg)

        p = figure(width=360, height=360, x_range=months)
        p.vbar(x='MonthYear', top='Price', width=0.9, source=source, color='#8CA8CD')

        p.xaxis.major_tick_line_color = None
        p.xaxis.minor_tick_line_color = None
        p.yaxis.major_tick_line_color = None
        p.yaxis.minor_tick_line_color = None

        p.yaxis[0].formatter = NumeralTickFormatter(format="0.0a")

        p.xaxis.axis_line_color = "#C7C3C3"
        p.yaxis.axis_line_color = "#C7C3C3"

        p.xaxis.major_label_text_color = "#8C8C8C"
        p.yaxis.major_label_text_color = "#8C8C8C"

        def callback(attr, old, new):
            if new != old:
                df = self.current_datasource[self.current_datasource['Category'] == new]
                agg = df.groupby(['MonthYear']).sum().reset_index().sort_values(by='MonthYear')
                source.data = ColumnDataSource(agg).data

        # menu = list(zip(unique_categories, unique_categories))
        dropdown = Select(title='Category:', value=unique_categories[0], options=unique_categories)
        dropdown.on_change('value', callback)

        return column(dropdown, p)

    def some_data(self):
        agg = self.current_datasource.groupby(['MonthYear']).sum().reset_index()

        val = agg['Price'].mean()
        text = 'Average expenses are: <p style="color:#9c2b19"> {} </p>'.format(val)
        t = Div(text=text, id="some_data_text")

        return t

    def test_table(self):

        agg = self.current_datasource.groupby(["MonthYear", "Category"]).sum()
        month_prices = agg.reset_index().groupby(["MonthYear"]).sum()
        agg = agg.merge(month_prices, how="inner", left_index=True, right_index=True).reset_index().sort_values(by=["MonthYear", "Category"])
        source = ColumnDataSource(agg)

        print(agg.columns)

        columns = [
            TableColumn(field="MonthYear", title="Month"),
            TableColumn(field="Category", title="Category"),
            TableColumn(field="Price_x", title="Price"),
            TableColumn(field="Price_y", title="MonthPrice")
        ]

        data_table2 = DataTable(source=source, columns=columns, width=480, height=240)

                            
        return data_table2