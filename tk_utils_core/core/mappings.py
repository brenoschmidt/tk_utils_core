""" 
Utils for mapping types
         
"""
from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any

from .converters import as_set


def deep_update(
        obj: MutableMapping, 
        other: MutableMapping,
        ) -> MutableMapping:
    """
    Update mutable maps, recursively

    Parameters
    ----------
    obj: MutableMapping
        Object to be updated

    other: MutableMapping
        Updating object


    Examples
    --------
    >>> dic = {'a': {'b': 1, 'c': 2}}
    >>> dic.update({'a': {'c': 99}}) # Normal update
    >>> print(dic)
    {'a': {'c': 99}}

    >>> dic = {'a': {'b': 1, 'c': 2}}
    >>> dic = deep_update(dic, {'a': {'c': 99}}) 
    >>> print(dic)
    {'a': {'b': 1, 'c': 99}}

    >>> dic = {'a': {'b': 1, 'c': 2}}
    >>> dic = deep_update(dic, {'a': {'d': 99}}) 
    >>> print(dic)
    {'a': {'b': 1, 'c': 2, 'd': 99}}

    >>> dic = {'a': {'b': 1, 'c': 2}}
    >>> dic = deep_update(dic, {'a': 1}) # Like dict.update 
    >>> print(dic)
    {'a': 1}

    Notes
    -----
    Adapted from pydantic.utils.deep_update

    """
    if hasattr(obj, 'copy'):
        updated_obj = obj.copy()
    else:
        updated_obj = _copy.copy(obj)

    for k, v in other.items():
        if (k in updated_obj 
            and isinstance(updated_obj[k], MutableMapping) 
            and isinstance(v, MutableMapping)):
            updated_obj[k] = deep_update(updated_obj[k], v)
        else:
            updated_obj[k] = v
    return updated_obj

def map_dot_get(
        base: MutableMapping,
        key: str) -> Any:
    """
    Retrieve value from a nested mapping using dot-separated key.
    Raise if intermediate key does not exist
    """
    keys = key.split(".")
    current = base
    for k in keys:
        current = current[k]
    return current

def map_dot_update(
        base: MutableMapping,
        key: str,
        value: Any) -> None:
    """
    Return a nested mapping containing only included dot-notated keys
    (optionally excluding some).

    Parameters
    ----------
    base : MutableMapping
        Input mapping to subset.

    includes : list of str, optional
        List of dot-notation keys to include. If None, includes all.

    excludes : list of str, optional
        List of dot-notation keys to exclude.

    Returns
    -------
    MutableMapping
        New mapping of the same type as `base`, containing the requested subset.
    """
    keys = key.split(".")
    current = base
    for k in keys[:-1]:
        if k not in current or not isinstance(current[k], MutableMapping):
            current[k] = type(base)()
        current = current[k]
    current[keys[-1]] = value

def map_dot_subset(
        base: MutableMapping,
        includes: list[str] | None = None,
        excludes: list[str] | None = None) -> MutableMapping:
    """
    Return a nested mapping containing only included dot-notated keys
    (optionally excluding some).

    Parameters
    ----------
    base : MutableMapping
        Input mapping to subset.

    includes : list of str, optional
        List of dot-notation keys to include. If None, includes all.

    excludes : list of str, optional
        List of dot-notation keys to exclude.

    Returns
    -------
    MutableMapping
        New mapping of the same type as `base`, containing the requested subset.
    """
    result = type(base)()

    excludes = as_set(excludes, none_as_empty=True)

    # Determine which keys to keep
    def select_keys(d: MutableMapping, prefix="") -> list[str]:
        keys = set()
        for k, v in d.items():
            full = f"{prefix}.{k}" if prefix else k
            # Remove all children
            if full in excludes:
                continue
            if isinstance(v, MutableMapping):
                keys = keys | select_keys(v, full)
            else:
                keys.add(full)
        return keys

    selected_keys = select_keys(base)


    if includes:
        def chk(key):
            for k in includes:
                if key.startswith(k):
                    return True
            return False
        selected_keys = set(x for x in selected_keys if chk(x))

    # Build the result mapping
    for key in selected_keys:
        val = map_dot_get(base, key)
        if val is not None:
            map_dot_update(result, key, val)

    return result
