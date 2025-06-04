""" 
Subprocess tools

         
"""
from __future__ import annotations

from collections import namedtuple
from types import SimpleNamespace
from typing import Any, Sequence
import importlib
import subprocess
import sys

def run(
        cmds: Sequence[str],
        err_msg: str = '',
        echo: bool = False,
        quiet: bool = False) -> None:
    """
    Run a subprocess command safely (shell=False).

    Parameters
    ----------
    cmds : list[str]
        Command and arguments to run (e.g. ['ls', '-l'])

    err_msg : str
        Extra message to append if command fails.

    echo : bool
        If True, prints the command being run.

    quiet : bool
        If True, suppresses stdout on success.
    """
    if not isinstance(cmds, (list, tuple)):
        raise TypeError(
                f"`cmds` must be a list or tuple of strings, got: {type(cmds)}")

    if echo:
        print(f"Running: {' '.join(cmds)}")

    r = subprocess.run(
        cmds,
        shell=False,
        capture_output=True,
        text=True,
        check=False,
    )

    if r.returncode != 0:
        msg = r.stderr.strip()
        if err_msg:
            msg = f"{err_msg}\n{msg}"
        raise RuntimeError(msg)

    if not quiet and r.stdout:
        print(r.stdout, end='')

    return r


def shell_exec(
        cmd: str,
        quiet: bool = False,
        echo: bool = False,
        check: bool = True,
        err_msg: str = '',
        **kargs: Any) -> namedtuple:
    """
    Run a shell command (string) using shell=True.

    Parameters
    ----------
    cmd : str
        The command to execute (as a shell string).

    quiet : bool, default False
        Suppress printing of stdout.

    echo : bool, default False
        Print the command before executing.

    check : bool, default True
        Raise RuntimeError on non-zero return code.

    err_msg : str, default ''
        Extra message included in the error if check fails.

    **kargs : Any
        Extra arguments passed to subprocess.run

    Returns
    -------
    Result
        Namedtuple(cmd, stdout, stderr, rc)
    """
    Result = namedtuple('Result', ['cmd', 'stdout', 'stderr', 'rc'])
    if echo:
        print(f"Running (shell): {cmd}")

    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        check=False,
        **kargs,
    )

    stdout = result.stdout or ''
    stderr = result.stderr or ''
    rc = result.returncode

    if not quiet and stdout:
        print(stdout, end='')

    if check and rc != 0:
        msg = f"Shell command failed [{rc}]: {cmd}"
        if err_msg:
            msg += f"\n{err_msg}"
        if stderr:
            msg += f"\n{stderr.strip()}"
        raise RuntimeError(msg)

    return Result(cmd=cmd, 
                  stdout=stdout.splitlines(), 
                  stderr=stderr.splitlines(), rc=rc)

