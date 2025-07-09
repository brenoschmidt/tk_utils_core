""" 
Code parsers
"""
from __future__ import annotations

from tk_utils_core.core.codeparser._codeparser import (
        diff_lines,
        )
from tk_utils_core.core.codeparser import (
        _ast as ast,
        _parso as parso,
        )

__all__ = [
        'diff_lines',
        'ast',
        'parso',
        ]

