"""
Tests the `tk_utils_core/webtools.py` module

"""

from __future__ import annotations

from unittest.mock import patch, MagicMock
import tempfile
import pathlib
import os

from tk_utils_core.testing.unittest_runner import (
        BaseTestCase,
        run_tests,
        )

from tk_utils_core.webtools import (
        download,
        download_to_tmp,
        github,
        )
from tk_utils_core.options import options

class TestWebtoolsMod(BaseTestCase):
    """
    Test the `tk_utils_core/webtools.py` module
    """
    _only_in_debug = [
            ]

    def test_download_to_tmp(self):
        """
        """
        self._start_msg()

        # Test success

        fake_text = "hello from the web"
        fake_url = "https://example.com/data.txt"

        mock_response = MagicMock()
        mock_response.text = fake_text
        mock_response.status_code = 200
        mock_response.encoding = "utf-8"
        mock_response.raise_for_status = MagicMock()

        with patch("requests.get", return_value=mock_response):
            tmp_path = download_to_tmp(fake_url)
            self.assertIsInstance(tmp_path, pathlib.Path)
            self.assertTrue(tmp_path.exists())
            with tmp_path.open("r", encoding="utf-8") as f:
                self.assertEqual(f.read(), fake_text)

        # Test failures
        with patch("requests.get", side_effect=Exception("timeout")):
            tmp = download_to_tmp("https://example.com/fail")
            self.assertIsNone(tmp)  # or check print/log if not returning None
        # Clean up
        #tmp_path.unlink()

    def test_download_success_to_new_file(self):
        """
        Download to a non-existent file path
        """
        self._start_msg()

        # Setup fake URL and destination path
        url = "https://example.com/fake.bin"
        tmp_dir = tempfile.TemporaryDirectory()
        dst = pathlib.Path(tmp_dir.name) / "file.bin"

        mock_response = MagicMock()
        mock_response.iter_content = lambda chunk_size: [b"data1", b"data2"]
        mock_response.__enter__.return_value = mock_response
        mock_response.raise_for_status = MagicMock()

        with patch("requests.get", return_value=mock_response):
            out_path = download(url, dst)
            self.assertTrue(out_path.exists())
            content = out_path.read_bytes()
            self.assertEqual(content, b"data1data2")

        tmp_dir.cleanup()

    def test_download_raises_if_file_exists(self):
        """
        Should raise FileExistsError if file exists and replace=False
        """
        self._start_msg()

        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        tmp_path = pathlib.Path(tmp_file.name)
        tmp_file.close()  # Leave file in place

        try:
            with self.assertRaises(FileExistsError):
                download("https://example.com", tmp_path, replace=False)
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_download_replaces_file(self):
        """
        Should overwrite file if replace=True
        """
        self._start_msg()

        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        tmp_path = pathlib.Path(tmp_file.name)
        tmp_path.write_text("OLD")

        mock_response = MagicMock()
        mock_response.iter_content = lambda chunk_size: [b"NEW"]
        mock_response.__enter__.return_value = mock_response
        mock_response.raise_for_status = MagicMock()

        with patch("requests.get", return_value=mock_response):
            download("https://example.com", tmp_path, replace=True)
            self.assertEqual(tmp_path.read_bytes(), b"NEW")

        tmp_path.unlink(missing_ok=True)

    def test_download_http_error(self):
        """
        Should raise if request fails
        """
        self._start_msg()

        dst = pathlib.Path(tempfile.gettempdir()) / "test_fail.bin"
        if dst.exists():
            dst.unlink()

        mock_response = MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_response.raise_for_status.side_effect = Exception("HTTP fail")

        with patch("requests.get", return_value=mock_response):
            with self.assertRaises(Exception):
                download("https://example.com", dst)

        if dst.exists():
            dst.unlink()

    def test_assert_github_repo_exists(self):
        """
        """
        func = github.assert_github_repo
        self._start_msg()
        func(
                user=options.github.tk_utils_core.user,
                repo=options.github.tk_utils_core.repo,
                )

    def test_assert_github_repo_user_not_exist(self):
        """
        """
        self._start_msg()
        with self.assertRaises(github.GitHubLookupError):
            github.assert_github_repo(
                user="this_user_does_not_exist_1234567890",
                repo="anyrepo",
            )
    def test_assert_github_repo_repo_not_exist(self):
        """
        """
        self._start_msg()
        with self.assertRaises(github.GitHubLookupError):
            github.assert_github_repo(
                user=options.github.tk_utils_core.user,
                repo="not_a_real_repo_xyz",
            )

    def test_assert_github_branch(self):
        """
        """
        self._start_msg()
        github.assert_github_branch(
            user=options.github.tk_utils_core.user,
            repo=options.github.tk_utils_core.repo,
            branch=options.github.tk_utils_core.branch,
            )

    def test_assert_github_branch_not_exist(self):
        """
        """
        self._start_msg()
        with self.assertRaises(github.GitHubBranchNotFoundError):
            github.assert_github_branch(
                user=options.github.tk_utils_core.user,
                repo=options.github.tk_utils_core.repo,
                branch="no_such_branch_abcdefg"
            )



def main(verbosity=2, *args, **kargs):
    cls = TestWebtoolsMod
    run_tests(
            cls=cls,
            debug=options.debug,
            verbosity=verbosity, *args, **kargs)

if __name__ == '__main__':
    main()
    #with options.set_values({'debug': True}):
    #    main()
