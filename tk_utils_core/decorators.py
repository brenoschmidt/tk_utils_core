""" 
Decorators

         
"""
from __future__ import annotations

import functools
import textwrap
import inspect

from tk_utils_core.messages import fmt_msg
from tk_utils_core.codeparser import ParsedFunc
from tk_utils_core.options import options

__all__ = [
        'describe',
        ]

def _mk_describe_opts(**kargs):
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
    Parse and describe a callable
    """
    msg = [f"Running {func.__qualname__}"]

    parsed = ParsedFunc(func)
    parts = parsed.as_ntup(dedent=True, use_doc_attr=True)

    if opts['show_sig'] is True:
        msg.append(parts.sig)
    if opts['show_doc']:
        msg.append('Docstring:')
        msg.append(textwrap.indent(parts.doc, '    '))
    if opts['show_body']:
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
    Decorator to describe the decorated function
    Does nothing if options.describe is False
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


