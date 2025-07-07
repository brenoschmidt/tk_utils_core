"""
Tests the `tk_utils_core/structs.py` module



"""
from __future__ import annotations

from tk_utils_core.testing.unittest_runner import (
        BaseTestCase,
        run_tests,
        )

from tk_utils_core.structs import (
        obj_dot_update,
        obj_dot_get,
        obj_dot_subset,
        obj_dot_delete,
        unflatten_dict,
        flatten_dict,
        AttrDict,
        )
from tk_utils_core.options import options

class TestStructsMod(BaseTestCase):
    """
    Test the `tk_utils_core/structs.py` module
    """
    _only_in_debug = [
            'test_obj_dot_update',
            'test_obj_dot_get',
            'test_obj_dot_subset',
            'test_unflatten_dict',
            'test_flatten_dict',
            ]

    def test_unflatten_dict(self):
        """
        """
        self._start_msg()
        self._run_doctest(unflatten_dict)

        self._add_msg("Simple nesting")
        d = {'a.b': 1, 'a.c': 2, 'x': 9}
        out = unflatten_dict(d)
        self.assertEqual(out, {'a': {'b': 1, 'c': 2}, 'x': 9})

        self._add_msg("Deep nesting")
        d = {'a.b.c.d': 1}
        out = unflatten_dict(d)
        self.assertEqual(out, {'a': {'b': {'c': {'d': 1}}}})

        self._add_msg("Conflict with existing flat key")
        d = {'a': 1, 'a.b': 2}
        with self.assertRaises(ValueError):
            unflatten_dict(d)

    def test_flatten_dict(self):
        """
        """

        self._start_msg()
        self._run_doctest(flatten_dict)

        self._add_msg("Flatten single level")
        d = {'a': {'b': 1}, 'x': 9}
        out = flatten_dict(d)
        self.assertEqual(out, {'a.b': 1, 'x': 9})

        self._add_msg("Flatten deep nesting")
        d = {'a': {'b': {'c': {'d': 1}}}}
        out = flatten_dict(d)
        self.assertEqual(out, {'a.b.c.d': 1})

        self._add_msg("Roundtrip flatten + unflatten")
        from tk_utils_core.structs import unflatten_dict
        original = {'m': 1, 'n': {'x': 1, 'y': {'z': 2}}}
        flat = flatten_dict(original)
        nested = unflatten_dict(flat)
        self.assertEqual(nested, original)

    def test_obj_dot_update(self):
        """
        """
        self._start_msg()
        self._run_doctest(obj_dot_update)


        class B:
            def __init__(self):
                self.c = 1

        class A:
            def __init__(self):
                self.b = B()

        a = A()
        obj_dot_update(a, "b.c", 42)
        self.assertEqual(a.b.c, 42)

        self._add_msg("Fails silently if path does not exist")
        # Attribute 'x' doesn't exist — should not raise
        obj_dot_update(a, "b.x.y", 99)
        self.assertFalse(hasattr(a.b, "x"))

    def test_obj_dot_get(self):
        """
        """
        self._start_msg()
        self._run_doctest(obj_dot_get)

        class B:
            def __init__(self):
                self.c = 123

        class A:
            def __init__(self):
                self.b = B()

        a = A()
        self.assertEqual(obj_dot_get(a, "b.c"), 123)

        self._add_msg("Raises KeyError if no default")
        with self.assertRaises((AttributeError, KeyError)):
            obj_dot_get(a, "b.x.y")

    def test_obj_dot_subset(self):
        """
        """
        self._start_msg()
        self._run_doctest(obj_dot_subset)

        class B:
            def __init__(self):
                self.c = 1
                self.d = 2

        class A:
            def __init__(self):
                self.b = B()
                self.x = 99

        a = A()

        self._add_msg("Subset by include")
        out = obj_dot_subset(a, includes=["b.c", "x"])
        self.assertEqual(out.b.c, 1)
        self.assertEqual(out.x, 99)
        self.assertFalse(hasattr(out.b, "d"))

        self._add_msg("Subset by exclude")
        out = obj_dot_subset(a, excludes=["b.d"])
        self.assertTrue(hasattr(out.b, "c"))
        self.assertFalse(hasattr(out.b, "d"))
        self.assertEqual(out.x, 99)

    def test_obj_dot_delete(self):
        """
        """
        self._start_msg()
        self._run_doctest(obj_dot_delete)

        class B:
            def __init__(self):
                self.c = 1
                self.d = 2

        class A:
            def __init__(self):
                self.b = B()
                self.x = 9

        a = A()
        obj_dot_delete(a, "b.d")
        self.assertFalse(hasattr(a.b, "d"))

        self._add_msg("Missing path does nothing")
        obj_dot_delete(a, "b.y.z")  # Should not raise

        self._add_msg("Top-level attribute")
        obj_dot_delete(a, "x")
        self.assertFalse(hasattr(a, "x"))

    def test_attrdict(self):
        """
        """
        self._start_msg()
        self._run_doctest(AttrDict)

def main(verbosity=2, *args, **kargs):
    cls = TestStructsMod
    run_tests(
            cls=cls,
            debug=options.debug,
            verbosity=verbosity, *args, **kargs)

if __name__ == '__main__':
    main()
    #with options.set_values({'debug': True}):
    #    main()
