"""
Utilities for filtering files in a directory tree using flexible
inclusion and exclusion rules.


Notes
-----
- Should work cross-platform (both POSIX and Windows systems).

- Hidden files and directories can be excluded 

- Relies on pydantic models for type validation

- Inclusion/exclusion patterns are applied to names (not full paths).

- Case sensitivity defaults to the underlying platform 
  (case-insensitive on Windows).

"""
from __future__ import annotations

import os
import pathlib
import fnmatch
import re
from typing import Callable, Iterator, Iterable

from pydantic import field_validator

from .. import (
        structs,
        validators,
        constants,
        )
__all__ = [
        'FilterParms',
        'WalkParms',
        'walk',
        'add_parents',
        'add_parents_to_paths',
        ]

DFLT_IGNORE_CASE = not constants.POSIX  # Default value for ignore_case

def add_parents(pth: pathlib.Path, root: pathlib.Path) -> list[pathlib.Path]:
    """
    Return a list of paths from `pth` up to (but not including) `root`.

    The list is ordered from `root`-relative parent folders to `pth` itself.
    """
    rpth = pth.relative_to(root)
    rpaths = list(rpth.parents)[::-1] + [rpth]
    return [root / rel for rel in rpaths]

def add_parents_to_paths(
        items: list[pathlib.Path],
        root: pathlib.Path) -> list[pathlib.Path]:
    """
    For each path in `items`, add all of its parents up to (but excluding) `root`.

    Ensures no duplicates. The result is sorted for consistency.

    Parameters
    ----------
    items : list of Path
        The input paths to expand.

    root : Path
        The common root path. All returned paths will be below this.

    Returns
    -------
    list of Path
        All input paths plus their parents up to `root`, with duplicates removed.
    """
    all_paths = set()
    for pth in items:
        all_paths.update(add_parents(pth, root))
    return sorted(all_paths)

def _is_literal(pat: str) -> bool:
    return not any(ch in pat for ch in "*?[")


def _norm_case(s: str, ignore_case: bool) -> str:
    return s.casefold() if ignore_case else s


class Pattern(structs.BaseParms):
    def __init__(self, **data):
        super().__init__(**data)
        lit = set()
        rgx = set()
        for p in self.pats:
            norm = _norm_case(p, self.ignore_case)
            if _is_literal(p):
                lit.add(norm)
            else:
                translated = fnmatch.translate(p)
                compiled = re.compile(translated, re.I if self.ignore_case else 0).fullmatch
                rgx.add(compiled)
        object.__setattr__(self, 'literals', lit)
        object.__setattr__(self, 'regexes', rgx)
    pats: list[str]
    ignore_case: bool
    literals: set[str] = set()
    regexes: set[Callable[[str], re.Match[str] | None]] = set()

    @field_validator('pats', mode='before')
    @classmethod
    def ensure_list(cls, v):
        if v is None:
            return []
        return [v] if isinstance(v, str) else list(v)


    def __call__(self, name: str) -> bool:
        norm = _norm_case(name, self.ignore_case)
        return norm in self.literals or any(rgx(norm) for rgx in self.regexes)


class Patterns(structs.BaseParms):
    incl_dirs: Pattern | None
    incl_files: Pattern | None
    excl_dirs: Pattern | None
    excl_files: Pattern | None

    @classmethod
    def from_parms(cls, parms: WalkParms) -> Patterns:
        def mk(name: str) -> Pattern | None:
            pats = getattr(parms, name)
            return Pattern(pats=pats, ignore_case=parms.ignore_case) if pats else None

        return cls(
            incl_dirs=mk("incl_dirs"),
            excl_dirs=mk("excl_dirs"),
            incl_files=mk("incl_files"),
            excl_files=mk("excl_files"),
        )

