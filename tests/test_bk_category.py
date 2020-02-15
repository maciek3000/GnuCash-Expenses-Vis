from flask_app.bkapp.bk_category import get_aggregated_dataframe_sum, get_unique_values_from_column
import pytest
import pandas as pd
import numpy as np
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
    result = get_unique_values_from_column(df, col_name)
    assert result == expected_result


@pytest.mark.parametrize(("df", "list_of_cols", "output"),
                         ((pd.DataFrame({"a": ["one", "one", "one", "one", "two", "two"],
                                         "b": [1, 2, 3, 4, 5, 6]}),
                           ["a"],
                           pd.DataFrame({"a": ["one", "two"],
                                         "b": [10, 11]})),
                          (pd.DataFrame({"a": ["one", "one", "one", "one", "two", "two"],
                                         "b": ["a", "b", "a", "b", "a", "b"],
                                         "c": [1, 2, 3, 4, 5, 6]}),
                           ["a", "b"],
                           pd.DataFrame({"a": ["one", "one", "two", "two"],
                                         "b": ["a", "b", "a", "b"],
                                         "c": [4, 6, 5, 6]})),
                          ))
def test_get_aggregated_dataframe_sum(df, list_of_cols, output):
    result = get_aggregated_dataframe_sum(df, list_of_cols)
    assert result.equals(output)


@pytest.mark.parametrize(("category", "output"),
                         (("Cat1", [6, 6, 13]),
                          ("Cat2", [9, 17, 52]),
                          ("Cat3", [np.nan, 17, np.nan])))
def test_get_source_data_for_multi_line_plot(bk_category, aggregated_category_df, category, output):
    source_data = bk_category._Category__get_source_data_for_multi_line_plot(aggregated_category_df, category)
    xs = source_data["xs"]
    ys = source_data["ys"]

    for x in xs:
        assert x == ["01-2019", "02-2019", "03-2019"]

    assert ys[0] == [15, 40, 65]
    assert ys[1] == output


@pytest.mark.parametrize(("category", "list_of_values", "output"),
                         (("Cat1", [[10, 15, 20, 25, 30], [1, 2, 3, 4, 5]],
                           {"category": "Cat1", "avg_all": 20, "avg_category": 3, "median_all": 20,
                            "median_category": 3}),
                          ("Cat2", [[12.698, 14.456, 90.378, 67.345, 90.9145], [2.498, 3.087, np.nan, 3.978, 5.6134]],
                           {"category": "Cat2", "avg_all": 55.1583, "avg_category": 3.7941,
                            "median_all": 67.3450, "median_category": 3.5325}),))
def test_get_statistics_data(bk_category, category, list_of_values, output):
    result = bk_category._Category__get_statistics_data(list_of_values, category)

    for key in output:
        assert key in result
        val = result[key]
        if type(val) == str:
            assert val == output[key]
        else:
            assert isclose(val, output[key])
