""" 
Options for the tk_utils_core module

Notes
-----

To temporarily modify options:

> with options.set_values({'debug': True}):
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
    Pretty-printing options.

    Controls how objects are formatted for display.

    Parameters
    ----------
    color : TOMLStrOrNone
    indent : str
    pretty : bool
    sort_dicts : bool
    depth : TOMLIntOrNone
    underscore_numbers : bool
    width : int
    compact : bool
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
    Options for controlling doctest output.

    Parameters
    ----------
    print_docstring : bool
    print_examples : bool
    print_hdr : bool
    print_mod : bool
    verbose : bool
    compileflags : bool
    """
    print_docstring: bool
    print_examples: bool
    print_hdr: bool
    print_mod: bool
    verbose: bool
    compileflags: bool

class PrettyErrors(BaseConfig):
    """
    Configuration for the pretty_errors module.

    Parameters
    ----------
    pretty_errors : bool
    line_number_first : bool
    display_link : bool
    """
    pretty_errors: bool
    line_number_first: bool
    display_link: bool

class TkUtilsGithub(BaseConfig):
    """
    Location of the tk_utils GitHub repository.

    Parameters
    ----------
    user : str
    repo : str
    branch : str
    base : str
    modules : list[str]
    """
    user: str
    repo: str
    branch: str
    base: str
    modules: list[str]

class TkUtilsCoreGithub(BaseConfig):
    """
    Location of the tk_utils_core GitHub repository.

    Parameters
    ----------
    user : str
    repo : str
    branch : str
    """
    user: str
    repo: str
    branch: str

class Dropbox(BaseConfig):
    """
    Dropbox shared folder configuration.

    Parameters
    ----------
    url : str
    """
    url: TOMLStrOrNone 

class Github(BaseConfig):
    """
    GitHub configuration for tk_utils and tk_utils_core.

    Parameters
    ----------
    tk_utils: TkUtilsGithub
    tk_utils_core: TkUtilsCoreGithub
    """
    tk_utils: TkUtilsGithub 
    tk_utils_core: TkUtilsCoreGithub
    

class PyCharmPaths(BaseConfig):
    """
    Paths related to PyCharm project structure.

    Parameters
    ----------
    root : str
    backup : str
    dropbox : str
    venv : str
    idea : str
    tk_utils : str
    toolkit_config : str
    tk_utils_config : str
    dropbox_zip : str
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
    PyCharm project options.

    Parameters
    ----------
    validate_paths : bool
    prjname : str
    paths : PyCharmPaths
    """
    validate_paths: bool
    prjname: str
    paths: PyCharmPaths

class Describe(BaseConfig):
    """
    Options for the `describe` decorator.

    Parameters
    ----------
    quiet : bool
    show_doc : bool
    show_decor : bool
    show_body : bool
    show_sig : bool
    """
    quiet: bool
    show_doc: bool
    show_decor: bool
    show_body: bool
    show_sig: bool


class Options(BaseConfig):
    """
    Configuration options for the `tk_utils_core` module.

    This class organizes all configurable options into logical groups,
    including debugging, pretty-printing, PyCharm integration, and more.

    Attributes
    ----------
    debug : bool
        Top-level debugging flag.

    describe : Describe
        Options for the `describe` decorator.

    pretty_errors : PrettyErrors
        Options for formatting error messages.

    doctests : Doctests
        Options that control doctest-related output.

    pycharm : PyCharm
        Configuration for PyCharm project layout.

    github : Github
        GitHub repository information for tk_utils and tk_utils_core.

    dropbox : Dropbox
        Dropbox shared folder configuration.

    pp : PP
        Pretty-printing options for debug output and internal formatting.

    dependencies : list of str
        List of external dependencies (by name or path).

    Notes
    -----
    To temporarily modify options:

    >>> with options.set_values({'debug': True}):
    ...     some_func()
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



