class FilterParms(structs.BaseParms):
    incl_dirs: list[str] | None = None
    incl_files: list[str] | None = None
    excl_dirs: list[str] | None = None
    excl_files: list[str] | None = None
    follow_symlinks: bool = False
    parents: bool = False
    ignore_case: bool = DFLT_IGNORE_CASE
    sort: bool = False
    exclude_hidden: bool = False

    @field_validator('incl_dirs', 'incl_files', 'excl_dirs', 'excl_files', mode='before')
    @classmethod
    def normalize_pattern_fields(cls, v):
        if v is None:
            return None
        return [v] if isinstance(v, str) else list(v)

    def __init__(self, **data):
        super().__init__(**data)
        self._validate_patterns()
        self._cached_dirs: set[pathlib.Path] = set()

    def _validate_patterns(self) -> None:
        for kind in ('dirs', 'files'):
            incl = getattr(self, f'incl_{kind}')
            excl = getattr(self, f'excl_{kind}')
            if incl and excl:
                conflict = set(incl) & set(excl)
                if conflict:
                    raise ValueError(f"{kind}: conflict between incl and excl: {conflict}")

        for dname in self.incl_dirs or []:
            if '/' in dname or '\\' in dname:
                raise ValueError(f"Directory pattern must not include '/' or '\\': {dname!r}")
        for dname in self.excl_dirs or []:
            if '/' in dname or '\\' in dname:
                raise ValueError(f"Directory pattern must not include '/' or '\\': {dname!r}")


class WalkParms(FilterParms):
    root: str | pathlib.Path
    as_path: bool = True

    @field_validator('root', mode='before')
    @classmethod
    def ensure_path(cls, v):
        return pathlib.Path(v)

    def __init__(self, **data):
        super().__init__(**data)


def _os_walk(root: pathlib.Path, parms: WalkParms):
    """Wrapper around os.walk using filter parameters."""
    return os.walk(root, topdown=True, followlinks=parms.follow_symlinks)


def _walk_with_incl_dirs(
        parms: WalkParms, pats: Patterns
        ) -> Iterator[str | pathlib.Path]:
    """
    Walk subtrees starting from directories whose names match incl_dirs.
    Applies _walk_pruned to filter content within matched subtrees.
    """
    root = parms.root
    incl_dirs = pats.incl_dirs if pats.incl_dirs else lambda _: True
    excl_dirs = pats.excl_dirs if pats.excl_dirs else lambda _: False
    for base, dirs, _ in _os_walk(root, parms):
        dirs[:] = [d for d in dirs if not excl_dirs(d)]
        valid_dirs = [d for d in dirs if incl_dirs(d)]
        for d in valid_dirs:
            subtree = os.path.join(base, d)
            yield from _walk_pruned(parms, pats, subtree)


def _walk_all_dirs(
    parms: WalkParms, 
    pats: Patterns) -> Iterator[str | pathlib.Path]:
    """
    Walk the entire directory tree starting from root, filtering according
    to excl_dirs, incl_files, excl_files, and hidden file settings.
    """
    return _walk_pruned(parms, pats, root=parms.root)



def _get_parents(
        full: str,
        parms: WalkParms,
        ) -> Iterator[str]:
    """ 
    Return all ancestor directories of a file, from root to immediate parent.

    These are only yielded if they have not been seen before,
    ensuring no duplicates. The paths are returned as Path objects
    or strings depending on the `as_path` flag.
    """
    parents = []

    # Walk from bottom to top, then reverse
    current = pathlib.Path(full).parent
    while (current != parms.root and current not in parms._cached_dirs):
        parms._cached_dirs.add(current)
        parents.append(current if parms.as_path else str(current))
        current = current.parent

    # walking is always with topdown=True so 
    # should yield root before parents
    if parms.root not in parms._cached_dirs:
        parms._cached_dirs.add(parms.root)
        parents.append(parms.root if parms.as_path else str(parms.root))
    return reversed(parents)


