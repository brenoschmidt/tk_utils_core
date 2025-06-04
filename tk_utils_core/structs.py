""" 
Structured data models 
         
"""
from __future__ import annotations

from collections.abc import MutableMapping

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
        )

from tk_utils_core.options import options


__all__ = [
        'PrivateAttr',
        'BaseModel', 
        'ConfigDict',
        'AfterValidator',
        'ValidationError',
        'Field',
        'computed_field',
        'field_validator',
        'model_validator',
        'BaseConfig',
        'BaseParms',
        'BaseFrozenParms',
        'obj_dot_update',
        'obj_dot_get',
        'obj_dot_subset',
        'obj_dot_delete',
        ]

