"""
Logging tools for redirecting stdout (and optionally stderr) to file.

"""

from __future__ import annotations

import sys
import io
import os
import pathlib
import functools
import inspect
import datetime as dt
import dataclasses as dc
from typing import Callable

from ._colorize import colorize, decolorize
from ..structs import BaseParms

__all__ = [
    'Tee',
    'LogParms',
    'LogFunc',
    'logfunc',
]


class Tee:
    """
    Duplicates `stdout` and optionally `stderr` to a file.

    Parameters
    ----------
    file_or_buffer : str or Path or file-like
        Destination file path or open file object.

    mode : str
        File mode (e.g., 'a', 'w', 'ab').

    buff : int, optional
        Buffering policy, not currently used.

    header : str, optional
        Optional header to prepend to the file.

    colorized : bool, default True
        If False, strips ANSI colors from file output.

    Attributes
    ----------
    stdout : stream
        Original `sys.stdout`.

    stderr : stream
        Original `sys.stderr` (if enabled).
    """

    def __init__(
            self,
            file_or_buffer: str | pathlib.Path,
            mode: str,
            buff: int = 0,
            header: str | None = None,
            colorized: bool = True,
            capture_stderr: bool = False,):
        if isinstance(file_or_buffer, io.IOBase):
            self.fobj = file_or_buffer
        else:
            encoding = None if "b" in mode else "utf-8"
            self.fobj = open(file_or_buffer, mode, encoding=encoding)

        self.header = header
        self.colorized = colorized
        self._write_header = header is not None
        self._closed = False

        self.stdout = sys.stdout
        sys.stdout = self

        self.capture_stderr = capture_stderr
        if capture_stderr:
            self.stderr = sys.stderr
            sys.stderr = self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self._closed:
            self.close()

    def decolorize(self, data: str) -> str:
        """Remove ANSI color codes."""
        return decolorize(data)

    def filter_file_data(self, data: str) -> str:
        if not self.colorized:
            data = self.decolorize(data)
        return data

    def filter_stream_data(self, data: str) -> str:
        return data

    def flush(self):
        """Flush all output streams."""
        self.fobj.flush()
        self.stdout.flush()
        if self.capture_stderr:
            self.stderr.flush()

    def close(self):
        self.flush()
        if self.capture_stderr:
            sys.stderr = self.stderr
        sys.stdout = self.stdout
        self.fobj.close()
        self._closed = True

    def write(self, data: str):
        """Write to both file and stream."""
        file_data = self.filter_file_data(data)
        stream_data = self.filter_stream_data(data)

        if self._write_header:
            header = self.header
            if not header.endswith('\n'):
                header += '\n'
            self.fobj.write(header)
            self._write_header = False

        self.fobj.write(file_data)
        self.stdout.write(stream_data)
        self.stdout.flush()

    def isatty(self):
        return False

    def __del__(self):
        if hasattr(self, '_closed') and not self._closed:
            self.close()


def _get_py_file(func: Callable) -> str | None:
    module = inspect.getmodule(func)
    if module and hasattr(module, '__file__'):
        return pathlib.Path(module.__file__).name
    return None


def _mk_header(
        func: Callable,
        started: dt.datetime,
        color: str = 'green') -> str:
    """
    Create a header string for the log file.

    Parameters
    ----------
    func : Callable
        Function being logged.

    started : datetime
        Start timestamp.

    color : str
        Color to apply to the header.

    Returns
    -------
    str
        Colorized header block.
    """
    sep = '-' * 50
    started_str = started.strftime('%Y-%m-%d %H:%M:%S')
    mod = _get_py_file(func) or "<unknown>"
    lines = [
        '',
        sep,
        f"Log started: {started_str}",
        f"File: {mod}",
        f"Func: {func.__name__}",
        sep,
        '',
    ]
    return '\n'.join(colorize(x, color=color) for x in lines)


@dc.dataclass
class LogParms:
    """
    Logging parameters for `LogFunc`.

    Either `root` or `pth` must be provided.

    Attributes
    ----------
    root : str or Path, optional
        Directory for the log file.

    mode : str
        File mode (e.g., 'a', 'w').

    basename : str, optional
        Name stem for the file, without date or suffix.

    name : str, optional
        Full file name (used if `pth` is None).

    started : datetime, optional
        Timestamp used in file naming.

    pth : Path, optional
        Explicit full path for the log file.
    """
    root: str | pathlib.Path | None = None
    mode: str = 'a'
    basename: str | None = None
    name: str | None = None
    started: dt.datetime | None = None
    pth: pathlib.Path | None = None

    def __post_init__(self):
        if self.started is None:
            self.started = dt.datetime.now()

        if self.pth is not None and self.root is not None:
            raise ValueError("Only one of `pth` or `root` may be set.")

        if self.pth is None and self.root is None:
            raise ValueError("Either `pth` or `root` must be provided.")

        if self.pth is None:
            if not isinstance(self.root, pathlib.Path):
                self.root = pathlib.Path(self.root)

            if self.name is None:
                if self.basename is None:
                    raise ValueError("Must provide either `name` or `basename`.")
                self.name = '.'.join([
                    self.basename,
                    self.started.strftime('%Y-%m-%d'),
                    'log'
                ])
            elif self.basename is not None:
                raise ValueError("If `name` is set, `basename` must be None.")

            self.pth = self.root / self.name
        else:
            self.root = self.pth.parent
            self.basename = self.pth.stem
            self.name = self.pth.name


class LogFunc(Tee):
    """
    Context manager that logs a function call to a timestamped log file.

    Parameters
    ----------
    root : str or Path
        Directory to save log file.

    func : Callable
        Function object (for naming and headers).

    basename : str, optional
        File name prefix (defaults to function name).

    mode : str, default 'a'
        File mode.

    Other Parameters
    ----------------
    Any other keyword arguments are passed to `LogParms`.

    Examples
    --------
    >>> with LogFunc(root='_logs', func=print):
    ...     print("Logging inside context.")
    """
    def __init__(
            self,
            root: str | pathlib.Path,
            func: Callable,
            basename: str | None = None,
            mode: str = 'a',
            **kargs):
        if basename is None:
            basename = func.__name__
        self.opts = LogParms(
            root=root,
            mode=mode,
            basename=basename,
            **kargs)

        self.opts.root.mkdir(parents=True, exist_ok=True)
        _header = _mk_header(func=func, started=self.opts.started)
        super().__init__(
            file_or_buffer=self.opts.pth,
            mode=self.opts.mode,
            header=_header,
        )


def logfunc(
        root: str | pathlib.Path,
        mode: str = 'a',
        **context_kargs):
    """
    Decorator to log stdout of a function to a timestamped file.

    Parameters
    ----------
    root : str or Path
        Directory for log output.

    mode : str, default 'a'
        File mode.

    **context_kargs
        Passed to `LogFunc` constructor.

    Returns
    -------
    Callable
        Wrapped function with logging applied.

    Examples
    --------
    >>> @logfunc(root='_log')
    ... def say_hello():
    ...     print("Hello!")
    >>> say_hello()
    Hello!
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kargs):
            with LogFunc(
                    root=root,
                    func=func,
                    mode=mode,
                    **context_kargs):
                return func(*args, **kargs)
        return wrapper
    return decorator
