""" 
Structured data models 
         
"""
from __future__ import annotations

import pprint as pp
import dataclasses as dc
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
        'BaseDC',
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


@dc.dataclass(kw_only=True)
class BaseDC:
    """
    Base dataclass with enhanced functionality:
    
    - Pretty string representation
    - Convenience methods for dictionary conversion, field replacement,
      and in-place updating
    """

    @classmethod
    def _get_parm_names(
            cls,
            ignore_underscored: bool = False) -> list[str]:
        """
        Return the names of dataclass fields.

        Parameters
        ----------
        ignore_underscored : bool, default False
            If True, exclude names starting with an underscore.

        Returns
        -------
        list of str
            Names of dataclass fields.

        Examples
        --------
        >>> @dc.dataclass
        ... class MyDC(BaseDC):
        ...     a: int
        ...     _b: int = 0
        >>> MyDC._get_parm_names()
        ['a', '_b']
        >>> MyDC._get_parm_names(ignore_underscored=True)
        ['a']
        """
        out = [f.name for f in dc.fields(cls)]
        if ignore_underscored:
            out = [x for x in out if not x.startswith('_')]
        return out

    def __str__(self) -> str:
        """
        Pretty-formatted string representation
        """
        return pp.pformat(self, width=options.pp.width)

    def _asdict(
            self,
            dict_factory: type = dict) -> dict:
        """
        Convert the dataclass to a dictionary

        Parameters
        ----------
        dict_factory : type, default dict
            Factory used to construct the output dictionary.

        Returns
        -------
        dict
            Dictionary representation of the dataclass.
        """
        return dc.asdict(self, dict_factory=dict_factory)

    def _replace(self, **kargs) -> BaseDC:
        """
        Return a copy of the instance with specified fields replaced.

        Parameters
        ----------
        **kargs : any
            Fields and values to replace in the new instance.

        Returns
        -------
        BaseDC
            A new instance with updated fields.
        """
        return dc.replace(self, **kargs)

    def _update(self, **kargs) -> None:
        """
        Update fields of the current instance in place.

        Parameters
        ----------
        **kargs : any
            Fields and values to update.

        Raises
        ------
        ValueError
            If any keyword does not match a declared dataclass field.

        Examples
        --------
        >>> @dc.dataclass
        ... class User(BaseDC):
        ...     name: str
        ...     age: int
        >>> u = User(name='Alice', age=30)
        >>> u._update(age=31)
        >>> u.age
        31
        >>> u._update(email='alice@example.com')
        Traceback (most recent call last):
            ...
        ValueError: The following are not valid parameters of User: email
        """
        parm_names = set(self.__class__._get_parm_names())
        invalid = set(kargs) - parm_names
        if invalid:
            clsname = self.__class__.__name__
            msg = f"The following are not valid parameters of {clsname}: "
            msg += ', '.join(sorted(invalid))
            raise ValueError(msg)

        for k, v in kargs.items():
            setattr(self, k, v)


