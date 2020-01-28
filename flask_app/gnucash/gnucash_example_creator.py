from piecash import Account, create_book, Transaction, Split
import pandas as pd
import random
from decimal import Decimal
import os
from collections import OrderedDict


class GnucashExampleCreator(object):
    """Creator of example Gnucash File for the app."""

    def __init__(self, file_path, currency, low_proba_value=0.05, medium_proba_value=0.3, high_proba_value=0.6,
                 shop_proba_value=0.4, date_range=pd.date_range("01-Jan-2019", "31-Dec-2019"), seed=42):

        # book settings
        self.file_path = file_path
        self.currency = currency
        self.date_range = date_range

        # random settings
        self.low_proba = low_proba_value
        self.medium_proba = medium_proba_value
        self.high_proba = high_proba_value
        self.shop_proba = shop_proba_value
        self.rng = random.Random()
        self.rng.seed(seed)

    def create_example_book(self):
        """Main function to create example gnucash file (piecash book).

            All Accounts and Transaction types are hardcoded.
            Some Transactions are fixed, meaning that their occurrence or price is always the same.
            Other Transaction days and/or prices are set at random,given the seed provided during initialization.

            What is more, some of the Transactions can also be a part of a Shop (Split) Transaction. The occurence
            of this is also subject to the random seed.

            Function doesn't return anything, but saves the created book in the file_path provided in __init__.
        """

        book = create_book(currency=self.currency, sqlite_file=self.file_path, overwrite=True)
        curr = book.default_currency

        # Accounts
        asset_acc = Account("Assets", "ASSET", curr, parent=book.root_account, placeholder=True)
        john_acc = Account("John", "ASSET", curr, parent=asset_acc)
        susan_acc = Account("Susan", "ASSET", curr, parent=asset_acc)
        family_acc = Account("Family", "ASSET", curr, parent=asset_acc)

        income = Account("Income", "INCOME", curr, parent=book.root_account, placeholder=True)
        john_income = Account("John's Income", "INCOME", curr, parent=income)
        susan_income = Account("Susan's Income", "INCOME", curr, parent=income)

        exp = Account("Expenses", "EXPENSE", curr, parent=book.root_account, placeholder=True)
        john_exp = Account("John's Expenses", "EXPENSE", curr, parent=exp, placeholder=True)
        clothes_john = Account("Clothes", "EXPENSE", curr, parent=john_exp)
        susan_exp = Account("Susan's Expenses", "EXPENSE", curr, parent=exp, placeholder=True)
        clothes_susan = Account("Clothes", "EXPENSE", curr, parent=susan_exp)
        family_exp = Account("Family", "EXPENSE", curr, parent=exp, placeholder=True)
        grocery = Account("Grocery", "EXPENSE", curr, parent=family_exp, placeholder=True)
        bread = Account("Bread", "EXPENSE", curr, parent=grocery)
        meat = Account("Meat", "EXPENSE", curr, parent=grocery)
        eggs = Account("Eggs", "EXPENSE", curr, parent=grocery)
        chips = Account("Chips", "EXPENSE", curr, parent=grocery)
        fruits = Account("Fruits and Vegetables", "EXPENSE", curr, parent=grocery)
        car = Account("Car", "EXPENSE", curr, parent=family_exp, placeholder=True)
        petrol = Account("Petrol", "EXPENSE", curr, parent=car)
        flat = Account("Flat", "EXPENSE", curr, parent=family_exp, placeholder=True)
        rent = Account("Rent", "EXPENSE", curr, parent=flat)
        water = Account("Water and Electricity", "EXPENSE", curr, parent=flat)
        bathroom = Account("Bathroom", "EXPENSE", curr, parent=family_exp, placeholder=True)
        toilet = Account("Toilet", "EXPENSE", curr, parent=bathroom)
        personal_john = Account("Personal - John", "EXPENSE", curr, parent=bathroom)
        personal_susan = Account("Personal - Susan", "EXPENSE", curr, parent=bathroom)
        other = Account("Other", "EXPENSE", curr, parent=family_exp)

        book.save()

        # Transactions
        acc_list = [john_acc, susan_acc, family_acc, clothes_john, clothes_susan, bread, meat, eggs,
                    chips, fruits, petrol, rent, water, toilet, personal_john, personal_susan, other]

        # Tuple(
        #       Tuple(
        #           Tuple(Name of Transaction/Split, From_Account),
        #           Tuple(Start of Price Range/Price, Stop of Price Range/ ),
        #           ),
        #       Tuple(...)
        #   ), ...
        planned_tr_list = [
            ((("Salary", john_income), (3000,)),),
            ((("Salary", susan_income), (3000,)),),
            ((("Transaction", john_acc), (500,)),
             (("Transaction", susan_acc), (500,))),
            ((("Clothes", john_acc), (100, 350)),),
            ((("Clothes", john_acc), (100, 350)),),
            ((("White Bread", family_acc), (1, 4)),
             (("Rye Bread", family_acc), (3, 6)),
             (("Butter", family_acc), (4, 7))),
            ((("Chicken", family_acc), (9, 16)),
             (("Cow", family_acc), (15, 30))),
            ((("Eggs", family_acc), (8, 16)),),
            ((("Chips", family_acc), (5, 17)),
             (("Lollipops", family_acc), (1, 2))),
            ((("Apple", family_acc), (3, 5)),
             (("Banana", family_acc), (5, 7)),
             (("Tomato", family_acc), (2, 4)),
             (("Pear", family_acc), (3, 5))),
            ((("Petrol", family_acc), (50, 250)),),
            ((("Rent", family_acc), (2000,)),),
            ((("Water and Electricity", family_acc), (20, 150)),),
            ((("Toilet Paper", family_acc), (5, 15)),
             (("Facial Tissues", family_acc),  (2, 8))),
            ((("Beard Balm", john_acc), (15, 50)),),
            ((("Shampoo", susan_acc),  (10, 15)),
             (("Face Cleanser", susan_acc), (10, 13))),
            ((("Other", family_acc), (1, 100)),)
        ]

        # Ordered Dict for reproducibility
        # key: Accounts, value: tuples of Transactions
        planned_tr_list = map(OrderedDict, planned_tr_list)
        stuff = OrderedDict(zip(acc_list, planned_tr_list))

        # Zipping Probabilities with Transactions
        low_proba_list = [clothes_john, clothes_susan, petrol, toilet, personal_john, personal_susan]
        medium_proba_list = [meat, chips, other]
        high_proba_list = [bread, eggs, fruits]

        probas = [
            (low_proba_list, self.low_proba),
            (medium_proba_list, self.medium_proba),
            (high_proba_list, self.high_proba)
        ]

        # Fixed Day Transactions
        fixed_transactions = [
            (20, (rent, water)),
            (25, (john_acc, susan_acc)),
            (26, (family_acc,))
        ]

        # Shops (Split Transaction Names)
        shops = ["Grocery Shop #1", "Grocery Shop #2"]
        shop_items = (high_proba_list,)

        self.__create_transactions(book, self.date_range, stuff, curr, probas, fixed_transactions, shops, shop_items)
        book.save()

    def __create_transactions(self, book, date_range, stuff, currency, probas, fixed_transactions, shops, shop_items):
        """Main workhorse of the GnucashExampleCreator.

            Loops through all the dates provided in the date_range and for each day, checks if the Transaction should
            be created.
            For Fixed Day Transactions it checks if the day of the month matches. For other Transactions, calls
            random.random() and if the chosen value is lesser or equal to provided Probability, the Transaction is
            created. For some of the Transactions, the Split Transaction is created (few Transactions under a common
            name - Shop Name).

            No return, as piecash book object requires saving and flushing upon changes.
        """

        # Main loop for date range
        for date_item in date_range:

            date = date_item.date()

            # Loop for Fixed Transactions
            for fixed in fixed_transactions:
                fixed_tr_date = fixed[0]
                fixed_accounts = fixed[1]

                if fixed_tr_date == date.day:
                    for fixed_to_account in fixed_accounts:
                        fixed_transaction_list = self.__extract_data(stuff, fixed_to_account)
                        for fixed_transaction in fixed_transaction_list:
                            self.__add_transaction(book, date, currency, fixed_to_account, fixed_transaction)

            # Loop for every other Transaction
            for _ in probas:
                to_account_list = _[0]
                proba = _[1]

                # Check if the Transaction will be Split (Shop) Transaction
                if to_account_list in shop_items and self.rng.random() <= self.shop_proba:
                    shop_description = self.rng.choice(shops)
                    list_of_splits = []
                    for to_account in to_account_list:
                        transaction_list = self.__extract_data(stuff, to_account)
                        for transaction in transaction_list:
                            if self.rng.random() <= proba:
                                list_of_splits.append((to_account, transaction))

                    # Check just in case no Transaction is created
                    if len(list_of_splits) > 0:
                        self.__add_shop_transaction(book, date, currency, list_of_splits, shop_description)

                # Loop for Normal Transaction
                else:
                    for to_account in to_account_list:
                        transaction_list = self.__extract_data(stuff, to_account)
                        for transaction in transaction_list:
                            if self.rng.random() <= proba:
                                self.__add_transaction(book, date, currency, to_account, transaction)

    def __extract_data(self, d, acc):
        """Extracts data from the d Dictionary of Transaction Tuples, given the provided acc Account.

            Returns Tuple(
                        Description of Transaction,
                        From_Account,
                        Price Range Tuple
                    )
            or the Tuple of such Tuples, depending on how many Transactions there are in the d dict.
        """
        internal_dict = d[acc].items()

        if len(internal_dict) > 1:
            ret_list = []
            for tpl in list(internal_dict):
                desc, second_acc = tpl[0]
                price_range = tpl[1]
                ret_list.append((desc, second_acc, price_range))
            ret_tuple = tuple(ret_list)

        else:
            _ = list(internal_dict)[0]
            desc, second_acc = _[0]
            price_range = _[1]
            ret_tuple = ((desc, second_acc, price_range),)

        return ret_tuple

    def __add_transaction(self, book, date, currency, to_account, transaction):
        """Adds Transaction to the piecash book.

            Description and Price Range are provided in transaction argument, whereas Currency is provided directly.
            from_account indicates the Asset Account, from which the money will be 'taken', whereas
            to_account indicates the Expense Account, which accumulates the expense.

            Price is decided on the structure of the Price Range Tuple - if the Tuple has len of 1, the value
            provided in it is taken directly. Otherwise, random.uniform() is called on the range and the random value
            from the range is chosen.
            Chosen Price is also rounded to 2 digits and converted to Decimal to adhere to piecash objects.

            Function calls book.flush() to save the Transaction, no value is returned.
        """
        description, from_account, price_range = transaction

        if len(price_range) > 1:
            value = self.rng.uniform(price_range[0], price_range[1])
        else:
            value = price_range[0]

        price = Decimal(str(round(value, 2)))
        tr = Transaction(currency=currency,
                         description=description,
                         post_date=date,
                         splits=[
                             Split(account=from_account, value=-price),
                             Split(account=to_account, value=price)
                         ])

        book.flush()

    def __add_shop_transaction(self, book, date, currency, list_of_splits, shop_name):
        """Adds Split (Shop) Transaction to the book.

            Instead of adding 1:1 Transaction with to_account and from_account, the function creates the list
            of 1:1 Splits of to_account and from_account complimenting each other. Then the whole list is provided
            to the main Transaction.
            Description of the Transaction is provided in the shop_name argument.

            Other arguments are described in __add_transaction, please refer to the comments in this function.
        """
        sp_list = []

        for split in list_of_splits:
            to_account = split[0]
            description, from_account, price_range = split[1]

            if len(price_range) > 1:
                value = self.rng.uniform(price_range[0], price_range[1])
            else:
                value = price_range[0]
            price = Decimal(str(round(value, 2)))

            sp_list.append(Split(account=to_account, memo=description, value=price))
            sp_list.append(Split(account=from_account, value=-price))

        tr = Transaction(currency=currency,
                         description=shop_name,
                         post_date=date,
                         splits=sp_list
                         )

        book.flush()

# Script for creating the example Gnucash file.
# File will be created in the same directory where this .py file is located.
if __name__ == "__main__":
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, "gnucash_examples", "example_gnucash.gnucash")
    currency = "PLN"
    example_creator = GnucashExampleCreator(file_path, currency)
    example_creator.create_example_book()
