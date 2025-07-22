"""
Parsers for Python objects using AST

"""
from __future__ import annotations

import ast
from functools import cached_property

from tk_utils_core.core.structs import (
        AttrDict,
        BaseDataModel,
        )
from tk_utils_core.core.converters import as_set


def get_import_names(node: ast.stmt) -> list[str]:
    """
    Extract import names from an import statement node.

    Parameters
    ----------
    node : ast.stmt
        A node that may be an `ast.Import` or `ast.ImportFrom` statement.

    Returns
    -------
    list of str
        The fully qualified import names found in the statement.
    """
    if isinstance(node, ast.Import):
        names = [alias.name for alias in node.names]
    elif isinstance(node, ast.ImportFrom):
        base = '.' * node.level + (node.module or '')
        names = [f"{base}.{alias.name}" for alias in node.names]
    else:
        names = []
    return names


class ParsedFunc(BaseDataModel):
    """
    """
    name: str
    src: str
    node: ast.AST

def get_funcs(
        cnts: str, 
        tree: ast.Node | None = None, 
        ignore_underscored: bool = True) -> dict:
    """
    Return all functions in a module, including nested ones.

    Function names are qualified by their parent structure (e.g. 'outer.inner').

    """
    tree = ast.parse(cnts) if not tree else tree
    out = {}
    def visit(node: ast.AST, parents: list[str]):
        if isinstance(node, ast.FunctionDef):
            if ignore_underscored is True and node.name.startswith('_'):
                return
            current_name = '.'.join(parents + [node.name])
            out[current_name] = ParsedFunc(
                    name=current_name,
                    src=ast.get_source_segment(cnts, node),
                    node=node)
            new_parents = parents + [node.name]
        else:
            new_parents = parents
        for child in ast.iter_child_nodes(node):
            visit(child, new_parents)
    visit(tree, [])
    return out


class ParsedModule:
    """
    """

    def __init__(
            self, 
            cnts: str,
            ignore_underscored: bool = False,
            ):
        self.cnts = cnts
        self.ignore_underscored = ignore_underscored

    @cached_property
    def tree(self):
        """
        Parsed AST tree of the file contents.

        Returns
        -------
        ast.Module
            AST tree of the file.

        Raises
        ------
        Exception
            If the file is empty.
        SyntaxError
            If the file contents cannot be parsed.
        """
        if self.cnts.strip() == '':
            raise Exception(f"File '{self.name}' is empty")
        try:
            return ast.parse(self.cnts)
        except SyntaxError as e:
            raise SyntaxError(
                f"Could not parse the contents of '{self.name}'\n{e}"
            ) from e

    def get_funcs(self, ignore_underscored: bool | None = None) -> dict:
        """ use AST to get function definitions
        """
        if ignore_underscored is None:
            ignore_underscored = self.ignore_underscored
        return get_funcs(cnts=self.cnts, tree=self.tree,
                        ignore_underscored=ignore_underscored)

    def get_attrs(
            self, 
            include: set | None = None,
            ignore_underscored: bool | None = None,
            ) -> dict:
        """ Returns the module attributes using ast
        """
        if ignore_underscored is None:
            ignore_underscored = self.ignore_underscored
        include = as_set(include, none_as_empty=False)
        out = {}
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Assign):
                for tgt in node.targets:
                    if not hasattr(tgt, 'id'):
                        continue
                    if include and tgt.id not in include:
                        continue
                    if ignore_underscored and tgt.id.startswith('_'):
                        continue
                    out[tgt.id] = ast.get_source_segment(self.cnts, node)
        return out


    @cached_property
    def funcs_names(self) -> set[str]:
        """
        All function names defined in the module.

        Returns
        -------
        set of str
            Fully qualified names of functions in the file.
        """
        return set(sorted(self.funcs.keys()))

    @cached_property
    def funcs(self) -> dict[str,ast.node]:
        """
        All function names defined in the module.

        Returns
        -------
        set of str
            Fully qualified names of functions in the file.
        """
        return self.get_funcs(
                ignore_underscored=self.ignore_underscored)


    @cached_property
    def imports(self) -> set[str]:
        """
        All import names in the module.

        Returns
        -------
        set of str
            Fully qualified import names used in the file.
        """
        nodes = [
            node for node in ast.walk(self.tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ]
        return set(chain.from_iterable(get_import_names(node) for node in nodes))

