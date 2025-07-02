""" 
Tests the tk_utils_core/system.py module

Structure of testing files

tests/
|__ test_system.py       # test file
|__ assets/
|   |__ test_files/
|   |   |__ sample.txt       # basic test file
|   |   |__ dir1/
|   |   |   |__ dir2/
|   |   |   |   |__ nested.txt  # nested test file
         
"""
from __future__ import annotations

import shutil
import pathlib
import tempfile
from pathlib import Path
from typing import Callable
import sys

import tk_utils_core
from tk_utils_core._imports import pretty_errors
from tk_utils_core.testing.unittest_runner import (
        BaseTestCase,
        run_tests,
        )
from tk_utils_core.options import options
from tk_utils_core.system import (
        validate_dependencies,
        run,
        shell_exec,
        copy_with_parents,
        safe_copy,
        safe_copytree,
        walk,
        add_parents,
        add_parents_to_paths,
        #get_module_defs,
        )

ASSETS = Path(__file__).parent / "assets" / "test_files"


class TestSystemMod(BaseTestCase):
    """
    Test the tk_utils_core/system.py module
    """
    _only_in_debug = [
        'test_validate_dependencies',
        'test_run',
        'test_shell_exec',
        'test_copy_with_parents',
        'test_safe_copy',
        'test_safe_copytree',
        'test_walk',
        'test_add_parents',
        'test_add_parents_to_paths',
        #'test_get_module_defs',
        ]

    #def test_get_module_defs(self):
    #    """
    #    """
    #    result = get_module_defs(tk_utils_core)
    #    for path, defs in result.items():
    #        self.assertIsInstance(defs.functions, list)
    #        self.assertIsInstance(defs.classes, list)
    #        for name in defs.functions + defs.classes:
    #            self.assertIsInstance(name, str)

    def test_validate_dependencies(self):
        """
        """
        self._start_msg()
        self._run_doctest(validate_dependencies)
        validate_dependencies(["python>=3.8"])


    def test_run(self):
        """
        """
        self._start_msg()
        self._run_doctest(run)

        # Success case
        cmds = [sys.executable, '-c', 'print("hello world")']
        for stream_output in [True]:
            self._add_msg(f"case: stream_output={stream_output}")
            out = run(cmds, stream_stdout=stream_output)
            assert out.rc == 0
            assert "hello world" in out.stdout

        # Failure case: invalid Python code
        cmds_fail = [sys.executable, '-c', 'raise SystemExit(1)']
        err_msg = "Command failed"
        for stream_output in [True, False]:
            self._add_msg(f"case: stream_output={stream_output}")
            try:
                run(cmds_fail, stream_stdout=stream_output, err_msg=err_msg)
            except RuntimeError as e:
                assert err_msg in str(e)
            else:
                assert False, "Expected RuntimeError but none was raised"


    def test_shell_exec(self):
        """
        """
        self._start_msg()
        self._run_doctest(shell_exec)
        pyexec = pathlib.Path(sys.executable).name

        cmd = f'''{pyexec} -c "print('hello world')"'''
        out = shell_exec(cmd)
        assert out.rc == 0
        assert "hello world" in out.stdout

        cmd = f'''{pyexec} -c "raise SystemExit(1)"'''
        err_msg = "Command failed"
        try:
            out = shell_exec(cmd, err_msg=err_msg)
        except RuntimeError as e:
            assert err_msg in str(e)
        else:
            assert False, "Expected RuntimeError but none was raised"


    def test_copy_with_parents(self):
        """
        """
        self._start_msg()
        self._run_doctest(copy_with_parents)
        src = ASSETS / "sample.txt"
        with tempfile.TemporaryDirectory() as tmpdir:
            dst = Path(tmpdir) / "outdir"
            copy_with_parents(src, dst)
            assert dst.exists() and dst.read_text() == src.read_text()

    def test_safe_copy(self):
        """
        """
        self._start_msg()
        self._run_doctest(safe_copy)
        src = ASSETS / "sample.txt"
        with tempfile.TemporaryDirectory() as tmpdir:
            dst = Path(tmpdir) / "sample.txt"
            # Copy one time
            copied = safe_copy(src, dst)
            assert dst.read_text() == src.read_text()
            assert copied is True
            # Copy again
            copied = safe_copy(src, dst)
            assert copied is False

    def test_safe_copytree(self):
        """
        """
        self._start_msg()
        self._run_doctest(safe_copytree)
        src = ASSETS / "dir1"
        with tempfile.TemporaryDirectory() as tmpdir:
            dst = Path(tmpdir) / "copied"

            # with dry_run=True, return paths
            paths = safe_copytree(src=src, dst=dst, dry_run=True)
            assert all(s.exists() for s, d in paths)
            assert not any(d.exists() for s, d in paths)

            # with dry_run=False, return None
            res = safe_copytree(src=src, dst=dst, dry_run=False)
            assert all(d.exists() for s, d in paths)
            assert res is None

    def test_walk(self):
        """
        """
        self._start_msg()
        self._run_doctest(walk)
        root = ASSETS / "dir1"
        paths = list(walk(root))
        assert all(p.name == "nested.txt" for p in paths)

        paths = list(walk(root, excl_files='nested.txt'))
        assert len(paths) == 0

    def test_add_parents(self):
        """
        """
        self._start_msg()
        self._run_doctest(add_parents)
        p = ASSETS / "dir1/dir2/nested.txt"
        out = list(add_parents(p, ASSETS))
        assert (ASSETS in out 
                and p in out
                and ASSETS/"dir1" in out
                and ASSETS/"dir1"/"dir2" in out)

    def test_add_parents_to_paths(self):
        """
        """
        self._start_msg()
        self._run_doctest(add_parents)
        paths = [ASSETS / "dir1/dir2/nested.txt"]
        out = list(add_parents_to_paths(paths, root=ASSETS))
        assert any(p.name == "dir1" for p in out)
        assert any(p.name == "dir2" for p in out)
        assert any(p.name == "nested.txt" for p in out)


def main(verbosity=2, *args, **kargs):
    cls = TestSystemMod
    run_tests(
            cls=cls,
            debug=options.debug,
            verbosity=verbosity, *args, **kargs)


if __name__ == "__main__":
    main()
    #with options.set_values({'debug': True}):
    #    main()
