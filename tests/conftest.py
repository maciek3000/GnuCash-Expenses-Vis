import pytest
import piecash
import tempfile
import os
from datetime import date, datetime
from decimal import Decimal
from flask_app.bkapp.color_map import ColorMap

from flask_app.observer import Observer
from flask_app.gnucash.gnucash_example_creator import GnucashExampleCreator
from flask_app.gnucash.gnucash_db_parser import GnuCashDBParser
from flask_app.bkapp.bk_category import Category
from flask_app.bkapp.bk_overview import Overview
from flask_app.bkapp.bk_trends import Trends
from flask_app.bkapp.bkapp import BokehApp
from flask_app.bkapp.bk_settings import Settings

# ========== gnucash_example_creator ========== #


@pytest.fixture
def gnucash_creator():
    """Test gnucash_example_creator Object"""
    example_fd, example_path = tempfile.mkstemp()
    currency = "PLN"
    seed = 1010

    yield GnucashExampleCreator(example_path, currency, seed=seed)

    # closing the link to the tempfile
    os.close(example_fd)
    os.unlink(example_path)


@pytest.fixture
def book():
    """Test piecash book Object"""
    book = piecash.create_book(currency="PLN")
    book.save()
    return book


@pytest.fixture
def to_account(book):
    """Test piecash Account (Expense)"""
    to_account = piecash.Account("Test Expense Account", "EXPENSE", book.default_currency, parent=book.root_account)
    book.save()
    return to_account


@pytest.fixture
def from_account(book):
    """Test piecash Account (Asset)"""
    from_account = piecash.Account("Test Asset Account", "ASSET", book.default_currency, parent=book.root_account)
    book.save()
    return from_account


@pytest.fixture
def to_account_two(book):
    """Test piecash Account #2 (Expense)"""
    to_account = piecash.Account("Test Expense Account 2", "EXPENSE", book.default_currency, parent=book.root_account)
    book.save()
    return to_account


@pytest.fixture
def from_account_two(book):
    """Test piecash Account #2 (Asset)"""
    from_account = piecash.Account("Test Asset Account 2", "ASSET", book.default_currency, parent=book.root_account)
    book.save()
    return from_account

# ========== gnucash_db_parser ========== #

def category_sep_for_test():
    return ":"


@pytest.fixture
def example_book_path():
    file_path = os.path.join(os.path.split(os.path.dirname(os.path.realpath(__file__)))[0],
                             "flask_app", "gnucash", "gnucash_examples", "example_gnucash.gnucash")
    return file_path


@pytest.fixture
def gnucash_db_parser_example_book(example_book_path):
    gdbp = GnuCashDBParser(file_path=example_book_path, category_sep=category_sep_for_test())
    return gdbp


