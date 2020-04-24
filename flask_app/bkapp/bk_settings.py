import pandas as pd
from datetime import datetime

from bokeh.models.widgets import RadioGroup, CheckboxGroup, DateRangeSlider
from bokeh.layouts import column

from ..observer import Observer
from .pandas_functions import create_combinations_of_sep_values


class Settings(object):
    """Settings Object used in BokehApp, providing means for the User to manipulate range of data
        in other Views in flask_app.

        Object expects:
            - 3 Series with Column data from Expense Dataframe:
                - .category Column
                - .all Column
                - .date Column
            - Category Sep String which defines how Elements in .all categories should be split
            - category_types labels defining what will be shown as Radio Buttons for Category Type
            - Observer instance which will be observing some attributes
            - bkapp parent attribute, which will be notified by observer on change of few attributes.

            Main methods are:
                - category_options that returns gridplot to manipulate Categories in the dataframe
                - month_range_options that returns gridplot to manipulate Months in the dataframe
                - initialize_settings_variables to initialize Object variables.


            Settings Object defines 3 watched properties:
                - chosen_categories
                - chosen_category_type
                - chosen_months
            Upon change on any of those properties, observer instance notifies parent "bkapp" object.

            Attributes of the instance Object are described as single-line comments in __init__() method;


        """

    # TODO: synchronize chosen months and categories - it might happen that there is no such category
    # TODO: in chosen Month Range

    chosen_categories = Observer.watched_property("observer", "chosen_categories", "parent")
    chosen_category_type = Observer.watched_property("observer", "chosen_category_type", "parent")
    chosen_months = Observer.watched_property("observer", "chosen_months", "parent")

    def __init__(self, simple_categories_series, extended_categories_series, date_series,
                 category_sep, category_types, observer, bkapp):

        # Observer Variables
        self.parent = bkapp
        self.observer = observer

        # Original Data
        self.original_simple_categories = simple_categories_series
        self.original_extended_categories = extended_categories_series
        self.original_dates = date_series

        # Initialization Variables
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

        # Initialization State
        self.are_categories_initialized = False
        self.is_month_range_initialized = False

    def category_options(self):
        """Returns gridplot (bokeh layout or Element) defining elements for the User to manipulate Data shown in
        other views.

            Function first checks if the category variables are initialized and if not, initializes them. Then two
            bokeh widgets are created: Radio Group and Checbox Group and both are put into the column layout.

            Category Type Radio Group allows to choose which category column will be used in dataframes (either
            .category or .all) and if the categories will be extracted as they are (either in "simple" or "extended"
            options) or if the "combinations" of categories will be created for User's choosing
            (e.g. Expenses:Family:Grocery:Fruits will provide 4 different categories:
                - "Expenses"
                - "Expenses:Family"
                - "Expenses:Family:Grocery"
                - "Expenses:Family:Grocery:Fruits".

            Checkbox Group will then provide all choosable categories (from chosen category type) for the User
            to check and uncheck and therefore filter/unfilter them from the dataframes.

            Elements on creation take data from respective instance attributes - this way navigating between
            different views and then coming back to Settings view will "remember" previous choice of the User.

            Callbacks are defined for each Element so that it will be responsive to User choosing.

            Additionally, Checkbox Group is set into .checkbox_group attribute so that change in Category Type
            can also trigger change in Checkbox Group.

            Returns column layout.
        """

        if self.are_categories_initialized is False:
            self.__initialize_categories()

        chosen_index = self.chosen_category_type

        category_type_chooser = RadioGroup(
            labels=self.category_type_labels, active=chosen_index,
            css_classes=["category_types_buttons"], inline=True
        )

        checkbox_group = CheckboxGroup(
            labels=self.all_categories,
            active=[self.all_categories.index(x) for x in self.chosen_categories],
            css_classes=["category_checkbox"]
        )

        # set as attribute for RadioGroup Buttons Updates to have access to it
        self.checkbox_group = checkbox_group

        # Callbacks
        def callback_on_category_type_change(attr, old, new):
            if new != old:
                self.__update_categories_on_category_type_change(new)

        category_type_chooser.on_change("active", callback_on_category_type_change)

        def callback_on_checkbox_change(new):
            self.__update_chosen_categories_on_new(new)

        checkbox_group.on_click(callback_on_checkbox_change)

        # Grid
        grid = column(
            category_type_chooser,
            checkbox_group
        )

        return grid

    def month_range_options(self):
        """Returns gridplot (bokeh layout or Element) defining elements for the User to manipulate Data shown in
        other views.

            Function first checks if the months variables are initialized and if not, initializes them. Then one
            bokeh widget - DateRangeSlider is created.

            DateRangeSlider will allow User to filter data to Months between two "borders" of the Slider. Even though
            DateRangeSlider defines step: 1 (so all days from the months are shown), formatter applied will only show
            month-year values ("%b-%Y).
            Additionally, defined callback checks months of start-stop values and compares them to months from
            old values. This way, callbacks aren't triggered for every slight change in the Slider and change in
            .chosen_months is only triggered when the actual change in months happens.

            Values for the Slider are also taken from instance attributes - this way User's previous choice is
            remembered and can be shown upon coming back to Settings View.

            Returns DateRangeSlider.
        """

        if self.is_month_range_initialized is False:
            self.__initialize_months()

        sld = DateRangeSlider(start=self.all_months[0], end=self.all_months[-1], step=1,
                              value=(self.chosen_months[0], self.chosen_months[-1]),
                              format="%b-%Y", title="Chosen Month Range: ",
                              css_classes=["month_range_slider"])

        def month_range_callback(attr, old, new):
            formatting = "%Y-%m"
            old_str = self.__create_timetuple_string_from_timestamp(old, formatting)
            new_str = self.__create_timetuple_string_from_timestamp(new, formatting)
            if old_str != new_str:
                self.__update_chosen_months(new)

        sld.on_change("value", month_range_callback)

        return sld

    def initialize_settings_variables(self):
        """Helper function for calling initialization different variables."""
        self.__initialize_categories()
        self.__initialize_months()

    def __initialize_categories(self):
        """Initializes variables for the Category Gridplot.

            Initialized instance attributes are:
                - .all_categories_simple - list of "simple" categories (taken from .category column)
                - .all_categories_extended - list of "extended" categories (taken from .all column)
                - .all_categories_combinations - list of "combinations" from .all column (see category_options() docs)

            Those attributes will be used as runtime containers for different categories values, from which
            User's choices will be extracted and loaded into .all_categories and .chosen_categories attributes.
            .all_categories and .chosen_categories are used as attributes for determining what is the User's choice.

            Additionally, .chosen_category_type is set to default 0 ("simple") and so are .all_categories and
            .chosen_categories attributes.

            .are_categories_initialized flag is set to True as a way to show that Category Variables are initialized.
        """
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
        """Initializes variables for the Month Gridplot.

            Initialized instance attributes are:
                - .all_months containing data of different months present in .date column
                - .chosen_months containing month range chosen by the User.

            .all_months attribute is created as a "MS" (MonthStart) pd.date_range between the first
            and the last date present in .original_dates Series (.date column from dataframe).

            Both .all_months and .chosen_months are used as variables for the DateRangeSlider to extract all months
            present in the dataframe and User's choice of filtering, respectively.

            .are_categories_initialized flag is set to True as a way to show that Category Variables are initialized.
        """
        start_date = self.original_dates.min()
        stop_date = self.original_dates.max()

        all_dates_range = pd.to_datetime(pd.date_range(start_date, stop_date, freq="MS")).tolist()

        self.all_months = all_dates_range
        self.chosen_months = all_dates_range

        self.is_month_range_initialized = True

    def __update_categories_on_category_type_change(self, index):
        """Callback used on a change to Category Type Radio Button.

            Index argument requires integer in range [0, 2]. This determines which category type was chosen and what
            data should be loaded into .all_categories and .chosen_categories variables.

            Index options are (hardcoded):
                - 0: simple categories
                - 1: extended categories
                - 2: combination categories

            Additionally to .all_categories and .chosen_categories variables, .chosen_category_type is also set to
            chosen index (as a way to preserve state).

            As change in Category Type should also propagate change to Category Checkbox, .checkbox_group Widget is
            updated with new categories:
                - .labels attribute with all possible Categories
                - .active attribute with list of Integers from 0 to len(New Categories).
        """

        if index == 0:
            new = self.all_categories_simple
        elif index == 1:
            new = self.all_categories_extended
        elif index == 2:
            new = self.all_categories_combinations
        else:
            raise Exception("How did I get here?")

        self.all_categories = new
        self.chosen_categories = new

        self.chosen_category_type = index

        self.checkbox_group.labels = new
        self.checkbox_group.active = list(range(len(new)))

    def __update_chosen_categories_on_new(self, new):
        """Updates .chosen_categories variable based on new attribute - list of indices.

            Function updates .chosen_categories with Categories (Strings) taken from .all_categories, based on
            indices provided in new attribute.

            .chosen_categories attribute is updated.
        """
        self.chosen_categories = [self.all_categories[x] for x in new]

    def __create_timetuple_string_from_timestamp(self, single_tuple, date_format):
        """Creates 2 Element Tuples of Strings formatted to date_format from 2 Element Tuples of Timestamps.

            Function accepts single_tuple tuple of Timestamp variables. As those Timestamps come from
            DateRangeSlider, they need to be divided by 1000 (1e3) for datetime.fromtimestamp to work.
            Datetime elements are then converted into Strings of date_format and returned.

            Additionally, if type of elements in the single_tuple is pd.Timestamp, values are first converted into
            timestamps and then multiplied by 1000 for the rest of the function to work. This is needed for
            the DateRangeSlider to work, as initially values are extracted might be pd.Timestamps.

            Returns 2 Element Tuple of Strings from Dates (with date_format).
        """

        # TODO: check if Timestamps are actually loaded
        # checking for Timestamp as they might be in Slider Values initially (before User interaction)
        if (type(single_tuple[0]) is pd.Timestamp) and (type(single_tuple[1]) is pd.Timestamp):
            single_tuple = tuple([x.timestamp() * 1e3 for x in single_tuple])

        # divided by 1000 (1e3) as DateRangeSlider provides timestamp multiplied by thousand
        val = tuple(map(lambda x: datetime.fromtimestamp(float(x) / 1e3).strftime(date_format), single_tuple))
        return val

    def __update_chosen_months(self, new):
        """Function updates .chosen_months attribute with date_range based on new tuples values.

            new tuple included two Timestamps from the DateRangeSlider - beginning and the end of the Date Range
            chosen by the User.
            Values from the tuple are first changed into datetime (divided by 1000 as they come from DateRangeSlider)
            and then their day is replaced to 1 (to avoid problems with missing months when date_range is created).
            Strings in format "%Y-%m-%d are created and then are inserted into pd.date_range which creates new
            range of dates with frequency "MS" (Month Start). Such DateRange is then loaded into .chosen_months
            attribute.

            .chosen_months attribute is updated.
        """
        # done to first convert timestamp to datetime and then to set datetime to day 1 - this way
        # date_range is properly created
        new = tuple(map(lambda x: datetime.fromtimestamp(float(x) / 1e3), new))

        # TODO: check if converting to String is necessary
        new = [datetime(year=x.year, month=x.month, day=1).strftime("%Y-%m-%d") for x in new]
        dr = pd.date_range(new[0], new[1], freq="MS", normalize=True).tolist()

        self.chosen_months = dr
