import pytest
import piecash
import tempfile
from flask_app.gnucash.gnucash_example_creator import GnucashExampleCreator

# ----- gnucash_example_creator ----- #

@pytest.fixture
def gnucash_creator():
    example_fd, example_path = tempfile.mkstemp()
    currency = "PLN"
    seed = 1010
    return GnucashExampleCreator(example_path, currency, seed=1010)

@pytest.fixture
def book():
    book = piecash.create_book(currency="PLN")
    book.save()
    return book

@pytest.fixture
def to_account(book):
    to_account = piecash.Account("Test Expense Account", "EXPENSE", book.default_currency, parent=book.root_account)
    book.save()
    return to_account

@pytest.fixture
def from_account(book):
    from_account = piecash.Account("Test Asset Account", "ASSET", book.default_currency, parent=book.root_account)
    book.save()
    return from_account

@pytest.fixture
def to_account_two(book):
    to_account = piecash.Account("Test Expense Account 2", "EXPENSE", book.default_currency, parent=book.root_account)
    book.save()
    return to_account

@pytest.fixture
def from_account_two(book):
    from_account = piecash.Account("Test Asset Account 2", "ASSET", book.default_currency, parent=book.root_account)
    book.save()
    return from_account