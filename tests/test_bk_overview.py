import pytest
import numpy as np
from datetime import datetime

from math import isclose, pi

from flask_app.bkapp.pandas_functions import unique_values_from_column

from bokeh.models import Select, ColumnDataSource
from bokeh.models.plots import Plot
from bokeh.models.widgets import Div


def test_initialize_grid_elements(bk_overview):
    """Testing if initialization of Overvied Grid Elements is performed correctly."""

    grid_elems = [
        (bk_overview.g_month_dropdown, Select),
        (bk_overview.g_month_title, Div),
        (bk_overview.g_expenses_chosen_month, Div),
        (bk_overview.g_expenses_chosen_month_subtitle, Div),
        (bk_overview.g_trivia_title, Div),
        (bk_overview.g_total_products_chosen_month, Div),
        (bk_overview.g_different_shops_chosen_month, Div),
        (bk_overview.g_savings_info, Div),
        (bk_overview.g_savings_piechart, Plot),
        (bk_overview.g_category_expenses_title, Div),
        (bk_overview.g_category_expenses, Plot)
    ]

    source_elems = [
        bk_overview.g_savings_piechart,
        bk_overview.g_category_expenses
    ]

    bk_overview.initialize_grid_elements()

    # checking if Grid Elements are initialized
    for name, element in grid_elems:
        assert name in bk_overview.grid_elem_dict
        assert isinstance(bk_overview.grid_elem_dict[name], element)

    # checking if ColumnDataSource is initialized for specified elements
    for source_name in source_elems:
        assert source_name in bk_overview.grid_source_dict
        assert isinstance(bk_overview.grid_source_dict[source_name], ColumnDataSource)


@pytest.mark.parametrize(
    ("test_date", "expected_chosen", "expected_next"),
    (
            ("2019-02", "2019-02", "2019-03"),
            ("2019-12", "2019-12", "2020-01"),
            ("2010-11", "2010-11", "2010-12")
    )
)
def test_update_chosen_and_next_months(bk_overview, test_date, expected_chosen, expected_next):
    """Testing if update_chosen_and_next_months function works correctly when date is passed to the function."""
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
    """Testing if update_chosen_and_next_months function works correctly when no date is passed as an argument."""
    bk_overview_initialized.server_date = server_date
    bk_overview_initialized._Overview__update_chosen_and_next_months()

    assert bk_overview_initialized.chosen_month == expected_chosen
    assert bk_overview_initialized.next_month == expected_next


@pytest.mark.parametrize(
    ("chosen_month", "next_month", "expected_sum_chosen", "expected_sum_next"),
    (
            ("2019-01", "2019-02", 5162.93, 4503.46),
            ("2019-02", "2019-03", 4503.46, 4613.9),
            ("2019-12", "2020-01", 4032.21, None)
    )
)
def test_update_expense_dataframes(
        bk_overview_initialized, chosen_month, next_month, expected_sum_chosen, expected_sum_next
):
    """Testing if updating Expense Dataframes work correctly."""

    bk_overview_initialized.chosen_month = chosen_month
    bk_overview_initialized.next_month = next_month

    bk_overview_initialized._Overview__update_expense_dataframes()

    df_chosen = bk_overview_initialized.chosen_month_expense_df
    df_next = bk_overview_initialized.next_month_expense_df

    chosen_month_months = unique_values_from_column(df_chosen, bk_overview_initialized.monthyear)
    next_month_months = unique_values_from_column(df_next, bk_overview_initialized.monthyear)

    assert {chosen_month} == set(chosen_month_months)
    assert isclose(
        bk_overview_initialized.chosen_month_expense_df[bk_overview_initialized.price].sum(), expected_sum_chosen
    )

    if expected_sum_next is not None:
        assert {next_month} == set(next_month_months)
        assert isclose(
            bk_overview_initialized.next_month_expense_df[bk_overview_initialized.price].sum(), expected_sum_next
        )
    else:
        assert len(set(next_month_months)) == 0
        assert bk_overview_initialized.next_month_expense_df[bk_overview_initialized.price].sum() == 0


def test_update_income_dataframes(bk_overview_initialized):
    """Testing if update_income_dataframes function correctly updates Income DataFrames"""

    months = bk_overview_initialized.months
    for i in range(len(months)):
        index_error_flag = False
        bk_overview_initialized.chosen_month = months[i]
        try:
            bk_overview_initialized.next_month = months[i+1]
        except IndexError:
            bk_overview_initialized.next_month = "2020-01"
            index_error_flag = True

        bk_overview_initialized._Overview__update_income_dataframes()

        chosen_month_months = set(
            unique_values_from_column(bk_overview_initialized.chosen_month_income_df, bk_overview_initialized.monthyear)
        )
        next_month_months = set(
            unique_values_from_column(bk_overview_initialized.next_month_income_df, bk_overview_initialized.monthyear)
        )
        assert chosen_month_months == {months[i]}
        assert bk_overview_initialized.chosen_month_income_df[bk_overview_initialized.price].sum() == -6000

        if not index_error_flag:
            assert next_month_months == {months[i+1]}
            assert bk_overview_initialized.next_month_income_df[bk_overview_initialized.price].sum() == -6000
        else:
            assert len(next_month_months) == 0
            assert bk_overview_initialized.next_month_income_df[bk_overview_initialized.price].sum() == 0


