""" 
Options for the tk_utils_core module

Notes
-----

To temporarily modify options:

> with options.updated(:
>     options._update({'debug': True})
>     some_func()
         
"""
from __future__ import annotations

from contextlib import contextmanager
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
    Pretty-printing options
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
    Doctests options
    """
    print_docstring: bool
    print_examples: bool
    print_hdr: bool
    print_mod: bool
    verbose: bool
    compileflags: bool

class PrettyErrors(BaseConfig):
    """
    Configuration options for the pretty_error module
    """
    pretty_errors: bool
    line_number_first: bool
    display_link: bool

class TkUtilsGithub(BaseConfig):
    """
    Location of the tk_utils module in Github
    """
    user: str
    repo: str
    branch: str
    base: str
    modules: list[str]

class TkUtilsCoreGithub(BaseConfig):
    """
    Location of the tk_utils module in Github
    """
    user: str
    repo: str
    branch: str

class Dropbox(BaseConfig):
    """
    Dropbox shared folder URL
    """
    url: TOMLStrOrNone 

class Github(BaseConfig):
    """
    """
    tk_utils: TkUtilsGithub 
    tk_utils_core: TkUtilsCoreGithub
    

class PyCharmPaths(BaseConfig):
    """
    Location of files and folders in PyCharm
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

class Describe(BaseConfig):
    """
    Controls the `describe` decorator
    """
    quiet: bool
    show_doc: bool
    show_decor: bool
    show_body: bool
    show_sig: bool


class Options(BaseConfig):
    """
    """
    debug: bool
    describe: Describe
    pretty_errors: PrettyErrors
    doctests: Doctests
    pycharm: PyCharm
    github: Github
    dropbox: Dropbox
    pp: PP
    dependencies: list[str]


    @contextmanager
    def set_values(self, updates: dict[str, Any]):
        """
        Temporarily update configuration values.

        Parameters
        ----------
        updates : dict of str to Any
            Dictionary of keys and temporary values. Keys may use dot notation
            for nested fields.

        Yields
        ------
        None
            Context where the config reflects the temporary updates.

        Examples
        --------
        Temporarily enable debug mode:

        >>> with options.set_values({'debug': True}):
        ...     some_func()

        Temporarily change a nested option:

        >>> with options.set_values({'pp.color': 'red'}):
        ...     some_func()

        After the block exits, the previous values are restored:

        >>> assert options.debug is False
        >>> assert options.pp.color != 'red'
        """
        original = self.model_dump()
        self._update(updates)
        try:
            yield
        finally:
            self._update(original)


def _mk_defaults() -> Options:
    pth = pathlib.Path(__file__).with_name("defaults.toml")
    dflts = load_toml_defaults(pth)
    return Options.model_validate(dflts)

options = _mk_defaults()

def configure(updates: dict):
    global options 
    options._update(updates, copy=False)

