"""
Tests the `tk_utils_core/mappings.py` module

"""

from __future__ import annotations


from tk_utils_core.testing.unittest_runner import (
        BaseTestCase,
        run_tests,
        )

from tk_utils_core.mappings import (
        deep_update,
        map_dot_get,
        map_dot_update,
        map_dot_subset,
        AttrDict,
        )
from tk_utils_core.options import options

class TestMappingsMod(BaseTestCase):
    """
    Test the `tk_utils_core/mappings.py` module
    """
    _only_in_debug = [
            'test_deep_update',
            'test_map_dot_get',
            'test_map_dot_update',
            'test_map_dot_subset',
            'test_attrdict_access',
            ]

    def test_deep_update(self):
        """
        """
        self._start_msg()
        self._run_doctest(deep_update)

        dic = {'a': {'b': 1, 'c': 2}}
        dic.update({'a': {'c': 99}}) # Normal update
        self.assertEqual(dic, {'a': {'c': 99}})

        dic = {'a': {'b': 1, 'c': 2}}
        dic = deep_update(dic, {'a': {'c': 99}}) 
        self.assertEqual(dic, {'a': {'b': 1, 'c': 99}})

        dic = {'a': {'b': 1, 'c': 2}}
        dic = deep_update(dic, {'a': {'d': 99}}) 
        self.assertEqual(dic, 
                         {'a': {'b': 1, 'c': 2, 'd': 99}})

        dic = {'a': {'b': 1, 'c': 2}}
        dic = deep_update(dic, {'a': 1}) 
        self.assertEqual(dic, {'a': 1})

    def test_map_dot_get(self):
        """
        """
        self._start_msg()
        self._run_doctest(map_dot_get)

        d = {"a": {"b": {"c": 1}}}
        self.assertEqual(map_dot_get(d, "a.b.c"), 1)
        self.assertEqual(map_dot_get(d, "a.b"), {"c": 1})
        self.assertEqual(map_dot_get(d, "a"), {"b": {"c": 1}})

        self._add_msg("Nonexistent path without default")
        with self.assertRaises(KeyError):
            map_dot_get(d, "x.y")

    def test_map_dot_update(self):
        """
        """
        self._start_msg()
        self._run_doctest(map_dot_update)

        d = {"a": {"b": {"c": 1}}}
        map_dot_update(d, "a.b.c", 42)
        self.assertEqual(d["a"]["b"]["c"], 42)

        self._add_msg("Creates new path if it doesn't exist")
        d = {}
        map_dot_update(d, "x.y.z", 99)
        self.assertEqual(d, {"x": {"y": {"z": 99}}})

    def test_map_dot_subset(self):
        """
        """
        self._start_msg()
        self._run_doctest(map_dot_subset)

        d = {
            "a": {"b": {"c": 1},
                  'd': 4},
            "x": 2,
            "y": {"z": 3},
        }

        flat = {
            "a.b.c": 1,
            "x": 2,
            "y.z": 3,
        }

        self._add_msg("Subset using includes")
        includes = ["a.b", "x"]
        expected = {
            "a": {"b": {"c": 1}},
            "x": 2,
        }
        subset = map_dot_subset(d, includes=includes)
        self.assertEqual(subset, expected)

        self._add_msg("Subset using excludes")
        excludes = ["a.b", "y.z"]
        expected = {
            "a": {'d': 4},
            'x': 2,
        }
        subset = map_dot_subset(d, excludes=excludes)
        self.assertEqual(subset, expected)

        self._add_msg("Subset with includes and excludes")
        includes = ["a.b", "x", "y.z"]
        excludes = ["x"]
        expected = {
            "a": {"b": {"c": 1}},
            "y": {"z": 3},
        }
        subset = map_dot_subset(d, includes=includes, excludes=excludes)
        self.assertEqual(subset, expected)

    def test_attrdict_access(self):
        """
        """
        self._start_msg()

        ad = AttrDict._from_dict({"a": 1, "b": {"c": 2}})
        self.assertEqual(ad.a, 1)
        self.assertIsInstance(ad.b, AttrDict)
        self.assertEqual(ad.b.c, 2)

        self._add_msg("Assignment via attribute")
        ad.x = 42
        self.assertEqual(ad["x"], 42)

        self._add_msg("Nested assignment via attribute")
        ad.b.d = 99
        self.assertEqual(ad["b"]["d"], 99)

        self._add_msg("Can convert back to dict")
        self.assertEqual(dict(ad), {"a": 1, "b": {"c": 2, "d": 99}, "x": 42})

def main(verbosity=2, *args, **kargs):
    cls = TestMappingsMod
    run_tests(
            cls=cls,
            debug=options.debug,
            verbosity=verbosity, *args, **kargs)

if __name__ == '__main__':
    main()
    #with options.set_values({'debug': True}):
    #    main()


