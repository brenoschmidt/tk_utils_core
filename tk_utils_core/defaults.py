""" 
Defaults
         
"""
from __future__ import annotations

import tomllib
import pathlib
from functools import lru_cache
from typing import Any

from .core.structs import (
        BaseConfig,
        Field,
        )
from .core._typing import (
        UNSET,
        TOMLStrOrNone,
        TOMLIntOrNone,
        )


@lru_cache(maxsize=2)
def load_toml_defaults(path: str | pathlib.Path) -> dict[str, Any]:
    """Read and cache TOML defaults from disk."""
    with open(pathlib.Path(path), "rb") as f:
        return tomllib.load(f)

class PP(BaseConfig):
    """
    """
    color: TOMLStrOrNone 
    indent: str
    pretty: bool
    sort_dicts: bool
    depth: TOMLIntOrNone
    underscore_numbers: bool
    width: int
    compact: bool


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

class TkUtilsGithub(BaseConfig):
    """
    """
    user: str
    repo: str
    base: str
    modules: list[str]

class TkUtilsCoreGithub(BaseConfig):
    """
    """
    user: str
    repo: str

class Dropbox(BaseConfig):
    """
    """
    url: TOMLStrOrNone 

class Github(BaseConfig):
    """
    """
    tk_utils: TkUtilsGithub 
    tk_utils_core: TkUtilsCoreGithub
    
class TkUtils(BaseConfig):
    """
    """
    config: str

class PyCharmDirnames(BaseConfig):
    """
    """
    backup: str
    dropbox: str
    venv: str
    tk_utils: str
    prj_root: str

class PyCharmFilenames(BaseConfig):
    """
    """
    toolkit_config: str

class PyCharm(BaseConfig):
    """
    """
    validate_paths: bool
    dirnames: PyCharmDirnames
    filenames: PyCharmFilenames
    tk_utils: TkUtils


class Defaults(BaseConfig):
    """
    """
    debug: bool = False
    pretty_errors: PrettyErrors
    doctests: Doctests
    pycharm: PyCharm
    github: Github
    dropbox: Dropbox
    pp: PP


def _mk_defaults() -> Defaults:
    pth = pathlib.Path(__file__).with_name("defaults.toml")
    dflts = load_toml_defaults(pth)
    return Defaults.model_validate(dflts)

defaults = _mk_defaults()

def configure(updates: dict):
    global defaults
    defaults._update(updates, copy=False)

