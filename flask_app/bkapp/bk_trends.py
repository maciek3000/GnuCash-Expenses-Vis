import pandas as pd
import numpy as np


class Trends(object):

    def __init__(self, category_colname, monthyear_colname, price_colname, product_colname,
                 date_colname, currency_colname, shop_colname, month_format, color_mapping):

        # Column Names
        self.category = category_colname
        self.monthyear = monthyear_colname
        self.price = price_colname
        self.product = product_colname
        self.date = date_colname
        self.currency = currency_colname
        self.shop = shop_colname

        # MonthYear Formatting
        self.monthyear_format = month_format  # formatting of date in MonthYear column

        # ColorMap
        self.color_map = color_mapping  # ColorMap object exposing attributes with specific colors

        # DataFrames
        self.original_expense_df = None  # original expense dataframe passed to the gridplot function

        # State Variables
        self.month = None

        # Grid Elements Dicts
        self.grid_elem_dict = None
        self.grid_source_dict = None

    def gridplot(self, expense_dataframe):

        # Trends ########################
        # Info                  # Hover Tool                    # Line Plot Title
        # Average Expenses      # Expenses                      # Line Plot with 2 lines (raw and % change)
        # Median                # Higher/Lower % than Average   # Line Plot with 2 lines (raw and % change)
        # Minimum               # Transactions Number           # Line Plot with 2 lines (raw and % change)
        # Maximum               #                               # Line Plot with 2 lines (raw and % change)
        # Standard Deviation    #                               # Line Plot with 2 lines (raw and % change)
        ###########################
        # HeatMap Title
        # Heatmap Options (Transactions # or Price Sum
        # # # # # # # # #
        # Heatmap
        # Heatmap
        # Heatmap

        self.original_expense_df = expense_dataframe

        self.initialize_gridplot()

    def initialize_gridplot(self):

        elem_dict = {}
        source_dict = {}



    def update_gridplot(self):
        pass