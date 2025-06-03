""" 
Utilities for representing objects as strings in diagnostic messages

         
"""
from __future__ import annotations

from collections import namedtuple
from collections.abc import Sequence
from functools import lru_cache
import datetime as dt
import textwrap
from typing import (
        Iterable,
        Callable,
        )


@lru_cache(maxsize=4)
def _map_justify(how: str) -> str:
    """
    Map justification keyword to string format specifier.

    Parameters
    ----------
    how : {'left', 'right', 'center'}
        Justification direction.

    Returns
    -------
    str
        Format specifier: '<', '>', or '^'.

    Raises
    ------
    ValueError
        If `how` is not a supported justification method.

    """
    fmt = {'left': '<', 'right': '>', 'center': '^'}
    if how not in fmt:
        raise ValueError(
                f"Invalid how: {how!r}. " 
                "Should be one of 'left', 'right', 'center'")
    return fmt[how]

def justify_values(
        values: Iterable[str],
        how: str) -> tuple[str, ...]:
    """
    Justify values using standard text alignment.

    Parameters
    ----------
    values : Iterable[str]
        Sequence of strings to justify.

    how : {'left', 'right', 'center'}
        Direction of justification.

    Returns
    -------
    tuple[str, ...]
        Aligned strings with uniform width.

    Examples
    --------
    >>> justify_values(['a', 'bbb', 'cc'], how='left')
    ('a  ', 'bbb', 'cc ')

    >>> justify_values(['a', 'bbb', 'cc'], how='right')
    ('  a', 'bbb', ' cc')

    >>> justify_values(['a', 'bbb', 'cc'], how='center')
    (' a ', 'bbb', 'cc ')
    """
    width = max(len(v) for v in values)
    fmt = _map_justify(how)
    return tuple(f'{v:{fmt}{width}}' for v in values)

def align_by_char(
        values: Iterable[str],
        char: str,
        how: str = 'left') -> tuple[str, ...]:
    """
    Align strings on the first occurrence of a given character.

    Parameters
    ----------
    values : Iterable[str]
        Sequence of strings.

    char : str
        Character to align by.

    how : {'left', 'right', 'center'}, default = 'left'
        Determines how to align content around the character:
        - 'left' aligns the left part and pads the right.
        - 'right' aligns the right part and pads the left.
        - 'center' centers the character.

    Returns
    -------
    tuple[str, ...]
        Strings aligned so that the alignment character lines up.

    Examples
    --------
    >>> align_by_char(['abc:def', 'a:xxx', 'long'], char=':', how='left')
    (' abc:def', '   a:xxx', '   long  ')

    >>> align_by_char(['abc:def', 'a:xxx', 'long'], char=':', how='right')
    ('abc:def ', '  a:xxx ', '    long')

    >>> align_by_char(['abc:def', 'a:xxx', 'long'], char=':', how='center')
    (' abc:def ', '  a:xxx ', '   long   ')
    """
    values = tuple(values)
    splits = []
    for v in values:
        if char in v:
            l, r = v.split(char, 1)
        else:
            l, r = v, ''
        splits.append((l, r))

    left_width = max(len(l) for l, _ in splits)
    right_width = max(len(r) for _, r in splits)

    result = []
    for l, r in splits:
        if how == 'left':
            result.append(f"{l.rjust(left_width)}{char}{r.ljust(right_width)}")
        elif how == 'right':
            result.append(f"{l.rjust(left_width)}{char}{r.ljust(right_width)}".rjust(left_width + right_width + 1))
        elif how == 'center':
            total_width = left_width + right_width + 1
            content = f"{l.rjust(left_width)}{char}{r.ljust(right_width)}"
            result.append(content.center(total_width))
        else:
            raise ValueError(f"Invalid how: {how!r}")
    return tuple(result)

