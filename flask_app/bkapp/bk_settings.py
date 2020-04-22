import pandas as pd
import numpy as np

from bokeh.models.widgets import RadioGroup, CheckboxGroup, Div
from bokeh.layouts import column
from bokeh.plotting import figure

from ..observer import Observer

from .pandas_functions import create_combinations_of_sep_values




class Settings(object):

    # all_categories = Observer.watched_property("observer", "all_categories")
    chosen_categories = Observer.watched_property("observer", "chosen_categories", "parent")
    chosen_category_type = Observer.watched_property("observer", "chosen_category_type", "parent")

    def __init__(self, simple_categories_series, extended_categories_series, date_series,
                 month_year_format, category_sep, category_types, observer, bkapp):

        self.parent = bkapp
        self.observer = observer

        self.original_simple_categories = simple_categories_series
        self.original_extended_categories = extended_categories_series
        self.original_dates = date_series

        self.monthyear_format = month_year_format
        self.category_sep = category_sep
        self.category_type_labels = category_types

        # # Elements
        # self.category_options_grid = None
        # self.month_range_grid = None

        # Category State Variables
        self.all_categories_simple = None
        self.all_categories_extended = None
        self.all_categories_combinations = None

        self.all_categories = None

        # Elements
        self.checkbox_group = None

        # Month Range Variables
        self.all_months = None
        self.chosen_months = None

        # State
        self.are_categories_initialized = False

    def category_options(self):
        g = self.__category_gridplot()

        return g

    def initialize_settings_variables(self):
        self.__initialize_categories()

    def __category_gridplot(self):

        if not self.are_categories_initialized:
            self.__initialize_categories()

        chosen_index = self.chosen_category_type

        category_type_chooser = RadioGroup(
            labels=self.category_type_labels, active=chosen_index,
            css_classes=["category_types_buttons"], inline=True
        )

        checkbox_group = CheckboxGroup(
            labels=self.all_categories,
            active=[self.all_categories.index(x) for x in self.chosen_categories],
        )

        # set as attribute for RadioGroup Buttons Updates to have access to it
        self.checkbox_group = checkbox_group

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

        return grid

    def __initialize_categories(self):

        simple = self.original_simple_categories.sort_values().unique().tolist()
        extended = self.original_extended_categories.sort_values().unique().tolist()
        combinations = create_combinations_of_sep_values(extended, self.category_sep)

        self.all_categories_simple = simple
        self.all_categories_extended = extended
        self.all_categories_combinations = combinations

        self.chosen_category_type = 0
        self.all_categories = simple
        self.chosen_categories = simple

        self.are_categories_initialized = True

    def __update_categories_on_category_type_change(self, index):

        if index == 0:
            new = self.all_categories_simple
        elif index == 1:
            new = self.all_categories_extended
        else:
            new = self.all_categories_combinations

        self.all_categories = new
        self.chosen_categories = new

        self.chosen_category_type = index

        self.checkbox_group.labels = new
        self.checkbox_group.active = list(range(len(new)))

    def __update_chosen_categories_on_new(self, new):
        self.chosen_categories = [self.all_categories[x] for x in new]

    def month_range_options(self):
        if self.month_range_grid is None:
            self.__initialize_month_range_grid()

        return self.month_range_grid

    def __initialize_month_range_grid(self):

        self.month_range_grid = column(Div(text="pierwsyz div"), Div(text="drugi div"), name="kolyumna")

