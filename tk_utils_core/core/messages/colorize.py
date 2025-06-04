""" 
Utils to colorize strings


References
----------

- colorama: https://github.com/tartley/colorama/tree/master

- ANSI escape codes: http://en.wikipedia.org/wiki/ANSI_escape_code

- termcolor: https://github.com/termcolor/termcolor/blob/main/src/termcolor/termcolor.py


"""
from __future__ import annotations

import re
from functools import lru_cache
from typing import Iterable
from types import SimpleNamespace

from .formatters import align

# ANSI escape codes reference:
# https://en.wikipedia.org/wiki/ANSI_escape_code

BASE_COLOR_MAP = {
    'black':         (30, 40),
    'red':           (31, 41),
    'green':         (32, 42),
    'yellow':        (33, 43),
    'blue':          (34, 44),
    'magenta':       (35, 45),
    'cyan':          (36, 46),
    'white':         (37, 47),
    'light_black':   (90, 100),
    'light_red':     (91, 101),
    'light_green':   (92, 102),
    'light_yellow':  (93, 103),
    'light_blue':    (94, 104),
    'light_magenta': (95, 105),
    'light_cyan':    (96, 106),
    'light_white':   (97, 107),
}

STYLE_MAP = {
    "bold": 1,
    "dark": 2,
    "underline": 4,
    "blink": 5,
    "reverse": 7,
    "concealed": 8,
}

def _mk_code(code: int) -> str:
    return f"\033[{code}m"

@lru_cache(1)
def _mk_ansi_codes() -> SimpleNamespace:
    """
    Return a namespace of ANSI escape codes grouped into fg, bg, styles, and reset.
    """
    fg = {name: _mk_code(fg) for name, (fg, _) in BASE_COLOR_MAP.items()}
    bg = {name: _mk_code(bg) for name, (_, bg) in BASE_COLOR_MAP.items()}
    styles = {name: _mk_code(code) for name, code in STYLE_MAP.items()}
    return SimpleNamespace(fg=fg, bg=bg, styles=styles, reset="\033[0m")

@lru_cache(1)
def _mk_ansi_escape_rgx() -> re.Pattern:
    return re.compile(r'''
    \x1B  # ESC
    (?:   # 7-bit C1 Fe (except CSI)
        [@-Z\\-_]
    |     # or [ for CSI, followed by a control sequence
        \[
        [0-?]*  # Parameter bytes
        [ -/]*  # Intermediate bytes
        [@-~]   # Final byte
    )
    ''', re.VERBOSE)

def _get_code(name: str, value: str, codes: dict[str, str]) -> str:
    if value not in codes:
        opts = ', '.join(sorted(codes))
        raise ValueError(
                f"Invalid value for parm `{name}`: '{value}'. "
                f"Must be one of: {opts}")
    return codes[value]

def colorize(
        text: str,
        color: str | None,
        style: str | Iterable[str] | None = None,
        bg: str | None = None,
        reset: bool = True,
        ) -> str:
    """
    Wrap text in ANSI codes for terminal color/styling.

    Parameters
    ----------
    text : str
        The string to colorize.
    color : str | None
        Foreground color name (e.g., "red").
    style : str | Iterable[str] | None
        Text style(s) (e.g., "bold", "underline").
    bg : str | None
        Background color name.
    reset : bool, default True
        If True, append the ANSI reset code at the end.

    Returns
    -------
    str
        Colorized string.
    """
    if not isinstance(text, str):
        raise TypeError(
                f"Parm `text` must be a 'str' not '{type(text).__name__}'")

    ansi = _mk_ansi_codes()
    fmts = []

    if color:
        fmts.append(_get_code('color', color, ansi.fg))
    if bg:
        fmts.append(_get_code('bg', bg, ansi.bg))
    if style:
        styles = [style] if isinstance(style, str) else style
        fmts.extend(_get_code('style', s, ansi.styles) for s in styles)

    for code in fmts:
        text = f"{code}{text}"

    if reset:
        text += ansi.reset
    return text

def decolorize(text: str) -> str:
    """
    Strip ANSI codes from a string.

    Parameters
    ----------
    text : str
        A string possibly containing ANSI codes.

    Returns
    -------
    str
        The decolorized string.
    """
    return _mk_ansi_escape_rgx().sub('', text)

def show_colors(as_str: bool = False) -> str | None:
    """
    Print or return a preview of available foreground colors.

    Parameters
    ----------
    as_str : bool, default False
        If True, return the string instead of printing it.

    Returns
    -------
    str | None
        Returns string if `as_str` is True, otherwise prints output.
    """
    codes = _mk_ansi_codes()
    rows = [(name, colorize(name, color=name)) for name in sorted(codes.fg)]
    out = align(rows)
    if as_str:
        return out
    print(out)
    return None












