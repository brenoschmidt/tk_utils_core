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
from ..options import options
from .doctests_runner import run_quiet_doctest

__all__ = ["BaseTestCase", "run_tests", "main"]


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
    Extension of `unittest.TestCase` with support for colorized debug output
    during development-mode test execution.

    Attributes
    ----------
    __debug_enabled__ : bool
        If True, enables additional debug output through helper methods.

    _only_in_debug : list of str
        List of test method names to run only when debug is True.

    Methods
    -------
    _start_msg(msg, color='green', as_hdr=True, **kargs)
        Start a formatted message block.

    _add_msg(msg, color='yellow', as_hdr=False, **kargs)
        Append a line to the current debug message block.

    _end_msg(msg=None, color='green', as_hdr=True, **kargs)
        Conclude the debug message block.

    _print_debug(obj, color=None, indent=None, as_hdr=None, 
            pretty=False, width=None, ...)
        Print structured debug output using pprint and ANSI color formatting.
    """
    __debug_enabled__: bool = False
    _only_in_debug = []

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

    def _run_doctest(self, func):
        self._add_msg(f"\n{func.__name__}: running doctests")
        return run_quiet_doctest(func)

    def _start_msg(
            self,
            msg: str | None = None,
            color: str | None = 'green',
            as_hdr: bool = True,
            **kargs):
        """
        Start a formatted message block.
        """
        if self.__debug_enabled__:
            print('\n' + fmt_msg(msg, color=color, as_hdr=as_hdr, **kargs))

    def _add_msg(
            self,
            msg: str | Iterable[str],
            as_hdr: bool = False,
            color: str = 'yellow',
            **kargs):
        """
        Add a message line to the current debug block.
        """
        if self.__debug_enabled__:
            print(fmt_msg(msg, color=color, as_hdr=as_hdr, **kargs))

    def _end_msg(
            self,
            msg: str | None = None,
            color: str | None = 'green',
            as_hdr: bool = True,
            **kargs):
        """
        End a message block with optional message.
        """
        if self.__debug_enabled__:
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
        if not self.__debug_enabled__:
            return
        color = options.pp.color if color is None else color
        indent = options.pp.indent if indent is None else indent

        if pretty:
            width = options.pp.width if width is None else width
            msg = pp.pformat(msg, width=width)
        else:
            msg = str(msg)

        output = '\n' + fmt_msg(msg, color=color, indent=indent, as_hdr=as_hdr)
        print(output, *args, **kargs)


def run_tests(
        cls: type[BaseTestCase],
        debug: bool = False,
        verbosity: int = 2,
        failfast: bool = True,
        *args,
        **kargs,
        ) -> None:
    """
    Run selected test methods from a test case class.

    Parameters
    ----------
    cls : BaseTestCase
        The test case class.
    debug : bool, default False
        If True, only methods in `cls._only_in_debug` are run and debug
        output is enabled.
    failfast: bool, default True
        If True, stop remaining tests after a single failure
    verbosity : int
        Output verbosity level.

    Examples
    --------
    To run only selected tests in debug mode:

    >>> from tk_utils_core.testing.unittest_utils import BaseTestCase, run_tests
    >>> from tk_utils_core.options import options
    >>>
    >>> class TestSomething(BaseTestCase):
    ...     _only_in_debug = ['test_one_thing']
    ...
    ...     def test_one_thing(self):
    ...         self._start_msg("Starting test")
    ...         self._print_debug({'example': 123})
    ...         self._end_msg()
    ...
    ...     def test_another(self):
    ...         pass
    >>>
    >>> def main():
    ...     run_tests(TestSomething, debug=options.debug)
    """
    suite = unittest.TestSuite()

    if debug and hasattr(cls, '__debug_enabled__'):
        cls.__debug_enabled__ = True
        tests = getattr(cls, '_only_in_debug', None)
    else:
        tests = None

    if tests is not None and len(tests) > 0:
        msg = [
            "=" * 40,
            "  DEBUG MODE ENABLED: SELECTIVE TESTS",
            "-" * 40,
            f"Class: {cls.__name__}",
        ]

        if not tests:
            msg += ["No tests found in _only_in_debug."]
        else:
            msg += ["Running only tests listed in: _only_in_debug"]
            msg += [f"  - {name}" for name in tests]

        msg += ["=" * 40]
        print(fmt_msg(msg, as_hdr=True, color='yellow'))

        for test in tests:
            suite.addTest(cls(test))
    else:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(cls)

    runner = unittest.TextTestRunner(
            verbosity=verbosity,
            failfast=failfast,
            )
    runner.run(suite)


def main(verbosity: int = 2, *args, **kargs):
    """
    Run all tests using unittest.main().
    """
    unittest.main(verbosity=verbosity, *args, **kargs)



