""" 
Validators

"""
from __future__ import annotations

import os
import pathlib
import sys

import pydantic
from pandas.api.types import (
        is_numeric_dtype,
        is_float_dtype,
        is_integer_dtype,
        is_datetime64_dtype,
        )

from .constants import (
        POSIX,
        )
from ._typing import (
        Any,
        )


if not POSIX:
    # Required by is_hidden if not POSIX
    import ctypes

def is_hidden(pth: str | pathlib.Path) -> bool:
    """
    Returns True if the given path points to a hidden file or folder.
    
    On POSIX, a file is considered hidden if its name starts with a dot.

    On Windows, a file is hidden if it has the FILE_ATTRIBUTE_HIDDEN
    attribute.

    """
    if isinstance(pth, pathlib.Path):
        pth = str(pth)

    if POSIX:
        return os.path.basename(pth).startswith('.')
    else:
        try:
            attrs = ctypes.windll.kernel32.GetFileAttributesW(pth)
            return bool(attrs & 0x02)  
        except Exception:
            return False

def is_namedtuple(obj: Any) -> bool:
    """ 
    Returns True if the object is a namedtuple instance.

    Parameters
    ----------
    obj : Any
        Object to check.

    Returns
    -------
    bool
        True if `obj` is a namedtuple instance, False otherwise.

    Examples
    --------
    >>> from collections import namedtuple
    >>> Point = namedtuple('Point', ['x', 'y'])
    >>> p = Point(1, 2)
    >>> is_namedtuple(p)
    True

    >>> is_namedtuple((1, 2))
    False

    >>> class NotNamedTuple(tuple):
    ...     pass
    >>> is_namedtuple(NotNamedTuple((1, 2)))
    False
    """
    return (isinstance(obj, tuple) 
            and hasattr(obj, '_asdict') 
            and hasattr(obj, '_fields'))

def is_pydantic_dc(obj) -> bool:
    """
    Return True if a pydantic dataclass or an instance of a pydantic dataclass
    """
    return any([
            pydantic.dataclasses.is_pydantic_dataclass(obj),
            pydantic.dataclasses.is_pydantic_dataclass(type(obj))])


def is_pydantic_model(obj) -> bool:
    """
    Return True if a pydantic model
    """
    return isinstance(obj, pydantic.BaseModel)


def assert_file_exists(pth: pathlib.Path | str) -> None:
    """
    Assert that `pth` points to an existing file.

    Raises an appropriate error if the path is not a valid file.

    Parameters
    ----------
    pth : str or pathlib.Path
        The path to check.

    Raises
    ------
    FileNotFoundError
        If the path does not exist or is a broken symlink.

    IsADirectoryError
        If the path exists but is not a file.
    
    Exception
        If the path exists but is not a file or directory
        (e.g., a device node or socket).
    """
    pth = pathlib.Path(pth)

    if pth.is_file():
        return

    if not pth.exists():
        if pth.is_symlink():
            raise FileNotFoundError(f"Broken symlink: '{pth}'")
        raise FileNotFoundError(f"File does not exist: '{pth}'")

    if pth.is_dir():
        raise IsADirectoryError(
                f"Path is a directory, not a file: '{pth}'")

    # Catch-all for sockets, devices, etc.
    raise Exception(f"Path exists but is not a regular file: '{pth}'")

