import pytest
import numpy as np
import pandas as pd
from math import isclose

from bokeh.models.widgets import Div, RadioGroup
from bokeh.models import Plot, ColumnDataSource


def test_initialize_grid_elements(bk_trends):
    """Testing if initializing grid elements of bk_trends grid is being done correctly."""

    grid_elems = [
        (bk_trends.g_histogram, Plot),
        (bk_trends.g_daily_statistics, Div),
        (bk_trends.g_daily_title, Div),
        (bk_trends.g_heatmap_title, Div),
        (bk_trends.g_heatmap, Plot),
        (bk_trends.g_line_plot, Plot),
        (bk_trends.g_heatmap_buttons, RadioGroup),
        (bk_trends.g_monthly_statistics, Div),
        (bk_trends.g_monthly_title, Div),
    ]

    source_elems = [
        bk_trends.g_histogram,
        bk_trends.g_line_plot,
        bk_trends.g_heatmap
    ]

    bk_trends.initialize_gridplot(0)

    assert len(grid_elems) == len(bk_trends.grid_elem_dict.keys())
    assert len(source_elems) == len(bk_trends.grid_source_dict.keys())

    # checking Grid Elements (e.g. Divs, Plot, etc)
    for name, single_type in grid_elems:
        assert name in bk_trends.grid_elem_dict
        assert isinstance(bk_trends.grid_elem_dict[name], single_type)

    # checking Grid ColumnDataSources connected with Elements
    for source_elem in source_elems:
        assert source_elem in bk_trends.grid_source_dict
        assert isinstance(bk_trends.grid_source_dict[source_elem], ColumnDataSource)


@pytest.mark.parametrize(
    ("indices", "expected_result"),
    (
            ([0, 1, 4], ["2019-01", "2019-02", "2019-05"]),
            ([0], ["2019-01"]),
            ([], ["2019-01", "2019-02", "2019-03", "2019-04", "2019-05", "2019-06",
                  "2019-07", "2019-08", "2019-09", "2019-10", "2019-11", "2019-12"]),
            ([1, 6, 3], ["2019-02", "2019-07", "2019-04"])
    )
)
def test_update_chosen_months(bk_trends_initialized, indices, expected_result):
    """Testing if __update_chosen_months function correctly assigns months corresponding to passed indices."""

    bk_trends_initialized._Trends__update_chosen_months(indices)

    assert bk_trends_initialized.chosen_months == expected_result


@pytest.mark.parametrize(
    ("chosen_months", "expected_sum"),
    (
            (["2019-03", "2019-04", "2019-05"], 14223.34),
            (["2019-05", "2019-01"], 9980.17),
            ([], 55653.90)
    )
)
def test_update_current_expense_df(bk_trends_initialized, chosen_months, expected_sum):
    """Testing if updating current_expense_df DataFrame based on .chosen_months attribute is done correctly."""

    if len(chosen_months) == 0:
        chosen_months = bk_trends_initialized.months

    bk_trends_initialized.chosen_months = chosen_months
    bk_trends_initialized._Trends__update_current_expense_df()

    actual_months = bk_trends_initialized.current_expense_df[bk_trends_initialized.monthyear].unique()
    actual_sum = bk_trends_initialized.current_expense_df[bk_trends_initialized.price].sum()

    assert set(actual_months) == set(chosen_months)
    assert isclose(actual_sum, expected_sum, rel_tol=1e-06)


@pytest.mark.parametrize(
    ("chosen_months", "dict_of_expected_values"),
    (
            (["2019-01", "2019-02", "2019-03"], {
                "mean": 4760.10,
                "median": 4613.90,
                "min": 4503.46,
                "max": 5162.93,
                "std": 353.21
            }),
            ([], {
                "mean": 4637.82,
                "median": 4665.99,
                "min": 3876.35,
                "max": 5339.19,
                "std": 433.47
            })
    )
)
def test__update_monthly_info(bk_trends_initialized, chosen_months, dict_of_expected_values):
    """Testing if __update_monthly_info function correctly calculates values and inserts them into HTML template."""

    expected_text = bk_trends_initialized.stats_template.format(**dict_of_expected_values)

    if len(chosen_months) == 0:
        chosen_months = bk_trends_initialized.months

    bk_trends_initialized.chosen_months = chosen_months
    bk_trends_initialized._Trends__update_current_expense_df()
    bk_trends_initialized._Trends__update_monthly_info()

    actual_text = bk_trends_initialized.grid_elem_dict[bk_trends_initialized.g_monthly_statistics].text

    assert actual_text == expected_text


