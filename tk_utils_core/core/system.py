""" 
System utils

         
"""
from __future__ import annotations

from collections import namedtuple
from types import SimpleNamespace
from typing import Any
import importlib
import shlex
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
        cmd: list[str] | str,
        shell: bool = True,
        quiet: bool = False,
        echo: bool = False,
        bufsize: int = 0,
        err_msg: str = '',
        **kargs: Any) -> namedtuple:
    """
    Run a shell or subprocess command and capture output.

    Parameters
    ----------
    cmd : list[str] | str
        Command to run.

    shell : bool, default True
        If True, run the command via the shell.

    quiet : bool, default False
        If True, do not print stdout.

    echo : bool, default False
        If True, print the command being executed.

    bufsize : int, default 0
        Buffer size passed to subprocess.Popen.

    err_msg : str, default ''
        Extra message to include if the command fails.

    **kargs : Any
        Passed to subprocess.Popen.

    Returns
    -------
    Result
        Named tuple with fields: cmd, stdout, stderr, rc (return code).
    """
    Result = namedtuple('Result', ['cmd', 'stdout', 'stderr', 'rc'])

    cmd_list = cmd if isinstance(cmd, list) else shlex.split(cmd)
    cmd_str = ' '.join(cmd_list) if shell else cmd_list

    if echo:
        print(f"Running: {cmd_str}")

    proc = subprocess.Popen(
        cmd_str,
        shell=shell,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=bufsize,
        **kargs,
    )
    out, err = proc.communicate()
    rc = proc.returncode

    out_str = out.decode('utf-8') if out else ''
    err_str = err.decode('utf-8') if err else ''

    if not quiet and out_str:
        print(out_str)

    if rc != 0:
        msg = f"Command failed [{rc}]: {cmd_str}"
        if err_msg:
            msg += f"\n{err_msg}"
        msg += f"\n{err_str.strip()}"
        raise RuntimeError(msg)

    return Result(cmd=cmd_str, stdout=out_str.splitlines(),
                  stderr=err_str.splitlines(), rc=rc)


















