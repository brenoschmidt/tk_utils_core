"""
Parsers for Python objects using parso

"""
from __future__ import annotations

from collections import namedtuple
from functools import cached_property
from typing import Callable
import dataclasses as dc
import inspect

import parso

from ..messages.formatters import dedent_by

FUNC_SIG_ATTRS = [
    'kw_def',
    'name',
    'parms',
    'arrow',
    'annotation',
    'colon',
]

FuncParts = namedtuple('FuncParts', FUNC_SIG_ATTRS + ['suite'])
ParsedFuncNtup = namedtuple('ParsedFuncNtup', ['decor', 'sig', 'doc', 'body'])
FuncSuiteParts = namedtuple('FuncSuiteParts', ['newlines', 'doc', 'body'])



class _BaseParsedCode:

    def __init__(self, name: str, src: str):
        """
        Parameters
        ----------
        name : str
            Name of the object

        src : str
            Source code containing the object definition
        """
        self.name = name
        self.src = src

    @cached_property
    def tree(self) -> parso.python.tree.Module:
        """
        Returns
        -------
        parso.python.tree.Module
            The parsed syntax tree from `parso`.
        """
        return parso.parse(self.src)


class _ParsedFuncNodes:
    """
    Extracts structural components (signature, suite, docstring, body)
    from a `parso` function definition node.

    This class is used internally by `ParsedFunc` to break down
    the tree representation of a function into its semantic parts.
    """

    def __init__(self, func: parso.python.tree.Function):
        """
        Parameters
        ----------
        func : parso.python.tree.Function
            A parso Function node representing a function definition.
        """
        self.func = func

    @cached_property
    def parts(self) -> FuncParts:
        """
        Parse and return the core components of the function signature
        and suite as a namedtuple.

        Returns
        -------
        FuncParts: 
            A namedtuple with attributes:
            'kw_def', 'name', 'parms', 'arrow', 'annotation',
            'colon', 'suite'.
        """
        # order matters here
        attrs = FuncParts._fields
        kargs = {x: None for x in attrs}

        kargs.update({
            'kw_def': self.func.children[0],
            'name': self.func.children[1],
            'parms': self.func.children[2],
        })

        # Remaining children
        # the next element is either the : operator or -> annotation
        arr_or_colon = self.func.children[3]
        children = [x for x in self.func.children[4:]]

        if arr_or_colon.type == 'operator' and arr_or_colon.value == ':':
            kargs.update({
                'colon': arr_or_colon,
                'suite': children.pop(0),
            })
        else:
            kargs.update({
                'arrow': arr_or_colon,
                'annotation': children.pop(0),
            })
            kargs['colon'] = children.pop(0)
            kargs['suite'] = children.pop(0)

        if len(children) > 0:
            raise Exception(f"Function children not parsed: {children}")

        return FuncParts(**kargs)

    @cached_property
    def suite(self) -> FuncSuiteParts:
        """
        Parse the function body suite into its components.

        Returns
        -------
        FuncSuiteParts
            A namedtuple with attributes:
            'newlines', 'doc', and 'body'.
        """
        suite = self.parts.suite

        kargs = {x: None for x in FuncSuiteParts._fields}

        if suite is None:
            return FuncSuiteParts(**kargs)

        children = [x for x in suite.children]

        newlines = []
        while True and len(children) > 0:
            child = children[0]
            if child.type == 'newline':
                newlines.append(child)
                children = children[1:]
            elif child.type == 'simple_stmt':
                first_leaf = child.children[0]
                if first_leaf.type == 'string':
                    kargs['doc'] = child
                    children = children[1:]
                    break
            else:
                break
        if len(newlines) > 0:
            kargs['newlines'] = newlines

        if len(children) > 0:
            kargs['body'] = children
        return FuncSuiteParts(**kargs)

    def mk_sig_nodes(self, attrs: list[str] | None = None):
        """
        Return selected signature-related child nodes.

        Parameters
        ----------
        attrs : list of str, optional
            Subset of keys from FUNC_SIG_ATTRS to include. 
            If None, includes all.

        Returns
        -------
        list of parso.tree.Node
            The corresponding nodes in order.
        """
        attrs = FUNC_SIG_ATTRS if attrs is None else attrs
        parts = [getattr(self.parts, attr) for attr in attrs]
        return [x for x in parts if x]

    @cached_property
    def sig(self) -> list[parso.tree.Node]:
        """
        Returns
        -------
        list of parso.tree.Node
            Nodes forming the function signature and any trailing newlines.
        """
        parts = self.mk_sig_nodes()
        if self.suite.newlines:
            parts.extend(self.suite.newlines)
        return parts

    @cached_property
    def doc(self) -> parso.tree.Node | None:
        """
        Returns
        -------
        parso.tree.Leaf or None
            Node containing the docstring, if present.
        """
        return self.suite.doc

    @cached_property
    def body(self) -> list[parso.tree.BaseNode] | None:
        """
        Returns
        -------
        list of parso.tree.BaseNode or None
            Function body statements, excluding the docstring.
        """
        return self.suite.body

    @cached_property
    def decor(self) -> list[parso.tree.Decorator] | None:
        """
        Returns
        -------
        list of parso.tree.Decorator or None
            List of decorator nodes if present.
        """
        out = self.func.get_decorators()
        return out if len(out) > 0 else None