@pytest.mark.parametrize(
    ("chosen_months", "dict_of_expected_values"),
    (
            (["2019-01", "2019-02", "2019-03"], {
                "mean": 158.67,
                "median": 53.75,
                "min": 6.88,
                "max": 2224.1,
                "std": 381.3
            }),
            ([], {
                "mean": 152.48,
                "median": 57.52,
                "min": 5.17,
                "max": 2430.76,
                "std": 381.21
            })
    )
)
def test__update_daily_info(bk_trends_initialized, chosen_months, dict_of_expected_values):
    """Testing if __update_daily_info function correctly calculates values and inserts them into HTML template."""

    expected_text = bk_trends_initialized.stats_template.format(**dict_of_expected_values)

    if len(chosen_months) == 0:
        chosen_months = bk_trends_initialized.months

    bk_trends_initialized.chosen_months = chosen_months
    bk_trends_initialized._Trends__update_current_expense_df()
    bk_trends_initialized._Trends__update_daily_info()

    actual_text = bk_trends_initialized.grid_elem_dict[bk_trends_initialized.g_daily_statistics].text

    assert actual_text == expected_text


def test_update_line_plot(bk_trends_initialized):
    """Testing if __update_line_plot correctly calculates new source values and changes y_range accordingly."""

    expected_values = [5162.93, 4503.46, 4613.9, 4792.20, 4817.24, 3876.35,
                       4277.18, 4524.62, 5339.19, 4718.09, 4996.53, 4032.21]

    expected_min = 0
    expected_high = 5392.58

    bk_trends_initialized._Trends__update_line_plot()

    source = bk_trends_initialized.grid_source_dict[bk_trends_initialized.g_line_plot]
    fig = bk_trends_initialized.grid_elem_dict[bk_trends_initialized.g_line_plot]

    actual_values = source.data["y"]
    actual_min = fig.y_range.start
    actual_high = fig.y_range.end

    assert isclose(actual_min, expected_min, rel_tol=1e-06)
    assert isclose(actual_high, expected_high, rel_tol=1e-06)

    assert len(actual_values) == len(expected_values)

    for i in range(len(actual_values)):
        assert isclose(actual_values[i], expected_values[i], rel_tol=1e-06)


@pytest.mark.parametrize(
    ("chosen_months",),
    (
            (["2019-01", "2019-02", "2019-03"],),
            ([],)

    )
)
def test_update_histogram(bk_trends_initialized, chosen_months):
    """Testing if __update_histogram correctly calculates values for histogram given .chosen_months attribute
        and updates them in corresponding CDS."""

    if len(chosen_months) == 0:
        chosen_months = bk_trends_initialized.months

    bk_trends_initialized.chosen_months = chosen_months
    bk_trends_initialized._Trends__update_current_expense_df()

    # values are grouped by date
    grouped_df = bk_trends_initialized.current_expense_df.groupby(by=[bk_trends_initialized.date]).sum()
    expected_hist, expected_edges = np.histogram(grouped_df[bk_trends_initialized.price], density=True, bins=50)

    bk_trends_initialized._Trends__update_histogram()
    source = bk_trends_initialized.grid_source_dict[bk_trends_initialized.g_histogram]

    actual_hist = source.data["hist"].tolist()
    actual_bottom_edges = source.data["bottom_edges"].tolist()
    actual_top_edges = source.data["top_edges"].tolist()

    assert actual_hist == expected_hist.tolist()
    assert actual_bottom_edges == expected_edges[1:].tolist()
    assert actual_top_edges == expected_edges[:-1].tolist()


@pytest.mark.parametrize(
    ("columns", "expected_results"),
    (
            (["Category", "MonthYear", "Price", "Product", "Date", "Currency", "Shop"], []),
            (["Category", "MonthYear", "Price", "Product", "week", "Currency", "Shop"], [
                "year", "year_str", "month", "month_str", "weekday", "weekday_str",
                "myWphgqp", "week_str", "date_str", "count", "monthyear_str"
            ]),
            (["Category", "year", "month", "weekday", "weekday_str", "Currency", "Shop"], [
                "myWphgqp", "year_str", "uQzFYYNG", "month_str", "JUbokwek", "xqDbSzlh",
                "week", "week_str", "date_str", "count", "monthyear_str"
            ]),
            (["Category", "month", "uQzFYYNG", "weekday", "JUbokwek", "Currency", "Shop"], [
                "year", "year_str", "myWphgqp", "month_str", "xqDbSzlh", "weekday_str",
                "week", "week_str", "date_str", "count", "monthyear_str"
            ])
    )
)
def test___create_new_column_names(bk_trends_initialized, columns, expected_results):
    """Testing if __create_new_column_names correctly creates new column names if some of the values
        are already taken."""

    seed = 456
    n = 8
    key_values = ["year", "year_str", "month", "month_str", "weekday",
                  "weekday_str", "week", "week_str", "date_str", "count", "monthyear_str"]

    if len(expected_results) == 0:
        expected_results = key_values

    expected_dict = dict(zip(key_values, expected_results))
    actual_dict = bk_trends_initialized._Trends__create_new_column_names(columns, n, seed)

    assert len(actual_dict) != 0
    assert len(actual_dict) == len(expected_dict)
    assert actual_dict == expected_dict


