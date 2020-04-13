import pytest
import piecash
import tempfile
import os
from datetime import date, datetime
from decimal import Decimal
from flask_app.bkapp.color_map import ColorMap

from flask_app.gnucash.gnucash_example_creator import GnucashExampleCreator
from flask_app.gnucash.gnucash_db_parser import GnuCashDBParser
from flask_app.bkapp.bk_category import Category
from flask_app.bkapp.bk_overview import Overview

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


@pytest.fixture
def example_book_path():
    file_path = os.path.join(os.path.split(os.path.dirname(os.path.realpath(__file__)))[0],
                             "flask_app", "gnucash", "gnucash_examples", "example_gnucash.gnucash")
    return file_path


@pytest.fixture
def gnucash_db_parser_example_book(example_book_path):
    gdbp = GnuCashDBParser(file_path=example_book_path)
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
    gdbp = GnuCashDBParser(simple_book_path)
    return gdbp

# ========== bkapp ========== #


def month_format():
    return "%Y-%m"


def bk_months():
    """Returns list of ALL months used in creation of bk_category object."""
    months = ["2019-{x:02d}".format(x=x) for x in range(1, 13)]

    return months


@pytest.fixture
def bk_categories():
    """Returns list of all categories used by some bk_category tests."""

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

# ========== bk_category ========== #


def bk_category_chosen_category():
    """Returns chosen category for creating bk_category object."""

    return "Bread"


@pytest.fixture
def bk_category(gnucash_db_parser_example_book):
    """Returns initialized bk_category Object.

        Set properties are:
            - chosen category
            - months (all)
            - original_df
    """

    columns = ["Category", "MonthYear", "Price", "Product", "Date", "Currency", "Shop"]
    month_format_category = month_format()
    color_map = ColorMap()

    args = columns + [month_format_category, color_map]

    category = Category(*args)
    category.chosen_category = bk_category_chosen_category()
    category.months = bk_months()
    category.original_df = gnucash_db_parser_example_book.get_expenses_df()
    return category


@pytest.fixture
def bk_category_initialized(bk_category):
    """Returns bk_category object (the same as from bk_category fixture), but with grid elements initialized."""

    bk_category.initialize_grid_elements()
    return bk_category


# ========== bk_overview ========== #


@pytest.fixture
def bk_overview(gnucash_db_parser_example_book):
    columns = ["Category", "MonthYear", "Price", "Product", "Date", "Currency", "Shop"]
    test_date = datetime(year=2019, month=2, day=1)
    month_format_overview = month_format()
    color_map = ColorMap()

    args = columns + [month_format_overview, test_date, color_map]
    overview = Overview(*args)
    overview.months = bk_months()
    overview.original_expense_df = gnucash_db_parser_example_book.get_expenses_df()
    overview.original_income_df = gnucash_db_parser_example_book.get_income_df()

    return overview


@pytest.fixture
def bk_overview_initialized(bk_overview):
    month = "2019-02"
    bk_overview.initialize_grid_elements(month)
    return bk_overview
