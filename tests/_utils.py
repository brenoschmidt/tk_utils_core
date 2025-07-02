""" 
Testing utils

         
"""
from __future__ import annotations

import pathlib
import os
import sys
from collections import namedtuple


# Add assets to system path
try:
    import eg_module
except ImportError:
    TEST_DIR = pathlib.Path(__file__).resolve().parent
    EXAMPLES_DIR = TEST_DIR.joinpath('assets', 'examples')
    sys.path.insert(0, str(EXAMPLES_DIR))
    import eg_module

ExampleObj = namedtuple('ExampleObj', [
    'obj',
    'src',
    'name',
    ])

def get_mod_src(mod):
    """
    """
    with open(pathlib.Path(mod.__file__).resolve()) as f:
        src = f.read()
    return src


def get_lines_between(
        text: str,
        start: str,
        end: str,
        as_list: bool = False) -> str | list[str] | None:
    """
    Extract lines between `start` and `end` markers.
    """
    lines = text.splitlines()
    in_block = False
    out = []
    for line in lines:
        if start in line:
            in_block = True
            continue
        if end in line:
            break
        if in_block:
            out.append(line)

    if len(out) == 0:
        return None
    elif as_list is False:
        return '\n'.join(out)
    else:
        return out

def get_tagged_src(mod, tag):
    """
    """
    cnts = get_mod_src(mod)
    start = f"<{tag}>"
    end = f"</{tag}>"
    for x in [start, end]:
        if x not in cnts:
            raise Exception(f"Tag {x} not found in {mod.__name__}\n{cnts}")
    return get_lines_between(cnts, start=start, end=end)