def align(
        tups: Iterable[str | tuple[str, ...]], 
        min_width: int = 0,
        sep: str = ' ',
        how: str | Sequence[str] = 'left',
        char: str | Sequence[str] | None = None,
        strip: bool = True) -> str:
    """
    Align a sequence of string tuples into a formatted text table.

    Each element of `tups` can be a string or a tuple of strings. Shorter
    tuples are padded with empty strings to match the widest row. Strings are
    treated as single-element rows.

    Parameters
    ----------
    tups : Iterable[str | tuple[str, ...]]
        Sequence of rows to align. Each row may be a string or tuple of strings.

    min_width : int, default = 0
        Minimum width for each column.

    sep : str, default = ' '
        Separator to join columns.

    how : str or Sequence[str], default = 'left'
        Justification for each column ('left', 'right', 'center').

    char : str or Sequence[str], optional
        Character to align within each column (e.g. '.', ':').

    strip : bool, default = True
        Whether to strip whitespace from input values.

    Returns
    -------
    str
        Aligned string with one row per line.

    Examples
    --------
    >>> align([('a', '1.2'), ('bb', '22.22')])
    'a  1.2  \\nbb 22.22'

    >>> align(['x', 'yy', 'zzz'], how='right')
    '  x\\n yy\\nzzz'

    >>> align([('a', '1.2'), ('bb', '22.22')], char='.')
    'a  1.2 \\nbb 22.22'

    >>> align([('abc:def',), ('a:xxx',), ('long',)], char=':', how='left')
    ' abc:def\\n   a:xxx\\n   long  '

    >>> align([('abc:def',), ('a:xxx',), ('long',)], char=':', how='right')
    'abc:def \\n  a:xxx \\n    long'
    """

    # Normalize input rows
    rows = []
    ncols = 0
    for row in tups:
        cells = (row,) if isinstance(row, str) else row
        if strip:
            cells = tuple(c.strip() for c in cells)
        else:
            cells = tuple(cells)
        rows.append(cells)
        ncols = max(ncols, len(cells))

    # Normalize per-column alignment rules
    def resolve(rule, default):
        if isinstance(rule, str) or rule is None:
            return [rule] * ncols
        if isinstance(rule, Sequence):
            return list(rule) + [default] * (ncols - len(rule))
        raise TypeError(f"Expected string or sequence, got {type(rule)}")

    hows = resolve(how, 'left')
    chars = resolve(char, None)

    # Pad rows and transpose to columns
    padded = [row + ('',) * (ncols - len(row)) for row in rows]
    columns = list(zip(*padded))

    # Align each column
    aligned_cols = []
    for col, h, c in zip(columns, hows, chars):
        col_values = col
        if min_width:
            width = max(min_width, max(len(v) for v in col_values))
            col_values = tuple(f'{v:<{width}}' for v in col_values)
        if h is not None:
            col_values = justify_values(col_values, h)
        if c is not None:
            col_values = align_by_char(col_values, char=c, how=h or 'left')
        aligned_cols.append(col_values)

    # Transpose back to rows
    final_rows = zip(*aligned_cols)
    return '\n'.join(sep.join(row) for row in final_rows)

def get_type_name(typ: type) -> str:
    """
    Get the name of a type object.

    Parameters
    ----------
    typ : type
        A type object.

    Returns
    -------
    str
        The name of the type (e.g., "int", "list").

    Examples
    --------
    >>> get_type_name(int)
    'int'
    >>> get_type_name(type(None))
    'NoneType'
    """
    return typ.__name__ if hasattr(typ, "__name__") else str(typ)

def fmt_type(typ: type, quotes: str = "'") -> str:
    """
    Format a type object as a quoted string.

    Parameters
    ----------
    typ : type
        The type to format.
    quotes : str, default="'"
        The character(s) to surround the type name.

    Returns
    -------
    str
        A quoted string with the type name.

    Examples
    --------
    >>> fmt_type(int)
    "'int'"
    >>> fmt_type(dict, quotes='"')
    '"dict"'
    """
    return f"{quotes}{get_type_name(typ)}{quotes}"

def fmt_name(name: str, quotes: str = '`') -> str:
    """
    Format a name string with quote characters.

    Parameters
    ----------
    name : str
        The name to format.
    quotes : str, default='`'
        The character(s) to surround the name.

    Returns
    -------
    str
        A quoted string with the name.

    Examples
    --------
    >>> fmt_name("x")
    '`x`'
    >>> fmt_name("value", quotes='"')
    '"value"'
    """
    return f"{quotes}{name}{quotes}"

def join_names(
        names: str | Iterable[str],
        conjunction: str = "and",
        formatter: Callable[[str], str] | None = None,
        ) -> str:
    """
    Join a sequence of names into a human-readable string with a 
    conjunction.

    If `formatter` is provided, each name is passed through it before
    formatting.

    Uses the Oxford comma when joining 3 or more items.

    Parameters
    ----------
    names: str | Iterable[str]
        A sequence of names to join.

    conjunction: str, default 'and' 
        The word to use before the final item (e.g., "and", "or").
    
    formatter: Callable[[str], str] | None)
        Optional function to format each name.

    Returns
    -------
    str: 
        A formatted string of the names joined with the specified 
        conjunction.

    Examples
    --------
    >>> join_names([])
    ''
    >>> join_names(['x'])
    'x'
    >>> join_names(['x', 'y'])
    'x and y'
    >>> join_names(['x', 'y'], conjunction='or')
    'x or y'
    >>> join_names(['x', 'y', 'z'])
    'x, y, and z'
    >>> join_names(['x', 'y', 'z'], conjunction='or')
    'x, y, or z'
    >>> join_names(['x', 'y', 'z'], formatter=str.upper)
    'X, Y, and Z'
    """
    if isinstance(names, str):
        names = [names]
    formatted = [formatter(x) if formatter else x for x in names]
    conjunction = conjunction.strip()

    if not formatted:
        return ""
    if len(formatted) == 1:
        return formatted[0]
    if len(formatted) == 2:
        return f"{formatted[0]} {conjunction} {formatted[1]}"
    return ", ".join(formatted[:-1]) + f", {conjunction} {formatted[-1]}"

