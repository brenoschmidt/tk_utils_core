""" 
Converters to coerce values from one type to another
         
"""
from __future__ import annotations

from functools import lru_cache
import copy
from types import SimpleNamespace
import dataclasses as dc
import pathlib
import re


from ._typing import (
        Any,
        AtomicTypes,
        MutableSequence,
        MutableMapping,
        ScalarLike,
        SequenceLike,
        )
from .validators import (
        is_namedtuple,
        is_pydantic_model,
        is_pydantic_dc,
        )


def as_path(pth: str | pathlib.Path) -> pathlib.Path:
    """
    Ensures `pth` is a pathlib.Path instance

    Parameters
    ----------
    pth: str | pathlib.Path
        Path

    Returns
    -------
    pathlib.Path

    Examples
    --------
    >>> import pathlib
    >>> from tk_utils.converters import as_path
    >>> pth = 'path_to_file'
    >>> print(pth, type(pth))
    path_to_file <class 'str'>

    >>> pth = as_path(pth)
    >>> print(isinstance(pth, pathlib.Path))
    True

    >>> new_pth = as_path(pth) # Does nothing if called on pathlib.Path
    >>> id(new_pth) == id(pth)
    True
    """
    return pathlib.Path(pth) if isinstance(pth, str) else pth

@dc.dataclass
class _AsDictOpts:
    """
    """
    dict_factory: type
    copy: bool
    none_as_empty: bool
    convert_ntups: bool

def _dc_to_dict(obj, opts: _AsDictOpts):
    return _as_dict( dc.asdict(obj, dict_factory=opts.dict_factory), opts)

def _ntup_to_dict(obj, opts: _AsDictOpts):
    if opts.convert_ntups:
        return opts.dict_factory(
            (k, _as_dict(getattr(obj, k), opts)) for k in obj._fields)
    else:
        return type(obj)(*[_as_dict(v, opts) for v in obj])

def _map_to_dict(obj, opts: _AsDictOpts):
    return opts.dict_factory(
            (_as_dict(k, opts), _as_dict(v, opts)) for k, v in obj.items())

def _ns_to_dict(obj, opts: _AsDictOpts):
    return opts.dict_factory(
            (k, _as_dict(v, opts)) for k, v in obj.__dict__.items())

def _as_dict(obj: Any, opts: _AsDictOpts):
    """
    """

    if obj is None:
        if opts.none_as_empty is True:
            return opts.dict_factory()
        else:
            return None
    elif isinstance(obj, AtomicTypes):
        return obj
    elif dc.is_dataclass(obj):
        return _dc_to_dict(obj, opts)
    elif is_pydantic_dc(obj) or is_pydantic_model(obj):
        return _as_dict(obj.model_dump(), opts)
    elif is_namedtuple(obj):
        return _ntup_to_dict(obj, opts)
    elif isinstance(obj, MutableMapping):
        return _map_to_dict(obj, opts)
    elif isinstance(obj, SimpleNamespace):
        return _ns_to_dict(obj, opts)
    elif isinstance(obj, (tuple, MutableSequence, set)):
        return type(obj)(_as_dict(v, opts) for v in obj)
    else:
        return copy.deepcopy(obj) if opts.copy is True else obj

def as_dict(
        obj: Any,
        dict_factory: type = dict,
        copy: bool = True,
        none_as_empty: bool = False,
        convert_ntups: bool = True,
        ):
    """ 
    Recursively converts objects to dictionaries

    Parameters
    ----------
    obj: object

    dict_factory: type, optional
        Dictionary factory. Defaults to dict
        
    copy: bool, default True
        If True, deep copies inner objects

    none_as_empty: bool, default False
        If True, convert None to empty dicts

    Examples
    --------
    >>> from dataclasses import dataclass
    >>> @dataclass
    ... class Point:
    ...     x: int
    ...     y: int

    >>> p = Point(1, 2)
    >>> as_dict(p)
    {'x': 1, 'y': 2}

    >>> from collections import namedtuple
    >>> ntup = namedtuple("Coord", ["lat", "lon"])
    >>> c = ntup(10, 20)
    >>> as_dict(c)
    {'lat': 10, 'lon': 20}

    >>> from pydantic import BaseModel
    >>> class UserModel(BaseModel):
    ...     name: str
    ...     age: int

    >>> u = UserModel(name="Joe", age=30)
    >>> as_dict(u)
    {'name': 'Joe', 'age': 30}

    >>> as_dict({'a': Point(1, 2), 'b': [ntup(3, 4)]})
    {'a': {'x': 1, 'y': 2}, 'b': [{'lat': 3, 'lon': 4}]}
        
    """
    opts = _AsDictOpts(
            dict_factory=dict_factory,
            copy=copy,
            none_as_empty=none_as_empty,
            convert_ntups=convert_ntups,
            )
    return _as_dict(obj, opts)

