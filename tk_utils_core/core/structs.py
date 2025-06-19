""" 
Structured data models used as configuration objects or to validate
parameters.
         
"""
from __future__ import annotations

import json
import copy as _copy
import pathlib
import re
from types import SimpleNamespace
from typing import (
        TYPE_CHECKING,
        Any,
        )

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
from ._typing import MutableMapping, ScalarLike
from .converters import as_set


# Regex used to map validation errors
RTYPE_ERR = re.compile(r'''
                        (is_instance
                        |_parsing
                        |type)
                        ''', re.I|re.S|re.X)


def _parse_validation_error(e: ValidationError):
    """ 
    Returns a tuple with the exception type and the message
    """
    errors = e.errors(
            include_url=False,
            )
    msgs = []
    ex = Exception
    parm_err = {}
    for err in errors:
        #msg = f"'{'.'.join(str(p) for p in err['loc'])}': {err['msg']}"
        loc = '.'.join(str(x) for x in err['loc'][0:-1])
        iput = err['input']
        if iput is None:
            key = loc
        else:
            key = f"{loc} = {iput}"

        if key not in parm_err:
            parm_err[key] = []

        parm_err[key].append(err['msg'])

        err_type = err['type']
        if RTYPE_ERR.match(err_type):
            ex = ValueError
        elif err_type.startswith("value"):
            ex = ValueError
    msgs = [f"{k}: {' OR '.join(v)}" for k, v in parm_err.items()]
    return (ex, '\n'.join(msgs))

class _BaseModel(BaseModel):
    """
    Base model with better representation and error messages
    """

    def __init__(__pydantic_self__, **kargs):
        try:
            super().__init__(**kargs)
        except ValidationError as e:
            (ex, msg) = _parse_validation_error(e)
            raise ex(msg) from None

    def __str__(self):
        fields = self.model_dump_json(indent=2)[1:-1]
        return f"{self.__class__.__name__}({fields})"


    if not TYPE_CHECKING:
        # Pydantic's assignment validator keeps throwing ValidationErrors
        def __setattr__(self, name: str, value: Any) -> None:
            try:
                if (setattr_handler := self.__pydantic_setattr_handlers__.get(name)) is not None:
                    setattr_handler(self, name, value)
                # if None is returned from _setattr_handler, the attribute was set directly
                elif (setattr_handler := self._setattr_handler(name, value)) is not None:
                    # call here to not memo on possibly unknown fields
                    setattr_handler(self, name, value)  
                    # memoize the handler for faster access
                    self.__pydantic_setattr_handlers__[name] = setattr_handler  
            except ValidationError as e:
                (ex, msg) = _parse_validation_error(e)
                raise ex(msg) from None

def _validate_model_updates(model: BaseModel, updates: dict[str, Any]) -> None:
    """
    Validate that the keys in `updates` correspond to fields in the Pydantic model.
    If any key is invalid, raises a ValueError.

    Parameters
    ----------
    model : BaseModel
        The Pydantic model whose fields should be validated.
    updates : dict[str, Any]
        Dictionary of updates to be applied to the model.

    Raises
    ------
    TypeError
        If `updates` is not a dictionary.
    ValueError
        If `updates` contains invalid field names.
    """
    if not isinstance(updates, dict):
        raise TypeError(
            f"Parm `updates` must be a dict, not '{type(updates).__name__}'"
        )

    invalid = ', '.join(f"'{k}'" for k in updates if k not in model.model_fields)
    if invalid:
        raise ValueError(
            f"Invalid fields for {model.__class__.__name__}: {invalid}"
        )

    for key, value in updates.items():
        current = getattr(model, key)
        if isinstance(current, BaseModel) and isinstance(value, dict):
            _validate_model_updates(current, value)

def _update_model_copy(
        model: BaseModel,
        updates: dict[str, Any],
        validate_updates: bool = True,
        ) -> BaseModel:
    """
    Create a new model instance with updated values.

    Parameters
    ----------
    model : BaseModel
        The model to copy and update.
    updates : dict[str, Any]
        The updates to apply to the model.
    validate_updates : bool, default True
        Whether to validate the updates before applying them.

    Returns
    -------
    BaseModel
        A new model instance with the updates applied.
    """
    if validate_updates:
        _validate_model_updates(model, updates)

    d = model.model_dump()
    for field_name, new_value in updates.items():
        current_value = getattr(model, field_name)
        if isinstance(current_value, BaseModel) and isinstance(new_value, dict):
            d[field_name] = _update_model_copy(current_value, new_value, False)
        else:
            d[field_name] = new_value
    return model.__class__(**d)

