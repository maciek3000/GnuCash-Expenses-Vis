import pytest

@pytest.mark.parametrize(
    ("test_date", "expected_current", "expected_future"),
    (
        ("02-2019", "02-2019", "03-2019"),
        ("12-2019", "12-2019", "01-2020"),
        ("11-2010", "11-2010", "12-2010"),
        (None, "01-2019", "02-2019")
    )
)
def test_update_current_and_future_months(bk_overview, test_date, expected_current, expected_future):

    if test_date is None:
        bk_overview._Overview__update_current_and_future_months()
    else:
        bk_overview._Overview__update_current_and_future_months(test_date)

    assert bk_overview.current_month == expected_current
    assert bk_overview.future_month == expected_future