class _ParsedFuncCodes:
    """
    Produces source code strings for components extracted by `_ParsedFuncNodes`.

    This class provides the string equivalents of decorators, signature,
    docstring, and body.
    """

    def __init__(self, nodes: _ParsedFuncNodes):
        """
        Parameters
        ----------
        nodes : _ParsedFuncNodes
            Parsed structure of a function's components.
        """
        self._nodes = nodes

    @cached_property
    def decor(self) -> str:
        """
        Returns
        -------
        str
            Concatenated decorator source code, or empty string if none.
        """
        nodes = self._nodes.decor
        return ''.join(n.get_code() for n in nodes) if nodes else ''

    @cached_property
    def sig(self) -> str:
        """
        Returns
        -------
        str
            Source code for the function signature and trailing newlines.
        """
        nodes = self._nodes.sig
        return ''.join(n.get_code() for n in nodes)

    @cached_property
    def doc(self) -> str:
        """
        Returns
        -------
        str
            Docstring text, or empty string if not present.
        """
        node = self._nodes.doc
        return node.get_code() if node else ''

    @cached_property
    def body(self) -> str:
        """
        Returns
        -------
        str
            Function body code, excluding the docstring.
        """
        nodes = self._nodes.body
        return ''.join(n.get_code() for n in nodes) if nodes else ''

class ParsedFuncCode(_BaseParsedCode):
    """
    Parses the source code of a Python function into structured components
    using `parso`.

    This class allows introspection of decorators, signature, docstring,
    and body, and provides a method to return those parts as dedented strings.
    """

    def __init__(self, name: str, src: str):
        """
        Parameters
        ----------
        name : str
            Name of the function

        src : str
            Source code containing a function definition
        """
        super().__init__(name=name, src=src)


    @cached_property
    def func(self) -> parso.python.tree.Function:
        """
        Returns
        -------
        parso.python.tree.Function
            The node representing the function definition in the AST.

        Raises
        ------
        TypeError
            If the resolved node is not a Function.
        """
        func = next(
            node for node in self.tree.iter_funcdefs()
            if node.name.value == self.name
        )
        if not isinstance(func, parso.python.tree.Function):
            raise TypeError("Could not extract Function node from tree")
        return func

    @cached_property
    def nodes(self) -> _ParsedFuncNodes:
        """
        Returns
        -------
        _ParsedFuncNodes
            Structural components extracted from the function node.
        """
        return _ParsedFuncNodes(func=self.func)

    @cached_property
    def codes(self) -> _ParsedFuncCodes:
        """
        Returns
        -------
        _ParsedFuncCodes
            Source code strings extracted from structural nodes.
        """
        return _ParsedFuncCodes(nodes=self.nodes)

    @cached_property
    def indent(self) -> str:
        """
        Returns
        -------
        str
            A string with spaces representing the function's indentation.
        """
        return ' ' * self.indent_size

    @cached_property
    def indent_size(self) -> int:
        """
        Returns
        -------
        int
            Number of leading spaces on the line containing the `def` keyword.
        """
        for line in self.codes.sig.splitlines():
            if line.strip().startswith('def'):
                return len(line) - len(line.lstrip())
        # The following should not happen...
        return 0

    def mk_sig(self, attrs: list[str]) -> str:
        """
        Return a custom signature string composed of selected attributes.

        Parameters
        ----------
        attrs : list of str
            Subset of attributes from the function's parsed parts to include.

        Returns
        -------
        str
            Concatenated source code for the selected signature nodes.
        """
        nodes = self.nodes.mk_sig_nodes(attrs)
        return ''.join(n.get_code() for n in nodes)