class BaseConfig(_BaseModel):
    """
    Base class for configuration models that supports recursive updates and
    temporary context-based mutations.

    Features
    --------
    - Enforces strict field validation and assignment.
    - Allows in-place or copy-based updates via `_update()`.
    - Supports temporary state changes using `with` blocks.

    Examples
    --------
    >>> class Address(BaseConfig):
    ...     city: str
    ...     zip: str
    >>> class User(BaseConfig):
    ...     name: str
    ...     age: int
    ...     address: Address

    >>> u = User(name='Alice', age=30, address=Address(city='NY', zip='10001'))

    # In-place update
    >>> u._update({'name': 'Bob'})
    >>> u.name
    'Bob'

    # Copy-based update
    >>> u2 = u._update({'name': 'Charlie', 'address': {'city': 'LA'}}, copy=True)
    >>> u2.name
    'Charlie'
    >>> u2.address.city
    'LA'
    >>> u.name
    'Bob'  # Original not changed

    # Temporary update in a context manager
    >>> with u:
    ...     u._update({'name': 'Dana', 'address': {'zip': '90210'}})
    ...     print(u.name, u.address.zip)
    Dana 90210
    >>> u.name  # Restored
    'Bob'
    >>> u.address.zip  # Restored
    '10001'

    """

    _context_depth: int = PrivateAttr(default=0)
    _backup_stack: list[dict[str, Any]] = PrivateAttr(default_factory=list)

    model_config = ConfigDict(
                    # Validate on changes
                    validate_assignment=True,
                    # No extra parms
                    extra='forbid',
                    # Whether instances will be frozen/hashable
                    frozen=False,
                    # Whether custom types are allowed
                    arbitrary_types_allowed=True,
                    # Validate instead of coerce types
                    strict=True,
                    # Whether to validate default values
                    validate_default=False,
                    )

    def _update(
            self,
            updates: dict[str, Any],
            *,
            copy: bool = False,
            validate_updates: bool = True
            ) -> BaseConfig | None:
        """
        Update the model with the given key-value pairs.

        Parameters
        ----------
        updates : dict[str, Any]
            Updates to apply to fields of the model.
        copy : bool, default False
            If True, returns a new model instance with updates applied.
            If False, updates the current model in-place.
        validate_updates : bool, default True
            Whether to validate update keys before applying them.

        Returns
        -------
        BaseConfig or None
            A new model instance if `copy` is True, otherwise None.
        """
        if validate_updates:
            _validate_model_updates(self, updates)
            validate_updates = False

        if copy:
            return _update_model_copy(self, updates, validate_updates=False)

        if self._context_depth > 0:
            if len(self._backup_stack) < self._context_depth:
                self._backup_stack.append(
                    _copy.deepcopy(self).model_dump()
                )

        for field_name, new_value in updates.items():
            current_value = getattr(self, field_name)
            if isinstance(current_value, BaseModel) and isinstance(new_value, dict):
                current_value._update(new_value, validate_updates=validate_updates)
            else:
                setattr(self, field_name, new_value)

        return None

    def __enter__(self) -> BaseConfig:
        self._context_depth += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._context_depth == 0:
            raise RuntimeError("Mismatched __exit__")
        if self._backup_stack:
            prior_state = self._backup_stack.pop()
            for k, v in prior_state.items():
                setattr(self, k, v)
        self._context_depth -= 1

class BaseParms(BaseConfig):
    """ 
    Base model for parameters
    """

class BaseFrozenParms(_BaseModel):
    """ 
    Hashable version of BaseParms
    """
    model_config = ConfigDict(
                    # Validate on changes
                    # (no need, frozen)
                    validate_assignment=False,
                    # No extra parms
                    extra='forbid',
                    # Whether instances will be frozen/hashable
                    frozen=True,
                    # Whether custom types are allowed
                    arbitrary_types_allowed=True,
                    # Validate instead of coerce types
                    strict=True,
                    # Whether to validate default values
                    validate_default=False,
                    )

def obj_dot_get(obj: object, attr: str) -> Any:
    """
    Safely retrieve a nested attribute using dot notation.
    Returns None if any intermediate attribute is missing.
    """
    for name in attr.split('.'):
        obj = getattr(obj, name)
    return obj

def flatten_dict(
        obj: dict[str, Any],
        parent_key: str = '',
        sep: str = '.') -> dict[str, Any]:
    """
    Flatten a nested dictionary into a flat dictionary with dot-delimited keys.

    Parameters
    ----------
    obj : dict of str to Any
        A nested dictionary.

    parent_key : str, optional
        Used internally during recursion to build full keys.

    sep : str, optional
        Separator to use when joining nested keys. Default is '.'

    Returns
    -------
    dict of str to Any
        A flat dictionary with dot-delimited keys.

    Examples
    --------
    >>> flatten_dict({'a': 1, 'b': {'c': 2}})
    {'a': 1, 'b.c': 2}

    >>> flatten_dict({'a': {'b': {'c': 3}}})
    {'a.b.c': 3}
    """
    items = {}
    for key, value in obj.items():
        full_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.update(flatten_dict(value, full_key, sep=sep))
        else:
            items[full_key] = value
    return items

