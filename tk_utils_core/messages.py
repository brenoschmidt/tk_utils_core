"""
Utilities for representing objects as strings in diagnostic messages
"""
from __future__ import annotations

from typing import Iterable

from .core.messages.errors import (
        type_err_msg,
        value_err_msg,
    )
from .core.messages.formatters import (
        align,
        justify_values,
        align_by_char,
        get_type_name,
        fmt_type,
        fmt_name,
        join_names,
        fmt_now,
        fmt_str,
        tdelta_to_ntup,
        fmt_elapsed,
        fmt_value,
        )
from .core.messages.logtools import (
        Tee,
        LogParms,
        LogFunc,
        logfunc,
        )
from .core.messages.colorize import colorize, decolorize
from .core.messages.dirtree import dirtree
from .options import options

__all__ = [
        'align',
        'align_by_char',
        'colorize',
        'decolorize',
        'dirtree',
        'fmt_name',
        'fmt_str',
        'fmt_now',
        'fmt_type',
        'fmt_valid_types',
        'fmt_valid_values',
        'fmt_value',
        'fmt_msg',
        'get_type_name',
        'join_names',
        'justify_values',
        'type_err_msg',
        'value_err_msg',
        'ask_yes',
        'fmt_elapsed',
        'tdelta_to_ntup',
        'Tee',
        'LogParms',
        'LogFunc',
        'logfunc',
        ]



def fmt_msg(
        msg: str | Iterable[str] | None, 
        color: str = None, 
        as_hdr: bool = False,
        indent: str = '',
        min_sep_width: int | None = None,
        max_sep_width: int | None = None,
        sep: str = '-',
        ) -> str:
    """
    Format a message string or sequence of strings for pretty display.

    The message is formatted with optional colorization, indentation, and
    header-like separators above and below. The width of these separators
    adapts to the length of the longest line, bounded by min/max widths.

    Parameters
    ----------
    msg : str or Iterable[str]
        A string (possibly multi-line) or an iterable of strings.
        If None and `as_hdr` is True, include a single separator
    color : str, optional
        If provided, applies ANSI color using `colorize`.
    as_hdr : bool, default False
        If True, adds a separator line before and after the message.
    indent : str, default ''
        Optional indentation applied to each line.
    min_sep_width : int or None, default: `options.pp.width`
        Minimum width for the header separator line.
    max_sep_width : int or None, default: `options.pp.width`
        Maximum width for the header separator line.
    sep : str, default '-'
        Character used to build the header separator.

    Returns
    -------
    str
        The formatted message string, ready for printing.

    Examples
    --------
    >>> print(fmt_msg("Important!", as_hdr=True))
    -----------
    Important!
    -----------

    >>> print(fmt_msg(["line 1", "line 2"], indent="  "))
      line 1
      line 2

    >>> print(fmt_msg("", as_hdr=True))  # empty message still gets separators
    -------
    
    -------
    """
    if isinstance(msg, str):
        lines = msg.splitlines()
    elif msg is None:
        lines = ['']
    else:
        lines = []
        for x in msg:
            lines.extend(x.splitlines())

    # Ensure lines is non-empty to avoid ValueError
    if not lines:
        lines = ['']

    min_sep_width = options.pp.width if min_sep_width is None else min_sep_width
    max_sep_width = options.pp.width if max_sep_width is None else max_sep_width

    sep_width = min(
        max_sep_width,
        max(min_sep_width, max(len(x) for x in lines))
    )

    if as_hdr:
        hdr_sep = sep * sep_width
        if lines == ['']:
            lines = [hdr_sep]
        else:
            lines = [hdr_sep] + lines + [hdr_sep]

    # Apply color per line (in case output lines need further parsing later)
    lines = [colorize(x, color=color) for x in lines]

    if indent:
        lines = [f"{indent}{x}" for x in lines]

    return '\n'.join(lines)


def ask_yes(
        msg: str | None = None,
        color: str = None,
        strict: bool = True,
        default_yes: bool = False,
        prompt: str | None = None) -> bool:
    """
    Ask for user confirmation and return True if confirmed.

    Supports optional strictness and ENTER-to-continue mode.

    Parameters
    ----------
    msg : str, optional
        Message to display before the prompt. A newline will separate it
        from the prompt if both are given.

    color : str, optional
        If provided, the full message (msg + prompt) will be colorized.

    strict : bool, default True
        If True, only accept "YES"/"NO". If False, also accept "y"/"n".

    default_yes : bool, default False
        If True, pressing ENTER counts as confirmation.

    prompt : str, optional
        Prompt string shown to the user. Defaults depend on `default_yes`.

    Returns
    -------
    bool
        True if user confirmed, False otherwise.
    """
    if default_yes:
        prompt = prompt or "Press [ENTER] to continue, or type NO to exit: "
        retry_hint = "You must either press [ENTER] or type YES/NO"
    else:
        prompt = prompt or "Please type YES to continue or NO to exit: "
        retry_hint = "You must type YES or NO"

    full_msg = f"{msg}\n{prompt}" if msg else prompt
    if color is not None:
        full_msg = colorize(full_msg, color=color)

    answer = input(full_msg)
    chk_answer = answer.casefold().strip().replace('"', '').replace("'", '')
    retry_prompt = f"{retry_hint}, not '{answer}'. Try again:"

    yes = {'yes', 'y'} if not strict else {'yes'}
    no = {'no', 'n'} if not strict else {'no'}

    if chk_answer in yes:
        return True
    elif chk_answer in no:
        return False
    elif chk_answer == "":
        return default_yes if default_yes else ask_yes(
            msg=None, prompt=retry_prompt,
            color=color, strict=strict, default_yes=default_yes)
    else:
        return ask_yes(
            msg=None, prompt=retry_prompt,
            color=color, strict=strict, default_yes=default_yes)

