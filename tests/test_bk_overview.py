import pytest
from datetime import datetime


@pytest.mark.parametrize(
    ("test_date", "expected_chosen", "expected_next"),
    (
        ("2019-02", "2019-02", "2019-03"),
        ("2019-12", "2019-12", "2020-01"),
        ("2010-11", "2010-11", "2010-12")
    )
)
def test_update_chosen_and_next_months(bk_overview, test_date, expected_chosen, expected_next):

    bk_overview._Overview__update_chosen_and_next_months(test_date)

    assert bk_overview.chosen_month == expected_chosen
    assert bk_overview.next_month == expected_next


@pytest.mark.parametrize(
    ("server_date", "expected_chosen", "expected_next"),
    (
        (datetime(year=2019, month=2, day=1), "2019-01", "2019-02"),
        (datetime(year=2019, month=6, day=1), "2019-05", "2019-06"),
        (datetime(year=2020, month=3, day=1), "2019-12", "2020-01")
    )
)
def test_update_chosen_and_next_months_with_different_server_date(
        bk_overview_initialized, server_date, expected_chosen, expected_next
):

    bk_overview_initialized.server_date = server_date
    bk_overview_initialized._Overview__update_chosen_and_next_months()

    assert bk_overview_initialized.chosen_month == expected_chosen
    assert bk_overview_initialized.next_month == expected_next
