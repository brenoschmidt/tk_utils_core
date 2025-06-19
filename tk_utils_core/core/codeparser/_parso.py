""" 
Parsers based on parso

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
        self.func = func

    @cached_property
    def parts(self) -> namedtuple:
        """
        A namedtuple with the function children

        func.children can have either 4 or 6 elements:

        0. <Keyword: def>
        1. <Name>
        2. parameter list (including open-paren and close-paren <Operator>s)
        3. or 5. <Operator: :>
        4. or 6. Node() representing function body
        3. -> (if annotation is also present)
        4. annotation (if present)

        """
        # In order
        attrs =  self.SIG_ATTRS + [
                'suite',
                ]
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
            raise Exception(
                    f"Function children not parsed: {children}")

        return namedtuple('FuncParts', attrs)(**kargs)


    @cached_property
    def suite(self) -> namedtuple:
        """
        """
        suite = self.parts.suite

        attrs = [
            'newlines',
            'doc',
            'body',
            ]
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
        list[parso.tree.Node]:
            The nodes containing the function signature,
            excluding the docstring and body. Also include trailing
            newlines.
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
        parso.tree.Leaf or None:
            Leaf with the docstring (if present)
        """
        return self.suite.doc

    @cached_property
    def body(self) -> list[parso.tree.BaseNode] | None:
        """
        Returns
        -------
        list[parso.tree.BaseNode] or None:
            List of statement nodes in the body, excluding the docstring.
        """
        return self.suite.body

    @cached_property
    def decor(self) -> list[parso.tree.Decorator] | None:
        """
        Returns
        -------
        list[parso.tree.Decorator] or None:
            A list of decorator nodes if the function is decorated, 
            otherwise None.
        """
        out = self.func.get_decorators()
        return out if len(out) > 0 else None


class _ParsedFuncCodes:
    """
    """

    def __init__(self, nodes: _ParsedFuncNodes):
        self._nodes = nodes

    @cached_property
    def decor(self) -> str:
        """
        Returns
        -------
        str:
            Source code for all decorators, or empty string if none.
        """
        nodes = self._nodes.decor
        return ''.join(n.get_code() for n in nodes) if nodes else ''


    @cached_property
    def sig(self) -> str:
        """
        Returns
        -------
        str:
            Source code for the function signature
        """
        nodes = self._nodes.sig
        return ''.join(n.get_code() for n in nodes)


    @cached_property
    def doc(self) -> str:
        """
        Returns
        -------
        str 
            Docstring for the function
        """
        node = self._nodes.doc
        return node.get_code() if node else ''

    @cached_property
    def body(self) -> str:
        """
        Returns
        -------
        str:
            Source code for the function body, excluding docstring.
        """
        nodes = self._nodes.body
        return ''.join(n.get_code() for n in nodes) if nodes else ''

class ParsedFunc:
    """
    An object that inspects the source code of a Python function
    using `parso` to extract structural components.
    """

    def __init__(
            self,
            obj: Callable | None = None,
            name: str | None = None,
            src: str | None = None,
            ):
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
            raise ValueError(
                    f"Parm `name` must not be None if `src` is not None")
        else:
            self.name = name 
            self.src = src
            self.obj = None


    @cached_property
    def tree(self) -> parso.python.tree.Module:
        """
        Returns
        -------
        parso.python.tree.Module:
            Parso tree starting from the module
        """
        return parso.parse(self.src)

    @cached_property
    def func(self) -> parso.python.tree.Function:
        """
        Returns
        -------
        parso.python.tree.Function:
            The node representing the function definition
        """
        func = next(
            node for node in self.tree.iter_funcdefs()
            if node.name.value == self.name
        )
        if not isinstance(func, parso.python.tree.Function):
            raise TypeError(
                    f"Could not extract Function node from tree")
        return func

    @cached_property
    def nodes(self) -> _ParsedFuncNodes:
        return _ParsedFuncNodes(func=self.func)

    @cached_property
    def codes(self) -> _ParsedFuncCodes:
        return _ParsedFuncCodes(nodes=self.nodes)


    @cached_property
    def indent(self) -> str:
        """
        Return a string with the indentation of the 
        function signature
        """
        return ' '*self.indent_size

    @cached_property
    def indent_size(self) -> int:
        """
        Number of leading spaces on the line with the 'def' keyword.
        """
        for line in self.codes.sig.splitlines():
            if line.strip().startswith('def'):
                return len(line) - len(line.lstrip())
        return 0  # fallback (shouldn't happen)

    def as_ntup(
            self, 
            dedent: bool = True,
            use_doc_attr: bool = False,
            ) -> namedtuple:
        """
        Namedtuple with function parts
        """
        attrs = [
                'decor',
                'sig',
                'doc',
                'body',
                ]
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
        """
        nodes = self.nodes.mk_sig_nodes(attrs)
        return ''.join(n.get_code() for n in nodes)




