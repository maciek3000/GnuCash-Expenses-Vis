import numpy as np
import pandas as pd

from ..observer import Observer
from .bk_category import Category
from .bk_overview import Overview
from .bk_trends import Trends
from .bk_settings import Settings
from .color_map import ColorMap


class BokehApp(object):
    """Main object responsible for creating appropriate gridplots with Visualizations.

        BokehApp is the workhorse of the application, serving different "Views" of the Visualizations. There are
        3 main Views defined:
            - Overview showing monthly summaries on expenses/income as well expenses distribution in categories;
            - Trends defining overall view on expenses in different months;
            - Category allowing for looking for details on specific Category.
        Additionally, Settings View exposes Bokeh Widgets with which User can interact to change filters
        applied to their data in regard to Categories and Date Range.

        Object requires following arguments for the initialization:
            - expense dataframe
            - income dataframe
            - col_mapping which should be a dict mapping "ideas" of column to their names in the dataframe.
                Keys that should be included:
                    - "date"
                    - "price"
                    - "currency"
                    - "product"
                    - "shop"
                    - "all"
                    - "type"
                    - "category"
                    - "monthyear"
            - monthyear_format which should be a string defining String Date Format in monthyear column
            - server_date - date at which BokehApp was initialized
            - category_sep - String used in "all" column to separate Category values (in a tree).

            During initialization, BokehApp creates all Views so that they can be accessed later on. Additionally,
            it updates .current_expense_dataframe to mirror filtering choices of the User.

            Settings View is connected via Observer - when some of it's properties are updated, they trigger
            changes to the BokehApp which in turn can update it's own state variables.
    """
    observer = Observer()
    category_types = ["Simple", "Expanded", "Combinations (Experimental)"]

    def __init__(self, expense_dataframe, income_dataframe, col_mapping, monthyear_format, server_date, category_sep):

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
        self.monthyear_format = monthyear_format
        category_sep = category_sep

        # Settings Object
        self.settings = Settings(self.original_expense_dataframe[self.category],
                                 self.original_expense_dataframe[self.all],
                                 self.original_expense_dataframe[self.date],
                                 category_sep,
                                 self.category_types,
                                 self.observer,
                                 self)

        # View Objects
        self.category_view = Category(self.category, self.monthyear, self.price, self.product,
                                      self.date, self.currency, self.shop, self.monthyear_format, color_mapping)
        self.overview_view = Overview(self.category, self.monthyear, self.price, self.product,
                                      self.date, self.currency, self.shop, self.monthyear_format, server_date,
                                      color_mapping)
        self.trends_view = Trends(self.category, self.monthyear, self.price, self.product,
                                  self.date, self.currency, self.shop, self.monthyear_format, color_mapping)

        # State Variables
        self.chosen_category_column = self.category
        self.current_chosen_categories = None
        self.current_chosen_months = None

        # Needs to be called during __init__ for the Observer decorator to correctly build functions
        self.settings.initialize_settings_variables()

    # TODO: change single gridplot to one gridplot function with mapping which gridplot should it return

    # Gridplot Functions
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
        """ "Notify" function, that is called upon change to properties watched by the Observer.

            Arguments required:
                - key - representing name of the property that was changed
                - value - representing value with which key property was changed.

            Function has it's own dictionary, which based on a provided key returns function that needs
            to be called.
        """
        key_func_dict = {
            "chosen_categories": self.__update_current_chosen_categories,
            "chosen_category_type": self.__update_category_choice,
            "chosen_months": self.__update_current_chosen_months
        }

        func = key_func_dict[key]
        func(value)

    def __update_current_chosen_categories(self, categories):
        """Updates .current_chosen_categories with categories argument."""
        self.current_chosen_categories = categories

    def __update_current_chosen_months(self, months):
        """Updates .current_chosen_months with months argument."""
        self.current_chosen_months = months

    def __update_category_choice(self, category_type):
        """Updates .chosen_category_column attribute based on provided category_type and calls .change_category_column
            in View Objects.

            Based on the provided category_type new category column is chosen (either .category or .all) and inserted
            into .chosen_category_column variable.

            Additionally, .change_category_column function of 3 Views Objects is called (Overview, Trends, Categories)
            as the change in Category column is something that they need to be informed of (and with that update
            their own variables).
        """

        d = {
            0: self.category,
            1: self.all,
            2: self.all
        }
        self.chosen_category_column = d[category_type]

        for obj in [self.overview_view, self.trends_view, self.category_view]:
            obj.change_category_column(self.chosen_category_column)

    def __update_current_expense_dataframe(self):
        """Updates .current_expense_dataframe with data from .original_expense_dataframe but filtered to choices
            stored in .current_chosen_months and .current_chosen_categories.

            Updates to dataframes need to be done in regard to two factors: month range and Categories chosen
            by the User. In theory, it could be done in one step.
            Unfortunately, filtering by Category can also be made as Combinations Categories (e.g.
            "Expenses:Family:Grocery" will be made into "Expenses", "Expenses:Family" and "Expenses:Family:Grocery".
            When User unchecks "Expenses:Family", then all rows that have "Expenses:Family" in them should be
            filtered out.
            Therefore, filtering comes in two steps: first, .original_expense_dataframe is filtered to only
            include chosen months (based on .current_chosen_months attribute and .monthyear column). Then
            "unchosen" categories are calculated (those that user unchecked in the Settings CheckboxGroup) and
            every row that contains that category is filtered out.

            Eventually .current_expense_dataframe is updated with the filtered dataframe.
        """

        # Month Filtering
        months = pd.to_datetime(self.current_chosen_months).strftime(self.monthyear_format)
        month_cond = np.isin(self.original_expense_dataframe[self.monthyear], months)
        df = self.original_expense_dataframe[month_cond]

        # TODO: possibly change .settings.all_categories to a variable from BokehApp directly
        # Categories Filtering
        unchosen_cats = set(self.settings.all_categories) - set(self.current_chosen_categories)

        for cat in unchosen_cats:
            cond = df[self.chosen_category_column].str.contains(cat)
            df = df[~cond]

        self.current_expense_dataframe = df
