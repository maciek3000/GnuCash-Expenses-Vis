import pandas as pd


def test_get_list_of_expense_transactions_example_book(gnucash_db_parser_example_book):
    """Testing returned list of transactions from Example Gnucash file"""

    returned_list = gnucash_db_parser_example_book._GnuCashDBParser__get_list_of_transactions(
        gnucash_db_parser_example_book.expense_name
    )
    assert len(returned_list) == 2480

def test_get_list_of_income_transactions_example_book(gnucash_db_parser_example_book):
    returned_list = gnucash_db_parser_example_book._GnuCashDBParser__get_list_of_transactions(
        gnucash_db_parser_example_book.income_name
    )
    assert len(returned_list) == 24

def test_get_list_of_expense_transactions_simple_book(gnucash_db_parser_simple_book):
    """Testing returned list of transactions from simple piecash book (created manually)"""

    curr = "PLN"
    expected_transactions = [
        ("Apples #1", "2019-01-01", "nan", "Expenses:Main Type #1:Fruits:Apples", "5", curr),
        ("Eggs #1", "2019-01-02", "nan", "Expenses:Main Type #2:Dairy:Eggs", "10", curr),
        ("Other Apples", "2019-01-03", "nan", "Expenses:Main Type #1:Fruits:Apples", "4.5", curr),
        ("Shop #1", "2019-01-10", "Apples #1", "Expenses:Main Type #1:Fruits:Apples", "3", curr),
        ("Shop #1", "2019-01-10", "Eggs #1", "Expenses:Main Type #2:Dairy:Eggs", "7", curr),
        ("Shop #2", "2019-01-11", "Other Apples", "Expenses:Main Type #1:Fruits:Apples", "3", curr),
        ("Shop #2", "2019-01-11", "Apples #1", "Expenses:Main Type #1:Fruits:Apples", "5", curr)
    ]

    returned_list = gnucash_db_parser_simple_book._GnuCashDBParser__get_list_of_transactions(
        gnucash_db_parser_simple_book.expense_name
    )
    assert len(returned_list) == 7

    for expected_tr, returned_tr in zip(expected_transactions, returned_list):
        for exp_elem, ret_elem in zip(expected_tr, returned_tr):
            assert exp_elem == ret_elem

def test_get_list_of_income_transactions_simple_book(gnucash_db_parser_simple_book):

    curr = "PLN"
    expected_income_list = [
        ("Salary", "2019-01-01", "nan", "Income:Income #1", "-1000", curr),
        ("Salary", "2019-01-01", "nan", "Income:Income #2", "-1500", curr)
    ]
    actual_income_list = gnucash_db_parser_simple_book._GnuCashDBParser__get_list_of_transactions(
        gnucash_db_parser_simple_book.income_name
    )
    assert len(actual_income_list) == 2

    for expected_income, actual_income in zip(expected_income_list, actual_income_list):
        for exp_elem, act_elem in zip(expected_income, actual_income):
            assert act_elem == exp_elem

def test_create_expense_df_from_simple_book(gnucash_db_parser_simple_book):
    """Testing DataFrame returned by GnucashDBParser from simple piecash book (created manually)"""

    d = {
        "Date": ["01-Jan-2019", "02-Jan-2019", "03-Jan-2019", "10-Jan-2019", "11-Jan-2019"],
        "Price": 37.5,
        "Currency": "PLN",
        "Product": ["Apples #1", "Eggs #1", "Other Apples"],
        "Shop": ["Shop #1", "Shop #2"],
        "ALL_CATEGORIES": ["Expenses:Main Type #1:Fruits:Apples", "Expenses:Main Type #2:Dairy:Eggs"],
        "Type": ["Main Type #1", "Main Type #2"],
        "Category": ["Apples", "Eggs"],
        "MonthYear": ["01-2019"]
    }

    df = gnucash_db_parser_simple_book.get_expenses_df()
    assert len(df.columns) == 9

    keys = list(d.keys())
    keys.remove("Price")
    keys.remove("Currency")
    keys.remove("Date")
    keys.remove("ALL_CATEGORIES")

    for col in keys:
        unique = list(df[col].unique())
        for elem in unique:
            if not pd.isna(elem):
                assert elem in d[col]

    # Price
    assert df['Price'].sum() == d['Price']

    # Currency
    unique_curr = df['Currency'].unique()
    assert unique_curr[0] == 'PLN' and len(unique_curr) == 1

    # Dates
    dates = df['Date'].unique()
    for single_date in dates:
        assert pd.to_datetime(str(single_date)).strftime("%d-%b-%Y") in d['Date']

    # ALL_CATEGORIES
    for elem in df['ALL_CATEGORIES']:
        assert elem in d['ALL_CATEGORIES']


def test_create_expense_df_from_example_book(gnucash_db_parser_example_book):
    """Testing DataFrame returned by GnucashDBParser from Example Gnucash file"""

    all_categories = set(map(lambda x: "Expenses:Family:" + x, [
        "Grocery:Bread",
        "Grocery:Eggs",
        "Grocery:Meat",
        "Grocery:Chips",
        "Grocery:Fruits and Vegetables",
        "Car:Petrol",
        "Flat:Rent",
        "Flat:Water and Electricity",
        "Bathroom:Toilet",
        "Bathroom:Personal - John",
        "Bathroom:Personal - Susan",
        "Other"
    ])).union(["Expenses:John's Expenses:Clothes",
               "Expenses:Susan's Expenses:Clothes", ])

    shops = ["Grocery Shop #1", "Grocery Shop #2"]

    date_range = pd.date_range("01-Jan-2019", "31-Dec-2019")
    types = ["Family", "John's Expenses", "Susan's Expenses"]
    products = [
        "Clothes",
        "White Bread",
        "Rye Bread",
        "Butter",
        "Chicken",
        "Cow",
        "Eggs",
        "Chips",
        "Lollipops",
        "Apple",
        "Banana",
        "Tomato",
        "Pear",
        "Petrol",
        "Rent",
        "Water and Electricity",
        "Toilet Paper",
        "Facial Tissues",
        "Beard Balm",
        "Shampoo",
        "Face Cleanser",
        "Other"
    ]
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

    test_dict = {
        "Shop": shops,
        "Date": date_range,
        "Type": types,
        "Category": categories,
        "Product": products
    }

    df = gnucash_db_parser_example_book.get_expenses_df()

    assert len(df) == 2480

    # cols from test_dict
    for col in test_dict.keys():
        unique = df[col].unique()
        for elem in unique:
            if not pd.isna(elem):
                assert elem in test_dict[col]

    # ALL_CATEGORIES
    for elem in df["ALL_CATEGORIES"]:
        assert elem in all_categories

    # Price
    assert round(df["Price"].sum(), 2) == 55653.90
