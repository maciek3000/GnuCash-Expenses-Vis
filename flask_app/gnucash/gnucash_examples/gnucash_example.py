from piecash import Account, create_book, Transaction, Split
import pandas as pd


book = create_book(currency="PLN", sqlite_file="example_gnucash.gnucash", overwrite=True)
curr = book.default_currency

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

import random
from decimal import *

random.seed(1010)

stuff = {
    john_acc : {("Salary", john_income): (3000, )},
    susan_acc : {("Salary", susan_income): (3000, )},
    family_acc : {("Transaction", john_acc): (500, ),
                  ("Transaction", susan_acc): (500, )},
    clothes_john : {("Clothes", john_acc): (100, 350)},
    clothes_susan : {("Clothes", susan_acc): (100, 350)},
    bread : {("White Bread", family_acc): (1, 4),
             ("Rye Bread", family_acc): (3, 6),
             ("Butter", family_acc): (4, 7)},
    meat : {("Chicken", family_acc): (9, 16),
            ("Cow", family_acc): (15, 30)},
    eggs : {("Eggs", family_acc): (8, 16)},
    chips : {("Chips", family_acc): (5, 17),
             ("Lollipops", family_acc): (1, 2)},
    fruits : {("Apple", family_acc): (3, 5),
              ("Banana", family_acc): (5, 7),
              ("Tomato", family_acc): (2, 4),
              ("Pear", family_acc): (3, 5)},
    petrol : {("Petrol", family_acc): (50, 250)},
    rent : {("Rent", family_acc): (2000,)},
    water : {("Water and Electricity", family_acc): (20, 150)},
    toilet : {("Toilet Paper", family_acc): (5, 15),
              ("Facial Tissues", family_acc): (2, 8)},
    personal_john : {("Beard Balm", john_acc): (15, 50)},
    personal_susan : {("Shampoo", susan_acc): (10, 15),
                      ("Face Cleanser", susan_acc): (10, 13)},
    other : {("Other", family_acc): (1, 100)}

}

low_proba_list = [clothes_john, clothes_susan, petrol, toilet, personal_john, personal_susan]
medium_proba_list = [meat, chips, other]
high_proba_list = [bread, eggs, fruits]

low_proba = 0.05
medium_proba = 0.3
high_proba = 0.6
shop_proba = 0.4

date_range = pd.date_range("01-Jan-2019", "31-Dec-2019")

def add_transaction(book, date, acc, second_acc, description, price_range):

    if len(price_range) > 1:
        price = Decimal(str(round(random.uniform(price_range[0], price_range[1]), 2)))
    else:
        price = Decimal(str(round(price_range[0], 2)))

    tr = Transaction(currency=curr,
                     description=description,
                     post_date=date,
                     splits=[
                         Split(account=second_acc, value=-price),
                         Split(account=acc, value=price)
                     ])

    book.flush()


def add_shop_transaction(book, date, acc, list_of_splits, shop_name):

    total_price = 0
    sp_list = []

    for split in list_of_splits:

        desc, second_acc, price_range = split

        if len(price_range) > 1:
            price = Decimal(str(round(random.uniform(price_range[0], price_range[1]), 2)))
        else:
            price = Decimal(str(round(price_range[0], 2)))

        total_price += price
        sp_list.append(Split(account=acc, memo=desc, value=price))

    sp_list.append(Split(account=second_acc, value=-total_price))

    tr = Transaction(currency=curr,
                     description=shop_name,
                     post_date=date,
                     splits=sp_list
                     )

    book.flush()

def extract_data(d, acc):
    internal_dict = d[acc].items()
    #print(internal_dict)

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

fixed_transactions = [(20, (rent, water)), (25, (john_acc, susan_acc)), (26, (family_acc, ))]


for date in date_range:

    for fixed in fixed_transactions:
        if date.day == fixed[0]:
            for acc in fixed[1]:
                transaction_list = extract_data(stuff, acc)
                for transaction in transaction_list:
                    desc, second_acc, price_range = transaction
                    add_transaction(book, date.date(), acc, second_acc, desc, price_range)


    for group_of_items in [(low_proba_list, low_proba),
                           (medium_proba_list, medium_proba),
                           (high_proba_list, high_proba)]:


        acc_list = group_of_items[0]
        proba = group_of_items[1]

        if acc_list is high_proba_list and random.random() <= shop_proba:
            shop_description = random.choice(["Grocery Shop #1", "Grocery Shop # 2"])
            for acc in acc_list:
                transaction_list = extract_data(stuff, acc)
                list_of_splits = []
                for transaction in transaction_list:
                    if random.random() <= proba:
                        desc, second_acc, price_range = transaction
                        list_of_splits.append((desc, second_acc, price_range))
                if len(list_of_splits) > 0:
                    add_shop_transaction(book, date.date(), acc, list_of_splits, shop_description)
        else:
            for acc in acc_list:
                transaction_list = extract_data(stuff, acc)
                for transaction in transaction_list:
                    if random.random() <= proba:
                        desc, second_acc, price_range = transaction
                        add_transaction(book, date.date(), acc, second_acc, desc, price_range)

