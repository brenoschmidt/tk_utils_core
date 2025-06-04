""" 
Github utils

         
"""
from __future__ import annotations


def git_url(user: str, repo: str):
    return f"https://github.com/{user}/{repo}.git"

def cnts_url(user: str, repo: str, branch: str):
    return f"https://raw.githubusercontent.com/{user}/{repo}/{branch}"



