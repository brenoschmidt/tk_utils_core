""" 
Github utils

         
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request

def git_url(
        user: str, 
        repo: str, 
        branch: str | None = None,
        assert_exists: bool = False) -> None:
    """
    Construct a GitHub HTTPS URL for a repository, optionally including a
    branch.

    Optionally verifies that the specified repository and/or branch exists
    using the GitHub REST API.

    Parameters
    ----------
    user : str
        GitHub username or organization.

    repo : str
        Name of the repository.

    branch : str, optional
        Name of the branch. If provided, the returned URL includes the branch
        in the format `https://github.com/user/repo.git@branch`.

    assert_exists : bool, default False
        If True, checks whether the specified repository and/or branch exists
        by calling `assert_github_repo` or `assert_github_branch`. Raises
        an exception if not found.

    Returns
    -------
    str
        The constructed GitHub HTTPS URL, optionally suffixed with `@branch`.

    Raises
    ------
    GitHubLookupError
        If the repository does not exist (only raised if `assert_exists=True`).

    GitHubBranchNotFoundError
        If the branch does not exist (only raised if `assert_exists=True` and `branch` is given).

    """
    if assert_exists is True:
        if branch:
            assert_github_branch(user=user, repo=repo, branch=branch)
        else:
            assert_github_repo(user=user, repo=repo)
    tgt = f"https://github.com/{user}/{repo}.git"
    if branch:
        tgt = f"{tgt}@{branch}"
    return tgt

def cnts_url(
        user: str, 
        repo: str, 
        branch: str,
        base: str | None = None,
        assert_exists: bool = False):
    """
    Construct a base URL to access raw content from a GitHub repository
    branch.

    This function builds a URL pointing to the raw content served by
    `raw.githubusercontent.com` for the specified user, repository, and
    branch.  An optional `base` subpath may be appended. Optionally, the
    existence of the repository and branch can be verified using the GitHub
    REST API.

    Parameters
    ----------
    user : str
        GitHub username or organization.

    repo : str
        Name of the repository.

    branch : str
        Name of the branch to fetch content from.

    base : str, optional
        Optional base path within the repository. If provided, it is appended
        to the constructed URL.

    assert_exists : bool, default False
        If True, verifies that the repository and branch exist by calling
        `assert_github_branch`. Raises an exception if either is not found.

    Returns
    -------
    str
        A URL of the form:
        `https://raw.githubusercontent.com/user/repo/branch` or
        `https://raw.githubusercontent.com/user/repo/branch/base`.

    Raises
    ------
    GitHubLookupError
        If the repository does not exist (only raised if `assert_exists=True`).

    GitHubBranchNotFoundError
        If the branch does not exist (only raised if `assert_exists=True`).

    """
    if assert_exists is True:
        if branch:
            assert_github_branch(user=user, repo=repo, branch=branch)
        else:
            assert_github_repo(user=user, repo=repo)
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



