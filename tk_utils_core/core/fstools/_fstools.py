"""
"""
from __future__ import annotations

import pathlib

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
