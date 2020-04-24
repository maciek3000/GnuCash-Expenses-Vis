import pandas as pd
import numpy as np
import piecash
from datetime import datetime


class GnuCashDBParser(object):
    """Parser for SQL DB GnuCash Files."""

    income_name = "INCOME"
    expense_name = "EXPENSE"
    default_col_mapping = {
        "name": "Name",
        "date": "Date",
        "split": "Split Description",
        "account": "Account",
        "price": "Price",
        "currency": "Currency",
        "product": "Product",
        "shop": "Shop",
        "all": "ALL_CATEGORIES",
        "type": "Type",
        "category": "Category",
        "monthyear": "MonthYear"
    }

    def __init__(self, file_path, columns_mapping=None, category_sep=":", monthyear_format="%Y-%m"):

        mapping = columns_mapping if columns_mapping else self.default_col_mapping
        self.__create_mapping(mapping)

        self.file_path = file_path
        self.expenses_df = None
        self.income_df = None
        self.category_sep = category_sep
        self.monthyear_format = monthyear_format

    def get_expenses_df(self):
        if self.expenses_df is None:
            self.expenses_df = self.__create_transactions_df(self.expense_name)
        return self.expenses_df

    def get_income_df(self):
        if self.income_df is None:
            self.income_df = self.__create_transactions_df(self.income_name)
        return self.income_df

    def __create_mapping(self, column_mapping):

        c = column_mapping
        self.name = c["name"]
        self.date = c["date"]
        self.split = c["split"]
        self.account = c["account"]
        self.price = c["price"]
        self.currency = c["currency"]
        self.product = c["product"]
        self.shop = c["shop"]
        self.all = c["all"]
        self.type = c["type"]
        self.category = c["category"]
        self.monthyear = c["monthyear"]

    def __create_transactions_df(self, transaction_type):
        # TODO: update desc of columns
        """Creates DataFrame from GnuCash DB file located in file_path.

            Name - name of the transaction;
            Date - date when transaction happened;
            Split description - Name of the split transaction;
            Account - Account from which transaction happened;
            Price - Amount of the transaction;
            Currency - currency of money which was used to make the transaction;

        """

        transaction_list = self.__get_list_of_transactions(transaction_type)

        if not len(transaction_list) > 0:
            raise NotImplementedError("No transactions were fetched.")

        return self.__create_expenses_df_from_list_of_transactions(transaction_list)

    def __get_list_of_transactions(self, transaction_type):
        """Creates list of transactions from GnuCash DB file parsed with piecash."""

        with piecash.open_book(self.file_path) as book:
            transaction_list = []
            for tr in book.transactions:
                split = tr.splits
                for single_row in split:
                    if single_row.account.type == transaction_type:
                        memo = single_row.memo.strip()
                        memo = memo if len(memo) > 0 else np.nan

                        temp_list = [tr.description, tr.post_date, memo, single_row.account.fullname,
                                     single_row.value, tr.currency.mnemonic]
                        transaction_list.append(list(map(str, temp_list)))

        return transaction_list

    def __create_expenses_df_from_list_of_transactions(self, transaction_list):

        column_names = [self.name, self.date, self.split, self.account, self.price, self.currency]
        df = pd.DataFrame(transaction_list, columns=column_names)

        # replacing nan strings with np.nan
        df[self.split] = df[self.split].replace('nan', np.nan)

        # adding Product
        df[self.product] = df[self.split].fillna(df[self.name])
        cond = df[self.split].isnull()
        df[self.shop] = np.where(cond, np.nan, df[self.name])

        # ALL_CATEGORIES as it might be helpful later on
        df[self.all] = df[self.account].apply(lambda x: x.split(":"))

        df[self.type] = df[self.all].apply(lambda x: x[1])
        df[self.category] = df[self.all].apply(lambda x: x[-1])

        # formatting Price and Date
        df[self.price] = df[self.price].apply(lambda x: float(x))
        df[self.date] = df[self.date].apply(lambda x: datetime.strptime(x, '%Y-%m-%d'))

        # adding MonthYear column for easier analysis
        df[self.monthyear] = df[self.date].dt.strftime(self.monthyear_format)

        # dropping columns that are no longer needed
        df = df.drop([self.name, self.split, self.account], axis=1)

        df[self.all] = df[self.all].apply(lambda x: self.category_sep.join(x))

        return df

    @classmethod
    def check_file(cls, file_path):
        result = False

        try:
            piecash.open_book(file_path)
            result = True
        except piecash.GnucashException:
            pass

        return result
