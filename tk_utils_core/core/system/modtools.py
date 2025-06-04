""" 
Packaging tools

         
"""
from __future__ import annotations

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


















