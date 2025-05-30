""" 
Doctest wrappers

         
"""
from __future__ import annotations

import doctest
import pydoc
import inspect
import textwrap
import typing as tp
import re
import inspect

from ..defaults import defaults


DOCTEST_OPTS = doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE

DOCTEST_KARGS = {
        'verbose': defaults.doctests.verbose, 
        'compileflags': defaults.doctests.compileflags, 
        'optionflags': DOCTEST_OPTS,
        }


def render_examples(test):
    """
    Returns the source and expected output for the examples in test
    """
    lines = []
    for eg in test.examples:
        lines.append(f">>> {eg.source}")
        lines.append(eg.want)
        #if eg.want != '':
        #    lines.append('\n')
    return ''.join(lines)



def render_doc(thing):
    """
    Modified doctest.render_doc
    """
    
    renderer = pydoc._PlainTextDoc()

    object, name = pydoc.resolve(thing, 0)
    desc = pydoc.describe(object)
    module = inspect.getmodule(object)

    if name and '.' in name:
        desc += ' in ' + name[:name.rfind('.')]

    elif module and module is not object:
        desc += ' in module ' + module.__name__

    if not (inspect.ismodule(object) 
            or inspect.isclass(object) 
            or inspect.isroutine(object) 
            or inspect.isdatadescriptor(object) 
            or pydoc._getdoc(object)):
        if hasattr(object, '__origin__'):
            object = object.__origin__
        else:
            object = type(object)
            desc += ' object'

    return  (desc, renderer.document(object, name))



def _doc(obj):
    """ 
    Render the docstring of `obj`
    """
    def _fmt(x):
        if x.startswith(' |'):
            x = '  ' + x[2:]
        return x

    desc, doc = render_doc(obj)
    if inspect.isclass(obj):
        doc = '\n'.join(_fmt(x) for x in doc.splitlines())
    return desc + '\n\n' + doc

def run_docstring_examples(
        f, 
        globs, 
        print_examples,
        verbose=False, 
        name="NoName",
        compileflags=None, 
        optionflags=0):
    """ Modified doctests.run_docstring_example
    """
    # Find, parse, and run all tests in the given module.
    finder = doctest.DocTestFinder(verbose=verbose, recurse=False)
    runner = doctest.DocTestRunner(verbose=verbose, optionflags=optionflags)
    
    for test in finder.find(f, name, globs=globs):
        if print_examples is True:
            print(render_examples(test))
        runner.run(test, compileflags=compileflags)

    return doctest.TestResults(runner.failures, runner.tries)


def _mk_doctest_kargs(obj, globs, **kargs):
    """ 
    Return a dictionary with the options to pass to 
    run_docstring_examples
    """
    globs = {} if globs is None else globs
    if obj.__name__ not in globs:
        globs[obj.__name__] = obj
    opts = DOCTEST_KARGS | {'globs': globs}
    return opts


def _mk_doctest_hdr(obj: object):
    """
    """
    sep = '-'*50
    if hasattr(obj, '__module__'):
        mod = f"{obj.__module__}."
    else:
        mod = ''

    msg = f"Running doctest for '{mod}{obj.__name__}'"
    lines = [sep, msg, sep]
    return '\n'.join(lines)

def _get_parm(parm, attr):
    return DEFAULTS['doctest'][attr] if parm is None else parm


def run_doctest(
        obj: tp.Callable,
        print_docstring: bool|None = None,
        print_examples: bool|None = None,
        print_hdr: bool|None = None,
        print_mod: bool|None = None,
        globs: dict|None = None,
        **kargs,
        ):
    """ 
    Display the docstring and run doctest

    Parameters
    ----------
    obj: callable

    **kargs
        Options for doctests, Defaults to DOCTEST_KARGS.
        Must not include 'globs'

    """
    print_docstring = _get_parm(print_docstring, 'print_docstring')
    print_hdr = _get_parm(print_hdr, 'print_hdr')
    print_mod = _get_parm(print_mod, 'print_mod')
    print_examples = _get_parm(print_examples, 'print_examples')

    opts = _mk_doctest_kargs(obj=obj, globs=globs, **kargs)
    opts['print_examples'] = print_examples

    if print_hdr is True:
        print(_mk_doctest_hdr(obj=obj))

    # Run doctest first
    n_err, _ = run_docstring_examples(
        f=obj, 
        **opts)
    if n_err > 0:
        raise Exception(f"Doctest failed")

    if print_docstring is True:
        # Then displays the docstring
        print(_doc(obj))
    #elif print_examples is True:
    #    m = REXAMPLES.search(obj.__doc__)
    #    if m:
    #        hdr = m.group().rstrip() + '\n'
    #        print(hdr)

