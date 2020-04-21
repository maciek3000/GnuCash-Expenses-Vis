import numpy as np
from itertools import accumulate


def unique_values_from_column(df, column_name):
    """Returns sorted and unique values from a column from a DataFrame df.

        If there are any NaN values, they are replaced to string "nan".
     """
    return sorted(df[column_name].replace({np.nan: "nan"}).unique().tolist())


def create_combinations_of_sep_values(list_of_values, sep=None):
    new_set = set()

    for val in list_of_values:
        if sep is None:
            new_set.add(val)
        else:
            elem_list = val.split(sep)
            elems = accumulate(elem_list, func=lambda x, y: sep.join([x, y]))
            for item in elems:
                new_set.add(item)

    new_list = list(new_set)
    new_list.sort()
    return new_list