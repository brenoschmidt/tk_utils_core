""" Types

         
"""
from __future__ import annotations

from collections import namedtuple
from types import (
        BuiltinFunctionType,
        CodeType,
        EllipsisType,
        FunctionType,
        GenericAlias,
        NoneType,
        NotImplementedType,
        UnionType,
        )
from collections.abc import (
        Collection,
        Generator,
        Hashable,
        Iterable,
        Iterator,
        Mapping,
        MutableMapping,
        MutableSequence,
        Sequence,
        Set,
        )
from os import PathLike
import pathlib
from typing import (
        Annotated,
        Any,
        Callable,
        ClassVar,
        Generic,
        Literal,
        NamedTuple,
        Optional,
        Protocol,
        TYPE_CHECKING,
        TextIO,
        Type as type_t,
        TypeVar,
        Union,
        )

import numpy as np
import pandas as pd
from pydantic import (
        AfterValidator,
        Field,
        Unset,
        UNSET,
        )


# ----------------------------------------------------------------------------
#  Types with validators
# ----------------------------------------------------------------------------
PathInput = Annotated[
    str | pathlib.Path,
    AfterValidator(lambda pth: pathlib.Path(pth) if isinstance(pth, str) else pth)
]

# ----------------------------------------------------------------------------
#   Custom types 
# ----------------------------------------------------------------------------
T = TypeVar("T")

# Includes sets
SequenceLike = Union[
        list,
        tuple,
        MutableSequence,
        Set,
        ]

ScalarLike = Union[
        int,
        float,
        bool,
        str,
        complex,
        bytes,
        np.generic,
        NoneType,
        pd._libs.Period,
        pd._libs.Interval,
        pd._libs.Timedelta,
        pd._libs.missing.NAType,
        ]

# used in decorators to preserve the signature of the function it decorates
# see https://mypy.readthedocs.io/en/stable/generics.html#declaring-decorators
FuncType = Callable[..., Any]
ClassType = type[...]


# Copied from python.dataclasses
# Atomic immutable types which don't require any recursive handling and for which deepcopy
# returns the same object. We can provide a fast-path for these types in asdict and astuple.
AtomicTypes = ScalarLike | Union[
    # Other types that are also unaffected by deepcopy
    EllipsisType,
    NotImplementedType,
    CodeType,
    BuiltinFunctionType,
    FunctionType,
    type,
    range,
    property,
    ]





# ----------------------------------------------------------------------------
#   Sentinel unset type 
# ----------------------------------------------------------------------------
#class UnsetType:
#
#    def __repr__(self):
#        return "<UNSET>"
#
#    def __bool__(self):
#        return False
#
#    def __eq__(self, other):
#        raise TypeError("Use `is UNSET` to check for unset values, not `==`")
#
#    def __ne__(self, other):
#        raise TypeError("Use `is not UNSET` to check for unset values, not `!=`")
#
#UNSET = UnsetType()



def annotated(
        typ: type[T],
        description: str | None = UNSET,
        default: T | Unset = UNSET,
        **kargs,
        ) -> Annotated[T, Field]:
    """
    Annotated field factory for use with Pydantic models.

    Parameters
    ----------
    typ : type
        The expected type of the field.
    description : str | None, optional
        A description for the field (for documentation).
    default : Any, optional
        The default value for the field.
    **kargs
        Additional keyword arguments to pass to `Field`.

    Returns
    -------
    Annotated[T, Field]
        An annotated type hint usable in a Pydantic model.
    """
    if description is not UNSET:
        kargs['description'] = description
    if default is not UNSET:
        kargs['default'] = default
    return Annotated[typ, Field(**kargs)]



