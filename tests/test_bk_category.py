from flask_app.bkapp.bk_category import get_aggregated_dataframe_sum, get_unique_values_from_column
import pytest
import pandas as pd
import numpy as np


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
