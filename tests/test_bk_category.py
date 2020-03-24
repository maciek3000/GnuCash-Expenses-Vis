from flask_app.bkapp.bk_category import unique_values_from_column
import pytest
import pandas as pd
import numpy as np
from bokeh.models.widgets import Div
from bokeh.models.plots import Plot
from bokeh.models import ColumnDataSource, DataTable, Select
from math import isclose


@pytest.mark.parametrize(("df", "col_name", "expected_result"), (
        (pd.DataFrame({"a": [1, 1, 4, 6, 8, 10], "b": [5, 5, 6, 7, 4, 10]}), "a", [1, 4, 6, 8, 10]),
        (pd.DataFrame({"a": [1, 1, 4, 6, 8, 10], "b": [5, 5, 6, 7, 4, 10]}), "b", [4, 5, 6, 7, 10]),
        (pd.DataFrame({"a": ["one", "two", "two", np.nan], "b": ["one", "on", "one2", "on"]}), "a",
         ["nan", "one", "two"]),
        (pd.DataFrame({"a": ["one", "two", "two", np.nan], "b": ["one", "on", "one2", "on"]}), "b",
         ["on", "one", "one2"]),
))
def test_get_unique_values_from_column(df, col_name, expected_result):
    result = unique_values_from_column(df, col_name)
    assert result == expected_result


def test_update_chosen_category(bk_category):
    new_category = "Bread"
    bk_category._Category__update_chosen_category(new_category)

    assert bk_category.chosen_category == new_category

@pytest.mark.parametrize(
    ("indices", "result"),
    (
     ([0, 1, 4], ["01-2019", "02-2019", "05-2019"]),
     ([0], ["01-2019"]),
     ([], ["01-2019", "02-2019", "03-2019", "04-2019", "05-2019", "06-2019",
              "07-2019", "08-2019", "09-2019", "10-2019", "11-2019", "12-2019"]),
     ([1, 6, 3], ["02-2019", "07-2019", "04-2019"])
     )
)
def test_update_selected_months(bk_category, indices, result):
    bk_category._Category__update_chosen_months(indices)

    assert result == bk_category.chosen_months

def test_initialize_grid_elements(bk_category):

    grid_elems = [
        (bk_category.g_category_title, Div),
        (bk_category.g_category_fraction, Div),
        (bk_category.g_category_products_fraction, Div),
        (bk_category.g_total_from_category, Div),
        (bk_category.g_total_products_from_category, Div),
        (bk_category.g_statistics_table, Div),
        (bk_category.g_line_plot, Plot),
        (bk_category.g_dropdown, Select),
        (bk_category.g_product_histogram, DataTable),
        (bk_category.g_transactions, DataTable)
    ]
    source_elems = [
        bk_category.g_line_plot,
        bk_category.g_transactions,
        bk_category.g_product_histogram
    ]

    bk_category.initialize_grid_elements()

    for name, single_type in grid_elems:
        assert name in bk_category.grid_elem_dict
        assert isinstance(bk_category.grid_elem_dict[name], single_type)

    for source_elem in source_elems:
        assert source_elem in bk_category.grid_source_dict
        assert isinstance(bk_category.grid_source_dict[source_elem], ColumnDataSource)

@pytest.mark.parametrize(
    ("category", "expected_sum"),
    (
        ("Bread", 2789.28),
        ("Petrol", 1661.97),
        ("Rent", 24000)
    )
)
def test_update_chosen_category_dataframe(bk_category, bk_category_categories, category, expected_sum):
    categories = bk_category_categories
    categories.remove(category)

    bk_category.chosen_category = category
    bk_category._Category__update_chosen_category_dataframe()

    assert isclose(bk_category.chosen_category_df[bk_category.price].sum(), expected_sum)

    for cat in categories:
        assert cat not in unique_values_from_column(bk_category.chosen_category_df, bk_category.category)

@pytest.mark.parametrize(
    ("months", "expected_sum"),
    (
        (["03-2019", "04-2019", "05-2019"], 727.01),
        (["05-2019", "01-2019"], 479.15),
        ([], 2789.28)
    )
)
def test_update_chosen_months_and_category_dataframe(bk_category, bk_category_categories, months, expected_sum):
    bk_category.chosen_category = "Bread"

    if len(months) == 0:
        months = bk_category.months

    bk_category.chosen_months = months
    bk_category._Category__update_chosen_months_and_category_dataframe()


    unique_months = unique_values_from_column(bk_category.chosen_months_and_category_df, bk_category.monthyear)
    unique_categories = unique_values_from_column(bk_category.chosen_months_and_category_df, bk_category.category)

    not_chosen_months = bk_category.months.copy()
    bk_category_categories.remove(bk_category.chosen_category)

    for new_month in months:
        not_chosen_months.remove(new_month)

    # assertions

    for cat in bk_category_categories:
        assert cat not in unique_categories

    for chosen_month in months:
        assert chosen_month in unique_months

    for month in not_chosen_months:
        assert month not in unique_months

    assert isclose(bk_category.chosen_months_and_category_df[bk_category.price].sum(), expected_sum)

