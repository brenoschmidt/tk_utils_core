""" 
Doctest wrappers

         
"""
from __future__ import annotations

import doctest
import pydoc
import inspect
from typing import Callable
from functools import lru_cache
from types import SimpleNamespace

from ..options import options


@lru_cache(1)
def _mk_dflt_opts():
    """
    Return a dictionary of default doctest options sourced from
    options.doctests.

    The returned dictionary includes:
    - compileflags
    - print_docstring
    - print_examples
    - print_hdr
    - print_mod
    - verbose
    - name: defaulted to 'NoName'
    - optionflags: doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE
    """
    attrs = [
        'compileflags',
        'print_docstring',
        'print_examples',
        'print_hdr',
        'print_mod',
        'verbose',
    ]
    out = {
        'name': 'NoName',
        'optionflags': doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE,
    }
    out.update((x, getattr(options.doctests, x)) for x in attrs)
    return out


@lru_cache(10)
def _mk_opts(**kargs):
    """
    Return a SimpleNamespace of doctest options by merging defaults with
    overrides.

    Parameters
    ----------
    **kargs : dict
        Optional keyword overrides for any of the doctest settings.

    Returns
    -------
    SimpleNamespace
        A namespace containing the full configuration.
    """
    dflt = dict(_mk_dflt_opts())
    dflt['globs'] = {}
    updates = {k: v for k, v in kargs.items() if v is not None}
    return SimpleNamespace(**(dflt | updates))


def render_examples(test):
    """
    Render doctest examples from a parsed DocTest object.

    Parameters
    ----------
    test : doctest.DocTest
        A doctest object containing examples.

    Returns
    -------
    str
        A formatted string showing each example's input and expected output.
    """
    lines = []
    for eg in test.examples:
        lines.append(f">>> {eg.source.rstrip()}")
        lines.append(eg.want.rstrip())
        lines.append("")  # Separate examples
    return ''.join(lines)


def render_doc(thing):
    """
    Render the documentation string for a Python object using pydoc.

    Parameters
    ----------
    thing : object
        The object whose documentation will be rendered.

    Returns
    -------
    tuple[str, str]
        A pair (description, docstring) suitable for printing.
    """
    renderer = pydoc._PlainTextDoc()
    obj, name = pydoc.resolve(thing, 0)
    desc = pydoc.describe(obj)
    module = inspect.getmodule(obj)

    if name and '.' in name:
        desc += ' in ' + name[:name.rfind('.')]
    elif module and module is not obj:
        desc += ' in module ' + module.__name__

    if not (
        inspect.ismodule(obj)
        or inspect.isclass(obj)
        or inspect.isroutine(obj)
        or inspect.isdatadescriptor(obj)
        or pydoc._getdoc(obj)
    ):
        if hasattr(obj, '__origin__'):
            obj = obj.__origin__
        else:
            obj = type(obj)
            desc += ' obj'

    return desc, renderer.document(obj, name)


def _doc(obj):
    """
    Format and return the docstring of a Python object.

    Parameters
    ----------
    obj : object
        The object whose docstring should be rendered.

    Returns
    -------
    str
        A formatted string combining a description and the docstring.
    """
    def _fmt(x):
        return '  ' + x[2:] if x.startswith(' |') else x

    desc, doc = render_doc(obj)
    if inspect.isclass(obj):
        doc = '\n'.join(_fmt(x) for x in doc.splitlines())
    return desc + '\n\n' + doc


def run_docstring_examples(
        f,
        globs,
        print_examples,
        verbose,
        name,
        compileflags,
        optionflags):
    """
    Run all docstring examples for a given callable using doctest.

    Parameters
    ----------
    f : Callable
        The object to test.
    globs : dict
        Global variables available to the doctest.
    print_examples : bool
        Whether to print the test examples before running them.
    verbose : bool
        Verbosity flag for doctest.
    name : str
        Name for the doctest context.
    compileflags : int
        Compile flags for doctest.
    optionflags : int
        Option flags for doctest.

    Returns
    -------
    doctest.TestResults
        Object with counts of failures and attempted tests.
    """
    finder = doctest.DocTestFinder(verbose=verbose, recurse=False)
    runner = doctest.DocTestRunner(verbose=verbose, optionflags=optionflags)

    for test in finder.find(f, name, globs=globs):
        if print_examples:
            print(render_examples(test))
        runner.run(test, compileflags=compileflags)

    return doctest.TestResults(runner.failures, runner.tries)


def _mk_doctest_hdr(obj: object):
    """
    Return a header string indicating the object being tested.

    Parameters
    ----------
    obj : object
        The object whose doctests are being run.

    Returns
    -------
    str
        A formatted header.
    """
    sep = '-' * 50
    mod = f"{obj.__module__}." if hasattr(obj, '__module__') else ''
    msg = f"Running doctest for '{mod}{obj.__name__}'"
    return '\n'.join([sep, msg, sep])


def run_doctest(
        obj: Callable,
        print_docstring: bool | None = None,
        print_examples: bool | None = None,
        print_hdr: bool | None = None,
        print_mod: bool | None = None,
        verbose: bool | None = None,
        globs: dict | None = None,
        name: str | None = None):
    """
    Display the docstring and run any inline doctests found in a callable.

    Parameters
    ----------
    obj : Callable
        The object to test (function, method, or class).
    print_docstring : bool, optional
        Whether to print the docstring after testing.
    print_examples : bool, optional
        Whether to print test examples before running.
    print_hdr : bool, optional
        Whether to print a header before testing.
    print_mod : bool, optional
        Whether to print module information (currently unused).
    verbose : bool, optional
        Whether to run doctest in verbose mode.
    globs : dict, optional
        A dictionary of globals for the doctest environment.
    name : str, optional
        Optional name to override the default for the doctest.

    Returns
    -------
    doctest.TestResults
        The result object containing number of failures and attempts.

    Raises
    ------
    Exception
        If any doctest fails.
    """
    opts = _mk_opts(
        print_docstring=print_docstring,
        print_examples=print_examples,
        print_hdr=print_hdr,
        print_mod=print_mod,
        verbose=verbose,
        globs=globs,
        name=name,
    )

    if obj.__name__ not in opts.globs:
        opts.globs[obj.__name__] = obj

    if opts.print_hdr:
        print(_mk_doctest_hdr(obj))

    results = run_docstring_examples(
        f=obj,
        globs=opts.globs,
        print_examples=opts.print_examples,
        verbose=opts.verbose,
        name=opts.name,
        compileflags=opts.compileflags,
        optionflags=opts.optionflags,
    )

    if results.failed > 0:
        raise Exception(f"Doctest failed: {results.failed} failures")

    if opts.print_docstring:
        print(_doc(obj))

    return results

def run_quiet_doctest(
        obj: Callable,
        globs: dict | None = None,
        name: str | None = None,
        ):
    """
    Run doctests silently

    Parameters
    ----------
    obj : Callable
        The object to test (function, method, or class).
    globs : dict, optional
        A dictionary of globals for the doctest environment.
    name : str, optional
        Optional name to override the default for the doctest.

    Returns
    -------
    doctest.TestResults
        The result object containing number of failures and attempts.

    Raises
    ------
    Exception
        If any doctest fails.
    """
    return run_doctest(
            obj=obj,
            name=name,
            globs=globs,
            print_docstring=False,
            print_examples=False,
            print_hdr=False,
            print_mod=False,
            verbose=False,
            )


