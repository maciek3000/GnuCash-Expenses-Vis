from flask_app.bkapp.pandas_functions import unique_values_from_column, create_combinations_of_sep_values

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
    """Testing extracting unique values from column from a passed DataFrame."""

    result = unique_values_from_column(df, col_name)
    assert result == expected_result

@pytest.mark.parametrize(
    ("list_of_values", "expected_result", "sep"),
    (
            (["A:B:C:D", "One:Two"], ["A", "A:B", "A:B:C", "A:B:C:D", "One", "One:Two"], ":"),
            (["One:Two:Three:Five", "One:Two:Three:Four"],
             ["One", "One:Two", "One:Two:Three", "One:Two:Three:Five", "One:Two:Three:Four"],
             ":"),
            (["A_B:C_D"], ["A", "A_B:C", "A_B:C_D"], "_"),
            (["A", "B", "C"], ["A", "B", "C"], None)
    )
)
def test_create_combinations_of_sep_values(list_of_values, expected_result, sep):
    """Testing creating combinations from lists with String with separators."""
    actual_result = create_combinations_of_sep_values(list_of_values, sep)
    assert actual_result == expected_result
