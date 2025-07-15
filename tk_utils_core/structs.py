""" 
Structured data models 
         
"""
from __future__ import annotations

import pprint as pp
import dataclasses as dc
from collections.abc import MutableMapping, Mapping

from pydantic import (
        AfterValidator,
        BaseModel, 
        ConfigDict,
        Field,
        PrivateAttr,
        ValidationError,
        computed_field,
        field_validator,
        model_validator,
        )

from tk_utils_core.core.structs import (
        AttrDict as _AttrDict,
        BaseConfig,
        BaseDC as _BaseDC,
        BaseDataModel,
        BaseFrozenParms,
        BaseParms,
        flatten_dict,
        obj_dot_delete,
        obj_dot_get,
        obj_dot_subset,
        obj_dot_update,
        unflatten_dict,
        )

from tk_utils_core.options import options


__all__ = [
        'AfterValidator',
        'AttrDict',
        'BaseConfig',
        'BaseDC',
        'BaseDataModel',
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


class AttrDict(_AttrDict):
    __doc__ = _AttrDict.__doc__

    def __str__(self):
        return pp.pformat(self, width=options.pp.width)


@dc.dataclass(kw_only=True)
class BaseDC(_BaseDC):
    __doc__ = _BaseDC.__doc__

    def __str__(self) -> str:
        return pp.pformat(self, width=options.pp.width)

