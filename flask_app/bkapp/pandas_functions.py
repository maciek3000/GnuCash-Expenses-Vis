import numpy as np


def unique_values_from_column(df, column_name):
    """Returns sorted and unique values from a column from a DataFrame df.

        If there are any NaN values, they are replaced to string "nan".
     """
    return sorted(df[column_name].replace({np.nan: "nan"}).unique().tolist())