@pytest.mark.parametrize(
    ("month",),
    (
        ("2019-01",),
        ("2020-01",),
        ("1990-10",),
    )
)
def test_update_chosen_month_title(bk_overview_initialized, month):
    """Testing if updating month_title Div works correctly."""

    expected_text = bk_overview_initialized.month_title.format(last_month=month)

    bk_overview_initialized.chosen_month = month
    bk_overview_initialized._Overview__update_chosen_month_title()

    actual_text = bk_overview_initialized.grid_elem_dict[bk_overview_initialized.g_month_title].text

    assert actual_text == expected_text


@pytest.mark.parametrize(
    ("month", "expected_sum"),
    (
        ("2019-01", 5162.93),
        ("2019-02", 4503.46)
    )
)
def test_update_expenses_chosen_month(bk_overview_initialized, month, expected_sum):
    """Testing if updating Div with calculated Expenses works correctly."""

    expected_text = bk_overview_initialized.expenses_chosen_month.format(expenses_chosen_month=expected_sum)

    bk_overview_initialized.chosen_month = month
    bk_overview_initialized._Overview__update_expense_dataframes()  # chosen dataframes need to be updated

    bk_overview_initialized._Overview__update_expenses_chosen_month()
    actual_text = bk_overview_initialized.grid_elem_dict[bk_overview_initialized.g_expenses_chosen_month].text

    assert actual_text == expected_text


@pytest.mark.parametrize(
    ("month", "expected_value"),
    (
        ("2019-01", 203),
        ("2019-10", 202),
        ("2019-06", 205)
    )
)
def test_update_total_products_chosen_month(bk_overview_initialized, month, expected_value):
    """Testing if update_total_products_chosen_month function correctly calculates and updates specific Div."""

    expected_text = bk_overview_initialized.total_products_chosen_month.format(
        total_products_chosen_month=expected_value
    )

    bk_overview_initialized.chosen_month = month
    bk_overview_initialized._Overview__update_expense_dataframes()  # chosen dataframes need to be updated

    bk_overview_initialized._Overview__update_total_products_chosen_month()
    actual_text = bk_overview_initialized.grid_elem_dict[bk_overview_initialized.g_total_products_chosen_month].text

    assert actual_text == expected_text


@pytest.mark.parametrize(
    ("month", "expected_value"),
    (
        ("2019-01", 3),
        ("2019-06", 3),
        ("2019-12", 3)
    )
)
def test_update_different_shops_chosen_month(bk_overview_initialized, month, expected_value):
    """Testing if update_different_shops_chosen_month function correctly updates specific Div."""

    expected_text = bk_overview_initialized.different_shops_chosen_month.format(
        different_shops_chosen_month=expected_value
    )

    bk_overview_initialized.chosen_month = month
    bk_overview_initialized._Overview__update_expense_dataframes()  # chosen dataframes need to be updated

    bk_overview_initialized._Overview__update_different_shops_chosen_month()
    actual_text = bk_overview_initialized.grid_elem_dict[bk_overview_initialized.g_different_shops_chosen_month].text

    assert actual_text == expected_text


@pytest.mark.parametrize(
    ("chosen_month", "expected_savings", "expected_income", "expected_expenses"),
    (
        ("2019-01", 0.1395, 6000, 5162.93),
        ("2019-03", 0.2310, 6000, 4613.9),
        ("2020-01", np.nan, None, None)
    )
)
def test_calculate_expense_percentage(
        bk_overview_initialized, chosen_month, expected_savings, expected_income, expected_expenses
):
    """Testing if calculating_expense_percentages works correctly."""

    bk_overview_initialized.chosen_month = chosen_month
    bk_overview_initialized._Overview__update_expense_dataframes()
    bk_overview_initialized._Overview__update_income_dataframes()

    actual_savings, actual_income, actual_expenses = bk_overview_initialized._Overview__calculate_expense_percentage()
    if expected_income is not None:
        assert isclose(expected_income, actual_income)
        assert isclose(expected_expenses, actual_expenses)
        assert isclose(expected_savings, actual_savings, rel_tol=1e-04)
    else:
        assert np.isnan(actual_savings)
        assert actual_income == 0
        assert actual_expenses == 0


@pytest.mark.parametrize(
    ("savings", "income", "expenses"),
    (
        (0.3549, 2000, 1290.05),
        (0.1840, 5879.25, 4796.99),
        (0.2500, 1000, 750),
        (0, 1000, 1000)
    )
)
def test_update_savings_info_positive(bk_overview_initialized, savings, income, expenses):
    """Testing if update_savings_info function works correctly when savings argument is positive or 0."""

    savings_id = "positive_savings"
    expected_text = (bk_overview_initialized.savings_positive + bk_overview_initialized.income_expenses_text).format(
        savings=savings, income=income, expenses=expenses, savings_id=savings_id
    )

    bk_overview_initialized._Overview__update_savings_info(savings, income, expenses)
    actual_text = bk_overview_initialized.grid_elem_dict[bk_overview_initialized.g_savings_info].text
    assert actual_text == expected_text