class ParsedFunc(ParsedFuncCode):
    """
    Parse a Python function into structured components using `parso`.

    This class allows introspection of decorators, signature, docstring,
    and body, and provides a method to return those parts as dedented strings.
    """

    def __init__(
            self,
            obj: Callable | None = None,
            name: str | None = None,
            src: str | None = None,
            ):
        """
        Parameters
        ----------
        obj : Callable, optional
            A Python function object. If provided, `src` must be None.

        name : str, optional
            Name of the function. Required if `src` is provided.

        src : str, optional
            Source code containing a function definition. If provided,
            `obj` must be None.

        Raises
        ------
        ValueError
            If both `obj` and `src` are provided or both are None.
        """
        if obj is not None and src is not None:
            raise ValueError(
                    f"Parms `src` and `obj` cannot be both None")
        elif obj is not None and src is not None:
            raise ValueError(
                    f"One of `obj` and `src` must not be None")
        elif obj is not None:
            self.obj = obj
            src = inspect.getsource(obj)
            name = self.obj.__name__
        elif name is None:
            raise ValueError("Parm `name` must not be None if `src` is not None")
        else:
            self.obj = None

        super().__init__(src=src, name=name)

    def as_ntup(
            self,
            dedent: bool = True,
            use_doc_attr: bool = False,
            ) -> ParsedFuncNtup:
        """
        Return a namedtuple with function components as strings.

        Parameters
        ----------
        dedent : bool, default=True
            Whether to remove the function's base indentation from each part.

        use_doc_attr : bool, default=False
            If True and a function object was provided, uses its `__doc__`
            attribute instead of re-parsing the docstring.

        Returns
        -------
        ParsedFuncNtup
            A namedtuple with fields: `decor`, `sig`, `doc`, `body`.
        """
        kargs = {}
        for attr in ParsedFuncNtup._fields:
            value = getattr(self.codes, attr)
            if dedent:
                value = dedent_by(value, self.indent_size)
            kargs[attr] = value

        if use_doc_attr is True and self.obj is not None:
            kargs['doc'] = self.obj.__doc__
        return ParsedFuncNtup(**kargs)

class ModuleDefs(_BaseParsedCode):
    """
    Collection of definitions inside a module

    Notes
    -----
    The base class sets the following attributes

    self.name -> name
    self.src -> src
    self.tree -> parso.python.tree.module

    """

    def __init__(
            self, 
            name: str, 
            src: str,
            add_mod_prefix: bool = False):
        """
        Parameters
        ----------
        name : str
            Name of the module

        src : str
            Source code 
        """
        super().__init__(name=name, src=src)
        self.mod_prefix = name if add_mod_prefix else ''


    def get_cls_or_func(self, node, base, prefix):
        attrs = ['funcdef', 'classdef']
        for child in node._search_in_scope(*attrs):
            name = child.name.value
            key = f"{prefix}.{name}" if prefix else name
            base[key] = child 
            base = self.get_cls_or_func(node=child, base=base, prefix=name)
        return base


    @cached_property
    def cls_or_func_defs(self):
        """
        Return a dictionary mapping names to funcdef/classdef nodes
        """
        out = self.get_cls_or_func(
                node=self.tree, 
                base={}, 
                prefix=self.mod_prefix)
        return {x:out[x] for x in sorted(out)}

    @cached_property
    def cls_or_func_suites(self):
        """
        Return a dictionary mapping names to function suites (last children
        element
        """
        out = {}
        for name, node in self.cls_or_func_defs.items():
            out[name] = node.children[-1]
        return {x:out[x] for x in sorted(out)}

    def get_imports(self, node, base, prefix):
        """
        Return a map between names and import nodes
        """
        for child in node.iter_imports():
            for name_node in child.get_defined_names():
                name = name_node.value
                key = f"{prefix}.{name}" if prefix else name
                base[key] = child
        return base

    @cached_property
    def imports(self):
        """
        Return a map between names and import nodes
        """
        # Start with the tree
        out = self.get_imports(
                node=self.tree, 
                base={}, 
                prefix=self.mod_prefix)

        # Then func/classes
        for pfix, node in self.cls_or_func_defs.items():
            out = out | self.get_imports(
                    node=node, 
                    base=out,
                    prefix=pfix)
        return {x:out[x] for x in sorted(out)}


    def get_variables(self, node, base, prefix):
        """
        Return a map between names and variable definitions
        """
        if not hasattr(node, 'children'):
            return base
        for child in node.children:
            if child.type == 'simple_stmt':
                expr = child.children[0]
                if expr.type == 'expr_stmt':
                    lhs = expr.children[0]
                    if lhs.type == 'name':
                        name = lhs.value
                        key = f"{prefix}.{name}" if prefix else name
                        base[key] = child
        return base
    
    @cached_property
    def variables(self):
        """
        Return a map between names and variable definitions
        """
        out = self.get_variables(
                node=self.tree, 
                base={}, 
                prefix=self.mod_prefix)

        for pfix, node in self.cls_or_func_suites.items():
            out = out | self.get_variables(
                    node=node, 
                    base=out,
                    prefix=pfix)
        return {x:out[x] for x in sorted(out)}

    @cached_property
    def defs(self):
        """
        Return a dictionary mapping names to nodes. Includes functions,
        classes, imports, and vars
        """
        out = (self.cls_or_func_defs 
               | self.imports
               | self.variables)
        return {x:out[x] for x in sorted(out)}





