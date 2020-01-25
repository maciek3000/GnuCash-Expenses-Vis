import pytest
from datetime import date


@pytest.mark.parametrize(("key", "output"), (
        ("First", ("Transaction #1", "From", (100, 200))),
        ("Second", ("Transaction #2", "From", (4000,))),
))
def test_extract_data_single_transaction(gnucash_creator, key, output):
    test_dict = {
        "First": {("Transaction #1", "From"): (100, 200)},
        "Second": {("Transaction #2", "From"): (4000,)},
    }

    func = gnucash_creator._GnucashExampleCreator__extract_data
    result= func(test_dict, key)[0]
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
    test_dict = {
        "First": {("Transaction #1", "From"): (100, 200),
                  ("Transaction #2", "From"): (300, )},
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

    assert len(book.transactions) == 0
    transaction = (description, from_account, price_range)
    func = gnucash_creator._GnucashExampleCreator__add_transaction
    func(book, date, book.default_currency, to_account, transaction)
    assert len(book.transactions) == 1

    for tr in book.transactions:
        assert tr.description == description
        assert tr.post_date == date

        for split in tr.splits:
            if split.account.type == "ASSET":
                assert split.account.name == from_account.name
                from_value = float(split.value)
            elif split.account.type == "EXPENSE":
                assert split.account.name == to_account.name
                to_value = float(split.value)

        assert from_value == -to_value

        if len(price_range) > 1:
            assert (price_range[0] <= to_value) and (to_value <= price_range[1])
        else:
            assert to_value == price_range[0]


@pytest.mark.parametrize(
    ("date", "shop_name", "transaction_list"),
    (date(2019, 1, 1), "Grocery Test Shop #1", [("Transaction #1", (300,)), ("Transaction #2", (400,))]),
    (date(2019, 2, 1), "Grocery Test Shop #2", [("Transaction #1", (400, 500)), ("Transaction #2", (1, 2))])
)
def test_add_shop_transaction_same_asset(gnucash_creator, book, from_account, to_account, to_account_two,
                                         date, shop_name, transaction_list):
    assert len(book.transactions) == 0

    currency = book.default_currency
    #split = (to_account, (description, from_account, price_range))
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

        for split in tr.splits:
            assert split.memo.strip() in list_of_transaction_names


