""" 
Subprocess tools

         
"""
from __future__ import annotations

from collections import namedtuple
from typing import Any, Sequence
import subprocess
import sys

Result = namedtuple('Result', ['cmd', 'stdout', 'stderr', 'rc'])


def _assert_success(
        r: Result,
        err_msg: str | None) -> None:
    """
    Raise a RuntimeError if the process did not complete successfully.

    Parameters
    ----------
    r : Result
        The result object from a subprocess.

    err_msg : str or None
        Additional context to add to the exception.
    """
    if r.rc != 0:
        msg = r.stderr.strip()
        if err_msg:
            msg = f"{err_msg}\n{msg}"
        raise RuntimeError(msg)


def _run_and_wait(
        cmds: Sequence[str],
        err_msg: str = '',
        quiet: bool = False) -> Result:
    """
    Run a subprocess command and wait for completion (shell=False).

    Parameters
    ----------
    cmds : list[str]
        Command and arguments to run (e.g. ['ls', '-l']).

    err_msg : str
        Extra message to append if command fails.

    quiet : bool
        If True, suppress stdout on success.

    Returns
    -------
    Result
        A namedtuple containing cmd, stdout, stderr, and return code.
    """
    r = subprocess.run(
        cmds,
        shell=False,
        capture_output=True,
        text=True,
        check=False,
    )
    result = Result(
        cmd=' '.join(cmds),
        stdout=r.stdout.strip(),
        stderr=r.stderr.strip(),
        rc=r.returncode,
    )
    _assert_success(result, err_msg)

    if not quiet and result.stdout:
        print(result.stdout, end='')

    return result


def _run_streaming(
        cmds: Sequence[str],
        err_msg: str = '',
        quiet: bool = False) -> Result:
    """
    Run a subprocess command with real-time stdout streaming.

    Parameters
    ----------
    cmds : list[str]
        Command and arguments to run (e.g. ['ls', '-l']).

    err_msg : str
        Extra message to append if command fails.

    quiet : bool
        If True, suppresses stdout on success.

    Returns
    -------
    Result
        A namedtuple containing cmd, stdout, stderr, and return code.
    """
    proc = subprocess.Popen(
        cmds,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=False,
        bufsize=1,
    )

    stdout_lines = []
    if proc.stdout is not None:
        for line in proc.stdout:
            stdout_lines.append(line)
            if not quiet:
                sys.stdout.write(line)
                sys.stdout.flush()

    stdout, stderr = proc.communicate()

    result = Result(
        cmd=' '.join(cmds),
        stdout='\n'.join(stdout_lines),
        stderr=stderr.strip(),
        rc=proc.returncode,
    )
    _assert_success(result, err_msg)

    return result


def run(
        cmds: Sequence[str],
        err_msg: str = '',
        stream_stdout: bool = False,
        quiet: bool = False,
        echo: bool = False) -> Result:
    """
    Run a subprocess command safely (shell=False).

    Parameters
    ----------
    cmds : list[str]
        Command and arguments to run (e.g. ['ls', '-l']).

    err_msg : str
        Extra message to append if command fails.

    stream_stdout : bool
        If True, streams output in real-time instead of capturing it.

    quiet : bool
        If True, suppresses stdout on success.

    echo : bool
        If True, prints the command being run.

    Returns
    -------
    Result
        A namedtuple containing cmd, stdout, stderr, and return code.
    """
    if not isinstance(cmds, (list, tuple)):
        raise TypeError(
            f"`cmds` must be a list or tuple of strings, got: {type(cmds)}")

    if echo:
        print(f"Running: {' '.join(cmds)}")

    kargs = {
        'cmds': cmds,
        'err_msg': err_msg,
        'quiet': quiet,
    }
    if stream_stdout:
        result = _run_streaming(**kargs)
    else:
        result = _run_and_wait(**kargs)

    return result


def shell_exec(
        cmd: str,
        quiet: bool = False,
        echo: bool = False,
        check: bool = True,
        err_msg: str = '',
        **kargs: Any) -> Result:
    """
    Run a shell command string using shell=True.

    Parameters
    ----------
    cmd : str
        The shell command to execute.

    quiet : bool
        If True, suppresses stdout on success.

    echo : bool
        If True, prints the command being run.

    check : bool
        If True, raises RuntimeError on non-zero return code.

    err_msg : str
        Additional message to include in error.

    **kargs : Any
        Additional arguments passed to subprocess.run.

    Returns
    -------
    Result
        A namedtuple containing cmd, stdout (list), stderr (list), and rc.
    """
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

    return Result(
        cmd=cmd,
        stdout=stdout.splitlines(),
        stderr=stderr.splitlines(),
        rc=rc,
    )