def as_list(
        obj: ScalarLike | SequenceLike,
        none_as_empty: bool = True,
        ) -> list | None:
    """
    Convert scalars to single-element lists and other sequences to lists.

    Parameters
    ----------
    obj : ScalarLike or SequenceLike
        The object to be converted to a list.

    none_as_empty : bool, default True
        If True, convert None to an empty list. If False, return None.

    Returns
    -------
    list or None
        A list containing the original object(s), or None if applicable.

    Examples
    --------
    >>> as_list(5)
    [5]

    >>> as_list("abc")
    ['abc']

    >>> as_list([1, 2, 3])
    [1, 2, 3]

    >>> as_list((4, 5))
    [4, 5]

    >>> as_list(None, none_as_empty=True)
    []

    >>> as_list(None, none_as_empty=False) is None
    True

    >>> sorted(as_list({"a", "b"}))
    ['a', 'b']  

    >>> as_list(object())  
    Traceback (most recent call last):
        ...
    ValueError: Cannot convert type <class 'object'> to list
    """
    if obj is None:
        return obj if none_as_empty is False else []
    elif isinstance(obj, ScalarLike):
        return [obj]
    elif isinstance(obj, list):
        return obj
    elif isinstance(obj, SequenceLike):
        return list(obj)
    else:
        raise ValueError(f"Cannot convert type {type(obj)} to list")

def as_set(
        obj: ScalarLike | SequenceLike,
        none_as_empty: bool = True,
        ) -> set | None:
    """
    Convert scalars to single-element sets and other sequences to sets.

    Parameters
    ----------
    obj : ScalarLike or SequenceLike
        The object to be converted to a set.

    none_as_empty : bool, default True
        If True, convert None to an empty set. If False, return None.

    Returns
    -------
    set or None
        A set containing the original object(s), or None if applicable.

    Examples
    --------
    >>> as_set(5)
    {5}

    >>> as_set("abc")
    {'abc'}

    >>> as_set([1, 2, 3])
    {1, 2, 3}

    >>> as_set(None, none_as_empty=True)
    set()

    >>> as_set(None, none_as_empty=False) is None
    True

    >>> as_set(object())  
    Traceback (most recent call last):
        ...
    ValueError: Cannot convert type <class 'object'> to set
    """
    if obj is None:
        return obj if none_as_empty is False else set()
    elif isinstance(obj, ScalarLike):
        return {obj}
    elif isinstance(obj, set):
        return obj
    elif isinstance(obj, SequenceLike):
        return set(obj)
    else:
        raise ValueError(f"Cannot convert type {type(obj)} to set")

def bytes2human(
        num: int, 
        suffix: str = 'B', 
        dec: int = 2,
        base: float = 1024.0,
        ) -> str:
    """
    Convert a byte value into a human-readable string.

    Parameters
    ----------
    num : int
        Number of bytes.
    suffix : str, default 'B'
        Unit suffix to append (e.g., 'B', 'bps').
    dec : int, default 2
        Number of significant digits.
    base: float, default 1024.0
        

    Returns
    -------
    str
        Human-readable string with binary prefix.
    """
    for unit in ['','K','M','G','T','P','E','Z','Y']:
        if abs(num) < base:
            return f"{num:.{dec}g} {unit}{suffix}"
        num /= base
    return f"{num:.{dec}g} Y{suffix}"

@lru_cache(maxsize=None)
def _size_regex():
    """Compiled regex pattern: number + optional unit"""
    return re.compile(r'''
        ^\s*
        (?P<size>[0-9.]+)
        \s*
        (?P<unit>([KMGTPZEY])i?B)?   # Optional unit suffix
        \s*$
        ''', re.I | re.S | re.X)

def human2bytes(s: str, base: int = 1024) -> int:
    """
    Convert a human-readable size string into a number of bytes.

    Parameters
    ----------
    s : str
        A string like '1.5 KB', '2 MiB', '10GB', or '1024'.
    base : int, default 1024
        Use 1024 for binary prefixes (KiB, MiB), or 1000 for SI units.

    Returns
    -------
    int
        Number of bytes.

    Examples
    --------
    >>> human2bytes("1.5 kb", base=1000)
    1500
    >>> human2bytes("2 MiB")
    2097152
    >>> human2bytes("1GiB")
    1073741824
    >>> human2bytes("1024")
    1024
    """
    match = _size_regex().fullmatch(s.strip())
    if not match:
        raise ValueError(f"Invalid size string: {s!r}")
    
    size = float(match.group("size"))
    unit = match.group("unit")

    if not unit:
        pwr = 0
    else:
        prefix = unit[0].lower()
        units = 'kmgtepzy'
        if prefix not in units:
            raise ValueError(f"Invalid unit prefix: {unit}")
        pwr = units.index(prefix) + 1  # 'k' => 1, 'm' => 2, etc...

    return int(size * (base ** pwr))





def to_namespace(base: MutableMapping) -> SimpleNamespace:
    """
    Recursively convert a nested dictionary into a SimpleNamespace.

    Each dictionary becomes a SimpleNamespace, allowing attribute-style access.
    Other values are kept unchanged.

    Parameters
    ----------
    base : MutableMapping
        A (possibly nested) dictionary to convert.

    Returns
    -------
    SimpleNamespace
        A SimpleNamespace version of the input mapping.

    Examples
    --------
    >>> ns = to_namespace({'a': 1, 'b': {'c': 2}})
    >>> ns.a
    1
    >>> ns.b.c
    2
    """
    out = {
        k: to_namespace(v) if isinstance(v, MutableMapping) else v
        for k, v in base.items()
    }
    return SimpleNamespace(**out)





























