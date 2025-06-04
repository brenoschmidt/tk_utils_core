""" 
Web utils

         
"""
from __future__ import annotations

from tk_utils_core.core.webtools.downloaders import (
        download,
        download_to_tmp,
        )
from tk_utils_core.core.webtools.github import (
        git_url,
        cnts_url,
        )

__all__ = [
        'download',
        'download_to_tmp',
        'git_url',
        'cnts_url',
        ]

