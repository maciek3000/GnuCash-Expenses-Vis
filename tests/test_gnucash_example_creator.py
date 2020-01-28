import pytest
import piecash
import os
from collections import Counter
from datetime import date


@pytest.mark.parametrize(("key", "output"), (
        ("First", ("Transaction #1", "From", (100, 200))),
        ("Second", ("Transaction #2", "From", (4000,))),
))
def test_extract_data_single_transaction(gnucash_creator, key, output):
    """Testing of Extracting data from Tuples in the d dictionary used in create_example_book.

        Test for Single Transaction in the Tuple.
    """

    test_dict = {
        "First": {("Transaction #1", "From"): (100, 200)},
        "Second": {("Transaction #2", "From"): (4000,)},
    }

    func = gnucash_creator._GnucashExampleCreator__extract_data
    result = func(test_dict, key)[0]
    assert result[0] == output[0]
    assert result[1] == output[1]
    assert result[2] == output[2]


@pytest.mark.parametrize(("key", "outputs"), (
        ("First", (("Transaction #1", "From", (100, 200)),
                   ("Transaction #2", "From", (300,)))),
        ("Third", (("Transaction #3", "From", (200, 300)),
                   ("Transaction #4", "From", (500,)))
         ),))
def test_extract_data_multiple_transaction(gnucash_creator, key, outputs):
    """Testing of Extracting data from Tuples in the d dictionary used in create_example_book.

        Test for Multiple Transactions in the Tuple.
    """

    test_dict = {
        "First": {("Transaction #1", "From"): (100, 200),
                  ("Transaction #2", "From"): (300,)},
        "Third": {("Transaction #3", "From"): (200, 300),
                  ("Transaction #4", "From"): (500,)},
    }

    func = gnucash_creator._GnucashExampleCreator__extract_data
    result_tuple = func(test_dict, key)
    for output in outputs:
        assert output in result_tuple


@pytest.mark.parametrize(("date", "description", "price_range"), (
        (date(year=2019, month=1, day=1), "First Transaction", (400,)),
        (date(year=2019, month=1, day=2), "Second Transaction", (500, 600)),
))
def test_add_transaction(gnucash_creator, book, from_account, to_account, date, description, price_range):
    """Testing adding Transactions to the piecash book.

        Only simple Transactions are tested here.
    """

    assert len(book.transactions) == 0

    transaction = (description, from_account, price_range)
    func = gnucash_creator._GnucashExampleCreator__add_transaction
    func(book, date, book.default_currency, to_account, transaction)

    assert len(book.transactions) == 1

    # loop to get the info on Transactions
    for tr in book.transactions:
        assert tr.description == description
        assert tr.post_date == date

        from_value = None
        to_value = None

        for split in tr.splits:
            if split.account.type == "ASSET":
                assert split.account.name == from_account.name
                from_value = float(split.value)
            elif split.account.type == "EXPENSE":
                assert split.account.name == to_account.name
                to_value = float(split.value)

        assert from_value is not None and to_value is not None and from_value == -to_value

        if len(price_range) > 1:
            assert (price_range[0] <= to_value) and (to_value <= price_range[1])
        else:
            assert to_value == price_range[0]


@pytest.mark.parametrize(
    ("date", "shop_name", "transaction_list"),
    (
            (date(year=2019, month=1, day=1), "Grocery Test Shop #1",
             [("Transaction #1", (300,)), ["Transaction #2", (400,)]]),
            (date(year=2019, month=2, day=1), "Grocery Test Shop #2",
             [("Transaction #1", (400, 500)), ["Transaction #2", (1, 2)]])
    ))
