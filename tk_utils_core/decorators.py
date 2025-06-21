""" 
Decorators

         
"""
from __future__ import annotations

import functools
import textwrap
from typing import Callable

from tk_utils_core.messages import fmt_msg
from tk_utils_core.codeparser import ParsedFunc
from tk_utils_core.options import options

__all__ = [
        'describe',
        ]

@functools.lru_cache(4)
def _mk_describe_opts(**kargs):
    """
    Merge runtime keyword arguments with default options.

    Parameters
    ----------
    **kargs : dict
        Optional overrides for `options.describe`. Only non-None values
        are applied.

    Returns
    -------
    dict
        A merged dictionary with resolved describe options.
    """
    out = options.describe.model_dump() 
    out.update(
            (k,v) for k, v in kargs.items() if v is not None)
    return out

def _mk_describe_msg(
        func: Callable,
        opts: dict,
        header: bool,
        ) -> str:
    """
    Construct a formatted description for a function call.

    Parameters
    ----------
    func : Callable
        The function being described.

    opts : dict
        Dictionary with description flags like `show_doc`, `show_sig`,
        and `show_body`.

    header : bool
        Whether to format the output using `fmt_msg(..., as_hdr=True)`.

    Returns
    -------
    str
        A formatted multiline string describing the function call.
    """
    parsed = ParsedFunc(func)
    parts = parsed.as_ntup(dedent=True, use_doc_attr=True)

    if opts['show_sig'] is True:
        sig = parsed.mk_sig(['name', 'parms', 'arrow', 'annotation'])
    else:
        sig = func.__qualname__

    if opts['show_decor'] is True and parsed.nodes.decor:
        sig = f"\n{parsed.codes.decor}\n{sig}"

    msg = [f"Running {sig}"]

    if opts['show_doc'] is True and parsed.nodes.doc:
        msg.append('Docstring:')
        msg.append(textwrap.indent(parts.doc, '    ').rstrip())
    if opts['show_body']:
        msg.append('Body:')
        msg.append(parts.body)

    msg = fmt_msg(msg, as_hdr=True, as_list=True)

    msg.append('Output:\n')
    return '\n'.join(msg)


def describe(
        _func=None,
        *,
        show_doc: bool | None = None,
        show_decor: bool | None = None,
        show_body: bool | None = None,
        show_sig: bool | None = None,
        quiet: bool | None = None,
        header: bool = True,
        ):
    """
    Decorator to print structured information before calling a function.

    When active, this decorator prints a structured header with selected
    metadata about the function — such as its signature, decorators,
    docstring, and body — before executing it.

    Parameters
    ----------
    _func : Callable or None
        Allows the decorator to be used with or without parentheses.

    show_doc : bool or None, optional
        Whether to print the function's docstring.

    show_decor : bool or None, optional
        Whether to print any decorators above the function definition.

    show_body : bool or None, optional
        Whether to print the function's source body.

    show_sig : bool or None, optional
        Whether to print a full signature (name, parameters, return
        annotation) instead of just the function name.

    quiet : bool or None, optional
        If True, suppress all output (overrides other options).

    header : bool, default True
        Whether to wrap the output in a standard header using `fmt_msg`.

    Returns
    -------
    Callable
        The decorated function.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kargs):
            opts = _mk_describe_opts(
                    show_doc=show_doc,
                    show_decor=show_decor,
                    show_body=show_body,
                    show_sig=show_sig,
                    quiet=quiet,
                    )
            if opts['quiet']:
                return func(*args, **kargs)
            else:
                msg = _mk_describe_msg(
                        func=func,
                        opts=opts,
                        header=header,
                        )
                print(msg)
                return func(*args, **kargs)
        return wrapper
    if _func is None:
        return decorator
    else:
        return decorator(_func)


