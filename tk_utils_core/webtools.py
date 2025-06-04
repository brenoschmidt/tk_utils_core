""" 
Web utils

         
"""
from __future__ import annotations

from .core.webtoos.downloaders import (
        download,
        download_to_tmp,
        )
from .core.webtoos.github import (
        git_url,
        cnts_url,
        )

__all__ = [
        'download',
        'download_to_tmp',
        'git_url',
        'cnts_url',
        ]

