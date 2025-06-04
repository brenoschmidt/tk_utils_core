""" 
System utils

         
"""
from __future__ import annotations

from collections import namedtuple
from types import SimpleNamespace
from typing import Any, Sequence
import importlib
import subprocess
import sys

from packaging.requirements import Requirement
from packaging.version import Version

def validate_dependencies(requirements: list[str]):
    """
    Validate that the current Python environment satisfies a list of
    PEP 508-style dependency strings.

    This function checks whether:
    - The current Python version satisfies the specified requirement (e.g., "python>=3.12").
    - Each listed package is importable.
    - If available, the installed package version satisfies the given version specifier.

    Parameters
    ----------
    requirements : list of str
        A list of PEP 508-style dependency strings, such as:
        ["python>=3.12", "pandas", "pydantic>=2,<3"]

    Raises
    ------
    RuntimeError
        If the current Python version or an installed package version
        does not satisfy its required version specifier.

    ImportError
        If any required packages are not installed.

    Notes
    -----
    - This function assumes that each non-Python package exposes a
      `__version__` attribute. If missing, version checks are skipped.
    - Package names with hyphens (e.g., "ruamel-yaml") are converted to
      underscores for import (e.g., "ruamel_yaml").
    """
    missing = []
    for req_str in requirements:
        req = Requirement(req_str)
        if req.name == 'python':
            version = Version(
                    f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
            if version not in req.specifier:
                raise RuntimeError(
                        f"Python version {version} does not satisfy {req_str}")
        else:
            try:
                mod = importlib.import_module(req.name.replace('-', '_'))
                version = Version(mod.__version__)
                if version not in req.specifier:
                    raise RuntimeError(
                            f"{req.name} version {version} does not satisfy {req_str}")
            except ImportError:
                missing.append(req.name)
            except AttributeError:
                # Module doesn't expose __version__, skip version check
                pass
    if missing:
        raise ImportError(f"Missing required packages: {', '.join(missing)}")




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

















