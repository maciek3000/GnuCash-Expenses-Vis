import pandas as pd


def test_get_list_of_transactions_example_book(gnucash_db_parser_example_book):
    returned_list = gnucash_db_parser_example_book._get_list_of_transactions(gnucash_db_parser_example_book.file_path)
    assert len(returned_list) == 2428


def test_get_list_of_transactions_simple_book(gnucash_db_parser_simple_book):
    curr = "PLN"
    expected_transactions = [
        ("Apples #1", "2019-01-01", "nan", "Expenses:Type #1:Fruits:Apples", "5", curr),
        ("Eggs #1", "2019-01-02", "nan", "Expenses:Type #2:Dairy:Eggs", "10", curr),
        ("Other Apples", "2019-01-03", "nan", "Expenses:Type #1:Fruits:Apples", "4.5", curr),
        ("Shop #1", "2019-01-10", "Apples #1", "Expenses:Type #1:Fruits:Apples", "3", curr),
        ("Shop #1", "2019-01-10", "Eggs #1", "Expenses:Type #2:Dairy:Eggs", "7", curr),
        ("Shop #2", "2019-01-11", "Other Apples", "Expenses:Type #1:Fruits:Apples", "3", curr),
        ("Shop #2", "2019-01-11", "Apples #1", "Expenses:Type #1:Fruits:Apples", "5", curr)
    ]

    returned_list = gnucash_db_parser_simple_book._get_list_of_transactions(gnucash_db_parser_simple_book.file_path)
    assert len(returned_list) == 7

    for expected_tr, returned_tr in zip(expected_transactions, returned_list):
        for exp_elem, ret_elem in zip(expected_tr, returned_tr):
            assert exp_elem == ret_elem


def test_create_df_from_simple_book(gnucash_db_parser_simple_book):
    # ['Date', 'Price', 'Currency', 'Product', 'Shop', 'ALL_CATEGORIES',
    #        'Type', 'Category', 'SubCategory', 'SubType', 'MonthYear'
    d = {
        "Date": ["01-Jan-2019", "02-Jan-2019", "03-Jan-2019", "10-Jan-2019", "11-Jan-2019"],
        "Price": 37.5,
        "Currency": "PLN",
        "Product": ["Apples #1", "Eggs #1", "Other Apples"],
        "Shop": ["Shop #1", "Shop #2"],
        "ALL_CATEGORIES": ["Expenses:Type #1:Fruits:Apples", "Expenses:Type #2:Dairy:Eggs"],
        "Type": ["Type #1", "Type #2"],
        "Category": ["Apples", "Eggs"],
        "MonthYear": ["01-2019"]
    }

    df = gnucash_db_parser_simple_book.get_df()
    assert len(df.columns) == 11

    keys = list(d.keys())
    keys.remove("Price")
    keys.remove("Currency")
    keys.remove("Date")
    keys.remove("ALL_CATEGORIES")

    for col in keys:
        print(col)
        unique = list(df[col].unique())
        print(unique)
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
        s = ":".join(elem)
        assert s in d['ALL_CATEGORIES']
