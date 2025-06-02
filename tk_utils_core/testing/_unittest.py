"""
Unittest wrappers
"""
from __future__ import annotations

import unittest
import logging
import sys
import pprint as pp
from typing import Iterable
from functools import lru_cache

from ..messages import colorize, fmt_msg
from ..defaults import defaults


@lru_cache(1)
def get_logger() -> logging.Logger:
    logger = logging.getLogger("unittest_logger")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger


class BaseTestCase(unittest.TestCase):
    """
    Simple extension of unittest.TestCase with colored message support.

    Usage
    -----
    >>> class MyTest(BaseTestCase):
    ...
    ...     def test_something(self):
    ...         self._start_msg("Start test")
    ...         self._add_msg("Running step...")
    ...         self._end_msg()

    >>> base.run_tests(cls=MyTest, tests=['test_something'])
    """
    _DEBUG = False

    def shortDescription(self) -> str:
        doc = self._testMethodDoc
        return self._enclose(doc.rstrip() if doc else '')

    def _enclose(self, s: str) -> str:
        lines = s.splitlines()
        if not lines:
            return '\n'
        length = max(len(x) for x in lines)
        sep = '-' * length
        return f"{sep}\n{s}\n{sep}\n"

    def _start_msg(
            self,
            msg: str | None = None,
            color: str | None = 'green',
            as_hdr: bool = True,
            **kargs):
        """Start a formatted message block."""
        if self._DEBUG:
            print('\n' + fmt_msg(msg, color=color, as_hdr=as_hdr, **kargs))

    def _add_msg(
            self,
            msg: str | Iterable[str],
            as_hdr: bool = False,
            color: str = 'yellow',
            **kargs):
        """Add a message line to the current debug block."""
        if self._DEBUG:
            print(fmt_msg(msg, color=color, as_hdr=as_hdr, **kargs))


    def _end_msg(
            self,
            msg: str | None = None,
            color: str | None = 'green',
            as_hdr: bool = True,
            **kargs):
        """End a message block with optional message."""
        if self._DEBUG:
            out = fmt_msg(msg, color=color, as_hdr=as_hdr, **kargs)
            if not out.endswith('\n'):
                out += '\n'
            print(out)

    def _print_debug(
            self,
            msg: object,
            color: str | None = None,
            indent: str | None = None,
            as_hdr: bool | None = None,
            pretty: bool = False,
            width: int | None = None,
            *args,
            **kargs,
            ):
        """
        Print a message with optional formatting and color using logger.

        Parameters
        ----------
        msg : object
            The message to print.
        color : str, optional
            ANSI color name.
        indent : str, optional
            Indentation prefix.
        as_hdr : bool, optional
            Whether to render as header.
        pretty : bool
            Pretty-print the object using pprint.
        width : int, optional
            Line width for pretty-printing.
        """
        if self._DEBUG is False:
            return
        color = defaults.pp.color if color is None else color
        indent = defaults.pp.indent if indent is None else indent

        if pretty:
            width = defaults.pp.width if width is None else width
            msg = pp.pformat(msg, width=width)
        else:
            msg = str(msg)

        output = '\n' + fmt_msg(msg, color=color, indent=indent, as_hdr=as_hdr)
        print(output, *args, **kargs)


def run_tests(
        cls: type[BaseTestCase],
        tests: list[str],
        verbosity: int = 2,
        debug: bool = False,
        *args,
        **kargs,
        ) -> None:
    """
    Run selected test methods from a test case class.

    Parameters
    ----------
    cls : BaseTestCase
        The test case class.
    tests : list of str
        Method names to run.
    verbosity : int
        Output verbosity level.
    """
    suite = unittest.TestSuite()
    for test in tests:
        cls._DEBUG = debug
        suite.addTest(cls(test))
    runner = unittest.TextTestRunner(verbosity=verbosity)
    runner.run(suite)


def main(verbosity: int = 2, *args, **kargs):
    """Run all tests using unittest.main()."""
    unittest.main(verbosity=verbosity, *args, **kargs)


