""" 
Utilities to setup and configure PyCharm
         
"""
from __future__ import annotations

import pathlib
from functools import cached_property
from collections import namedtuple
import copy as _copy
from types import SimpleNamespace

from tk_utils_core.defaults import defaults
from tk_utils_core.messages import dirtree
from tk_utils_core.fstools import walk
from tk_utils_core.converters import (
        to_namespace, 
        as_set,
        as_path,
        )
from tk_utils_core.core.constants import POSIX
from tk_utils_core.mappings import map_dot_update
from tk_utils_core.structs import (
        obj_dot_update, 
        obj_dot_subset,
        obj_dot_get,
        )

def has_idea_folder(pth: pathlib.Path) -> bool:
    """
    True if the folder `pth` has a .idea sub-folder
    """
    return pth.is_dir() and pth.joinpath('.idea').is_dir()

def all_parents(path: pathlib.Path) -> list[pathlib.Path]:
    """
    Return a list of all parent directories of a relative path, 
    including '.' (the current directory) and the path itself.

    Parameters
    ----------
    path : Path
        A relative Path object.

    Returns
    -------
    list of Path
        All parents from '.' up to the full path, in ascending order.
    """
    if path.is_absolute():
        raise ValueError("Path must be relative")

    parts = list(path.parents)[::-1]  # from shallow to deep
    return [pathlib.Path('.')] + parts + [path]


