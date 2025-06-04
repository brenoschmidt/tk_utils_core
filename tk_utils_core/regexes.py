"""
Common regex objects with lazy compilation.

This module defines the `Regexes` class, which exposes a collection of regular
expressions as lazily-evaluated, cached properties. A shared instance `rgx` is
created at the module level for reuse across imports.

"""
from __future__ import annotations

import re
from functools import cached_property

__all__ = [
        'rgx',
        ]

def _rc(s, 
        dotall: bool = True,
        verbose: bool = True,
        ignore_case: bool = True,
        ):
    args = None
    if ignore_case is True:
        args = re.I
    if verbose is True:
        args = args|re.X
    if dotall is True:
        args = args|re.S
    if args is None:
        return re.compile(s)
    else:
        return re.compile(s, args)

class Regexes:
    """ 
    Lazily compiled regular expression patterns.
    """
    __slots__ = ()

    @cached_property
    def rquotes(self) -> re.Pattern:
        """
        Return a compiled regex pattern that matches single or double quote characters.

        Matches:
            - Single quote: '
            - Double quote: "
        """
        return re.compile(r'''["']''')

    @cached_property
    def rspc(self) -> re.Pattern:
        """
        Match exactly one space character.

        Examples
        --------
        >>> from tk_utils.regexes import rgx
        >>> rgx.rspc.fullmatch(' ')
        <re.Match object ...>
        >>> rgx.rspc.fullmatch('\\t') is None
        True
        >>> rgx.rspc.fullmatch('  ') is None
        True
        """
        return re.compile(r' ')

    @cached_property
    def rspcs(self) -> re.Pattern:
        """
        Match one or more consecutive space characters.

        Examples
        --------
        >>> from tk_utils.regexes import rgx
        >>> rgx.rspcs.fullmatch('   ')
        <re.Match object ...>
        >>> rgx.rspcs.fullmatch(' ') is not None
        True
        >>> rgx.rspcs.fullmatch('\\t') is None
        True
        >>> rgx.rspcs.fullmatch(' \\t ') is None
        True
        """
        return re.compile(r' +')




rgx = Regexes()





