""" 
Structured data models used as configuration objects or to validate
parameters.
         
"""
from __future__ import annotations

import json
import copy as _copy
import pathlib
import re
from pprint import pformat
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
from ._typing import MutableMapping


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
    >>> from tk_core.utils import deep_update

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


