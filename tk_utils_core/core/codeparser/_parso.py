"""
Parsers for Python functions using `parso`.

"""
from __future__ import annotations

from functools import cached_property
from typing import Callable
from collections import namedtuple
import inspect

import parso

from ..messages.formatters import dedent_by


class _ParsedFuncNodes:
    """
    Extracts structural components (signature, suite, docstring, body)
    from a `parso` function definition node.

    This class is used internally by `ParsedFunc` to break down
    the tree representation of a function into its semantic parts.
    """

    SIG_ATTRS = [
        'kw_def',
        'name',
        'parms',
        'arrow',
        'annotation',
        'colon',
    ]

    def __init__(self, func: parso.python.tree.Function):
        """
        Parameters
        ----------
        func : parso.python.tree.Function
            A parso Function node representing a function definition.
        """
        self.func = func

    @cached_property
    def parts(self) -> namedtuple:
        """
        Parse and return the core components of the function signature
        and suite as a namedtuple.

        Returns
        -------
        namedtuple
            A namedtuple with attributes:
            'kw_def', 'name', 'parms', 'arrow', 'annotation',
            'colon', 'suite'.
        """
        # order matters here
        attrs = self.SIG_ATTRS + ['suite']
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

        return namedtuple('FuncParts', attrs)(**kargs)

    @cached_property
    def suite(self) -> namedtuple:
        """
        Parse the function body suite into its components.

        Returns
        -------
        namedtuple
            A namedtuple with attributes:
            'newlines', 'doc', and 'body'.
        """
        suite = self.parts.suite

        attrs = ['newlines', 'doc', 'body']
        ntup = namedtuple('SuiteParts', attrs)
        kargs = {x: None for x in attrs}

        if suite is None:
            return ntup(**kargs)

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
        return ntup(**kargs)

    def mk_sig_nodes(self, attrs: list[str] | None = None):
        """
        Return selected signature-related child nodes.

        Parameters
        ----------
        attrs : list of str, optional
            Subset of keys from SIG_ATTRS to include. If None, includes all.

        Returns
        -------
        list of parso.tree.Node
            The corresponding nodes in order.
        """
        if attrs is None:
            attrs = self.SIG_ATTRS

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


class ParsedFunc:
    """
    Parses a Python function into structured components using `parso`.

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
            self.src = inspect.getsource(obj)
            self.name = self.obj.__name__
        elif name is None:
            raise ValueError("Parm `name` must not be None if `src` is not None")
        else:
            self.name = name
            self.src = src
            self.obj = None

    @cached_property
    def tree(self) -> parso.python.tree.Module:
        """
        Returns
        -------
        parso.python.tree.Module
            The parsed syntax tree from `parso`.
        """
        return parso.parse(self.src)

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

    def as_ntup(
            self,
            dedent: bool = True,
            use_doc_attr: bool = False,
            ) -> namedtuple:
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
        namedtuple
            A namedtuple with fields: `decor`, `sig`, `doc`, `body`.
        """
        attrs = ['decor', 'sig', 'doc', 'body']
        ntup = namedtuple('FuncParts', attrs)
        kargs = {}
        for attr in attrs:
            value = getattr(self.codes, attr)
            if dedent:
                value = dedent_by(value, self.indent_size)
            kargs[attr] = value

        if use_doc_attr is True and self.obj is not None:
            kargs['doc'] = self.obj.__doc__
        return ntup(**kargs)

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