def test_add_shop_transaction_same_asset(gnucash_creator, book, from_account, to_account, to_account_two, date,
                                         shop_name, transaction_list):
    """Testing adding Split (Shop) Transactions to the piecash book.

        All Transactions tested here have the same from_account (Asset Account).
    """

    assert len(book.transactions) == 0

    currency = book.default_currency
    list_of_splits = []
    list_of_transaction_names = []
    list_of_price_ranges = []

    for acc, transaction in zip([to_account, to_account_two], transaction_list):
        desc = transaction[0]
        single_price_range = transaction[1]
        list_of_transaction_names.append(desc)
        list_of_price_ranges.append(single_price_range)
        list_of_splits.append((acc, (desc, from_account, single_price_range)))

    func = gnucash_creator._GnucashExampleCreator__add_shop_transaction
    func(book, date, currency, list_of_splits, shop_name)

    assert len(book.transactions) == 1

    for tr in book.transactions:
        assert tr.description == shop_name
        assert tr.post_date == date

        total_price = 0
        for split in tr.splits:
            if split.account.type == "EXPENSE":
                assert split.memo.strip() in list_of_transaction_names
                total_price += float(split.value)

        price_zipped_list = [x[0] + x[1] for x in zip(*list_of_price_ranges)]
        if len(price_zipped_list) > 1:
            assert price_zipped_list[0] <= total_price <= price_zipped_list[1]
        else:
            assert total_price == price_zipped_list[0]


@pytest.mark.parametrize(
    ("date", "shop_name", "transaction_list"),
    (
            (date(year=2019, month=1, day=1), "Grocery Test Shop #1",
             [("Transaction #1", (300,)), ["Transaction #2", (400,)]]),
            (date(year=2019, month=2, day=1), "Grocery Test Shop #2",
             [("Transaction #1", (400, 500)), ["Transaction #2", (1, 2)]])
    ))
def test_add_shop_transaction_different_asset(gnucash_creator, book, from_account, from_account_two, to_account,
                                              to_account_two, date, shop_name, transaction_list):
    """Testing adding Split (Shop) Transactions to the piecash book.

        Every Transaction tested have a different from_account (Asset Account) from the other Transaction.
    """
    assert len(book.transactions) == 0

    currency = book.default_currency
    list_of_splits = []
    list_of_transaction_names = []
    list_of_price_ranges = []

    for accounts, transaction in zip([(to_account, from_account), (to_account_two, from_account_two)],
                                     transaction_list):
        desc = transaction[0]
        single_price_range = transaction[1]
        list_of_transaction_names.append(desc)
        list_of_price_ranges.append(single_price_range)
        list_of_splits.append((accounts[0], (desc, accounts[1], single_price_range)))

    func = gnucash_creator._GnucashExampleCreator__add_shop_transaction
    func(book, date, currency, list_of_splits, shop_name)

    assert len(book.transactions) == 1

    for tr in book.transactions:
        assert tr.description == shop_name
        assert tr.post_date == date

        total_price = 0
        total_asset = 0
        for split in tr.splits:
            if split.account.type == "EXPENSE":
                assert split.memo.strip() in list_of_transaction_names
                total_price += float(split.value)
            if split.account.type == "ASSET":
                total_asset += float(split.value)

        assert total_price == -total_asset

        price_zipped_list = [x[0] + x[1] for x in zip(*list_of_price_ranges)]
        if len(price_zipped_list) > 1:
            assert price_zipped_list[0] <= total_price <= price_zipped_list[1]
        else:
            assert total_price == price_zipped_list[0]


def test_create_book(gnucash_creator):
    """Testing reproducibility of the create_example_book function."""

    gnucash_creator.create_example_book()

    example_file_dir = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
    example_file_path = os.path.join(example_file_dir, "flask_app", "gnucash", "gnucash_examples",
                                     "example_gnucash.gnucash")

    test_book = piecash.open_book(gnucash_creator.file_path)
    compare_book = piecash.open_book(example_file_path)

    assert len(test_book.transactions) == len(compare_book.transactions)

    compare_list = []
    tr_list = []
    for book in (test_book, compare_book):
        total_price = 0
        tr_dict = Counter()
        for tr in book.transactions:
            for sp in tr.splits:
                if sp.account.type == "EXPENSE":
                    total_price += round(float(sp.value), 2)
            tr_dict[tr.description] += 1
        compare_list.append(total_price)
        tr_list.append(tr_dict)

    assert compare_list[0] == compare_list[1]

    for key in tr_list[0]:
        assert key in tr_list[1]
        assert tr_list[0][key] == tr_list[1][key]
