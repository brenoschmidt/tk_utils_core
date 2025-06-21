"""
Utilities for representing objects as strings in diagnostic messages
"""
from __future__ import annotations

import contextlib
import io
from typing import Iterable

from tk_utils_core.core.messages.errors import (
        type_err_msg,
        value_err_msg,
    )
from tk_utils_core.core.messages.formatters import (
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
        trim_values,
        dedent_by,
        )
from tk_utils_core.core.messages.logtools import (
        Tee,
        LogParms,
        LogFunc,
        logfunc,
        )
from tk_utils_core.core.messages.colorize import colorize, decolorize
from tk_utils_core.core.messages.dirtree import dirtree
from tk_utils_core.options import options

__all__ = [
        'align',
        'align_by_char',
        'colorize',
        'decolorize',
        'dedent_by',
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
        'trim_values',
        'LogParms',
        'LogFunc',
        'logfunc',
        'CapureStdout',
        'get_lines_between',
        ]




class CaptureStdout(contextlib.AbstractContextManager):
    """
    Context manager that captures stdout and returns it as a string.

    Usage
    -----
    >>> with CaptureStdout() as output:
    ...     help(len)
    >>> print(str(output)[:10])
    'Help on '
    """

    def __enter__(self) -> CaptureStdout:
        self._buf = io.StringIO()
        self._ctx = contextlib.redirect_stdout(self._buf)
        self._ctx.__enter__()
        return self

    def __exit__(
            self,
            exc_type,
            exc_val,
            exc_tb) -> bool | None:
        self._ctx.__exit__(exc_type, exc_val, exc_tb)
        self.value = self._buf.getvalue()
        self._buf.close()
        return None  # Let exceptions propagate

    def __str__(self) -> str:
        return self.value

def fmt_hdr_sep(
        max_line_width: int,
        sep: str = '-',
        min_sep_width: int | None = None,
        max_sep_width: int | None = None,
        ) -> str:
    """
    Create a header separator string
    """
    min_sep_width = options.pp.width if min_sep_width is None else min_sep_width
    max_sep_width = options.pp.width if max_sep_width is None else max_sep_width

    sep_width = min(
        max_sep_width,
        max(min_sep_width, max_line_width)
    )
    return sep * sep_width

def fmt_msg(
        msg: str | Iterable[str] | None, 
        color: str = None, 
        as_hdr: bool = False,
        indent: str = '',
        min_sep_width: int | None = None,
        max_sep_width: int | None = None,
        sep: str = '-',
        as_list: bool = False,
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

    if as_hdr:
        hdr_sep = fmt_hdr_sep(
                sep=sep,
                max_line_width=max(len(x) for x in lines),
                min_sep_width=min_sep_width,
                max_sep_width=max_sep_width,
                )
        if lines == ['']:
            lines = [hdr_sep]
        else:
            lines = [hdr_sep] + lines + [hdr_sep]

    # Apply color per line (in case output lines need further parsing later)
    lines = [colorize(x, color=color) for x in lines]

    if indent:
        lines = [f"{indent}{x}" for x in lines]

    if as_list is True:
        return lines
    else:
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
            msg=None, 
            prompt=retry_prompt,
            color=color, 
            strict=strict, 
            default_yes=default_yes)
    else:
        return ask_yes(
            msg=None, 
            prompt=retry_prompt,
            color=color, 
            strict=strict, 
            default_yes=default_yes)

def get_lines_between(
        text: str,
        start: str,
        end: str,
        as_list: bool = False) -> str | list[str] | None:
    """
    Extract lines between `start` and `end` markers.

    Parameters
    ----------
    text : str
        Input string with multiple lines.

    start : str
        Marker string indicating the beginning of the block.

    end : str
        Marker string indicating the end of the block.

    as_list : bool, default False
        If True, return the extracted lines as a list of strings.
        If False, return as a single joined string.

    Returns
    -------
    str or list of str or None
        Lines between the first `start` and `end` markers (exclusive).
        Returns None if no such block is found.

    Examples
    --------
    >>> text = '''
    ... skip
    ... <tag>
    ... line 1
    ... line 2
    ... </tag>
    ... after'''
    >>> get_lines_between(text, "<tag>", "</tag>", as_list=True)
    ['line 1', 'line 2']
    >>> get_lines_between(text, "<tag>", "</tag>")
    'line 1\nline 2'
    """
    lines = text.splitlines()
    in_block = False
    out = []

    for line in lines:
        if start in line:
            in_block = True
            continue
        if end in line and in_block:
            break
        if in_block:
            out.append(line)

    if not out:
        return None
    return out if as_list else '\n'.join(out)