def create_simple_book(currency, file_path):
    book = piecash.create_book(currency=currency, sqlite_file=file_path, overwrite=True)

    curr = book.default_currency
    assets = piecash.Account("Assets", "ASSET", curr, parent=book.root_account, placeholder=True)
    acc1 = piecash.Account("Asset #1", "ASSET", curr, parent=assets)
    acc2 = piecash.Account("Asset #2", "ASSET", curr, parent=assets)

    expenses = piecash.Account("Expenses", "EXPENSE", curr, parent=book.root_account, placeholder=True)
    type1 = piecash.Account("Main Type #1", "EXPENSE", curr, parent=expenses, placeholder=True)
    type2 = piecash.Account("Main Type #2", "EXPENSE", curr, parent=expenses, placeholder=True)
    fruits = piecash.Account("Fruits", "EXPENSE", curr, parent=type1, placeholder=True)
    dairy = piecash.Account("Dairy", "EXPENSE", curr, parent=type2, placeholder=True)
    apples = piecash.Account("Apples", "EXPENSE", curr, parent=fruits)
    eggs = piecash.Account("Eggs", "EXPENSE", curr, parent=dairy)

    incomes = piecash.Account("Income", "INCOME", curr, parent=book.root_account, placeholder=True)
    inc1 = piecash.Account("Income #1", "INCOME", curr, parent=incomes)
    inc2 = piecash.Account("Income #2", "INCOME", curr, parent=incomes)

    book.save()

    simple_transactions = [
        (date(year=2019, month=1, day=1), acc1, apples, "Apples #1", Decimal("5")),
        (date(year=2019, month=1, day=2), acc1, eggs, "Eggs #1", Decimal("10")),
        (date(year=2019, month=1, day=3), acc2, apples, "Other Apples", Decimal("4.5"))
    ]

    shop_transactions = [
        ("Shop #1", date(year=2019, month=1, day=10), (
            (acc1, apples, "Apples #1", Decimal("3")),
            (acc1, eggs, "Eggs #1", Decimal("7"))
        )),
        ("Shop #2", date(year=2019, month=1, day=11), (
            (acc2, apples, "Other Apples", Decimal("3")),
            (acc1, apples, "Apples #1", Decimal("5"))
        ))
    ]

    income_transactions = [
        (date(year=2019, month=1, day=1), inc1, acc1, "Salary", Decimal("1000")),
        (date(year=2019, month=1, day=1), inc2, acc2, "Salary", Decimal("1500"))
    ]

    # add 2 income transactions
    for income_tr in income_transactions:
        tr = piecash.Transaction(
            currency=curr,
            description=income_tr[3],
            post_date=income_tr[0],
            splits=[
                piecash.Split(account=income_tr[1], value=-income_tr[4]),
                piecash.Split(account=income_tr[2], value=income_tr[4])
            ]
        )
        book.flush()

    # add 3 simple transactions
    for simple_tr in simple_transactions:
        tr = piecash.Transaction(
            currency=curr,
            description=simple_tr[3],
            post_date=simple_tr[0],
            splits=[
                piecash.Split(account=simple_tr[1], value=-simple_tr[4]),
                piecash.Split(account=simple_tr[2], value=simple_tr[4])
            ]
        )
        book.flush()

    # add 2 shop transactions
    for shop_tr in shop_transactions:
        shop_name = shop_tr[0]
        day = shop_tr[1]
        list_of_splits = []
        for simple_tr in shop_tr[2]:
            list_of_splits.append(piecash.Split(account=simple_tr[0], value=-simple_tr[3]))
            list_of_splits.append(piecash.Split(account=simple_tr[1], value=simple_tr[3], memo=simple_tr[2]))
        tr = piecash.Transaction(
            currency=curr,
            description=shop_name,
            post_date=day,
            splits=list_of_splits
        )
        book.flush()

    book.save()


@pytest.fixture
def simple_book_path():

    example_fd, example_path = tempfile.mkstemp()
    currency = "PLN"
    create_simple_book(currency, example_path)

    yield example_path

    os.close(example_fd)
    os.unlink(example_path)


@pytest.fixture
def gnucash_db_parser_simple_book(simple_book_path):
    gdbp = GnuCashDBParser(simple_book_path, category_sep=category_sep_for_test())
    return gdbp

# ========== variables ========== #


def month_format():
    return "%Y-%m"

@pytest.fixture
def bk_months():
    """Returns list of ALL months used in creation of bk_category object."""
    months = ["2019-{x:02d}".format(x=x) for x in range(1, 13)]

    return months


def bk_column_names():
    """Returns list of column names from test piecash books, that are needed in creation of several bokeh views."""
    columns = ["Category", "MonthYear", "Price", "Product", "Date", "Currency", "Shop"]
    return columns


def bk_column_mapping():

    d = {
        "date": "Date",
        "price": "Price",
        "currency": "Currency",
        "product": "Product",
        "shop": "Shop",
        "all": "ALL_CATEGORIES",
        "type": "Type",
        "category": "Category",
        "monthyear": "MonthYear"
    }

    return d


@pytest.fixture
def bk_categories_simple():
    """Returns list of all categories used by some tests."""

    categories = [
        "Clothes",
        "Bread",
        "Eggs",
        "Fruits and Vegetables",
        "Meat",
        "Chips",
        "Petrol",
        "Rent",
        "Water and Electricity",
        "Toilet",
        "Personal - John",
        "Personal - Susan",
        "Other"
    ]
    return categories


@pytest.fixture
def bk_categories_extended():
    """Returns list of all "extended" categories used by some tests."""

    categories = [
        "Expenses:Family:Bathroom:Personal - John",
        "Expenses:Family:Bathroom:Personal - Susan",
        "Expenses:Family:Bathroom:Toilet",
        "Expenses:Family:Car:Petrol",
        "Expenses:Family:Flat:Rent",
        "Expenses:Family:Flat:Water and Electricity",
        "Expenses:Family:Grocery:Bread",
        "Expenses:Family:Grocery:Chips",
        "Expenses:Family:Grocery:Eggs",
        "Expenses:Family:Grocery:Fruits and Vegetables",
        "Expenses:Family:Grocery:Meat",
        "Expenses:Family:Other",
        "Expenses:John's Expenses:Clothes",
        "Expenses:Susan's Expenses:Clothes"
    ]

    return categories