def _walk_pruned(
    parms: WalkParms,
    pats: Patterns,
    root: pathlib.Path) -> Iterator[str | pathlib.Path]:
    """
    Walk a subtree rooted at the given path, applying:
      - Directory pruning via excl_dirs and hidden file exclusion
      - File inclusion/exclusion using incl_files and excl_files
    Yields matching files as paths or strings depending on as_path.

    """
    excl_hidden = parms.exclude_hidden
    sort = parms.sort
    as_path = parms.as_path

    incl_files = pats.incl_files
    excl_files = pats.excl_files
    excl_dirs = pats.excl_dirs

    for dirpath, dirnames, filenames in _os_walk(root, parms):
        if excl_hidden:
            dirnames[:] = [d for d in dirnames 
                           if not validators.is_hidden(os.path.join(dirpath, d))]
        if excl_dirs:
            dirnames[:] = [d for d in dirnames if not excl_dirs(d)]
        if sort:
            dirnames.sort()
            filenames.sort()
        for file in filenames:
            full = os.path.join(dirpath, file)
            if excl_hidden and validators.is_hidden(full):
                continue
            if (not incl_files or incl_files(file)) and \
               (not excl_files or not excl_files(file)):

                if parms.parents:
                    for parent in _get_parents(full, parms):
                        yield parent

                yield pathlib.Path(full) if as_path else full

def _walk(parms: WalkParms) -> Iterator[str | pathlib.Path]:
    """
    Selects which walking strategy to use based on inclusion parameters.
    Returns a generator of matched files (and optionally parent directories).
    """
    pats = Patterns.from_parms(parms)
    if pats.incl_dirs:
        return _walk_with_incl_dirs(parms, pats)
    return _walk_all_dirs(parms, pats)

def walk(
        root: str | pathlib.Path,
        parents: bool = False,
        incl_dirs: str | Iterable[str] | None = None,
        incl_files: str | Iterable[str] | None = None,
        excl_dirs: str | Iterable[str] | None = None,
        excl_files: str | Iterable[str] | None = None,
        follow_symlinks: bool = False,
        ignore_case: bool = DFLT_IGNORE_CASE,
        sort: bool = False,
        exclude_hidden: bool = False,
        dirs_first: bool = True,
        as_path: bool = True) -> list[str | pathlib.Path]:
    """
    Return a list with filtered files/folders in a directory tree.

    Parameters can include inclusion/exclusion patterns for files and
    directories, as well as flags for case sensitivity, symbolic link
    following, hidden file exclusion, and sorting.

    Parameters (as keyword arguments):
    ----------------------------------
    root : str | Path
        The starting directory to search.
    parents: bool, default False
        Whether to return the containing folders of filtered files
    incl_dirs, excl_dirs : str | list[str] | None
        Directory name patterns to include or exclude (matched by name only).
    incl_files, excl_files : str | list[str] | None
        File name patterns to include or exclude.
    ignore_case : bool (default platform-dependent)
        Whether to apply case-insensitive pattern matching.
    follow_symlinks : bool (default False)
        Whether to follow symbolic links.
    sort : bool (default False)
        Whether to sort directories and files before processing.
    exclude_hidden : bool (default False)
        Whether to skip hidden files and directories.
    as_path : bool (default True)
        Whether to return results as pathlib.Path objects.
    dirs_first: bool, default True
        If True, directories will be returned first.

    Yields
    ------
    str | Path
        File paths matching the criteria.

    Examples
    --------
    >>> list(walk(root=".", incl_files="*.py"))
    [PosixPath('script.py'), PosixPath('test/test_util.py')]

    >>> list(walk(
    ...     root="src", incl_dirs=["core"], excl_files=["test_*"]
    ... ))
    [PosixPath('src/core/main.py')]
    """
    parms = WalkParms(
        root=root,
        incl_dirs=incl_dirs,
        incl_files=incl_files,
        excl_dirs=excl_dirs,
        parents=parents,
        excl_files=excl_files,
        follow_symlinks=follow_symlinks,
        ignore_case=ignore_case,
        sort=sort,
        exclude_hidden=exclude_hidden,
        as_path=as_path
    )
    paths = list(_walk(parms))

    if dirs_first is True:
        if as_path is False:
            _paths = [pathlib.Path(x) for x in paths]
        else:
            _paths = paths
        paths = sorted(_paths, key=lambda x: (not x.is_dir(), str(x)))
        if as_path is False:
            paths = [str(x) for x in paths]

    return paths




