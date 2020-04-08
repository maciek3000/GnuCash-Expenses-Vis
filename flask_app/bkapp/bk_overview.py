import pandas as pd
import numpy as np

from bokeh.models import ColumnDataSource, FactorRange
from bokeh.models.widgets import Div, Select
from bokeh.layouts import column, row
from bokeh.plotting import figure

from datetime import datetime

from .pandas_functions import unique_values_from_column

from math import pi

class Overview(object):

    month_title = " Overview"

    expenses_chosen_month = "<span>{expenses_last_month:,.2f}</span>"
    expenses_chosen_month_subtitle = "Total Expenses This Month"

    trivia_title = "Trivia"
    total_products_chosen_month = "Products Bought: <span>{total_products_last_month}</span>"
    different_shops_chosen_month = "Unique Shops visited: <span>{different_shops_last_month}</span>"
    savings_positive = "Congratulations! You saved <span id='positive_savings'>{savings:.2%}</span> of your income this month!"
    savings_negative = "Uh oh.. You overpaid <span id='negative_savings'>{savings:.2%}</span> of your income"

    category_expenses_title = "Expenses from Categories"

    piechart_start_angle = (pi/2)

    def __init__(self, category_colname, monthyear_colname, price_colname, product_colname,
                 date_colname, currency_colname, shop_colname, month_format, server_date, color_mapping):

        # Column Names
        self.category = category_colname
        self.monthyear = monthyear_colname
        self.price = price_colname
        self.product = product_colname
        self.date = date_colname
        self.currency = currency_colname
        self.shop = shop_colname

        self.monthyear_format = month_format
        self.server_date = server_date

        self.color_map = color_mapping

        self.grid_elem_dict = None
        self.grid_source_dict = None

        self.original_expense_df = None
        self.original_income_df = None
        self.chosen_month_expense_df = None
        self.next_month_expense_df = None
        self.chosen_month_income_df = None
        self.next_month_income_df = None

        self.months = None
        self.chosen_month = None
        self.next_month = None

        self.g_month_dropdown = "Month Dropdown"
        self.g_month_title = "Month Title"
        self.g_expenses_chosen_month = "Expenses Last Month"
        self.g_expenses_chosen_month_subtitle = "Expenses Last Month Subtitle"
        self.g_trivia_title = "Trivia Title"
        self.g_total_products_chosen_month = "Products Last Month"
        self.g_different_shops_chosen_month = "Unique Shops"
        self.g_savings_info = "Savings Information"
        self.g_savings_piechart = "Savings Piechart"
        self.g_category_expenses_title = "Category Expenses Title"
        self.g_category_expenses = "Category Expenses"

    def gridplot(self, expense_dataframe, income_dataframe):

        self.original_expense_df = expense_dataframe
        self.original_income_df = income_dataframe
        self.months = unique_values_from_column(self.original_expense_df, self.monthyear)

        self.initialize_grid_elements()



        self.update_gridplot()

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

        def dropdown_callback(attr, old, new):
            if new != old:
                self.update_gridplot(new)

        self.grid_elem_dict[self.g_month_dropdown].on_change("value", dropdown_callback)

        # TODO: add draft row for Budget

        output = column(
            row(
                self.grid_elem_dict[self.g_month_dropdown],
                self.grid_elem_dict[self.g_month_title],
                css_classes=["title_row"],
            ),
            row(
                column(
                    self.grid_elem_dict[self.g_expenses_chosen_month],
                    self.grid_elem_dict[self.g_expenses_chosen_month_subtitle],
                    self.grid_elem_dict[self.g_trivia_title],
                    self.grid_elem_dict[self.g_total_products_chosen_month],
                    self.grid_elem_dict[self.g_different_shops_chosen_month],
                    css_classes=["info_column"]
                ),
                column(
                    self.grid_elem_dict[self.g_savings_info],
                    self.grid_elem_dict[self.g_savings_piechart],
                    css_classes=["piechart_column"]
                ),
                column(
                    self.grid_elem_dict[self.g_category_expenses_title],
                    self.grid_elem_dict[self.g_category_expenses],
                    css_classes=["barchart_column"]
                ),
            css_classes=["chosen_month_row"]
            )
        )

        return output

    def initialize_grid_elements(self):

        elem_dict = {}
        source_dict = {}

        elem_dict[self.g_month_dropdown] = Select(options=self.months,
                                                  css_classes=["month_dropdown"])
        elem_dict[self.g_month_title] = Div(text="", css_classes=["month_title"])

        info_element_class = "info_element"

        elem_dict[self.g_expenses_chosen_month] = Div(
            text="", css_classes=[info_element_class]
        )
        elem_dict[self.g_expenses_chosen_month_subtitle] = Div(
            text=self.expenses_chosen_month_subtitle, css_classes=[info_element_class])

        elem_dict[self.g_trivia_title] = Div(text=self.trivia_title, css_classes=[info_element_class])
        elem_dict[self.g_total_products_chosen_month] = Div(text="", css_classes=[info_element_class])
        elem_dict[self.g_different_shops_chosen_month] = Div(text="", css_classes=[info_element_class])

        elem_dict[self.g_savings_info] = Div(text="", css_classes=["savings_information"])

        source_dict[self.g_savings_piechart] = self.__create_savings_piechart_source()
        elem_dict[self.g_savings_piechart] = self.__create_savings_piechart(source_dict[self.g_savings_piechart])

        elem_dict[self.g_category_expenses_title] = Div(text=self.category_expenses_title, css_classes=[
            "category_expenses_title"
        ])
        source_dict[self.g_category_expenses] = self.__create_category_barplot_source()
        elem_dict[self.g_category_expenses] = self.__create_category_barplot(source_dict[self.g_category_expenses])

        self.grid_elem_dict = elem_dict
        self.grid_source_dict = source_dict

    def update_gridplot(self, month=None):

        self.__update_chosen_and_next_months(month)
        self.__update_dataframes()

        self.__update_last_month_title()
        self.__update_expenses_last_month()
        self.__update_total_products_last_month()
        self.__update_different_shops_last_month()

        self.__update_piechart()
        self.__update_category_barplot()


    # ========== Creation of Grid Elements ========== #

    def __create_savings_piechart_source(self):

        data = {
            "end_angle": [0.5*pi],
            "color": ["red"],
            "start_angle": [self.piechart_start_angle]
        }

        source = ColumnDataSource(
            data=data
        )

        return source

    def __create_savings_piechart(self, source):

        wedge_kwargs = {
            "x": 0,
            "y": 1,
            "radius": 0.2,
            "direction": "clock",
        }

        p = figure(height=250, width=250, x_range=(-wedge_kwargs["radius"], wedge_kwargs["radius"]),
                   toolbar_location=None)

        p.wedge(
            start_angle=0, end_angle=2*pi,
            fill_color=self.color_map["background_gray"], line_color=self.color_map["background_gray"],
            **wedge_kwargs
        )

        p.wedge(
            start_angle="start_angle", end_angle='end_angle',
            fill_color="color", line_color="color",
            source=source,
            **wedge_kwargs
        )

        p.axis.visible = False
        p.axis.axis_label = None

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

        # TODO: add hover tool

        p = figure(width=550, height=400, x_range=source.data["x"], toolbar_location=None)
        p.vbar("x", top="top", width=0.9, color=self.color_map["link_background"], source=source)

        p.xaxis.major_label_orientation = 0.9
        p.axis.major_tick_in = None
        p.axis.minor_tick_in = None
        p.axis.major_tick_line_color = self.color_map["background_gray"]
        p.axis.minor_tick_out = None
        p.axis.axis_line_color = "white"
        p.axis.major_label_text_font_size = "13px"
        p.axis.major_label_text_color = "#C5C5C5"

        return p

    # ========== Updating Grid Elements ========== #

    def __update_chosen_and_next_months(self, month=None, date_format=None):
        if date_format is None:
            date_format = self.monthyear_format

        if month is None:
            chosen_month = (pd.Timestamp(self.server_date) - pd.DateOffset(months=1)).strftime(date_format)
            if chosen_month not in self.months:
                chosen_month = self.months[-1]

            # if month is not passed, it means that this is View Initialization and Dropdown Selection should be done
            self.grid_elem_dict[self.g_month_dropdown].value = chosen_month
        else:
            chosen_month = month

        next_month = (pd.Timestamp(datetime.strptime(chosen_month, date_format)) + pd.DateOffset(months=1)).strftime(date_format)
        self.chosen_month = chosen_month
        self.next_month = next_month

    def __update_dataframes(self):

        self.__update_expense_dataframes()
        self.__update_income_dataframes()

    def __update_expense_dataframes(self):
        self.chosen_month_expense_df = self.original_expense_df[self.original_expense_df[self.monthyear] == self.chosen_month]
        self.next_month_expense_df = self.original_expense_df[self.original_expense_df[self.monthyear] == self.next_month]

    def __update_income_dataframes(self):
        self.chosen_month_income_df = self.original_income_df[self.original_income_df[self.monthyear] == self.chosen_month]
        self.next_month_income_df = self.original_income_df[self.original_income_df[self.monthyear] == self.next_month]

    def __update_last_month_title(self):
        last_month = self.chosen_month
        self.grid_elem_dict[self.g_month_title].text = self.month_title.format(last_month=last_month)

    def __update_expenses_last_month(self):
        expenses_last_month = self.chosen_month_expense_df[self.price].sum()
        self.grid_elem_dict[self.g_expenses_chosen_month].text = self.expenses_chosen_month.format(expenses_last_month=expenses_last_month)

    def __update_total_products_last_month(self):
        total_products_last_month = self.chosen_month_expense_df.shape[0]
        self.grid_elem_dict[self.g_total_products_chosen_month].text = self.total_products_chosen_month.format(total_products_last_month=total_products_last_month)

    def __update_different_shops_last_month(self):
        different_shops_last_month = len(unique_values_from_column(self.chosen_month_expense_df, self.shop))
        self.grid_elem_dict[self.g_different_shops_chosen_month].text = self.different_shops_chosen_month.format(different_shops_last_month=different_shops_last_month)

    def __update_piechart(self):

        savings = self.__calculate_expense_percentage()

        self.__update_savings_info(savings)
        self.__update_savings_piechart(savings)

    def __calculate_expense_percentage(self):

        # negative as income is expressed as negative transaction
        income_month = -(self.chosen_month_income_df[self.price].sum())
        expense_month = self.chosen_month_expense_df[self.price].sum()

        difference = income_month - expense_month

        if income_month == 0:
            part = np.nan
        else:
            part = difference / income_month

        return part

    def __update_savings_info(self, savings):

        if savings >= 0:
            savings_text = self.savings_positive
        else:
            savings = -savings
            savings_text = self.savings_negative

        self.grid_elem_dict[self.g_savings_info].text = savings_text.format(savings=savings)

    def __update_savings_piechart(self, savings):

        if savings >= 0:
            part = savings
            color = "#0f5e3b"
        else:
            part = -savings
            color = self.color_map["contrary"]

        # negative values move angle clockwise
        angle_value = -(part*2*pi) + self.piechart_start_angle

        #
        limit = -(2*pi)
        if angle_value <= limit:
            angle_value = limit

        angles = [angle_value]

        source = self.grid_source_dict[self.g_savings_piechart]
        source.data["end_angle"] = angles
        source.data["color"] = [color]

    def __update_category_barplot(self):

        agg_df = self.chosen_month_expense_df.groupby([self.category]).sum().reset_index().sort_values(by=[self.price], ascending=False)

        fig = self.grid_elem_dict[self.g_category_expenses]
        source = self.grid_source_dict[self.g_category_expenses]

        # TODO: if category length is too big, reduce it to some factor (e.g. every third element)

        fig.x_range.factors = agg_df[self.category].tolist()

        source.data["x"] = agg_df[self.category]
        source.data["top"] = agg_df[self.price]






