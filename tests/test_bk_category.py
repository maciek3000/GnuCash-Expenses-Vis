from flask_app.bkapp.pandas_functions import unique_values_from_column
import pytest
import numpy as np
from bokeh.models.widgets import Div
from bokeh.models.plots import Plot
from bokeh.models import ColumnDataSource, DataTable, Select
from math import isclose


def test_update_chosen_category(bk_category):
    """Testing if the chosen_category attribute of bk_category is being updated correctly."""

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
    """Testing if updating selected months based on provided indices works correctly."""
    bk_category._Category__update_chosen_months(indices)

    assert result == bk_category.chosen_months


def test_initialize_grid_elements(bk_category):
    """Testing if initializing grid elements of bk_category grid is being done correctly."""

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

    # checking Grid Elements (e.g. Divs, Plot, etc)
    for name, single_type in grid_elems:
        assert name in bk_category.grid_elem_dict
        assert isinstance(bk_category.grid_elem_dict[name], single_type)

    # checking Grid ColumnDataSources connected with Elements
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
    """Testing if updating DataFrame based on provided category functions correctly."""

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
def test_update_chosen_months_and_category_dataframe(bk_category, months, expected_sum):
    """Testing if updating DataFrame based on chosen category and months works correctly."""

    bk_category.chosen_category = "Bread"

    if len(months) == 0:
        months = bk_category.months

    bk_category.chosen_months = months
    bk_category._Category__update_chosen_months_and_category_dataframe()

    unique_months = unique_values_from_column(bk_category.chosen_months_and_category_df, bk_category.monthyear)
    unique_categories = unique_values_from_column(bk_category.chosen_months_and_category_df, bk_category.category)

    # assertions

    assert set(unique_categories) == {bk_category.chosen_category}
    assert set(unique_months) == set(months)
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
    """Testing if Category Title Div is being updated correctly."""

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
    """Testing if the Statistics Table Div is being updated with correct values."""

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
    """Testing if the Total Sum from a Category Div is being updated correctly."""

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
    """Testing if the Category Fraction (Percentage) Expenses Div is being updated correctly."""

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
    """Testing if Total Products Count Div is being updated with correct values."""

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
    """Testing if Products Count Fraction (Percentage) Div is being updated correctly."""

    bk_category_initialized.chosen_category = category
    bk_category_initialized._Category__update_chosen_category_dataframe()
    bk_category_initialized._Category__update_category_products_fraction()

    expected_text = bk_category_initialized.category_products_fraction.format(
        category_products_fraction=product_fraction)
    actual_text = bk_category_initialized.grid_elem_dict[bk_category_initialized.g_category_products_fraction].text

    assert actual_text == expected_text


@pytest.mark.parametrize(
    ("category", "expected_values", "expected_range_end"),
    (
            ("Bread", [223.089, 190.850, 270.110, 200.840, 256.060, 253.010,
                       276.370, 258.180, 221.270, 204.660, 206.800, 228.040], 279.1337),
            ("Petrol", [np.nan, 343.43, 278.89, 156.92, 293.96, np.nan,
                        np.nan, np.nan, 184.81, 182.06, 221.9, np.nan], 346.8643),
            ("Rent", [2000] * 12, 2020)
    )
)
def test_update_line_plot(bk_category_initialized, category, expected_values, expected_range_end):
    """Testing if the Line Plot and corresponding ColumnDataSource is being updated correctly."""

    bk_category_initialized.chosen_category = category
    bk_category_initialized._Category__update_chosen_category_dataframe()
    bk_category_initialized._Category__update_line_plot()

    actual_values = bk_category_initialized.grid_source_dict[bk_category_initialized.g_line_plot].data["y"]
    actual_range_end = bk_category_initialized.grid_elem_dict[bk_category_initialized.g_line_plot].y_range.end

    for i in range(len(actual_values)):
        if np.isnan(actual_values[i]):
            assert np.isnan(expected_values[i])
        else:
            assert isclose(actual_values[i], expected_values[i], rel_tol=1e-02)
    assert actual_range_end == expected_range_end


@pytest.mark.parametrize(
    ("category", "chosen_months", "expected_values"),
    (
            ("Bread", ["01-2019", "03-2019", "04-2019"], {"White Bread": 54,
                                                          "Rye Bread": 48,
                                                          "Butter": 62}),
            ("Petrol", ["01-2019", "02-2019", "03-2019", "04-2019", "05-2019", "06-2019",
                        "07-2019", "08-2019", "09-2019", "10-2019", "11-2019", "12-2019"],
             {
                 "Petrol": 11,
             }),
            ("Rent", ["06-2019"], {"Rent": 1})
    )
)
def test_update_product_histogram_table(bk_category_initialized, category, chosen_months, expected_values):
    """Testing if the Product Histogram (Product Counts) DataTable ColumnDataSource is being updated correctly."""

    bk_category_initialized.chosen_category = category
    bk_category_initialized.chosen_months = chosen_months
    bk_category_initialized._Category__update_chosen_months_and_category_dataframe()
    bk_category_initialized._Category__update_product_histogram_table()

    source_data_values = bk_category_initialized.grid_source_dict[
        bk_category_initialized.g_product_histogram].data
    product = source_data_values["index"]
    count = source_data_values["Product"]

    actual_values = dict(zip(product, count))

    assert set(expected_values.keys()) == set(actual_values.keys())
    for val in expected_values:
        assert expected_values[val] == actual_values[val]


@pytest.mark.parametrize(
    ("category", "chosen_months", "expected_sum", "expected_count"),
    (
            ("Bread", ["01-2019", "03-2019", "04-2019"], 694.04, 164),
            ("Petrol", ["01-2019", "02-2019", "03-2019", "04-2019", "05-2019", "06-2019",
                        "07-2019", "08-2019", "09-2019", "10-2019", "11-2019", "12-2019"],
             1661.97, 11),
            ("Rent", ["06-2019"], 2000.00, 1)
    )
)
def test_update_transactions_table(bk_category_initialized, category, chosen_months, expected_sum, expected_count):
    """Testing if the All Transactions DataTable ColumnDataSource is being updated correctly."""

    bk_category_initialized.chosen_category = category
    bk_category_initialized.chosen_months = chosen_months
    bk_category_initialized._Category__update_chosen_months_and_category_dataframe()
    bk_category_initialized._Category__update_transactions_table()

    source_data_values = bk_category_initialized.grid_source_dict[bk_category_initialized.g_transactions].data
    actual_count = len(source_data_values[bk_category_initialized.product])
    actual_sum = sum(source_data_values[bk_category_initialized.price])

    assert actual_count == expected_count
    assert isclose(actual_sum, expected_sum, rel_tol=1e-02)
