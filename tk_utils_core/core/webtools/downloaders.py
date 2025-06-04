""" 
Downloaders

         
"""
from __future__ import annotations

import pathlib
import requests
import tempfile

from ..converters import as_path


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


def download(
        url: str,
        pth: str | pathlib.Path,
        replace: bool = False) -> pathlib.Path:
    """
    Download a file from a URL to a local path.

    Parameters
    ----------
    url : str
        The URL of the file to download.

    pth : str | Path
        The destination path to save the downloaded file.

    replace : bool, default False
        If False and the destination file exists, raises FileExistsError.

    Returns
    -------
    Path
        The path to the downloaded file.

    Raises
    ------
    FileExistsError
        If the file exists and `replace=False`.

    requests.HTTPError
        If the HTTP request fails.
    """
    pth = pathlib.Path(pth)

    if pth.exists() and not replace:
        raise FileExistsError(f"File exists and `replace` is False:\n{pth}")

    # Ensure parent directory exists
    pth.parent.mkdir(parents=True, exist_ok=True)

    # Perform request
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(pth, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

    return pth