def unflatten_dict(
        obj: dict[str, Any]) -> dict[str, Any]:
    """
    Convert a flat dictionary with dot-delimited keys into a nested dictionary.

    Parameters
    ----------
    obj : dict of str to Any
        A flat dictionary where some keys use dot notation to express nesting.

    Returns
    -------
    dict of str to Any
        A nested dictionary equivalent to the flattened input.

    Raises
    ------
    ValueError
        If dot-based nesting conflicts with an existing non-dict value.

    Examples
    --------
    >>> unflatten_dict({'a': 1, 'b.c': 2})
    {'a': 1, 'b': {'c': 2}}

    >>> unflatten_dict({'a.b': 1, 'a.c': 2})
    {'a': {'b': 1, 'c': 2}}

    >>> unflatten_dict({'a': 1, 'a.b': 2})
    Traceback (most recent call last):
        ...
    ValueError: Cannot nest key 'a.b' under non-dict value at 'a'
    """
    out = {}
    for key, value in obj.items():
        parts = key.split(".")
        current = out
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                if part in current and isinstance(current[part], dict):
                    raise ValueError(
                        f"Cannot assign value to key '{key}' because "
                        f"a nested dict already exists at '{part}'"
                    )
                current[part] = value
            else:
                if part not in current:
                    current[part] = {}
                elif not isinstance(current[part], dict):
                    raise ValueError(
                        f"Cannot nest key '{key}' under non-dict value at '{part}'"
                    )
                current = current[part]
    return out


def obj_dot_update(
        obj: object,
        attr: str,
        value: Any) -> None:
    """
    Update a (potentially nested) object using dot-separated attribute names.

    This function only updates the attribute if all intermediate attributes
    exist. If any attribute in the chain is missing, nothing is changed.

    Parameters
    ----------
    obj : object
        The object to update.

    attr : str
        Dot-separated attribute name, e.g., "a.b.c".

    value : Any
        Value to assign to the final attribute.
    """
    attrs = attr.split(".")
    current = obj
    for a in attrs[:-1]:
        if not hasattr(current, a):
            return  # Abort early if any attribute in chain is missing
        current = getattr(current, a)
    if hasattr(current, attrs[-1]):
        setattr(current, attrs[-1], value)

def get_all_dot_attrs(
        obj: object,
        prefix: str = "",
        *,
        skip_private: bool = True,
        force_public: list[str] | None = None,
        max_depth: int | None = None,
        _depth: int = 0) -> list[str]:
    """
    Recursively collect dot-notated attribute paths from an object.

    Parameters
    ----------
    obj : object
        The object to inspect.

    prefix : str, default ""
        The prefix to prepend to attribute names (used for recursion).

    skip_private : bool, default True
        If True, skips attributes starting with an underscore.

    max_depth : int or None, default None
        If set, limits recursion depth to this many levels.

    force_public: list[str], optional
        If given, attributes will be included even if they start with
        an underscore and skip_private is True
    _depth : int
        Internal parameter used for recursive depth tracking.

    Returns
    -------
    list of str
        Dot-notated attribute names, e.g. ['a.b', 'a.c.d']
    """
    if max_depth is not None and _depth >= max_depth:
        return []

    force_public = as_set(force_public, none_as_empty=True)

    result = []
    for name in dir(obj):
        if skip_private and name.startswith("_") and name not in force_public:
            continue
        try:
            val = getattr(obj, name)
        except Exception:
            continue  # avoid triggering properties or descriptors

        full_name = f"{prefix}.{name}" if prefix else name
        if hasattr(val, "__dict__") and not isinstance(val, ScalarLike):
            result.extend(
                get_all_dot_attrs(
                    val, 
                    prefix=full_name, 
                    skip_private=skip_private,
                    force_public=force_public,
                    max_depth=max_depth, _depth=_depth + 1)
            )
        else:
            result.append(full_name)
    return result

def obj_dot_delete(obj: object, attr: str) -> None:
    """
    Delete a nested attribute if all parents exist and the final attr is
    present.
    """
    parts = attr.split(".")
    for name in parts[:-1]:
        if not hasattr(obj, name):
            return
        obj = getattr(obj, name)
    if hasattr(obj, parts[-1]):
        delattr(obj, parts[-1])

def obj_dot_subset(
        obj: object,
        force_public: list[str] | None = None, 
        includes: list[str] | None = None,
        excludes: list[str] | None = None,
        ) -> object:
    """
    Return a deep copy of the object with a subset of attributes using dot
    notation.

    Attributes not in `includes` or in `excludes` will be removed.

    """
    out = _copy.deepcopy(obj)

    # Start with all attributes
    all_attrs = set(get_all_dot_attrs(
        out, 
        force_public=force_public,
        ))

    keep = set(all_attrs)

    # Excludes
    if excludes:
        def _keep(key):
            for k in excludes:
                if key.startswith(k):
                    return False
            return True
        keep = set(x for x in keep if _keep(x))

    # includes
    if includes:
        def _keep(key):
            for k in includes:
                if key.startswith(k):
                    return True
            return False
        keep = set(x for x in keep if _keep(x))

    for attr in all_attrs:
        if attr not in keep:
            obj_dot_delete(out, attr)
    return out

