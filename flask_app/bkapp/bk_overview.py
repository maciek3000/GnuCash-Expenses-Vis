import pandas as pd
import numpy as np

from bokeh.models import ColumnDataSource
from bokeh.models.widgets import Div
from bokeh.layouts import column, row
from bokeh.plotting import figure
from bokeh.transform import cumsum

from datetime import datetime

from .pandas_functions import unique_values_from_column

from math import pi

class Overview(object):

    last_month = "{last_month}"
    expenses_last_month = "Total Expenses: {expenses_last_month:.2f}"
    total_products_last_month = "Products Bought: {total_products_last_month}"
    different_shops_last_month = "Unique Shops visited: {different_shops_last_month}"

    def __init__(self, category_colname, monthyear_colname, price_colname, product_colname,
                 date_colname, currency_colname, shop_colname, server_date):

        # Column Names
        self.category = category_colname
        self.monthyear = monthyear_colname
        self.price = price_colname
        self.product = product_colname
        self.date = date_colname
        self.currency = currency_colname
        self.shop = shop_colname

        self.server_date = server_date

        self.grid_elem_dict = None
        self.grid_source_dict = None

        self.original_expense_df = None
        self.original_income_df = None
        self.last_month_expense_df = None
        self.current_month_expense_df = None

        self.months = None
        self.last_month = None
        self.current_month = None

        self.g_last_month = "Last Month"
        self.g_expenses_last_month = "Expenses Last Month"
        self.g_total_products_last_month = "Products Last Month"
        self.g_different_shops_last_month = "Unique Shops"
        self.g_savings_info = "Savings Information"
        self.g_savings_piechart = "Savings Piechart"
        self.g_category_expenses = "Category Expenses"

    def gridplot(self, expense_dataframe, income_dataframe):

        self.original_expense_df = expense_dataframe
        self.original_income_df = income_dataframe
        self.months = unique_values_from_column(self.original_expense_df, self.monthyear)

        self.initialize_grid_elements()

        self.__update_current_and_future_months()

        # ##################################################### #
        # Month             Saved or over bought        Bar Plot with Categories (comparison to Last Month Budget?)
        # Expenses          Saved or over bought        Bar Plot with Categories
        # Stat 1            Piechart                    Bar Plot with Categories
        # Stat 2            Piechart                    Bar Plot with Categories
        # ##################################################### #
        # TBD TBD TBD TBD TBD TD TBD TBD TBD TBD TBD TD TBD TBD TBD TBD TBD TD
        # Budget
        # Categories R/IR                   Bar Plot with Regular Category Expenses (Irregular one Bar)
        # Box
        # Box
        # Box
        # Box

        output = row(
            column(
                self.grid_elem_dict[self.g_last_month],
                self.grid_elem_dict[self.g_expenses_last_month],
                self.grid_elem_dict[self.g_total_products_last_month],
                self.grid_elem_dict[self.g_different_shops_last_month]
            ),
            column(
                self.grid_elem_dict[self.g_savings_info],
                self.grid_elem_dict[self.g_savings_piechart]
            ),
            column(
                self.grid_elem_dict[self.g_category_expenses]
            )
        )

        return output

    def initialize_grid_elements(self):

        elem_dict = {}
        source_dict = {}

        minor_stat_class = "last_month_minor_info"
        elem_dict[self.g_last_month] = Div(text="", css_classes=["last_month"])
        elem_dict[self.g_expenses_last_month] = Div(text="", css_classes=["expenses_last_month"])
        elem_dict[self.g_total_products_last_month] = Div(text="", css_classes=[minor_stat_class])
        elem_dict[self.g_different_shops_last_month] = Div(text="", css_classes=[minor_stat_class])

        elem_dict[self.g_savings_info] = Div(text="", css_classes=["savings_information"])

        source_dict[self.g_savings_piechart] = self.__create_savings_piechart_source()
        elem_dict[self.g_savings_piechart] = self.__create_savings_piechart(source_dict[self.g_savings_piechart])

        source_dict[self.g_category_expenses] = self.__create_category_barplot_source()
        elem_dict[self.g_category_expenses] = self.__create_category_barplot(source_dict[self.g_category_expenses])

        self.grid_elem_dict = elem_dict
        self.grid_source_dict = source_dict

    def update_gridplot(self, month=None):

        self.__update_current_and_future_months(month)


    # ========== Creation of Grid Elements ========== #

    def __create_savings_piechart_source(self):

        data = {
            "angle": [0.5*pi, 1.5*pi],
            "color": ["red", "blue"]
        }

        source = ColumnDataSource(
            data=data
        )

        return source

    def __create_savings_piechart(self, source):

        p = figure(plot_height=150, x_range=(-0.5, 1.0))

        p.wedge(
            x=0, y=1, radius=0.4,
            start_angle=cumsum("angle", include_zero=True), end_angle=cumsum("angle"),
            fill_color="color",
            source=source
        )

        return p

    def __create_category_barplot_source(self):

        data = {
            "x": ["a"],
            "top": [1]
        }

        source = ColumnDataSource(
            data=data
        )

        return source

    def __create_category_barplot(self, source):

        p = figure(width=480, height=360, x_range=source.data["x"])
        p.vbar("x", top="top", width=0.9, source=source)

        return p

    # ========== Updating Grid Elements ========== #

    def __update_current_and_future_months(self, month=None, date_format="%m-%Y"):
        if month is None:
            chosen_month = (pd.Timestamp(self.server_date) - pd.DateOffset(months=1)).strftime(date_format)
        else:
            chosen_month = month

        next_month = (pd.Timestamp(datetime.strptime(chosen_month, date_format)) + pd.DateOffset(months=1)).strftime(date_format)
        self.last_month = chosen_month
        self.current_month = next_month

    def __update_dataframes(self):

        self.__update_expense_dataframe()
        self.__update_income_dataframe()

    def __update_expense_dataframe(self):
        pass

    def __update_income_dataframe(self):
        pass
