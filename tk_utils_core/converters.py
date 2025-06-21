""" 
Converters to coerce values from one type to another
         
"""
from __future__ import annotations

import csv
import io

import pandas as pd

from tk_utils_core.core.converters import (
        as_path,
        as_dict,
        as_list,
        as_set,
        bytes2human,
        human2bytes,
        to_namespace,
        )

__all__ = [
        'as_path',
        'as_dict',
        'as_list',
        'as_set',
        'bytes2human',
        'human2bytes',
        'to_namespace',
        'csv_to_df',
        ]



def csv_to_df(
        cnts: str,
        *args,
        strip: bool = True,
        **kargs) -> pd.DataFrame:
    """
    Convert a CSV-formatted string into a pandas DataFrame.

    Parameters
    ----------
    cnts : str
        A string containing CSV-formatted data.

    *args
        Positional arguments passed to `pandas.read_csv`.

    strip : bool, default True
        If True, whitespace around each field is stripped before parsing.

    **kargs
        Keyword arguments passed to `pandas.read_csv`.

    Returns
    -------
    DataFrame
        A DataFrame containing the parsed data.

    Examples
    --------
    Basic usage:

    >>> cnts = '''
    ...     date, ticker, ret
    ...     2020-01-01, AAPL, 0.01
    ...     2020-01-02, AAPL, -0.02
    ... '''
    >>> df = csv_to_df(cnts)
    >>> df.columns.tolist()
    ['date', 'ticker', 'ret']
    >>> len(df)
    2

    With index column:

    >>> df = csv_to_df(cnts, index_col='date')
    >>> df.index.name
    'date'

    Disable field stripping:

    >>> raw = "  a , b \\n 1 , 2 "
    >>> csv_to_df(raw, strip=False).columns.tolist()
    ['  a ', ' b ']
    """
    if strip:
        cnts = cnts.strip()
    reader = csv.reader(io.StringIO(cnts))
    buffer = io.StringIO()
    writer = csv.writer(buffer)

    for row in reader:
        if strip:
            row = [x.strip() for x in row]
        writer.writerow(row)

    buffer.seek(0)
    return pd.read_csv(buffer, *args, **kargs)