def fmt_str(
        s: str,
        width: int | None = None,
        indent: str = "",
        dedent: bool = False,
        max_lines: int | None = None,
        placeholder: str = " [...]",
        ) -> str:
    """
    Format a string with optional dedenting, wrapping, indentation, and line limit.

    Parameters
    ----------
    s : str
        The input string to format.
    width : int, optional
        Maximum line width. If None, no wrapping is applied.
    indent : str, default=""
        A string to prefix each line with (e.g., "  ").
    dedent : bool, default=False
        If True, use `textwrap.dedent` to remove common leading whitespace.
    max_lines : int, optional
        If provided, limits the number of output lines.
    placeholder : str, default=" [...]"
        Suffix to append if the text is truncated due to max_lines.

    Returns
    -------
    str
        A formatted, potentially wrapped and indented string.

    Examples
    --------
    >>> fmt_str("This is a long sentence that should wrap.", width=10)
    'This is a\\nlong\\nsentence\\nthat\\nshould\\nwrap.'
    >>> fmt_str("  indented", dedent=True)
    'indented'
    >>> fmt_str("a b c d e f g", width=5, max_lines=2)
    'a b\\nc d [...]'
    """
    text = textwrap.dedent(s) if dedent else s

    if width is None:
        return indent + text.replace("\n", "\n" + indent)

    wrapper = textwrap.TextWrapper(
        width=width,
        initial_indent=indent,
        subsequent_indent=indent,
        max_lines=max_lines,
        placeholder=placeholder,
    )

    return wrapper.fill(text)

def fmt_value(
        value: object,
        none_as_empty: bool = False,
        representer: Callable[[object], str] = repr,
        **kargs) -> str:
    """
    Format an object as a string for display in messages.

    Parameters
    ----------
    value : object
        The object to format.

    none_as_empty : bool, default=False

        If True, represent `None` as an empty string. Otherwise, return
        "None".

    representer : Callable[[object], str], default=repr
        Function used to convert the object to a string.

    **kargs
        Additional keyword arguments passed to `fmt_str`, such as `width`,
        `indent`, `dedent`, `max_lines`, and `placeholder`.

    Returns
    -------
    str
        A formatted string representation of the value.

    Examples
    --------
    >>> fmt_value(None)
    ''
    >>> fmt_value(None, none_as_empty=False)
    'None'
    >>> fmt_value([1, 2, 3], representer=str)
    '[1, 2, 3]'
    >>> fmt_value("abc def ghi", width=5)
    'abc\\ndef\\nghi'
    >>> fmt_value("a" * 100, max_lines=1, width=10)
    'aaaaaaaaaa [...]'
    """
    if value is None:
        return "" if none_as_empty else "None"
    out = representer(value)
    return fmt_str(out, **kargs) if len(kargs) > 0 else out



def tdelta_to_ntup(elapsed: dt.timedelta) -> namedtuple:
    """
    Convert a timedelta into a named tuple of time components.

    Parameters
    ----------
    elapsed : datetime.timedelta
        Duration to convert.

    Returns
    -------
    Elapsed
        A named tuple with fields: days, hours, mins, secs, ms.
    """
    Elapsed = namedtuple('Elapsed', ['days', 'hours', 'mins', 'secs', 'ms'])
    total_secs = int(elapsed.total_seconds())
    days, rem = divmod(total_secs, 86400)
    hours, rem = divmod(rem, 3600)
    mins, secs = divmod(rem, 60)
    ms = elapsed.microseconds  # keep as microseconds for now
    return Elapsed(days, hours, mins, secs, ms)


def fmt_elapsed(elapsed: dt.timedelta) -> str:
    """
    Format a timedelta as a human-readable string.

    Parameters
    ----------
    elapsed : datetime.timedelta
        Duration to format.

    Returns
    -------
    str
        A string like "2 hours, 3 mins, 45.123456 secs".
    """
    ntup = tdelta_to_ntup(elapsed)
    parts = []

    for unit in ['days', 'hours', 'mins']:
        val = getattr(ntup, unit)
        if parts or val > 0:
            parts.append(f"{val} {unit}")

    # Format seconds (include microseconds as fraction)
    secs_total = ntup.secs + ntup.ms / 1_000_000
    secs_str = f"{secs_total:.6f}" if secs_total < 60 else f"{secs_total:.2f}"
    parts.append(f"{secs_str} secs")

    return ', '.join(parts)

def fmt_now() -> str:
    """
    String representation of current time
    """
    return dt.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')


