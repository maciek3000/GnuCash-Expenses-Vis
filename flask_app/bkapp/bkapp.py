import numpy as np
import pandas as pd

from bokeh.models.widgets import CheckboxGroup, Div, Select
from bokeh.models import ColumnDataSource, CDSView, NumeralTickFormatter, GroupFilter, DataTable, TableColumn, CustomJS
from bokeh.plotting import figure
from bokeh.layouts import column, layout, row

from .bk_category import Category
from .bk_overview import Overview
from .bk_trends import Trends

from .color_map import ColorMap

class BokehApp(object):

    category_types = ["Simple", "Extended"]

    def __init__(self, expense_dataframe, income_dataframe, col_mapping, server_date):
        self.expense_org_datasource = expense_dataframe
        self.expense_current_datasource = expense_dataframe
        self.income_org_datasource = income_dataframe
        self.income_current_datasource = income_dataframe

        self.date = col_mapping["date"]
        self.price = col_mapping["price"]
        self.currency = col_mapping["currency"]
        self.product = col_mapping["product"]
        self.shop = col_mapping["shop"]
        self.all = col_mapping["all"]
        self.type = col_mapping["type"]
        self.category = col_mapping["category"]
        self.monthyear = col_mapping["monthyear"]

        color_mapping = ColorMap()

        month_format = "%Y-%m"

        self.category_view = Category(self.category, self.monthyear, self.price, self.product,
                                 self.date, self.currency, self.shop, month_format, color_mapping)
        self.overview_view = Overview(self.category, self.monthyear, self.price, self.product,
                                 self.date, self.currency, self.shop, month_format, server_date, color_mapping)

        self.trends_view = Trends(self.category, self.monthyear, self.price, self.product,
                                self.date, self.currency, self.shop, month_format, color_mapping)

    def settings(self, cat_name):
        all_cats = sorted(self.expense_org_datasource[cat_name].unique().tolist())
        current_cats = self.expense_current_datasource[cat_name].unique().tolist()

        def callback(new):
            chosen_filters = [all_cats[i] for i in new]
            cond = np.isin(self.expense_org_datasource[cat_name], chosen_filters)
            self.expense_current_datasource = self.expense_org_datasource[cond]
            self.current_source = ColumnDataSource(self.expense_current_datasource)

        checkbox_group = CheckboxGroup(
            labels=all_cats,
            active=[all_cats.index(x) for x in current_cats]
        )

        checkbox_group.on_click(callback)

        return checkbox_group

    def category_gridplot(self):

        return self.category_view.gridplot(self.expense_current_datasource)

    def overview_gridplot(self):
        return self.overview_view.gridplot(self.expense_current_datasource, self.income_current_datasource)

    def trends_gridplot(self):
        return self.trends_view.gridplot(self.expense_current_datasource)

    #TODO: category type radio buttons

    # Category Type radio buttons
    # TODO: functionality of Category Type
    #category_type_buttons = RadioGroup(labels=self.category_types,
    #                                   active=0)

    ########## old functions ##########

    def trends(self, month_name):

        agg = self.expense_current_datasource.groupby([month_name]).sum().reset_index().sort_values(by=month_name)
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
        unique_categories = self.expense_current_datasource['Category'].unique().tolist()
        unique_categories.sort()

        months = self.expense_current_datasource['MonthYear'].unique().tolist()
        months.sort()

        df = self.expense_current_datasource[self.expense_current_datasource['Category'] == unique_categories[0]]
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
                df = self.expense_current_datasource[self.expense_current_datasource['Category'] == new]
                agg = df.groupby(['MonthYear']).sum().reset_index().sort_values(by='MonthYear')
                source.data = ColumnDataSource(agg).data

        # menu = list(zip(unique_categories, unique_categories))
        dropdown = Select(title='Category:', value=unique_categories[0], options=unique_categories)
        dropdown.on_change('value', callback)

        return column(dropdown, p)

    def some_data(self):
        agg = self.expense_current_datasource.groupby(['MonthYear']).sum().reset_index()

        val = agg['Price'].mean()
        text = 'Average expenses are: <p style="color:#9c2b19"> {} </p>'.format(val)
        t = Div(text=text, id="some_data_text")

        return t

    def test_table(self):

        agg = self.expense_current_datasource.groupby(["MonthYear", "Category"]).sum()
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
