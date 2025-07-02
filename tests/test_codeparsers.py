"""
Tests the `tk_utils_core/codeparser.py` module

"""
from __future__ import annotations

import pathlib
import os
import pprint as pp
import sys

from tk_utils_core.testing.unittest_runner import (
        BaseTestCase,
        run_tests,
        )

from tk_utils_core.codeparser import (
        ParsedFunc,
        ModuleDefs,
        )
from tk_utils_core.options import options

from _utils import (
        eg_module,
        get_tagged_src,
        get_mod_src,
        ExampleObj,
        )


class TestParsedFunc(BaseTestCase):
    """
    Test the ParsedFunc class in the codeparser module
    """
    _only_in_debug = [
            'test_init_with_obj',
            'test_init_with_src',
            'test_tree_is_module',
            'test_func_node_type',
            'test_nodes_and_codes',
            'test_indent_and_indent_size',
            'test_mk_sig_subset',
            'test_as_ntup_default',
            'test_as_ntup_with_doc_attr',
            'test_decorators_present',
            'test_suite_doc_and_body',
            'test_signature_with_newlines',
            'test_errors_on_double_input',
            ]

    def setUp(self):
        self.cls = ParsedFunc

        self.simple_func = ExampleObj(
                obj=eg_module.square,
                name=eg_module.square.__name__,
                src=get_tagged_src(eg_module, 'func_square'),
                )

        self.decor_func = ExampleObj(
                obj=eg_module.say_hello,
                name=eg_module.say_hello.__name__,
                src=get_tagged_src(eg_module, 'func_say_hello'),
                )

        self.pf_simple_func = ParsedFunc(obj=self.simple_func.obj)

    def test_init_with_obj(self):
        """
        """
        self._start_msg()
        obj = self.simple_func.obj
        pf = self.cls(obj=obj)
        self.assertEqual(pf.name, obj.__name__)
        self.assertIn(f"def {obj.__name__}", pf.src)

    def test_init_with_src(self):
        """
        """
        self._start_msg()
        src = self.simple_func.src
        name = self.simple_func.name
        pf = self.cls(src=src, name=name)
        self.assertEqual(pf.name, name)
        self.assertIn(f"def {name}", pf.src)

    def test_tree_is_module(self):
        """
        """
        self._start_msg()
        tree = self.pf_simple_func.tree
        self.assertEqual(tree.type, "file_input")

    def test_func_node_type(self):
        """
        """
        src = self.simple_func.src
        name = self.simple_func.name
        pf = self.cls(src=src, name=name)
        func_node = pf.func
        self.assertEqual(func_node.type, "funcdef")
        self.assertEqual(func_node.name.value, name)

    def test_nodes_and_codes(self):
        """
        """
        pf = self.pf_simple_func
        name = self.simple_func.name
        nodes = pf.nodes
        codes = pf.codes
        self.assertEqual(nodes.func.name.value, name)
        self.assertIn(f"def {name}", codes.sig)

    def test_indent_and_indent_size(self):
        """
        """
        self._start_msg()
        pf = self.pf_simple_func
        indent = pf.indent
        size = pf.indent_size
        self.assertIsInstance(indent, str)
        self.assertEqual(len(indent), size)

    def test_mk_sig_subset(self):
        """
        """
        self._start_msg()
        pf = self.pf_simple_func
        name = self.pf_simple_func.name
        sig = pf.mk_sig(["kw_def", "name"])
        self.assertTrue(sig.startswith("def"))
        self.assertIn(name, sig)

    def test_as_ntup_default(self):
        """
        """
        self._start_msg()
        pf = self.pf_simple_func
        name = self.pf_simple_func.name
        tup = pf.as_ntup()
        self.assertIn(name, tup.sig)
        self.assertIn("Return the square", tup.doc)
        self.assertIn("return", tup.body)

    def test_as_ntup_with_doc_attr(self):
        """
        """
        self._start_msg()
        obj = self.simple_func.obj
        pf = self.cls(obj=obj)
        tup = pf.as_ntup()
        tup = pf.as_ntup(use_doc_attr=True)
        self.assertEqual(tup.doc.strip(), obj.__doc__)

    def test_decorators_present(self):
        """
        """
        self._start_msg()
        obj = self.decor_func.obj
        pf = self.cls(obj=obj)
        self.assertTrue(pf.codes.decor.startswith("@trace"))

    def test_suite_doc_and_body(self):
        """
        """
        self._start_msg()
        pf = self.pf_simple_func
        doc = pf.codes.doc
        body = pf.codes.body
        self.assertIn("Return the square", doc)
        self.assertIn("return x", body)

    def test_signature_with_newlines(self):
        """
        """
        self._start_msg()
        obj = self.simple_func.obj
        name = self.simple_func.name
        pf = self.cls(obj=obj)
        sig = pf.codes.sig
        self.assertIn(f"def {name}", sig)
        self.assertIn("(x)", sig)

    def test_errors_on_double_input(self):
        """
        """
        self._start_msg()
        obj = self.simple_func.obj
        name = self.simple_func.name
        src = self.simple_func.src

        with self.assertRaises(ValueError):
            ParsedFunc(obj=obj, src=src)

        with self.assertRaises(ValueError):
            ParsedFunc(obj=None, src=None)

        with self.assertRaises(ValueError):
            ParsedFunc(src=src)