def test_aggregated_expense_df(bk_trends_initialized):
    """Testing if __aggregated_expense_df function makes correct transformations to the expense DataFrame."""

    columns = [
        bk_trends_initialized.category,
        bk_trends_initialized.monthyear,
        bk_trends_initialized.price,
        bk_trends_initialized.product,
        bk_trends_initialized.date,
        bk_trends_initialized.currency,
        bk_trends_initialized.shop
    ]

    chosen_months = ["2019-01", "2019-02"]

    df = bk_trends_initialized.original_expense_df
    df = df[df[bk_trends_initialized.monthyear].isin(chosen_months)]

    bk_trends_initialized.heatmap_df_column_dict = bk_trends_initialized._Trends__create_new_column_names(columns)

    actual_df = bk_trends_initialized._Trends__aggregated_expense_df(df)

    assert len(actual_df) == 59
    assert set(actual_df.columns) == {bk_trends_initialized.date, bk_trends_initialized.price, "year", "month",
                                      "weekday", "year_str", "month_str", "weekday_str", "date_str", "week", "week_str",
                                      "count", "monthyear_str"}

    assert set(actual_df["year"]) == {2019}
    assert set(actual_df["year_str"]) == {"2019"}

    assert set(actual_df["month"]) == {1, 2}
    assert set(actual_df["month_str"]) == {"Jan", "Feb"}

    assert set(actual_df["monthyear_str"]) == {"2019-01", "2019-02"}

    assert set(actual_df["weekday"]) == {0, 1, 2, 3, 4, 5, 6}
    assert set(actual_df["weekday_str"]) == {"0", "1", "2", "3", "4", "5", "6"}

    expected_date_range = pd.date_range(start="1/1/2019", end="28/2/2019", freq="d")

    assert actual_df[bk_trends_initialized.date].tolist() == expected_date_range.tolist()
    assert actual_df["date_str"].tolist() == expected_date_range.strftime("%d-%b-%Y").tolist()

    # first Monday is 07-Jan-2019 and last Sunday is 29-Dec-2019
    expected_week_numbers = ([[-1] * 6]) + [[x] * 7 for x in range(7)] + [[7] * 4]
    expected_week_numbers = [x for sublist in expected_week_numbers for x in sublist]

    assert actual_df["week"].tolist() == expected_week_numbers
    assert actual_df["week_str"].tolist() == list(map(lambda x: "{x:04d}".format(x=x), expected_week_numbers))


def test_create_first_week_to_month_dict_no_time_gap(bk_trends_initialized):
    """Testing if __create_first_week_to_month_dict function creates correct mapping between week numbers and
        corresponding Month strings, when there is no gap between months."""

    expected_dict = {
        "0000": "(2019) Feb",
        "0004": "Mar",
        "0008": "Apr",
        "0013": "May",
        "0017": "Jun",
        "0021": "Jul",
        "0026": "Aug",
        "0030": "Sep",
        "0035": "Oct",
        "0039": "Nov",
        "0043": "Dec",
        "0048": "(2020) Jan"
    }

    columns = [
        bk_trends_initialized.category,
        bk_trends_initialized.monthyear,
        bk_trends_initialized.price,
        bk_trends_initialized.product,
        bk_trends_initialized.date,
        bk_trends_initialized.currency,
        bk_trends_initialized.shop
    ]

    df = bk_trends_initialized.original_expense_df

    # masking done to change January 2019 to January 2020
    df[bk_trends_initialized.date] = df[bk_trends_initialized.date].mask(
        df[bk_trends_initialized.date].dt.month == 1,
        df[bk_trends_initialized.date] + pd.DateOffset(year=2020)
    )

    bk_trends_initialized.heatmap_df_column_dict = bk_trends_initialized._Trends__create_new_column_names(columns)
    agg = bk_trends_initialized._Trends__aggregated_expense_df(df)

    actual_dict = bk_trends_initialized._Trends__create_first_week_to_month_dict(agg)
    assert actual_dict == expected_dict


