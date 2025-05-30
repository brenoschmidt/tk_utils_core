""" 
Utilities for representing objects as strings in diagnostic messages

         
"""
from __future__ import annotations

import textwrap

from typing import (
        Iterable,
        Callable,
        )


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