class TestModuleDefs(BaseTestCase):
    """
    """
    _only_in_debug = [
            #'test_cls_or_func_defs',
            #'test_imports',
            #'test_variables',
            'test_defs',
            ]

    def setUp(self):
        self.cls = ModuleDefs

        self.simple_mod = ExampleObj(
                obj=eg_module,
                name='eg_module',
                src=get_mod_src(eg_module),
                )

    def test_cls_or_func_defs(self):
        """
        """
        self._start_msg()
        c = self.cls(
                name=self.simple_mod.name, 
                src=self.simple_mod.src)
        res = c.cls_or_func_defs
        #pp.pprint(res, width=40)

        expected = {
                'Greeter': '<Class: Greeter',
                'Greeter.__init__': '<Function: __init__',
                'Greeter.greet': '<Function: greet',
                'func_with_import': '<Function: func_with_import',
                'func_with_vardef': '<Function: func_with_vardef',
                'say_hello': '<Function: say_hello',
                'square': '<Function: square',
                'trace': '<Function: trace',
                'trace.wrapper': '<Function: wrapper',
                 }
        for k, v in expected.items():
            assert k in res, f"Key not found: '{k}'"
            value = res[k]
            assert str(value).startswith(v), (
                    f"Object does not match\n"
                    f"Key: {k}\n"
                    f"Expected: {v}\n"
                    f"Got: {value}\n"
                    )
            res.pop(k)
        assert len(res) == 0, (
                f"Unable to process all keys/values\n"
                f"{res}")

    def test_imports(self):
        """
        """
        self._start_msg()
        c = self.cls(
                name=self.simple_mod.name, 
                src=self.simple_mod.src)
        res = c.imports
        #pp.pprint(res, width=40)

        expected = {
                'annotations': '<ImportFrom: from __future__ import annotations',
                'defaultdict': '<ImportFrom: from collections import (     defaultdict,     namedtuple as nt, )',
                'func_with_import.pp': '<ImportName: import pprint as pp',
                'nt': '<ImportFrom: from collections import (     defaultdict,     namedtuple as nt, )',
                'operating_system': '<ImportName: import os as operating_system',
                'sqrt': '<ImportFrom: from math import sqrt',
                'sys': '<ImportName: # --- Variations of import statements import sys',
                'wraps': '<ImportFrom: from functools import wraps',
                }

        for k, v in expected.items():
            assert k in res, f"Key not found: '{k}'"
            value = res[k]
            assert str(value).startswith(v), (
                    f"Object does not match\n"
                    f"Key: {k}\n"
                    f"Expected: {v}\n"
                    f"Got: {value}\n"
                    )
            res.pop(k)
        assert len(res) == 0, (
                f"Unable to process all keys/values\n"
                f"{res}")

    def test_variables(self):
        """
        """
        self._start_msg()
        c = self.cls(
                name=self.simple_mod.name, 
                src=self.simple_mod.src)
        res = c.variables
        #pp.pprint(res, width=40)

        expected = {
                'PI': 'PythonNode(simple_stmt, [<ExprStmt: # --- Module level constants PI = 3.14159',
                'func_with_vardef.y': 'PythonNode(simple_stmt, [<ExprStmt: y = x',
                'trace.wrapper.result': 'PythonNode(simple_stmt, [<ExprStmt: result = func(*args, **kwargs)',
                 }
        for k, v in expected.items():
            assert k in res, f"Key not found: '{k}'"
            value = res[k]
            assert str(value).startswith(v), (
                    f"Object does not match\n"
                    f"Key: {k}\n"
                    f"Expected: {v}\n"
                    f"Got: {value}\n"
                    )
            res.pop(k)
        assert len(res) == 0, (
                f"Unable to process all keys/values\n"
                f"{res}")

    def test_defs(self):
        """
        """
        self._start_msg()
        c = self.cls(
                name=self.simple_mod.name, 
                src=self.simple_mod.src)
        res = c.defs
        #pp.pprint(res, width=40)
        expected = {
            'Greeter': '<Class: Greeter',
            'Greeter.__init__': '<Function: __init__',
            'Greeter.greet': '<Function: greet',
            'PI': 'PythonNode(simple_stmt, [<ExprStmt: # --- Module level constants PI = 3.14159',
            'annotations': '<ImportFrom: from __future__ import annotations',
            'defaultdict': '<ImportFrom: from collections import (     defaultdict,     namedtuple as nt, )',
            'func_with_import': '<Function: func_with_import',
            'func_with_import.pp': '<ImportName: import pprint as pp',
            'func_with_vardef': '<Function: func_with_vardef',
            'func_with_vardef.y': 'PythonNode(simple_stmt, [<ExprStmt: y = x',
            'nt': '<ImportFrom: from collections import (     defaultdict,     namedtuple as nt, )',
            'operating_system': '<ImportName: import os as operating_system',
            'say_hello': '<Function: say_hello',
            'sqrt': '<ImportFrom: from math import sqrt',
            'square': '<Function: square',
            'sys': '<ImportName: # --- Variations of import statements import sys',
            'trace': '<Function: trace',
            'trace.wrapper': '<Function: wrapper',
            'trace.wrapper.result': 'PythonNode(simple_stmt, [<ExprStmt: result = func(*args, **kwargs)',
            'wraps': '<ImportFrom: from functools import wraps',
            }
        for k, v in expected.items():
            assert k in res, f"Key not found: '{k}'"
            value = res[k]
            assert str(value).startswith(v), (
                    f"Object does not match\n"
                    f"Key: {k}\n"
                    f"Expected: {v}\n"
                    f"Got: {value}\n"
                    )
            res.pop(k)
        assert len(res) == 0, (
                f"Unable to process all keys/values\n"
                f"{res}")

def main(verbosity=2, *args, **kargs):
    cls_lst = [
        TestParsedFunc,
        TestModuleDefs,
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