@pytest.mark.parametrize(
    ("savings", "income", "expenses"),
    (
        (-0.2843, 2000, 2568.76),
        (-1.4870, 4985.23, 12398.58),
        (-0.25, 1000, 1250)
    )
)
def test_update_savings_info_negative(bk_overview_initialized, savings, income, expenses):
    """Testing if update_savings_info function works correctly when savings argument is negative."""

    savings_id = "negative_savings"
    expected_savings = - savings
    expected_text = (bk_overview_initialized.savings_negative + bk_overview_initialized.income_expenses_text).format(
        savings=expected_savings, income=income, expenses=expenses, savings_id=savings_id
    )

    bk_overview_initialized._Overview__update_savings_info(savings, income, expenses)
    actual_text = bk_overview_initialized.grid_elem_dict[bk_overview_initialized.g_savings_info].text
    assert actual_text == expected_text


@pytest.mark.parametrize(
    ("savings", "start_angle", "expected_angle"),
    (
        (0.25,  pi, 0.5 * pi),
        (1, (pi/2), -1.5 * pi),
        (0.56, 0, -1.12 * pi)
    )
)
def test_update_savings_piechart_positive_savings(bk_overview_initialized, savings, start_angle, expected_angle):
    """Testing if update_savings_piechart function correctly assigns color and end angle when savings are positive."""

    expected_color = bk_overview_initialized.color_map.positive_color

    bk_overview_initialized.piechart_start_angle = start_angle
    bk_overview_initialized._Overview__update_savings_piechart(savings)

    source = bk_overview_initialized.grid_source_dict[bk_overview_initialized.g_savings_piechart]

    actual_color = source.data["color"][0]
    actual_angle = source.data["end_angle"][0]

    assert actual_color == expected_color
    assert isclose(actual_angle, expected_angle, rel_tol=1e-07)


@pytest.mark.parametrize(
    ("savings", "start_angle", "expected_angle"),
    (
        (-0.25, pi, 0.5 * pi),
        (-1, (pi / 2), -1.5 * pi),
        (-0.56, 0, -1.12 * pi),
        (-3.14, 1.5*pi, -2*pi)
    )
)
def test_update_savings_piechart_negative_savings(bk_overview_initialized, savings, start_angle, expected_angle):
    """Testing if update_savings_piechart function correctly assigns color and end angle when savings are negative."""

    expected_color = bk_overview_initialized.color_map.negative_color

    bk_overview_initialized.piechart_start_angle = start_angle
    bk_overview_initialized._Overview__update_savings_piechart(savings)

    source = bk_overview_initialized.grid_source_dict[bk_overview_initialized.g_savings_piechart]

    actual_color = source.data["color"][0]
    actual_angle = source.data["end_angle"][0]

    assert actual_color == expected_color
    assert isclose(actual_angle, expected_angle, rel_tol=1e-07)


@pytest.mark.parametrize(
    ("chosen_month", "expected_categories", "expected_values"),
    (
        (
            "2019-01",
            ["Rent", "Clothes", "Other", "Meat", "Fruits and Vegetables", "Bread", "Eggs", "Chips",
             "Water and Electricity", "Personal - Susan", "Toilet"],
            [2000, 1403.98, 364.52, 319.86, 299.73, 223.09, 191.64, 148.66, 146.55, 40.02, 24.88]
        ),
        (
            "2019-06",
            ["Rent", "Other", "Fruits and Vegetables", "Bread", "Meat", "Eggs", "Clothes", "Chips",
             "Personal - John", "Water and Electricity", "Toilet", "Personal - Susan"],
            [2000, 403.32, 302.78, 253.01, 238.09, 200.61, 126.91, 107.05, 97.73, 92.49, 39.75, 14.61]
        )
    )
)
def test_update_category_barplot(bk_overview_initialized, chosen_month, expected_categories, expected_values):
    """Testing if updating category expenses barplot works correctly."""

    bk_overview_initialized.chosen_month = chosen_month
    bk_overview_initialized._Overview__update_expense_dataframes()

    bk_overview_initialized._Overview__update_category_barplot()

    fig = bk_overview_initialized.grid_elem_dict[bk_overview_initialized.g_category_expenses]
    source = bk_overview_initialized.grid_source_dict[bk_overview_initialized.g_category_expenses]

    actual_x_range = fig.x_range.factors
    actual_categories = source.data["x"].tolist()
    actual_values = source.data["top"].tolist()

    assert actual_x_range == expected_categories
    assert actual_categories == expected_categories

    assert len(actual_values) > 0

    for i in range(len(actual_values)):
        assert isclose(actual_values[i], expected_values[i], rel_tol=1e-04)
