""" 
Structured data models 
         
"""
from __future__ import annotations

import pprint as pp
from collections.abc import MutableMapping, Mapping

from pydantic import (
        PrivateAttr,
        BaseModel, 
        ConfigDict,
        AfterValidator,
        ValidationError,
        Field,
        computed_field,
        field_validator,
        model_validator,
        )

from tk_utils_core.core.structs import (
        BaseConfig,
        BaseParms,
        BaseFrozenParms,
        obj_dot_update,
        obj_dot_get,
        obj_dot_subset,
        obj_dot_delete,
        unflatten_dict,
        flatten_dict,
        )

from tk_utils_core.options import options


__all__ = [
        'AfterValidator',
        'AttrDict',
        'BaseConfig',
        'BaseFrozenParms',
        'BaseModel', 
        'BaseParms',
        'ConfigDict',
        'Field',
        'PrivateAttr',
        'ValidationError',
        'computed_field',
        'field_validator',
        'flatten_dict',
        'model_validator',
        'obj_dot_delete',
        'obj_dot_get',
        'obj_dot_subset',
        'obj_dot_update',
        'unflatten_dict',
        ]


class AttrDict(dict):
    """
    Dictionary subclass with attribute-style access and recursive construction.

    `AttrDict` behaves like a standard dictionary but allows keys to be accessed
    as attributes. Nested mappings are automatically converted to `AttrDict`
    instances using the `_from_dict` constructor.

    Notes
    -----
    - Only keys that are valid Python identifiers and do not shadow existing
      methods or attributes can be accessed via dot notation.
    - Reserved attributes (e.g., `update`, `items`) cannot be set or deleted
      using attribute syntax.
    - Keys not accessible via attributes can still be accessed via item syntax.

    Examples
    --------
    Create a simple instance:

    >>> obj = AttrDict({'a': 1, 'b': 2})
    >>> print(obj)
    {'a': 1, 'b': 2}
    >>> obj.a
    1

    Add keys using attribute syntax:

    >>> obj.c = 3
    >>> obj['c']
    3
    >>> print(obj)
    {'a': 1, 'b': 2, 'c': 3}

    Attempting to overwrite a reserved method:

    >>> obj.update = 123
    Traceback (most recent call last):
        ...
    AttributeError: Cannot set reserved attribute: update

    Recursively convert nested dictionaries:

    >>> nested = {'meta': {'user': {'name': 'Alice'}}}
    >>> ad = AttrDict._from_dict(nested)
    >>> ad.meta.user.name
    'Alice'

    Mixed containers are also handled:

    >>> data = {'rows': [{'x': 1}, {'x': 2}]}
    >>> ad = AttrDict._from_dict(data)
    >>> ad.rows[1].x
    2

    Invalid attribute access:

    >>> ad.not_there
    Traceback (most recent call last):
        ...
    AttributeError: No such attribute: not_there
    """

    def __init__(self, other=(), /, **kwds):
        """
        The signature is the same as regular dictionaries.  
        Keyword argument order is preserved.
        """
        self.update(other, **kwds)

    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError(f"No such attribute: {name}")

    def __setattr__(self, name, value):
        if name in dir(self.__class__):
            raise AttributeError(f"Cannot set reserved attribute: {name}")
        self[name] = value

    def __delattr__(self, name):
        if name in dir(self.__class__):
            raise AttributeError(f"Cannot delete reserved attribute: {name}")
        elif name in self:
            del self[name]
        else:
            raise AttributeError(f"No such attribute: {name}")

    def update(self, other=(), /, **kwds):
        """
        Recursively update this dictionary with values from another mapping
        or iterable of pairs.
        """
        # Trade-off: Efficient vs user friendliness
        # Create a dictionary from other
        if not isinstance(other, MutableMapping):
            try:
                other = dict(other)
            except Exception:
                raise TypeError("update() expects a mapping or iterable of pairs")

        for k, v in other.items():
            self[k] = self.__class__._from_dict(v)


    @classmethod
    def _from_dict(cls, base):
        """ Returns an instance from a dict
        """
        if isinstance(base, MutableMapping):
            output = cls({})
            for k, v in base.items():
                output[k] = cls._from_dict(v)
            return output
        elif isinstance(base, (list, tuple, set)):
            return type(base)(cls._from_dict(x) for x in base)
        else:
            return base


    def __str__(self):
        return pp.pformat(self, width=options.pp.width)




