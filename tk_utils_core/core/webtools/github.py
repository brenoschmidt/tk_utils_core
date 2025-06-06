""" 
Github utils

         
"""
from __future__ import annotations


def git_url(user: str, repo: str, branch: str | None = None):
    tgt = f"https://github.com/{user}/{repo}.git"
    if branch:
        tgt = f"{tgt}@{branch}"
    return tgt

def cnts_url(user: str, repo: str, branch: str):
    return f"https://raw.githubusercontent.com/{user}/{repo}/{branch}"



