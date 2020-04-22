import numpy as np
import pandas as pd

from ..observer import Observer

from .bk_category import Category
from .bk_overview import Overview
from .bk_trends import Trends
from .bk_settings import Settings

from .color_map import ColorMap


class BokehApp(object):


    observer = Observer()
    category_types = ["Simple", "Expanded", "Combinations (Experimental)"]

    def __init__(self, expense_dataframe, income_dataframe, col_mapping, server_date, category_sep):

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
        self.month_format = "%Y-%m"  # TODO: move to bkserver
        category_sep = category_sep

        # Settings Object
        self.settings = Settings(self.original_expense_dataframe[self.category],
                                 self.original_expense_dataframe[self.all],
                                 self.original_expense_dataframe[self.date],
                                 self.month_format,
                                 category_sep,
                                 self.category_types,
                                 self.observer,
                                 self)



        # View Objects
        self.category_view = Category(self.category, self.monthyear, self.price, self.product,
                                 self.date, self.currency, self.shop, self.month_format, color_mapping)
        self.overview_view = Overview(self.category, self.monthyear, self.price, self.product,
                                 self.date, self.currency, self.shop, self.month_format, server_date, color_mapping)
        self.trends_view = Trends(self.category, self.monthyear, self.price, self.product,
                                self.date, self.currency, self.shop, self.month_format, color_mapping)


        # State Variables
        self.chosen_category_column = self.category
        self.current_chosen_categories = None
        self.current_chosen_months = None

        # needs to be updated at the end for the observer decorator
        self.settings.initialize_settings_variables()


    def category_gridplot(self):
        self.__update_current_expense_dataframe()
        return self.category_view.gridplot(self.current_expense_dataframe, self.settings.chosen_categories)

    def overview_gridplot(self):
        self.__update_current_expense_dataframe()
        return self.overview_view.gridplot(self.current_expense_dataframe, self.current_income_dataframe)

    def trends_gridplot(self):
        self.__update_current_expense_dataframe()
        return self.trends_view.gridplot(self.current_expense_dataframe)

    def settings_categories(self):
        return self.settings.category_options()

    def settings_month_range(self):
        return self.settings.month_range_options()

    @observer.register
    def update_on_change(self, key, value):
        key_func_dict = {
            "chosen_categories": self.__update_current_chosen_categories,
            "chosen_category_type": self.__update_category_choice,
            "chosen_months": self.__update_current_chosen_months
             }

        func = key_func_dict[key]
        func(value)

    def __update_current_chosen_categories(self, categories):
        self.current_chosen_categories = categories

    def __update_current_chosen_months(self, months):
        self.current_chosen_months = months

    def __update_category_choice(self, category_type):

        d = {
            0: self.category,
            1: self.all,
            2: self.all
        }

        chosen_index = category_type
        self.chosen_category_column = d[chosen_index]

        for obj in [self.overview_view, self.trends_view, self.category_view]:
            obj.change_category_column(self.chosen_category_column)

    def __update_current_expense_dataframe(self):

        category_type = self.chosen_category_column
        months = pd.to_datetime(self.current_chosen_months).strftime(self.month_format)

        month_cond = np.isin(self.original_expense_dataframe[self.monthyear], months)

        # Last Category Type is Experimental
        if category_type != len(self.category_types):

            unchosen_cats = set(self.settings.all_categories) - set(self.current_chosen_categories)
            df = self.original_expense_dataframe[month_cond]

            for cat in unchosen_cats:
                cond = df[self.chosen_category_column].str.contains(cat)
                df = df[~cond]

            self.current_expense_dataframe = df

        else:
            cats = self.current_chosen_categories
            cond = np.isin(self.original_expense_dataframe[self.chosen_category_column], cats)
            self.current_expense_dataframe = self.original_expense_dataframe[cond & month_cond]


