""" 
Code parsers

         
"""
from __future__ import annotations

import difflib

def diff_lines(
        a: str,
        b: str,
        fromfile: str = 'a',
        tofile: str = 'b',
        context: bool = False,
        n: int = 3) -> str:
    """
    Return a unified diff between two strings (line-by-line).

    Parameters
    ----------
    a : str
        First input string (e.g., original file contents).
    b : str
        Second input string (e.g., modified file contents).
    fromfile : str, default 'a'
        Label for the first input (shown in diff header).
    tofile : str, default 'b'
        Label for the second input (shown in diff header).
    context : bool, default False
        If True, show contextual diff (like `diff -c`).
        If False, show unified diff (like `diff -u`).
    n : int, default 3
        Number of context lines to show.

    Returns
    -------
    str
        A unified diff string showing line-by-line differences.
    """
    a_lines = a.splitlines(keepends=True)
    b_lines = b.splitlines(keepends=True)

    if context:
        diff = difflib.context_diff(
            a_lines, b_lines, fromfile=fromfile, tofile=tofile, n=n)
    else:
        diff = difflib.unified_diff(
            a_lines, b_lines, fromfile=fromfile, tofile=tofile, n=n)

    return ''.join(diff)

