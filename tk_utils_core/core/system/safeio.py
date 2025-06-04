""" 
Utilities to copy/move files safely

         
"""
from __future__ import annotations

import os
import pathlib
import shutil

from ..converters import (
        as_path,
        )
from .walk import walk 



def copy_with_parents(src: pathlib.Path, dst: pathlib.Path) -> None:
    """
    Copies `src` to `dst`, creating parent directories of `dst` if needed.

    Parameters
    ----------
    src : str | Path
        Source file to copy.

    dst : str | Path
        Destination path.
    """
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

def safe_copy(
        src: str | pathlib.Path,
        dst: str | pathlib.Path,
        raise_if_exists: bool = False) -> bool:
    """ 
    Copies a file from `src` to `dst` if `dst` does not exist.

    If `dst` does not exist, its parent directories are created.
    Raises an exception if `src` does not exist, is not a file, or if `src`
    and `dst` point to the same file.

    Parameters
    ----------
    src : str | Path
        Source file to copy.

    dst : str | Path
        Destination path.

    raise_if_exists : bool
        Whether to raise an error if the destination file exists.

    Returns
    -------
    bool
        True if file was copied, False if the destination already existed.
    """
    src = as_path(src)
    dst = as_path(dst)

    if not src.exists():
        raise FileNotFoundError(f"File does not exist:\n  {src}")
    if not src.is_file():
        raise ValueError(f"Source is not a file:\n  {src}")
    if src.resolve() == dst.resolve():
        raise ValueError(f"`src` and `dst` refer to the same file:\n  {src}")

    if dst.exists():
        if raise_if_exists:
            raise FileExistsError(
                f"Destination exists and `raise_if_exists` is True:\n  {dst}"
            )
        return False

    copy_with_parents(src=src, dst=dst)
    return True

def safe_copytree(
        src: str | pathlib.Path, 
        dst: str | pathlib.Path,
        raise_if_exists: bool = False,
        dry_run: bool = False,
        **kargs) -> list[tuple[pathlib.Path, pathlib.Path]] | None:
    """
    Recursively copies all files under `src` that do not exist under `dst`.
    Empty directories are not copied.

    Parameters
    ----------
    src : str | Path
        Source folder.

    dst : str | Path
        Destination folder.

    raise_if_exists : bool, default False
        If True, raises if any destination file exists.

    dry_run : bool, default False
        If True, returns a list of (src, dst) pairs that would be copied.

    **kargs : Any
        Passed to `walk(...)`. The keys 'root', 'as_path', and 'parents'
        are explicitly disallowed.

    Returns
    -------
    list of (Path, Path) if dry_run is True, else None
    """
    src = as_path(src)
    dst = as_path(dst)
    resolved_src = src.resolve()
    resolved_dst = dst.resolve()

    if not src.exists():
        raise FileNotFoundError(f"Source folder does not exist:\n  {src}")
    if not src.is_dir():
        raise ValueError(f"`src` must be a folder:\n  {src}")
    if resolved_src == resolved_dst:
        raise ValueError(f"`src` and `dst` refer to the same location:\n  {src}")
    if dst.exists() and not dst.is_dir():
        raise ValueError(f"`dst` must be a folder:\n  {dst}")
    if dst.is_relative_to(src) or resolved_dst.is_relative_to(resolved_src):
        raise ValueError(
            f"`dst` must not be a subdirectory of `src`:\n"
            f"  src: {src}\n"
            f"  dst: {dst}"
        )
    for key in kargs:
        if key in {"root", "as_path", "parents"}:
            raise ValueError(f"`{key}` is not an allowed keyword argument")

    paths: list[tuple[pathlib.Path, pathlib.Path]] = []
    for src_pth in walk(root=src, as_path=True, parents=False, **kargs):
        dst_pth = dst / src_pth.relative_to(src)
        if dst_pth.exists():
            if raise_if_exists:
                raise FileExistsError(
                    f"Destination exists and `raise_if_exists` is True:\n  {dst_pth}"
                )
        else:
            paths.append((src_pth, dst_pth))

    if dry_run:
        return paths

    for src_pth, dst_pth in paths:
        assert not dst_pth.exists(), f"Unexpected: {dst_pth} exists"
        copy_with_parents(src=src_pth, dst=dst_pth)

    return None






