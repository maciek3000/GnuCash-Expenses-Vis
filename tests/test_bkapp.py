import pytest
import pandas as pd


@pytest.mark.parametrize(
    ("index", "expected_column"),
    (
            (0, "Category"),
            (1, "ALL_CATEGORIES"),
            (2, "ALL_CATEGORIES")
    )
)
def test_update_category_choice(bkapp, index, expected_column):
    """Testing if updating .chosen_category_column attribute based on provided index works correctly."""
    bkapp._BokehApp__update_category_choice(index)

    assert bkapp.chosen_category_column == expected_column


@pytest.mark.parametrize(
    ("category_column", "popped_categories"),
    (
            ("Category", ["Bread", "Rent"]),
            ("Category", ["Clothes"]),
            ("ALL_CATEGORIES", ["Expenses:Family:Car:Petrol", "Expenses:Family:Bathroom:Toilet"]),
            ("ALL_CATEGORIES", ["Expenses:Family:Rent"])
    )
)
def test_update_current_expense_dataframe_categories_only_simple_extended(bkapp, category_column, popped_categories,
                                                                          bk_categories_simple, bk_categories_extended):
    """Testing if update_current_expense_dataframe function correctly updates the dataframe.
    Categories only (no months filters), only Simple and Extended type of Category."""

    d_category = {
        "Category": bk_categories_simple,
        "ALL_CATEGORIES": bk_categories_extended
    }

    expected_categories = d_category[category_column]
    expected_categories = [x for x in expected_categories if x not in popped_categories]
    expected_categories.sort()

    # Setting all necessary variables
    bkapp.chosen_category_column = category_column
    bkapp.current_chosen_categories = expected_categories
    if category_column == "Category":
        bkapp.settings.all_categories = bkapp.settings.all_categories_simple
    else:
        bkapp.settings.all_categories = bkapp.settings.all_categories_extended

    # Function call
    bkapp._BokehApp__update_current_expense_dataframe()

    actual_categories = bkapp.current_expense_dataframe[category_column].sort_values().unique().tolist()

    assert actual_categories == expected_categories


@pytest.mark.parametrize(
    ("popped_categories", "expected_popped_categories"),
    (
            (["Expenses:Family:Grocery"], [
                "Expenses:Family:Grocery:Bread",
                "Expenses:Family:Grocery:Chips",
                "Expenses:Family:Grocery:Eggs",
                "Expenses:Family:Grocery:Fruits and Vegetables",
                "Expenses:Family:Grocery:Meat"
            ]),
            (["Expenses:Family:Car", "Expenses:Family:Bathroom"], [
                "Expenses:Family:Bathroom:Toilet",
                "Expenses:Family:Bathroom:Personal - John",
                "Expenses:Family:Bathroom:Personal - Susan",
                "Expenses:Family:Car:Petrol"
            ])
    )
)
def test_update_current_expense_dataframe_categories_only_combinations(
        bkapp, bk_categories_combinations, bk_categories_extended, popped_categories, expected_popped_categories):
    """Testing if update_current_expense_dataframe function correctly updates the dataframe.
    Categories only (no months filters), only Combination type of Category."""

    expected_categories = [x for x in bk_categories_extended if x not in expected_popped_categories]
    expected_categories.sort()

    cats = bk_categories_combinations
    for cat in popped_categories:
        cats.remove(cat)

    # Setting all necessary variables
    bkapp.settings.all_categories = bkapp.settings.all_categories_combinations
    bkapp.chosen_category_column = "ALL_CATEGORIES"
    bkapp.current_chosen_categories = cats

    # Function call
    bkapp._BokehApp__update_current_expense_dataframe()

    actual_categories = bkapp.current_expense_dataframe["ALL_CATEGORIES"].sort_values().unique().tolist()

    assert actual_categories == expected_categories


@pytest.mark.parametrize(
    ("time_tuple", "popped_months",),
    (
            (("2019-03", "2019-11"), ["2019-01", "2019-02", "2019-12"],),
            (("2019-02", "2019-10"), ["2019-01", "2019-11", "2019-12"])
    )
)
def test_update_current_expense_dataframe_month_only(bkapp, bk_months, time_tuple, popped_months):
    """Testing if update_current_expense_dataframe function correctly updates the dataframe.
    Month filters only (no Category)."""

    expected_months = [x for x in bk_months if x not in popped_months]

    chosen_months = pd.to_datetime(pd.date_range(time_tuple[0], time_tuple[1], freq="MS"))

    # Setting all necessary variables
    bkapp.current_chosen_months = chosen_months
    bkapp.chosen_category_column = "ALL_CATEGORIES"
    bkapp.settings.all_categories = bkapp.settings.all_categories_extended
    bkapp.current_chosen_categories = bkapp.settings.all_categories

    # Function Call
    bkapp._BokehApp__update_current_expense_dataframe()

    actual_months = bkapp.current_expense_dataframe[bkapp.monthyear].sort_values().unique().tolist()

    assert actual_months == expected_months


@pytest.mark.parametrize(
    ("chosen_categories", "chosen_months_tuple"),
    (
            (["Expenses:Family:Car:Petrol", "Expenses:Family:Grocery:Bread", "Expenses:John's Expenses:Clothes"],
             ("2019-03", "2019-09")),
            (["Expenses:Family:Bathroom:Personal - John", "Expenses:Family:Grocery:Eggs"],
             ("2019-01", "2019-08")),
    )
)
def test_update_current_expense_dataframe_month_categories(bkapp, chosen_categories, chosen_months_tuple):
    """Testing if update_current_expense_dataframe function correctly updates the dataframe.
    Months and Category Filters combined."""

    date_range = pd.date_range(chosen_months_tuple[0], chosen_months_tuple[1], freq="MS")
    expected_date_range = date_range.strftime("%Y-%m").tolist()

    # Setting all necessary variables
    bkapp.chosen_category_column = "ALL_CATEGORIES"
    bkapp.settings.all_categories = bkapp.settings.all_categories_extended
    bkapp.current_chosen_months = date_range
    bkapp.current_chosen_categories = chosen_categories

    # Function Call
    bkapp._BokehApp__update_current_expense_dataframe()

    actual_categories = bkapp.current_expense_dataframe["ALL_CATEGORIES"].sort_values().unique().tolist()
    actual_monthyear = bkapp.current_expense_dataframe[bkapp.monthyear].sort_values().unique().tolist()

    assert actual_categories == chosen_categories
    assert actual_monthyear == expected_date_range
