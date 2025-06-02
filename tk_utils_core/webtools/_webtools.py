""" 
Downloaders

         
"""
from __future__ import annotations

import pathlib
import requests
import tempfile


def download_to_tmp(url: str) -> pathlib.Path:
    """
    Request and download to a temporary file and return its location
    """
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()

        with tempfile.NamedTemporaryFile("w", 
                                         encoding=r.encoding or "utf-8", 
                                         delete=False) as f:
            f.write(r.text)
            tmp = pathlib.Path(f.name)
        return tmp 
    except Exception as e:
        print(f"Download failed: {e}")








