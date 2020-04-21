import numpy as np
import pandas as pd

from bokeh.models.widgets import CheckboxGroup, Div, Select, Slider
from bokeh.models import ColumnDataSource, CDSView, NumeralTickFormatter, GroupFilter, DataTable, TableColumn, CustomJS
from bokeh.plotting import figure
from bokeh.layouts import column, layout, row

from .bk_category import Category
from .bk_overview import Overview
from .bk_trends import Trends

from .color_map import ColorMap

class BokehApp(object):

    category_types = ["Simple", "Expanded", "Combinations"]

    def __init__(self, expense_dataframe, income_dataframe, col_mapping, server_date):

        # DataFrames
        self.original_expense_dataframe = expense_dataframe
        self.current_expense_dataframe = expense_dataframe
        self.original_income_dataframe = income_dataframe
        self.current_income_dataframe = income_dataframe

        # Column Names
        self.date = col_mapping["date"]
        self.price = col_mapping["price"]
        self.currency = col_mapping["currency"]
        self.product = col_mapping["product"]
        self.shop = col_mapping["shop"]
        self.all = col_mapping["all"]
        self.type = col_mapping["type"]
        self.category = col_mapping["category"]
        self.monthyear = col_mapping["monthyear"]

        # Variables and Objects
        color_mapping = ColorMap()
        month_format = "%Y-%m"

        # View Objects
        self.category_view = Category(self.category, self.monthyear, self.price, self.product,
                                 self.date, self.currency, self.shop, month_format, color_mapping)
        self.overview_view = Overview(self.category, self.monthyear, self.price, self.product,
                                 self.date, self.currency, self.shop, month_format, server_date, color_mapping)
        self.trends_view = Trends(self.category, self.monthyear, self.price, self.product,
                                self.date, self.currency, self.shop, month_format, color_mapping)

        # Category State Variables
        self.category_column = None
        self.all_categories_simple = None
        self.all_categories_extended = None
        self.all_categories_combinations = None

        self.all_categories = None
        self.chosen_categories = None

        # Month Range Variables
        self.all_months = None
        self.chosen_months = None

        self.__create_initial_categories()
        self.__create_initial_months_list()

    def category_gridplot(self):
        return self.category_view.gridplot(self.current_expense_dataframe)

    def overview_gridplot(self):
        return self.overview_view.gridplot(self.current_expense_dataframe, self.current_income_dataframe)

    def trends_gridplot(self):
        return self.trends_view.gridplot(self.current_expense_dataframe)

    def settings_categories(self):


        cat_name = "ALL_CATEGORIES"
        all_cats = sorted(self.original_expense_dataframe[cat_name].unique().tolist())
        current_cats = self.current_expense_dataframe[cat_name].unique().tolist()

        def callback(new):
            chosen_filters = [all_cats[i] for i in new]
            cond = np.isin(self.original_expense_dataframe[cat_name], chosen_filters)
            self.current_expense_dataframe = self.original_expense_dataframe[cond]

        checkbox_group = CheckboxGroup(
            labels=all_cats,
            active=[all_cats.index(x) for x in current_cats]
        )

        checkbox_group.on_click(callback)

        return checkbox_group

    def month_range_slider(self):

        p = Slider(start=1, end=10)

        return p

    def __create_initial_categories(self):
        df = self.original_expense_dataframe

    #TODO: category type radio buttons

    # Category Type radio buttons
    # TODO: functionality of Category Type
    #category_type_buttons = RadioGroup(labels=self.category_types,
    #                                   active=0)

    ########## old functions ##########

    def trends(self, month_name):

        agg = self.current_expense_dataframe.groupby([month_name]).sum().reset_index().sort_values(by=month_name)
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
        unique_categories = self.current_expense_dataframe['Category'].unique().tolist()
        unique_categories.sort()

        months = self.current_expense_dataframe['MonthYear'].unique().tolist()
        months.sort()

        df = self.current_expense_dataframe[self.current_expense_dataframe['Category'] == unique_categories[0]]
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
                df = self.current_expense_dataframe[self.current_expense_dataframe['Category'] == new]
                agg = df.groupby(['MonthYear']).sum().reset_index().sort_values(by='MonthYear')
                source.data = ColumnDataSource(agg).data

        # menu = list(zip(unique_categories, unique_categories))
        dropdown = Select(title='Category:', value=unique_categories[0], options=unique_categories)
        dropdown.on_change('value', callback)

        return column(dropdown, p)

    def some_data(self):
        agg = self.current_expense_dataframe.groupby(['MonthYear']).sum().reset_index()

        val = agg['Price'].mean()
        text = 'Average expenses are: <p style="color:#9c2b19"> {} </p>'.format(val)
        t = Div(text=text, id="some_data_text")

        return t

    def test_table(self):

        agg = self.current_expense_dataframe.groupby(["MonthYear", "Category"]).sum()
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