class TreeChecker:
    """
    Ensure the proper location of files and folders relative to a base folder

    Parameters
    ----------
    ref_dir: pathlib.Path
        Reference folder (meant to be the location of tk_utils)

        <PYCHARM_PRJ_FOLDER>/
        |
        |__ tk_utils/           <- Reference folder (root)


    """

    def __init__(
            self,
            ref_dir: pathlib.Path,
            ):
        self.ref_dir = as_path(ref_dir)


        if not self.ref_dir.is_dir():
            raise NotADirectoryError(
                    f"Not an existing directory: {self.ref_dir}")

        self._toolkit_validated = False

    @cached_property
    def bin_dirname(self):
        """
        """
        return 'bin' if POSIX is True else 'Scripts'

    @cached_property
    def py_execname(self):
        """
        """
        return 'python' if POSIX is True else 'python.exe'

    @cached_property
    def dirnames(self):
        return defaults.pycharm.dirnames

    @cached_property
    def expected_root(self) -> pathlib.Path:
        return pathlib.Path('.', self.dirnames.prj_root)

    @cached_property
    def actual_root(self) -> pathlib.Path:
        return self.ref_dir.parent

    @cached_property
    def actual_rroot(self) -> pathlib.Path:
        return self.actual_root.parent


    def _mk_tree(self, root: pathlib.Path, tk_root: pathlib.Path):
        """
        Parameters
        ----------
        root: pathlib.Path
            Assumed to be the PyCharm project folder
        """
        venv_root = root.joinpath(self.dirnames.venv)
        venv_root_bin = venv_root.joinpath(self.bin_dirname)

        out = {
            'toolkit/': {
                'loc': root,
                'is_dir': True,
                },
            'toolkit/tk_utils/': {
                'loc': tk_root,
                'is_dir': True,
                },
            'toolkit/_backup/': {
                'loc': root.joinpath(self.dirnames.backup),
                'is_dir': True,
                },
            'toolkit/_dropbox/': {
                'loc': root.joinpath(self.dirnames.dropbox),
                'is_dir': True,
                },
            'toolkit/.idea/': {
                'loc': root.joinpath('.idea'),
                'is_dir': True,
                },
            'toolkit/.venv/': {
                'loc': venv_root,
                'is_dir': True,
                },
            'toolkit/.venv/bin/': {
                'loc': venv_root_bin,
                'is_dir': True,
                },
            'toolkit/.venv/bin/pip': {
                'loc': venv_root_bin.joinpath('pip'),
                'is_dir': False,
                },
            'toolkit/.venv/bin/python': {
                'loc': venv_root_bin.joinpath(self.py_execname),
                'is_dir': False,
                },
            }
        for mod in defaults.pycharm.tk_utils.github.modules:
            out[f'toolkit/tk_utils/{mod}'] = {
                    'loc': tk_root.joinpath(mod),
                    'is_dir': False,
                    }
        return {k: SimpleNamespace(**v) for k, v in out.items()}

    def _add_parents(self, paths, root):
        """
        """
        paths = as_set(paths)
        parents = set()
        for pth in paths:
            for p in list(pth.parents)[::-1]:
                if p.is_relative_to(root) and p not in parents:
                    parents.add(p)
        return paths | parents


    @cached_property
    def expected_tree(self):
        tk_root = self.expected_root.joinpath(self.dirnames.tk_utils)
        return self._mk_tree(self.expected_root, tk_root)

    @cached_property
    def actual_tree(self):
        return self._mk_tree(self.actual_root, self.ref_dir)


    def _get_dirs(self, tree, root):
        dirs = [v.loc for _, v in tree.items() if v.is_dir]
        dirs = self._add_parents(dirs, root)
        dirs = [x.relative_to(root) for x in dirs]
        return [str(x) for x in dirs]

    @cached_property
    def expected_dirs(self):
        # always relative
        root = self.expected_root
        tree = self.expected_tree
        return self._get_dirs(root=root, tree=tree)

    @cached_property
    def actual_dirs(self):
        root = self.actual_root
        tree = self.actual_tree
        return self._get_dirs(root=root, tree=tree)


    def _subset_tree(
            self,
            tree: dict,
            includes: list[str] | None = None,
            excludes: list[str] | None = None,
            ):
        """
        """
        excludes = as_set(excludes, none_as_empty=True)
        
        if includes is None:
            includes = set(x for x in tree if x not in excludes)
        else:
            includes = as_set(includes)
            includes = set(x for x in includes if x not in excludes)

        # Make sure there are no misspellings in includes
        tree = {x: tree[x] for x in includes}
        return tree


    def _get_paths(self, tree, root):
        """
        """
        paths = set(v.loc for _, v in tree.items())
        paths = self._add_parents(paths, root)
        return sorted(paths)

    def mk_expected_dirtree(
            self, 
            notes: dict | None = None,
            includes: list[str] | None = None,
            excludes: list[str] | None = None,
            ):
        """
        """
        tree = self._subset_tree(
                self.expected_tree,
                includes=includes, 
                excludes=excludes)
        paths = self._get_paths(tree, root=self.expected_root)
        return dirtree(
                root=self.expected_root, 
                dirs=self.expected_dirs,
                paths=paths, 
                notes=notes, 
                note_align_width=defaults.pp.width)

    def mk_actual_dirtree(
            self, 
            notes: dict | None = None,
            includes: list[str] | None = None,
            excludes: list[str] | None = None,
            ):
        """
        """
        root = self.actual_root
        tree = self._subset_tree(
                self.actual_tree,
                includes=includes, 
                excludes=excludes)
        paths = self._get_paths(tree, root=root)
        return dirtree(
                root=root, 
                dirs=self.expected_dirs,
                paths=paths, 
                notes=notes, 
                note_align_width=defaults.pp.width)

    def validate_toolkit(self):
        """
        Checks if actual toolkit has a valid .idea folder
        """
        if (defaults.pycharm.validate_paths is False 
            or self._toolkit_validated is True):
            return 

        if not has_idea_folder(self.actual_root):
            msg = [
                    '',
                    f"{self.dirnames.tk_utils} not under PyCharm's project folder",
                    '',
                    ]
            edirtree = self.mk_expected_dirtree(
                    includes='toolkit/tk_utils/',
                    notes={
                        'tk_utils': 'tk_utils should be here',
                        '.': 'PyCharm project folder',
                        },
                    )
            
            name = self.ref_dir.name 
            adirtree = self.mk_actual_dirtree(
                    includes='toolkit/tk_utils/',
                    notes={
                        name: 'Folder containing this module',
                        '.': 'NOT PyCharm project folder',
                        },
                    )
            msg.extend([
                'EXPECTED:',
                '',
                edirtree,
                '',
                'GOT:',
                '',
                adirtree,
                '',
                ])

            raise Exception('\n'.join(msg))


