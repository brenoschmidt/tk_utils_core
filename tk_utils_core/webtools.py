""" 
Web utils

         
"""
from __future__ import annotations

from .core.webtools.downloaders import (
        download,
        download_to_tmp,
        )
from .core.webtools.github import (
        git_url,
        cnts_url,
        )

__all__ = [
        'download',
        'download_to_tmp',
        'git_url',
        'cnts_url',
        ]

