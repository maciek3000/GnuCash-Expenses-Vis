import numpy as np
import pandas as pd

from bokeh.models.widgets import CheckboxGroup, Div, Select
from bokeh.models import ColumnDataSource, CDSView, NumeralTickFormatter, GroupFilter, DataTable, TableColumn, CustomJS
from bokeh.plotting import figure
from bokeh.layouts import column, layout, row
from .bk_category import Category


class BokehApp(object):

    category_types = ["Simple", "Extended"]

    def __init__(self, dataframe, col_mapping):
        self.org_datasource = dataframe
        self.current_datasource = dataframe

        self.date = col_mapping["date"]
        self.price = col_mapping["price"]
        self.currency = col_mapping["currency"]
        self.product = col_mapping["product"]
        self.shop = col_mapping["shop"]
        self.all = col_mapping["all"]
        self.type = col_mapping["type"]
        self.category = col_mapping["category"]
        self.monthyear = col_mapping["monthyear"]

        self.category_creator = Category(self.category, self.monthyear, self.price, self.product,
                                         self.date, self.currency, self.shop)

    def settings(self, cat_name):
        all_cats = sorted(self.org_datasource[cat_name].unique().tolist())
        current_cats = self.current_datasource[cat_name].unique().tolist()

        def callback(new):
            chosen_filters = [all_cats[i] for i in new]
            cond = np.isin(self.org_datasource[cat_name], chosen_filters)
            self.current_datasource = self.org_datasource[cond]
            self.current_source = ColumnDataSource(self.current_datasource)

        checkbox_group = CheckboxGroup(
            labels=all_cats,
            active=[all_cats.index(x) for x in current_cats]
        )

        checkbox_group.on_click(callback)

        return checkbox_group

    def category_gridplot(self):

        return self.category_creator.gridplot(self.current_datasource)

    #TODO: category type radio buttons

    # Category Type radio buttons
    # TODO: functionality of Category Type
    #category_type_buttons = RadioGroup(labels=self.category_types,
    #                                   active=0)

    ########## old functions ##########

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