@pytest.fixture
def bk_categories_combinations():
    """Returns list of all "combination" categories used by some tests."""

    categories = [
        'Expenses',
        'Expenses:Family',
        'Expenses:Family:Bathroom',
        'Expenses:Family:Bathroom:Personal - John',
        'Expenses:Family:Bathroom:Personal - Susan',
        'Expenses:Family:Bathroom:Toilet',
        'Expenses:Family:Car',
        'Expenses:Family:Car:Petrol',
        'Expenses:Family:Flat',
        'Expenses:Family:Flat:Rent',
        'Expenses:Family:Flat:Water and Electricity',
        'Expenses:Family:Grocery',
        'Expenses:Family:Grocery:Bread',
        'Expenses:Family:Grocery:Chips',
        'Expenses:Family:Grocery:Eggs',
        'Expenses:Family:Grocery:Fruits and Vegetables',
        'Expenses:Family:Grocery:Meat',
        'Expenses:Family:Other',
        "Expenses:John's Expenses",
        "Expenses:John's Expenses:Clothes",
        "Expenses:Susan's Expenses",
        "Expenses:Susan's Expenses:Clothes"
    ]

    return categories
# ========== bk_category ========== #


def bk_category_chosen_category():
    """Returns chosen category for creating bk_category object."""

    return "Bread"


@pytest.fixture
def bk_category(gnucash_db_parser_example_book, bk_months):
    """Returns initialized bk_category Object.

        Set properties are:
            - chosen category
            - months (all)
            - original_df
    """

    columns = bk_column_names()
    month_format_category = month_format()
    color_map = ColorMap()

    args = columns + [month_format_category, color_map]

    category = Category(*args)
    category.chosen_category = bk_category_chosen_category()
    category.months = bk_months
    category.original_df = gnucash_db_parser_example_book.get_expenses_df()
    return category


@pytest.fixture
def bk_category_initialized(bk_category):
    """Returns bk_category object (the same as from bk_category fixture), but with grid elements initialized."""

    bk_category.initialize_grid_elements()
    return bk_category


# ========== bk_overview ========== #


@pytest.fixture
def bk_overview(gnucash_db_parser_example_book, bk_months):
    columns = bk_column_names()
    test_date = datetime(year=2019, month=2, day=1)
    month_format_overview = month_format()
    color_map = ColorMap()

    args = columns + [month_format_overview, test_date, color_map]
    overview = Overview(*args)
    overview.months = bk_months
    overview.original_expense_df = gnucash_db_parser_example_book.get_expenses_df()
    overview.original_income_df = gnucash_db_parser_example_book.get_income_df()

    return overview


@pytest.fixture
def bk_overview_initialized(bk_overview):
    month = "2019-02"
    bk_overview.initialize_grid_elements(month)
    return bk_overview


# ========== bk_trends ========== #


@pytest.fixture
def bk_trends(gnucash_db_parser_example_book, bk_months):
    columns = bk_column_names()
    month_format_trends = month_format()
    color_map = ColorMap()

    args = columns + [month_format_trends, color_map]
    trends = Trends(*args)
    trends.months = bk_months
    trends.original_expense_df = gnucash_db_parser_example_book.get_expenses_df()

    return trends


@pytest.fixture
def bk_trends_initialized(bk_trends):
    bk_trends.initialize_gridplot(0)

    return bk_trends

# ========== bkapp ========== #


@pytest.fixture
def bkapp(gnucash_db_parser_example_book):

    bkapp = BokehApp(gnucash_db_parser_example_book.get_expenses_df(), gnucash_db_parser_example_book.get_income_df(),
                     bk_column_mapping(), month_format(), datetime(year=2019, month=2, day=1), category_sep_for_test())

    return bkapp

# ========== bk_settings ========== #


@pytest.fixture
def bk_settings(gnucash_db_parser_example_book, bkapp):
    df = gnucash_db_parser_example_book.get_expenses_df()
    mapping = bk_column_mapping()
    cat_types = ["Simple", "Extended", "Combinations"]
    settings = Settings(
        df[mapping["category"]],
        df[mapping["all"]],
        df[mapping["date"]],
        category_sep_for_test(),
        cat_types,
        bkapp.observer,
        bkapp
    )

    return settings


@pytest.fixture
def bk_settings_initialized(bk_settings):

    bk_settings.initialize_settings_variables()

    return bk_settings

# ========== Observer ========== #


@pytest.fixture
def observer():
    observer = Observer()
    return observer
