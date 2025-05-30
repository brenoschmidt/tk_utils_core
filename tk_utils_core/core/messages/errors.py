""" 
Error messages

         
"""
from __future__ import annotations

from typing import Iterable, Any

from .formatters import (
    get_type_name,
    join_names,
    fmt_name,
    fmt_type,
    fmt_str,
    fmt_value,
    )


def fmt_valid_types(types: type | Iterable[type], **kargs) -> str:
    """
    Format a single type or a sequence of types into a readable string.

    Converts each type to its name and joins them using commas and "or",
    suitable for use in validation messages.

    Parameters
    ----------
    types : type or Iterable[type]
        A single type or a collection of types to be formatted.

    **kargs
        Additional keyword arguments passed to `fmt_str`.

    Returns
    -------
    str

        A string listing the types, joined with "or" as the final conjunction.

    Examples
    --------
    >>> fmt_valid_types(int)
    'int'
    >>> fmt_valid_types((str, int))
    'str or int'
    >>> fmt_valid_types((int, float, str))
    'int, float, or str'
    """
    if isinstance(types, type):
        return fmt_type(types)
    out = join_names((fmt_type(t) for t in types), conjunction="or")
    return fmt_str(out, **kargs)


def fmt_valid_values(values: Iterable[Any], **kargs) -> str:
    """
    Format a set of valid values into a readable string.

    Ensures single strings are treated as atomic values, not iterables.

    Parameters
    ----------
    values : Iterable[Any]
        A sequence of valid values to format.

    **kargs
        Additional keyword arguments passed to `fmt_str`.

    Returns
    -------
    str
        A formatted string of the values joined with "or".

    Examples
    --------
    >>> fmt_valid_values(['yes', 'no'])
    "'yes' or 'no'"
    >>> fmt_valid_values([1, 2, 3])
    '1, 2, or 3'
    """
    if isinstance(values, str):
        values = [values]
    out = join_names((fmt_value(x) for x in values), conjunction="or")
    return fmt_str(out, **kargs)


def type_err_msg(
        name: str,
        typ: type,
        valid_types: type | Iterable[type],
        value: Any | None = None,
        **kargs
        ) -> str:
    """
    Format an error message for an invalid type.

    Parameters
    ----------
    name : str
        The name of the variable or parameter.
    typ : type
        The actual type received.
    valid_types : type or Iterable[type]
        The expected type(s).
    value : object, optional
        The actual value, included for debugging.
    **kargs
        Additional formatting options passed to `fmt_str`.

    Returns
    -------
    str
        A formatted error message.

    Examples
    --------
    >>> type_err_msg('x', list, (str, int))
    "Invalid type for `x`: Expecting 'str' or 'int', got 'list'"
    """
    _name = fmt_name(name)
    _valid_types = fmt_valid_types(valid_types)
    _typ = fmt_type(typ)
    msg = f"Invalid type for {_name}: Expecting {_valid_types}, got {_typ}"
    if value is not None:
        _value = fmt_value(value)
        msg += f" (value: {_value})"
    return fmt_str(msg, **kargs)


def value_err_msg(
        name: str,
        value: Any,
        valid_values: Iterable[Any],
        **kargs
        ) -> str:
    """
    Format an error message for an invalid value.

    Parameters
    ----------
    name : str
        The name of the variable or parameter.
    value : object
        The value that caused the error.
    valid_values : Iterable[Any]
        The set of valid values.
    **kargs
        Additional formatting options passed to `fmt_str`.

    Returns
    -------
    str
        A formatted error message.

    Examples
    --------
    >>> value_err_msg('mode', 'fast', ['slow', 'medium'])
    "Invalid value for `mode`: `fast` Expecting 'slow' or 'medium'"
    """
    _name = fmt_name(name)
    _value = fmt_name(value)
    _valid_values = fmt_valid_values(valid_values)
    msg = f"Invalid value for {_name}: {_value} Expecting {_valid_values}"
    return fmt_str(msg, **kargs)



