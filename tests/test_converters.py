"""
Tests the `tk_utils_core/converters.py` module

"""

from __future__ import annotations

from types import SimpleNamespace
import pathlib 
import dataclasses as dc
from pydantic import BaseModel

from tk_utils_core.testing.unittest_runner import (
        BaseTestCase,
        run_tests,
        )

from tk_utils_core.converters import (
        as_path,
        as_dict,
        as_list,
        as_set,
        bytes2human,
        human2bytes,
        to_namespace,
        csv_to_df,
        )
from tk_utils_core.options import options

class TestConvertersMod(BaseTestCase):
    """
    Test the `tk_utils_core/converters` module
    """
    _only_in_debug = [
            'test_to_namespace',
            'test_as_dict',
            'test_as_path',
            'test_as_list',
            'test_as_set',
            'test_bytes2human',
            'test_human2bytes',
            ]

    def test_to_namespace(self):
        """
        """
        self._start_msg()
        self._run_doctest(to_namespace)
        d = {"a": 1, "b": {"c": 2}}
        ns = to_namespace(d)
        self.assertEqual(ns.a, 1)
        self.assertEqual(ns.b.c, 2)

    def test_as_dict(self):
        """
        """
        self._start_msg()
        self._run_doctest(as_dict)

        self._add_msg("Namespaces to dict")
        ns = SimpleNamespace(a=1, b=SimpleNamespace(c=2))
        out = as_dict(ns)
        self.assertEqual(out, {"a": 1, "b": {"c": 2}})
        
        self._add_msg("DC to dict")

        @dc.dataclass
        class DC0:
            parm0: str = 'x'
            parm00: int = 2

        @dc.dataclass
        class DC1:
            parm1: dict 
            parm11: DC0
            parm111: list

        test_dc = DC1(
                parm1={'a': '1'}, 
                parm11=DC0(),
                parm111=[1, 2, 3],
                )
        expected = {
                'parm1': {'a': '1'},
                'parm11': {
                    'parm0': 'x',
                    'parm00': 2,
                    },
                'parm111': [1, 2, 3],
                }
        out = as_dict(test_dc)
        self.assertEqual(out, expected)

        self._add_msg("pydantic model to dict")

        class Model1(BaseModel):
            parm1: dict
            parm11: DC0
            parm111: list

        test_mod = Model1(**expected)
        out = as_dict(test_mod)
        self.assertEqual(out, expected)

    def test_as_path(self):
        """
        """
        self._start_msg()
        self._run_doctest(as_path)

        self._add_msg("String input")
        p = as_path("a/b/c")
        self.assertIsInstance(p, pathlib.Path)
        self.assertEqual(str(p), "a/b/c")

        self._add_msg("Already a path")
        q = pathlib.Path("x/y")
        self.assertIs(as_path(q), q)

    def test_as_list(self):
        """
        """
        self._start_msg()
        self._run_doctest(as_list)

        self._add_msg("Already a list")
        self.assertEqual(as_list([1, 2]), [1, 2])

        self._add_msg("Tuple to list")
        self.assertEqual(as_list((1, 2)), [1, 2])

        self._add_msg("Set to list")
        self.assertEqual(set(as_list({1, 2})), {1, 2})

        self._add_msg("String to list")
        self.assertEqual(as_list("abc"), ["abc"])

    def test_as_set(self):
        """
        """
        self._start_msg()
        self._run_doctest(as_set)

        self._add_msg("List to set")
        self.assertEqual(as_set([1, 2]), {1, 2})

        self._add_msg("Set stays the same")
        s = {3, 4}
        self.assertEqual(as_set(s), s)

        self._add_msg("String to set")
        self.assertEqual(as_set("abc"), {"abc"})

    def test_bytes2human(self):
        """
        """
        self._start_msg()
        self._run_doctest(bytes2human)

        self._add_msg("Integer bytes to string")
        self.assertEqual(bytes2human(1024), "1 KB")
        self.assertEqual(bytes2human(1048576), "1 MB")

        self._add_msg("Zero bytes")
        self.assertEqual(bytes2human(0), "0 B")

    def test_human2bytes(self):
        """
        """
        self._start_msg()
        self._run_doctest(human2bytes)

        self._add_msg("KiB to bytes")
        self.assertEqual(human2bytes("1 KiB"), 1024)

        self._add_msg("MiB to bytes")
        self.assertEqual(human2bytes("1 MiB"), 1048576)


    def test_csv_to_df(self):
        """
        """
        self._start_msg()
        self._run_doctest(csv_to_df)


def main(verbosity=2, *args, **kargs):
    cls = TestConvertersMod
    run_tests(
            cls=cls,
            debug=options.debug,
            verbosity=verbosity, *args, **kargs)

if __name__ == '__main__':
    main()
    #with options.set_values({'debug': True}):
    #    main()
