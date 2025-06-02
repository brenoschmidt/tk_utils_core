""" 
Directory trees

         
"""
from __future__ import annotations

import pathlib
from functools import cached_property
from typing import Iterable


BRANCH_SEP: str = '|   '
BRANCH_END: str = '|__ '
DIR_END: str = '/'


def _as_path(pth: str | pathlib.Path) -> pathlib.Path:
    """
    Convert input to a pathlib.Path if it is not already one.

    Parameters
    ----------
    pth : str | pathlib.Path
        The path to convert.

    Returns
    -------
    pathlib.Path
        The converted path.
    """
    return pathlib.Path(pth) if not isinstance(pth, pathlib.Path) else pth

class Branch:
    """
    Represents a single entry (file or directory) in the tree.
    """

    def __init__(
        self,
        root: pathlib.Path,
        pth: pathlib.Path,
        note: str | None = None,
        ):
        self.root = root
        self.pth = pth
        self.rpth = pth.relative_to(root)
        self.parts = self.rpth.parts
        self.is_dir = pth.is_dir()
        self.key = '/'.join(self.parts)
        if self.key == '':
            self.key = '.'
        self.note = note
        self.name = pth.name
        self.branch_level = len(self.parts) - 1
        self.branch = None

    def fmt_branch(self) -> None:
        """
        Format this branch as a string representing its location in the tree.

        The result is stored in the `branch` attribute.
        """
        name = f"{self.name}{DIR_END}" if self.is_dir else self.name
        if len(self.parts) == 0:
            self.branch = name
        else:
            self.branch = BRANCH_SEP * self.branch_level + BRANCH_END + name

class DirTree:
    """
    Constructs a directory tree representation with optional notes and
    directory overrides.

    """

    def __init__(
        self,
        root: str | pathlib.Path,
        paths: Iterable[str | pathlib.Path],
        dirs: Iterable[str] | None = None,
        notes: dict[str, str] | None = None,
        note_align_width: int = 0,
    ):
        self.root = _as_path(root)
        self.paths = [_as_path(x) for x in paths]
        self.notes = {} if notes is None else notes
        self.dirs = set(dirs) if dirs is not None else set()
        self.dirs = set(str(x) for x in self.dirs)
        self.dirs.add('.') # root is always a dir
        self.note_align_width = note_align_width

    @cached_property
    def branches(self) -> dict[pathlib.Path, Branch]:
        """
        Create and cache a dictionary of Branch objects for all paths.

        Returns
        -------
        dict[pathlib.Path, Branch]
            A mapping from full paths to their corresponding Branch.
        """
        out = {}
        for pth in self.paths:
            b = Branch(pth=pth, root=self.root)
            if b.key in self.dirs:
                b.is_dir = True
            if b.key in self.notes:
                b.note = self.notes[b.key]
            b.fmt_branch()
            out[pth] = b
        return out

    def make(self) -> str:
        """
        Generate the full tree string with optional aligned notes.

        Returns
        -------
        str
            The formatted directory tree.
        """
        tree = []
        max_length = max(len(b.branch) for _, b in self.branches.items())
        max_length = min(self.note_align_width, max_length)

        for pth in self.paths:
            b = self.branches[pth]
            branch = b.branch.ljust(max_length)
            if b.note is not None:
                branch = f"{branch} <- {b.note}"
            tree.append(branch)

        return '\n'.join(tree)

def dirtree(
    root: pathlib.Path,
    paths: Iterable[str | pathlib.Path],
    dirs: Iterable[str] | None,
    notes: dict[str, str] | None,
    excludes: Iterable[str | pathlib.Path] | None = None,
    note_align_width: int = 0) -> str:
    """
    Generate a formatted directory tree string from the given paths.

    Parameters
    ----------
    root : pathlib.Path
        The root folder for computing relative paths.

    paths : Iterable[str | pathlib.Path]
        A list of paths to include in the tree.

    dirs : Iterable[str], optional
        A list of relative paths that should be treated as directories.

    notes : dict[str, str], optional
        Mapping of relative paths to annotation strings.

    note_align_width : int
        Maximum width used for aligning notes in the output.

    excludes: Iterable[str], optional
        If given, exclude any relative path or ancestors with these names 
        are excluded

    Returns
    -------
    str
        A formatted directory tree.
    """
    root = _as_path(root)
    paths = [_as_path(x) for x in paths]

    if excludes is not None:
        if isinstance(excludes, str):
            excludes = set([excludes])
        else:
            excludes = set(excludes)
        paths = [x for x in paths if \
                set(x.relative_to(root).parts).isdisjoint(excludes)]
    tree = DirTree(
        root=root,
        paths=paths,
        dirs=dirs,
        notes=notes,
        note_align_width=note_align_width,
    )
    return tree.make()


