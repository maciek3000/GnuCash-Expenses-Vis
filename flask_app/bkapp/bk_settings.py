import pandas as pd

from datetime import datetime

from bokeh.models.widgets import RadioGroup, CheckboxGroup, DateRangeSlider
from bokeh.layouts import column

from ..observer import Observer

from .pandas_functions import create_combinations_of_sep_values


class Settings(object):

    chosen_categories = Observer.watched_property("observer", "chosen_categories", "parent")
    chosen_category_type = Observer.watched_property("observer", "chosen_category_type", "parent")
    chosen_months = Observer.watched_property("observer", "chosen_months", "parent")

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

        # Category State Variables
        self.all_categories_simple = None
        self.all_categories_extended = None
        self.all_categories_combinations = None

        self.all_categories = None

        # Elements
        self.checkbox_group = None

        # Month Range Variables
        self.all_months = None

        # State
        self.are_categories_initialized = False
        self.is_month_range_initialized = False

    def category_options(self):
        g = self.__category_gridplot()

        return g

    def month_range_options(self):
        g = self.__month_range_gridplot()

        return g

    def initialize_settings_variables(self):
        self.__initialize_categories()
        self.__initialize_months()


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

    def __month_range_gridplot(self):

        if not self.is_month_range_initialized:
            self.__initialize_months()


        fig = DateRangeSlider(start=self.all_months[0], end=self.all_months[-1], step=1,
                          value=(self.chosen_months[0], self.chosen_months[-1]),
                          format="%b-%Y", title="Chosen Month Range: ",
                          css_classes=["month_range_slider"])


        def month_range_callback(attr, old, new):
            old_str = self.__create_timetuple_string_from_timestamp(old, self.monthyear_format)
            new_str = self.__create_timetuple_string_from_timestamp(new, self.monthyear_format)
            if old_str != new_str:
                self.__update_chosen_months(new)

        fig.on_change("value", month_range_callback)

        return fig

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

    def __initialize_months(self):

        start_date = self.original_dates.min()
        stop_date = self.original_dates.max()

        all_dates_range = pd.to_datetime(pd.date_range(start_date, stop_date, freq="M")).tolist()

        self.all_months = all_dates_range
        self.chosen_months = all_dates_range

        self.is_month_range_initialized = True

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


    def __create_timetuple_string_from_timestamp(self, single_tuple,  date_format):
        if type(single_tuple[0]) is pd.Timestamp:
            single_tuple = tuple([x.timestamp() for x in single_tuple])
        val = tuple(map(lambda x: datetime.fromtimestamp(float(x) / 1e3).strftime(date_format), single_tuple))
        return val

    def __update_chosen_months(self, new):

        # done to first convert timestamp to datetime and then to set datetime to day 1 - this way
        # date_range is properly created
        new = tuple(map(lambda x: datetime.fromtimestamp(float(x) / 1e3), new))
        new = [datetime(year=x.year, month=x.month, day=1).strftime("%Y-%m-%d") for x in new]

        dr = pd.date_range(new[0], new[1], freq="MS", normalize=True).tolist()

        self.chosen_months = dr
