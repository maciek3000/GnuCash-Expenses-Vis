import pytest
import piecash
import tempfile
import os
from flask_app.gnucash.gnucash_example_creator import GnucashExampleCreator

# ========== gnucash_example_creator ========== #


@pytest.fixture
def gnucash_creator():
    """Test gnucash_example_creator Object"""
    example_fd, example_path = tempfile.mkstemp()
    currency = "PLN"
    seed = 42

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
