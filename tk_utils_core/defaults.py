""" 
Defaults

#PP_DEFAULTS = {
#    'color': None,
#    'indent': '',
#    'pretty': True,
#    'width': 60,
#    'sort_dicts': False,
#    'compact': False,
#    'depth': None,
#    'as_hdr': False,
#    'underscore_numbers': True,
#    'show_type': False,
#    'df_info': False,
#    'df_max_cols': None,
#    'df_max_rows': None,
#    'min_sep_width': 40,
#    'max_sep_width': None,
#    }
         
"""
from __future__ import annotations

import tomllib
import pathlib
from functools import lru_cache
from typing import Any

from tk_utils_core.core.structs import (
        BaseConfig,
        Field,
        )
from tk_utils_core.core._typing import (
        UNSET,
        )

@lru_cache(maxsize=1)
def load_toml_defaults(path: str | pathlib.Path) -> dict[str, Any]:
    """Read and cache TOML defaults from disk."""
    with open(pathlib.Path(path), "rb") as f:
        return tomllib.load(f)

class Doctests(BaseConfig):
    """
    """
    print_docstring: bool
    print_examples: bool
    print_hdr: bool
    print_mod: bool
    verbose: bool
    compileflags: bool

class PrettyErrors(BaseConfig):
    """
    """
    pretty_errors: bool
    line_number_first: bool
    display_link: bool


class Defaults(BaseConfig):
    """
    """
    debug: bool = False
    pretty_errors: PrettyErrors
    doctests: Doctests

def _mk_defaults() -> Defaults:
    pth = pathlib.Path(__file__).with_name("defaults.toml")
    dflts = load_toml_defaults(pth)
    return Defaults.model_validate(dflts)


defaults = _mk_defaults()

def configure(updates: dict):
    global defaults
    defaults._update(updates, copy=False)



