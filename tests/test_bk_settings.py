import pytest
import pandas as pd
from datetime import datetime

from flask_app.bkapp.pandas_functions import create_combinations_of_sep_values


def test_initialize_categories(bk_settings, bk_categories):
    """Testing if Category variables are being initialized correctly."""

    expected_simple_categories = sorted(bk_categories)

    expected_extended_categories = bk_settings.original_extended_categories.sort_values().unique().tolist()
    expected_combination_categories = create_combinations_of_sep_values(
        bk_settings.original_extended_categories, sep=":")

    bk_settings._Settings__initialize_categories()

    assert bk_settings.all_categories_simple == expected_simple_categories
    assert bk_settings.all_categories_extended == expected_extended_categories
    assert bk_settings.all_categories_combinations == expected_combination_categories

    assert bk_settings.all_categories == expected_simple_categories
    assert bk_settings.chosen_categories == expected_simple_categories
    assert bk_settings.chosen_category_type == 0

    assert bk_settings.are_categories_initialized is True


def test_initialize_months(bk_settings):
    """Testing if Month variables are being initialized correctly."""

    expected_months = [datetime(year=2019, month=x, day=1) for x in range(1, 13)]

    bk_settings._Settings__initialize_months()

    assert bk_settings.all_months == expected_months
    assert bk_settings.chosen_months == expected_months

    assert bk_settings.is_month_range_initialized is True


@pytest.mark.parametrize(
    ("index", "category_list_attr",),
    (
            (0, "simple"),
            (1, "extended"),
            (2, "combinations")
    )
)
def test_update_categories_on_category_type_change(bk_settings_initialized, index, category_list_attr):
    """Testing if updating categories on Category Type change (via Radio Button) works correctly."""

    expected_list_of_labels = getattr(bk_settings_initialized, "all_categories_" + category_list_attr)
    expected_list_of_active = list(range(len(expected_list_of_labels)))

    # called to update .checkbox_group
    grid = bk_settings_initialized.category_options()
    bk_settings_initialized._Settings__update_categories_on_category_type_change(index)

    assert bk_settings_initialized.chosen_category_type == index

    assert bk_settings_initialized.all_categories == expected_list_of_labels
    assert bk_settings_initialized.chosen_categories == expected_list_of_labels

    assert bk_settings_initialized.checkbox_group.labels == expected_list_of_labels
    assert bk_settings_initialized.checkbox_group.active == expected_list_of_active


@pytest.mark.parametrize(
    ("indices",),
    (
            ([0, 1, 2, 3],),
            ([0],),
            ([],)
    )
)
def test_update_chosen_categories_on_new(bk_settings_initialized, indices):
    """Testing if updating .chosen_categories attribute works correctly."""
    if len(indices) == 0:
        indices = list(range(len(bk_settings_initialized.all_categories)))
    expected_chosen_categories = [bk_settings_initialized.all_categories[x] for x in indices]

    bk_settings_initialized._Settings__update_chosen_categories_on_new(indices)

    assert bk_settings_initialized.chosen_categories == expected_chosen_categories


@pytest.mark.parametrize(
    ("test_tuple", "expected_tuple", "date_format"),
    (
            ((1546340400000.0, 1552647600000.0), ("2019-01", "2019-03"), "%Y-%m"),
            ((1262322000000.0, 1302901200000.0), ("2010-01-01", "2011-04-15"), "%Y-%m-%d"),
            (
                    ((pd.Timestamp(year=2019, month=12, day=1, hour=12),
                      pd.Timestamp(year=2020, month=2, day=10, hour=15)),
                     ("01-12-19", "10-02-20"),
                     "%d-%m-%y")
            )
    ))
def test_create_timetuple_string_from_timestamp(bk_settings_initialized, test_tuple, expected_tuple, date_format):
    """Testing if creating String tuples (from timestamps) works correctly."""
    actual_tuple = bk_settings_initialized._Settings__create_timetuple_string_from_timestamp(test_tuple, date_format)

    assert actual_tuple == expected_tuple


@pytest.mark.parametrize(
    ("test_tuple", "expected_start", "expected_stop"),
    (
            ((1546340400000.0, 1552647600000.0), "2019-01-01", "2019-03-01"),
            ((1262322000000.0, 1302901200000.0), "2010-01-01", "2011-04-01"),
            ((1293750000000.0, 1464645600000.0), "2010-12-1", "2016-05-01")
    )
)
def test_update_chosen_months(bk_settings_initialized, test_tuple, expected_start, expected_stop):
    """Testing if updating .chosen_month attribute works correctly."""
    expected_range = pd.date_range(expected_start, expected_stop, freq="MS").tolist()

    bk_settings_initialized._Settings__update_chosen_months(test_tuple)
    actual_range = bk_settings_initialized.chosen_months

    assert actual_range == expected_range
