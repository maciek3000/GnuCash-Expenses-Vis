import pandas as pd
import numpy as np

from bokeh.models.widgets import RadioGroup, CheckboxGroup
from bokeh.layouts import column
from bokeh.plotting import figure

from ..observer import Observer

from .pandas_functions import create_combinations_of_sep_values




class Settings(object):

    # all_categories = Observer.watched_property("observer", "all_categories")
    chosen_categories = Observer.watched_property("observer", "chosen_categories")


    category_types = ["Simple", "Expanded", "Combinations"]

    def __init__(self, simple_categories_series, extended_categories_series, date_series,
                 month_year_format, observer):

        self.observer = observer

        self.original_simple_categories = simple_categories_series
        self.original_extended_categories = extended_categories_series
        self.original_dates = date_series

        self.monthyear_format = month_year_format


        # Elements
        self.category_options_grid = None
        self.month_range_grid = None

        # Category State Variables
        self.all_categories_simple = None
        self.all_categories_extended = None
        self.all_categories_combinations = None

        # Watched Category Properties
        self.all_categories = None
        self.chosen_categories = None
        self.chosen_category_type = None

        self.checkbox_group = None

        # Month Range Variables
        self.all_months = None
        self.chosen_months = None



    def category_options(self):
        if self.category_options_grid is None:
            self.__initialize_category_options_grid()

        return self.category_options_grid

    def month_range_options(self):
        if self.month_range_grid is None:
           self.__initialize_month_range_grid()

        return self.month_range_grid


    def __initialize_category_options_grid(self):

        self.__initialize_categories()


        first_selected_index = 0

        category_type_chooser = RadioGroup(
            labels=self.category_types, active=first_selected_index,
            css_classes=["category_types_buttons"], inline=True
        )

        checkbox_group = CheckboxGroup(
            labels=[],
            active=[],
        )

        self.checkbox_group = checkbox_group

        self.__update_categories_on_category_type_change(first_selected_index)

        def callback_on_category_type_change(attr, old, new):
            if new != old:
                self.__update_categories_on_category_type_change(new)

        category_type_chooser.on_change("active", callback_on_category_type_change)

        def callback_on_checkbox_change(new):
            self.__update_chosen_categories_on_new(new)

        checkbox_group.on_click(callback_on_checkbox_change)

        grid = column(
            category_type_chooser,
            checkbox_group
        )

        self.category_options_grid = grid

    def __initialize_month_range_grid(self):

        self.month_range_grid = figure()

    def __initialize_categories(self):

        simple = self.original_simple_categories.unique().tolist()
        extended = self.original_extended_categories.unique().tolist()
        combinations = create_combinations_of_sep_values(extended, ":")

        self.all_categories_simple = simple
        self.all_categories_extended = extended
        self.all_categories_combinations = combinations

    def __update_categories_on_category_type_change(self, index):

        if index == 0:
            new = self.all_categories_simple
        elif index == 1:
            new = self.all_categories_extended
        else:
            new = self.all_categories_combinations

        self.all_categories = new
        self.chosen_categories = new

        self.chosen_category_type = self.category_types[index]

        self.checkbox_group.labels = new
        self.checkbox_group.active = list(range(len(new)))

    def __update_chosen_categories_on_new(self, new):
        self.chosen_categories = [self.all_categories[x] for x in new]

