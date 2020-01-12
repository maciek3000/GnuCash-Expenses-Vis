import pandas as pd
import numpy as np
import piecash
from datetime import datetime


class ColumnMapper(object):

    def __init__(self, column_names):
        attr_list = ['name', 'date', 'split', 'account', 'price', 'currency', 'product', 'shop', 'all',
                     'type', 'category', 'subcategory', 'subtype', 'monthyear']
        for attr, val in (attr_list, column_names):
            setattr(self, attr, val)


class GnuCashDBParser(object):
    """Parser for SQL DB GnuCash Files."""

    expense_name = "EXPENSE"
    default_column_names = ['Name', 'Date', 'Split Description', 'Account', 'Price', 'Currency',
                            'Product', 'Shop', 'ALL_CATEGORIES', 'Type', 'Category', 'SubCategory',
                            'SubType', 'MonthYear']

    def __init__(self, file_path, names, columns=None):

        cols = columns if columns else self.default_column_names
        self.col_map = ColumnMapper(cols)

        self.file_path = file_path
        self.names = names
        self.expenses_df = self.create_df(file_path, names)

    def create_df(self, file_path, names):
        # TODO: update desc of columns
        """Creates DataFrame from GnuCash DB file located in file_path.

            Name - name of the transaction;
            Date - date when transaction happened;
            Split description - Name of the split transaction;
            Account - Account from which transaction happened;
            Price - Amount of the transaction;
            Currency - currency of money which was used to make the transaction;

        """

        transaction_list = self._get_list_of_transactions(file_path)

        # TODO: error handling
        if not len(transaction_list) > 0:
            raise NotImplementedError

        return self._create_df_from_list_of_transactions(transaction_list, names)

    def _get_list_of_transactions(self, file_path):
        """Creates list of transactions from GnuCash DB file parsed with piecash."""

        with piecash.open_book(file_path) as book:
            transaction_list = []
            for tr in book.transactions:
                split = tr.splits
                for single_row in split:
                    if single_row.account.type == self.expense_name:
                        memo = single_row.memo.strip()
                        memo = memo if len(memo) > 0 else np.nan

                        temp_list = [tr.description, tr.post_date, memo, single_row.account.fullname,
                                     single_row.value, tr.currency.mnemonic]
                        transaction_list.append(list(map(str, temp_list)))

        return transaction_list

    # is it really that helpful with ColumnMapper?
    def _create_df_from_list_of_transactions(self, transaction_list, names):

        # TODO: repetition of columns accross functions
        column_names = ['Name', 'Date', 'Split Description', 'Account', 'Price', 'Currency']
        df = pd.DataFrame(transaction_list, columns=column_names)

        # replacing nan strings with np.nan
        df[self.col_map.split] = df[self.col_map.split].replace('nan', np.nan)

        # adding Product
        df[self.col_map.product] = df[self.col_map.split].fillna(df[self.col_map.name])
        cond = df[self.col_map.split].isnull()
        df[self.col_map.shop] = np.where(cond, np.nan, df[self.col_map.name])

        # ALL_CATEGORIES as it might be helpful later on
        df[self.col_map.all] = df[self.col_map.account].apply(lambda x: x.split(':'))

        # extracting info from account
        """Account -> 'Wydatki:Wspólne:Zakupy:Chemia:Osobiste - Justyna:Artykuły Do Makijażu'
            2nd: Type
            3rd to OneBeforeLast: SubCategory
            Last: Category
        """
        #cols_to_create = list(map(getattr(self.col_map, 'type')))

        df[self.col_map.type] = df[self.col_map.all].apply(lambda x: x[1])
        df[self.col_map.category] = df[self.col_map.all].apply(lambda x: x[-1])
        df[self.col_map.subcategory] = df[self.col_map.all].apply(lambda x: ':'.join(x[2:-1]) if len(x[2:-1]) > 0
                                                                  else np.nan)
        df[self.col_map.subtype] = df[self.col_map.all].apply(lambda x: self._check_name_for_sub_type(names))

        # formatting Price and Date
        df[self.col_map.price] = df[self.col_map.price].apply(lambda x: float(x))
        df[self.col_map.date] = df[self.col_map.date].apply(lambda x: datetime.strptime(x, '%Y-%m-%d'))

        # adding MonthYear column for easier analysis
        df[self.col_map.monthyear] = df[self.col_map.date].dt.strftime('%m-%Y')

        # dropping columns that are no longer needed
        df = df.drop([self.col_map.name, self.col_map.split, self.col_map.account], axis = 1)

        return df

    def __check_name_for_sub_type(self, string_list, names):
        """Checks for name from names in list of strings.
            Only checks from the 3rd value up to one before last [2:-1].

            Returns name if it's found, or np.nan otherwise
        """
        return_string = np.nan
        for name in names:
            return_string = name if name in ','.join(string_list[2:-1]) else return_string

        return return_string

    def get_df(self):
        return self.expensed_df