@pytest.mark.parametrize(
    ("category", "expected_text"),
    (
        ("Bread", "Bread"),
        ("Grocery is cool", "Grocery is cool"),
        ("Testing", "Testing")
    )
)
def test_update_category_title(bk_category_initialized, category, expected_text):
    bk_category_initialized.chosen_category = category
    bk_category_initialized._Category__category_title = "{category}"
    bk_category_initialized._Category__update_category_title()

    actual_text = bk_category_initialized.grid_elem_dict[bk_category_initialized.g_category_title].text
    assert actual_text == expected_text
    assert actual_text != ""
    assert len(actual_text) > 0

@pytest.mark.parametrize(
    ("category", "dict_of_expected_values"),
    (
        ("Eggs", {
            "last": 278.32,
            "mean": 229.44,
            "std": 31.13,
            "median": 226.22,
            "min": 191.06,
            "max": 284.08,
            "count": 223,
            "curr": "PLN"
        }),
        ("Petrol", {
            "last": np.nan,
            "mean": 237.42,
            "std": 69.17,
            "min": 156.92,
            "median": 221.90,
            "max": 343.43,
            "count": 7,
            "curr": "PLN"
        })
    )
)
def test_update_statistics_table(bk_category_initialized, category, dict_of_expected_values):

    bk_category_initialized.chosen_category = category
    bk_category_initialized._Category__update_chosen_category_dataframe()

    bk_category_initialized._Category__update_statistics_table()

    expected_text = bk_category_initialized.statistics_table.format(**dict_of_expected_values)
    actual_text = bk_category_initialized.grid_elem_dict[bk_category_initialized.g_statistics_table].text

    assert expected_text == actual_text

@pytest.mark.parametrize(
    ("category", "total_from_category"),
    (
        ("Bread", 2789.28),
        ("Other", 6903.35),
        ("Rent", 24000)
    )
)
def test_update_total_from_category(bk_category_initialized, category, total_from_category):

    bk_category_initialized.chosen_category = category
    bk_category_initialized._Category__update_chosen_category_dataframe()
    bk_category_initialized._Category__update_total_from_category()

    expected_text = bk_category_initialized.total_from_category.format(total_from_category=total_from_category)
    actual_text = bk_category_initialized.grid_elem_dict[bk_category_initialized.g_total_from_category].text

    assert actual_text == expected_text


@pytest.mark.parametrize(
    ("category", "category_fraction"),
    (
        ("Bread", 0.0501),
        ("Other", 0.124),
        ("Rent", 0.4312)
    )
)
def test_update_category_fraction(bk_category_initialized, category, category_fraction):
    bk_category_initialized.chosen_category = category
    bk_category_initialized._Category__update_chosen_category_dataframe()
    bk_category_initialized._Category__update_category_fraction()

    expected_text = bk_category_initialized.category_fraction.format(category_fraction=category_fraction)
    actual_text = bk_category_initialized.grid_elem_dict[bk_category_initialized.g_category_fraction].text

    assert actual_text == expected_text

@pytest.mark.parametrize(
    ("category", "total_products"),
    (
        ("Bread", 669),
        ("Other", 136),
        ("Rent", 12)
    )
)
def test_update_total_products_from_category(bk_category_initialized, category, total_products):
    bk_category_initialized.chosen_category = category
    bk_category_initialized._Category__update_chosen_category_dataframe()
    bk_category_initialized._Category__update_total_products_from_category()

    expected_text = bk_category_initialized.total_products_from_category.format(
        total_products_from_category=total_products)
    actual_text = bk_category_initialized.grid_elem_dict[bk_category_initialized.g_total_products_from_category].text

    assert actual_text == expected_text

@pytest.mark.parametrize(
    ("category", "product_fraction"),
    (
        ("Bread", 0.2698),
        ("Other", 0.0548),
        ("Rent", 0.0048)
    )
)
def test_update_category_products_fraction(bk_category_initialized, category, product_fraction):
    bk_category_initialized.chosen_category = category
    bk_category_initialized._Category__update_chosen_category_dataframe()
    bk_category_initialized._Category__update_category_products_fraction()

    expected_text = bk_category_initialized.category_products_fraction.format(
        category_products_fraction=product_fraction)
    actual_text = bk_category_initialized.grid_elem_dict[bk_category_initialized.g_category_products_fraction].text

    assert actual_text == expected_text