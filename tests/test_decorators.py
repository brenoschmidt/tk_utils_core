"""
Tests the `tk_utils_core/decorators.py` module

"""
from __future__ import annotations

import tempfile
import io
import textwrap
import contextlib
import pathlib
import os

from tk_utils_core.testing.unittest_runner import (
        BaseTestCase,
        run_tests,
        )
from tk_utils_core.messages import decolorize
from tk_utils_core.decorators import (
        describe,
        )
from tk_utils_core.options import options


def simple_func(name="World"):
    """Print a greeting."""
    print(f"Hello, {name}!")


def get_output(func, *args, **kargs):
    with CaptureStdout() as output:
        func(*args, **kargs)
    return decolorize(str(output))

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

class TestDescribe(BaseTestCase):
    """
    Test the describe decorator
    """
    _only_in_debug = [
            ]


    def test_simple_func(self):
        """
        """
        self._start_msg()
        dflts = {
                'show_doc': False,
                'show_decor': False,
                'show_body': False,
                'show_sig': False,
                'quiet': False,
                }


        # All parms to false
        opts = dflts | {}
        decorated = describe(**opts)(simple_func)
        expected = textwrap.dedent(f'''\
        ----------------------------------------
        Running simple_func
        ----------------------------------------
        Output:

        Hello, World!
        ''')
        got = get_output(decorated)
        assert got.startswith(expected), f"\n{got}"

        # show_doc
        opts = dflts | {'show_doc': True}
        decorated = describe(**opts)(simple_func)
        expected = textwrap.dedent('''\
        ----------------------------------------
        Running simple_func
        Docstring:
            Print a greeting.
        ----------------------------------------
        Output:

        Hello, World!
        ''')
        got = get_output(decorated)
        assert got.startswith(expected), f"\n{got}"

        # show_sig
        opts = dflts | {'show_sig': True}
        decorated = describe(**opts)(simple_func)
        expected = textwrap.dedent('''\
        ----------------------------------------
        Running  simple_func(name="World")
        ----------------------------------------
        Output:

        Hello, World!
        ''')
        got = get_output(decorated)
        assert got.startswith(expected), f"\n{got}"

        # show_body
        opts = dflts | {'show_body': True}
        decorated = describe(**opts)(simple_func)
        expected = textwrap.dedent('''\
        ----------------------------------------
        Running simple_func
        Body:
            print(f"Hello, {name}!")
        ----------------------------------------
        Output:

        Hello, World!
        ''')
        got = get_output(decorated)
        assert got.startswith(expected), f"\n{got}"

        # show all
        opts = dflts | {
                'show_sig': True, 
                'show_body': True,
                'show_doc': True,
                }
        decorated = describe(**opts)(simple_func)
        expected = textwrap.dedent('''\
        ----------------------------------------
        Running  simple_func(name="World")
        Docstring:
            Print a greeting.
        Body:
            print(f"Hello, {name}!")
        ----------------------------------------
        Output:

        Hello, World!
        ''')
        got = get_output(decorated)
        assert got.startswith(expected), f"\n{got}"


def main(verbosity=2, *args, **kargs):
    cls_lst = [
        TestDescribe,
        ]
    for cls in cls_lst:
        run_tests(
            cls=cls,
            debug=options.debug,
            verbosity=verbosity, *args, **kargs)

if __name__ == '__main__':
    main()
    #with options.set_values({'debug': True}):
    #    main()
