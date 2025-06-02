""" 
File system utils

         
"""
from __future__ import annotations

import os
import pathlib
import shutil
import zipfile

from .core.fstools.safeio import (
        copy_with_parents,
        safe_copy,
        safe_copytree,
        )
from .core.fstools.walk import walk 


__all__ = [
        'copy_with_parents',
        'safe_copy',
        'safe_copytree',
        'walk',
        'unzip',
        ]


class _ZipFile(zipfile.ZipFile):
    """ 
    Patched ZipFile class to prevent errors of the type

        ValueError: Empty filename.

    when calling extractall
    """

    def extractall(self, path=None, members=None, pwd=None):
        """
        Extract all members from the archive to the current working
        directory. `path' specifies a different directory to extract to.
        `members' is optional and must be a subset of the list returned
        by namelist().
        """
        if members is None:
            members = self.namelist()
        if path is None:
            path = os.getcwd()
        else:
            path = os.fspath(path)

        for zipinfo in members:
            if zipinfo == '/':
                continue
            self._extract_member(zipinfo, path, pwd)

def unzip(src: str | pathlib.Path, dst: str | pathlib.Path):
    """  
    Extract `src` to `dst`

    """
    try:
        with zipfile.ZipFile(tmp) as zf:
            zf.extractall(dst)
    except ValueError:
        with _ZipFile(tmp) as zf:
            zf.extractall(dst)


