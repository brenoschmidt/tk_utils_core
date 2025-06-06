""" 
Github utils

         
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request

def git_url(user: str, repo: str, branch: str | None = None):
    tgt = f"https://github.com/{user}/{repo}.git"
    if branch:
        tgt = f"{tgt}@{branch}"
    return tgt

def cnts_url(
        user: str, 
        repo: str, 
        branch: str,
        base: str | None = None):
    out = f"https://raw.githubusercontent.com/{user}/{repo}/{branch}"
    if base:
        out = f"{out}/{base}"
    return out


class GitHubLookupError(Exception):
    """Raised when the GitHub user or repository is not found."""
    pass

class GitHubBranchNotFoundError(Exception):
    """Raised when the specified branch is not found in the repository."""
    pass

def assert_github_repo(
        user: str,
        repo: str) -> None:
    """
    Assert that a repo exists in a public GitHub repository.

    Parameters
    ----------
    user : str
        GitHub username or organization.

    repo : str
        Repository name.

    Raises
    ------
    GitHubLookupError
        If the user or repo does not exist.

    """
    url = f"https://api.github.com/repos/{user}/{repo}"
    
    # Check repo exists
    try:
        with urllib.request.urlopen(url) as r:
            if r.status != 200:
                raise GitHubLookupError(f"Repo not found: {user}/{repo}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise GitHubLookupError(f"Repo not found: {user}/{repo}")
        raise


def assert_github_branch(
        user: str,
        repo: str,
        branch: str) -> None:
    """
    Assert that a branch exists in a public GitHub repository.

    Parameters
    ----------
    user : str
        GitHub username or organization.

    repo : str
        Repository name.

    branch : str
        Branch name to check.

    Raises
    ------
    GitHubLookupError
        If the user or repo does not exist.

    GitHubBranchNotFoundError
        If the branch does not exist.
    """
    assert_github_repo(user=user, repo=repo)
    
    url = f"https://api.github.com/repos/{user}/{repo}/branches/{branch}"
    # Check branch exists
    try:
        with urllib.request.urlopen(url) as r:
            if r.status != 200:
                raise GitHubBranchNotFoundError(
                    f"Branch '{branch}' not found in {user}/{repo}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise GitHubBranchNotFoundError(
                f"Branch '{branch}' not found in {user}/{repo}")
        raise



