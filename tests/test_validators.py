"""
Tests the `tk_utils_core/validators.py` module

"""

from __future__ import annotations

from collections import namedtuple
from pydantic import BaseModel
from pydantic.dataclasses import dataclass as pydantic_dc
from pydantic.dataclasses import is_pydantic_dataclass

from tk_utils_core.testing.unittest_runner import (
        BaseTestCase,
        run_tests,
        )

from tk_utils_core.validators import (
        #is_hidden,
        is_namedtuple,
        is_pydantic_dc,
        is_pydantic_model,
        )
from tk_utils_core.options import options

class TestValidatorsMod(BaseTestCase):
    """
    Test the `tk_utils_core/validators.py` module
    """
    _only_in_debug = [
            ]

    def test_is_namedtuple(self):
        """
        """
        self._start_msg()
        self._run_doctest(is_namedtuple)

        Point = namedtuple("Point", "x y")
        p = Point(1, 2)

        self.assertTrue(is_namedtuple(p))
        self.assertFalse(is_namedtuple((1, 2)))
        self.assertFalse(is_namedtuple({"x": 1, "y": 2}))

    def test_is_pydantic_model(self):
        """
        """
        self._start_msg()
        self._run_doctest(is_pydantic_model)

        class Model1(BaseModel):
            a: int

        m = Model1(a=1)
        self.assertTrue(is_pydantic_model(m))
        self.assertFalse(is_pydantic_model({"a": 1}))

    def test_is_pydantic_dc(self):
        """
        """
        self._start_msg()
        self._run_doctest(is_pydantic_dc)

        @pydantic_dc
        class DC:
            a: int

        d = DC(a=1)
        self.assertTrue(is_pydantic_dc(d))
        self.assertFalse(is_pydantic_dc({"a": 1}))

def main(verbosity=2, *args, **kargs):
    cls = TestValidatorsMod
    run_tests(
            cls=cls,
            debug=options.debug,
            verbosity=verbosity, *args, **kargs)

if __name__ == '__main__':
    main()
    #with options.set_values({'debug': True}):
    #    main()
