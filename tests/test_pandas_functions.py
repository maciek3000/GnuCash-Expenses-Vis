from flask_app.bkapp.pandas_functions import unique_values_from_column

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
