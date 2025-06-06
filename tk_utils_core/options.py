""" 
Options
         
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
        TOMLStrOrNone,
        TOMLIntOrNone,
        )

__all__ = [
        'options',
        'configure',
        ]


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
    branch: TOMLStrOrNone 

class Dropbox(BaseConfig):
    """
    """
    url: TOMLStrOrNone 

class Github(BaseConfig):
    """
    """
    tk_utils: TkUtilsGithub 
    tk_utils_core: TkUtilsCoreGithub
    

class PyCharmPaths(BaseConfig):
    """
    """
    root: str
    backup: str
    dropbox: str
    venv: str
    idea: str
    tk_utils: str
    toolkit_config: str
    tk_utils_config: str
    dropbox_zip: str


class PyCharm(BaseConfig):
    """
    """
    validate_paths: bool
    prjname: str
    paths: PyCharmPaths

class Options(BaseConfig):
    """
    """
    debug: bool
    pretty_errors: PrettyErrors
    doctests: Doctests
    pycharm: PyCharm
    github: Github
    dropbox: Dropbox
    pp: PP
    dependencies: list[str]


def _mk_defaults() -> Options:
    pth = pathlib.Path(__file__).with_name("defaults.toml")
    dflts = load_toml_defaults(pth)
    return Options.model_validate(dflts)

options = _mk_defaults()

def configure(updates: dict):
    global options 
    options._update(updates, copy=False)