def test_create_first_week_to_month_dict_time_gap(bk_trends_initialized):
    """Testing if __create_first_week_to_month_dict function creates correct mapping between week numbers and
    corresponding Month strings, when there is a gap between months."""

    expected_dict = {
        "0000": "(2019) Feb",
        "0004": "Mar",
        "0008": "Apr",
        "0013": "May",
        "0017": "Jun",
        "0021": "Jul",
        "0026": "Aug",
        "0030": "Sep",
        "0035": "Oct",
        "0039": "Nov",
        "0043": "Dec",
        "0096": "(2020) Dec"
    }

    columns = [
        bk_trends_initialized.category,
        bk_trends_initialized.monthyear,
        bk_trends_initialized.price,
        bk_trends_initialized.product,
        bk_trends_initialized.date,
        bk_trends_initialized.currency,
        bk_trends_initialized.shop
    ]

    df = bk_trends_initialized.original_expense_df

    # masking is done to change data for January 2019 into December 2020
    df[bk_trends_initialized.date] = df[bk_trends_initialized.date].mask(
        df[bk_trends_initialized.date].dt.month == 1,
        df[bk_trends_initialized.date] + pd.DateOffset(year=2020, month=12)
    )

    bk_trends_initialized.heatmap_df_column_dict = bk_trends_initialized._Trends__create_new_column_names(columns)
    agg = bk_trends_initialized._Trends__aggregated_expense_df(df)

    actual_dict = bk_trends_initialized._Trends__create_first_week_to_month_dict(agg)
    assert actual_dict == expected_dict


def test_update_heatmap(bk_trends_initialized):
    """Testing if __update_heatmap function correclty updates corresponding CDS and figure range for heatmap."""

    expected_date = pd.date_range(start="1/1/2019", end="31/12/2019", freq="d").strftime("%d-%b-%Y").tolist()
    expected_week = ["{x:04d}".format(x=x) for x in range(-1, 52)]
    expected_weekday = {"0", "1", "2", "3", "4", "5", "6"}
    selected_index = 0

    bk_trends_initialized._Trends__update_heatmap(selected_index)

    data = bk_trends_initialized.grid_source_dict[bk_trends_initialized.g_heatmap].data
    fig = bk_trends_initialized.grid_elem_dict[bk_trends_initialized.g_heatmap]

    assert data["date"].tolist() == expected_date
    assert set(data["week"]) == set(expected_week)
    assert set(data["weekday"]) == expected_weekday

    actual_range = fig.x_range.factors

    assert actual_range == expected_week


@pytest.mark.parametrize(
    ("selected_index", "expected_series", "minimum", "maximum"),
    (
            (0, "price", 5.17, 1296.105),
            (1, "count", 2, 12)
    )
)
def test_update_heatmap_values(bk_trends_initialized, selected_index, expected_series, minimum, maximum):
    """Testing if __update_heatmap_values correctly assings "value" column in heatmap CDS and calculates min and max
        attributes of bk_trends.heatmap_color_mapper ColorMapper depending on passed selected_index."""

    columns = [
        bk_trends_initialized.category,
        bk_trends_initialized.monthyear,
        bk_trends_initialized.price,
        bk_trends_initialized.product,
        bk_trends_initialized.date,
        bk_trends_initialized.currency,
        bk_trends_initialized.shop
    ]

    df = bk_trends_initialized.original_expense_df

    bk_trends_initialized.heatmap_df_column_dict = bk_trends_initialized._Trends__create_new_column_names(columns)
    agg = bk_trends_initialized._Trends__aggregated_expense_df(df)

    source = bk_trends_initialized.grid_source_dict[bk_trends_initialized.g_heatmap]

    source.data["price"] = agg[bk_trends_initialized.price]
    source.data["count"] = agg["count"]

    bk_trends_initialized._Trends__update_heatmap_values(selected_index)

    cmap = bk_trends_initialized.heatmap_color_mapper

    assert source.data["value"].tolist() == source.data[expected_series].tolist()
    assert isclose(cmap.low, minimum, rel_tol=1e-06)
    assert isclose(cmap.high, maximum, rel_tol=1e-06)


def test_update_heatmap_values_error(bk_trends_initialized):
    """Testing if __update_heatmap_values raises error when incompatible selected_index is passed."""

    columns = [
        bk_trends_initialized.category,
        bk_trends_initialized.monthyear,
        bk_trends_initialized.price,
        bk_trends_initialized.product,
        bk_trends_initialized.date,
        bk_trends_initialized.currency,
        bk_trends_initialized.shop
    ]

    df = bk_trends_initialized.original_expense_df

    bk_trends_initialized.heatmap_df_column_dict = bk_trends_initialized._Trends__create_new_column_names(columns)
    agg = bk_trends_initialized._Trends__aggregated_expense_df(df)

    source = bk_trends_initialized.grid_source_dict[bk_trends_initialized.g_heatmap]

    source.data["price"] = agg[bk_trends_initialized.price]
    source.data["count"] = agg["count"]

    with pytest.raises(Exception):
        bk_trends_initialized._Trends__update_heatmap_values(2)

