""" 
Utilities to setup and configure PyCharm and venv
         
"""
from __future__ import annotations

from collections import namedtuple
from functools import cached_property, lru_cache
from types import SimpleNamespace
import copy as _copy
import pathlib
import shutil
import subprocess
import sys

import requests

from tk_utils_core.defaults import defaults
from tk_utils_core.messages import (
        dirtree,
        ask_yes,
        fmt_now,
        fmt_msg,
        )
from tk_utils_core.webtools import (
        download,
        download_to_tmp,
        _github as github,
        )
from tk_utils_core.fstools import (
        safe_copytree,
        safe_copy,
        walk,
        unzip,
        add_parents_to_paths,
        )
from tk_utils_core.converters import (
        to_namespace, 
        as_set,
        as_path,
        )
from tk_utils_core.core.constants import POSIX
from tk_utils_core.mappings import map_dot_update
from tk_utils_core.structs import (
        obj_dot_update, 
        obj_dot_subset,
        obj_dot_get,
        )
from tk_utils_core.system import run
from tk_utils_core import fstools

def has_idea_folder(pth: pathlib.Path) -> bool:
    """
    True if the folder `pth` has a .idea sub-folder
    """
    return pth.is_dir() and pth.joinpath('.idea').is_dir()

def all_parents(path: pathlib.Path) -> list[pathlib.Path]:
    """
    Return a list of all parent directories of a relative path, 
    including '.' (the current directory) and the path itself.

    Parameters
    ----------
    path : Path
        A relative Path object.

    Returns
    -------
    list of Path
        All parents from '.' up to the full path, in ascending order.
    """
    if path.is_absolute():
        raise ValueError("Path must be relative")

    parts = list(path.parents)[::-1]  # from shallow to deep
    return [pathlib.Path('.')] + parts + [path]


class TKPaths:
    """
    Location of files and folders relative to the PyCharm project 
    folder
    """

    def __init__(
            self, 
            prjroot: pathlib.Path,
            validate: bool | None = None,
            tk_utils_init: pathlib.Path | None = None,
            ):
        """
        """
        self._root = as_path(prjroot)
        self.prjname = defaults.pycharm.prjname
        self._tk_utils_init = tk_utils_init

        if validate is None:
            self.validate = defaults.pycharm.validate_paths
        elif isinstance(validate, bool):
            self.validate = validate
        else:
            raise TypeError(
                    f"Parm `validate` must be a bool, "
                    f"not {type(validate).__name__}")

    @cached_property
    def validate_tracker(self):
        """
        Track validation over lifetime of instance
        """
        kargs = {
                'tk_utils_validated': False,
                'backup_validated': False,
                'dropbox_validated': False,
                'venv_validated': False,
                }
        return SimpleNamespace(**kargs)

    @cached_property
    def root(self) -> SimpleNamespace:
        """
        PyCharm's project folder
        """
        return self._root.joinpath(defaults.pycharm.paths.root)

    @cached_property
    def tk_utils_init(self):
        """
        Location of the <root>/tk_utils/__init__.py file
        """
        if self._tk_utils_init is not None:
            return as_path(self._tk_utils_init)
        else:
            return self.root.joinpath(defaults.pycharm.paths.tk_utils,
                                      '__init__.py')

    def mk_paths(self, root):
        """
        """
        _paths = defaults.pycharm.paths
        attrs = [
                'backup',
                'dropbox',
                'tk_utils',
                'tk_utils_config',
                'toolkit_config',
                'dropbox_zip',
                'idea',
                ]
        kargs = {'root': root} | {
                p: root.joinpath(getattr(_paths, p))
                for p in attrs}
        venv_root = root.joinpath(_paths.venv)
        venv_bin = venv_root.joinpath('bin' if POSIX else 'Scripts')
        venv = {
                'root': venv_root,
                'bin': venv_bin,
                'pip': venv_bin.joinpath('pip'),
                'pyexec': venv_bin.joinpath('python' if POSIX else 'python.exe'),
                }
        kargs['venv'] = venv
        return to_namespace(kargs)

    @cached_property
    def paths(self) -> SimpleNamespace:
        """
        Namespace with actual paths from self.root
        """
        return self.mk_paths(self.root)

    @cached_property
    def expected_paths(self) -> SimpleNamespace:
        """
        Namespace with "expected" paths (relative)
        """
        root = pathlib.Path('.', self.prjname)
        return self.mk_paths(root)


    def dirtree_from_path(self, root, path, notes):
        """
        Return a tree representation of a file and its parents, 
        all the way to the PyCharm project folder
        """
        parents = [root.joinpath(x) for x in
                   path.relative_to(root).parents[::-1]]
        paths = parents + [path]
        dirs = [x.relative_to(root) for x in parents]
        return dirtree(
                root=root,
                dirs=dirs,
                paths=paths, 
                notes=notes, 
                note_align_width=defaults.pp.width)

    def _mk_tk_utils_tree_err(self, err_msg, notes):
        """
        """
        # Expected dirtree
        eroot = self.expected_paths.root
        etk_utils = self.expected_paths.tk_utils
        epath = etk_utils.joinpath('__init__.py')
        init_key = str(epath.relative_to(eroot))
        enotes = {
            '.': "PyCharm's project folder",
            etk_utils.name: "tk_utils module should be here",
            init_key: "The __init__.py module",
            }
        etree = self.dirtree_from_path(root=eroot, path=epath, notes=enotes)
        # Actual tree
        atree = self.dirtree_from_path(
                root=self.tk_utils_init.parent.parent, 
                path=self.tk_utils_init,
                notes=notes)
        msg = [
                err_msg,
                '',
                'Your files:',
                atree,
                '',
                'EXPECTED:',
                etree,
                '',
                ]
        return '\n'.join(msg)

    def validate_tk_utils_init(self):
        """
        Ensure the proper location of the tk_utils/__init__.py folder
        """
        if self.validate is False or self.validate_tracker.tk_utils_validated is True:
            return 

        valid_name = self.tk_utils_init.name == "__init__.py"
        root = self.tk_utils_init.parent.parent
        inside_prjroot = has_idea_folder(root)

        if not valid_name:
            err_msg =  f"Missing __init__.py file"
            notes = {
                    str(self.tk_utils_init.relative_to(root)): 'This file',
                    }
            raise Exception(
                    self._mk_tk_utils_tree_err(err_msg=err_msg, notes=notes))
        elif not inside_prjroot:
            err_msg = f"Module {self.expected_paths.tk_utils.name} NOT under PyCharm's project folder"
            notes = {
                    '.': 'Not a PyCharm project folder',
                    str(self.tk_utils_init.relative_to(root)): 'This file',
                    }
            raise Exception(
                    self._mk_tk_utils_tree_err(err_msg=err_msg, notes=notes))
        else:
            self.validate_tracker.tk_utils_validated = True

    def validate_venv(self):
        """
        Ensure the venv environment is activate and configured
        """
        if self.validate is False or self.validate_tracker.venv_validated is True:
            return None

        env_dir = self.paths.venv.root
        renv_dir = self.paths.venv.root.relative_to(self.paths.root)
        is_active = sys.prefix == str(env_dir.resolve())

        if not env_dir.exists():
            raise FileNotFoundError(
                f"Directory '{renv_dir}' does not exist. "
                f"Please run the tk_utils/setup.py script."
            )
        elif sys.prefix == str(env_dir.resolve()) and self.paths.venv.pip.exists():
            self.validate_tracker.venv_validated = True
            return 
        elif not self.paths.venv.pip.exists():
            raise FileNotFoundError(
                f"Could not find pip executable inside '{renv_dir}'. "
                f"Please run the tk_utils/setup.py script."
            )
        else:
            raise Exception(
                f"Directory '{renv_dir}' contains a venv but it is not active. "
                "Try restarting your IDE, or run the tk_utils/setup.py script"
            )

    def _validate_folder(self, path, track_attr):
        """
        Validates a folder inside PyCharm's project folder
        - Folder must be inside a PyCharm project folder
        - Folder must exist (otherwise create)
        """
        validated = getattr(self.validate_tracker, track_attr)
        if self.validate is False or validated is True:
            return 

        exists = path.exists()
        is_dir = path.is_dir()

        if not path.parent.exists() or not has_idea_folder(path.parent):
            raise Exception("Cannot create folder '{path}': Not inside a "
                            "PyCharm project")
        elif not path.exists():
            print(f"Folder '{path.name}' does not exist, creating...")
            path.mkdir()
        elif not path.is_dir():
            raise Exception(
                    f"File '{path.name}' exists but is not a folder")
        else:
            pass
        setattr(self.validate_tracker, track_attr, True)

    def validate_backup(self):
        """
        Ensure the _backup folder exists 
        """
        return self._validate_folder(self.paths.backup, 'backup_validated')

    def validate_dropbox(self):
        """
        Ensure the _dropbox folder exists 
        """
        return self._validate_folder(self.paths.dropbox, 'dropbox_validated')


class SysUtils:
    """
    System utilities
    """


    def __init__(
            self,
            tkpaths: TKPaths,
            ):
        if isinstance(tkpaths, TKPaths):
            self.tkpaths = tkpaths
        else:
            raise ValueError(
                    f"Parm `tkpaths` must be an instance of TKPaths")

    def mk_tmp(self, pth: pathlib.Path) -> pathlib.Path | None:
        """
        Create a tmp file by appending a .tmp suffix (or .tmpN if needed).

        Parameters
        ----------
        pth : Path
            Path to an existing file or directory.

        Returns
        -------
        Path | None
            The new path with the .tmp suffix, or None if the original path does not exist.
        """
        if not pth.exists():
            return None

        suffix = '.tmp'
        tmp = pth.with_name(pth.name + suffix)
        i = 0
        while tmp.exists():
            i += 1
            tmp = pth.with_name(f"{pth.name}{suffix}{i}")

        return tmp

    def sync_dbox(self, url: str | None = None):
        """
        Download the most recent files from the shared Dropbox folder.

        If `url` is not provided, the function uses the default from the config
        (defaults.dropbox.url). The downloaded file is saved to the Dropbox ZIP
        location. If the file already exists, it is first downloaded to a temporary
        file to avoid overwriting valid content on failure.

        Parameters
        ----------
        url : str | None
            Optional override for the Dropbox shared folder URL.

        Raises
        ------
        FileNotFoundError
            If no URL is provided and none is found in the config.

        requests.HTTPError
            If the download fails.

        ValueError
            If the Dropbox URL is missing or improperly configured.
        """
        _paths = self.tkpaths.paths
        if url is None and defaults.dropbox.url is None:

            cfg = _paths.tk_utils_config.relative_to(_paths.root)
            raise ValueError("\n".join([
                "Missing Dropbox URL in your configuration.",
                f"Please edit the file '{cfg}' and update the [dropbox] section as shown below:",
                "",
                "Current:",
                "  [dropbox]",
                '  url = ""',
                "",
                "Update to:",
                "  [dropbox]",
                '  url = \"<URL_TO_SHARED_FOLDER>\"',
                "",
                "Replace <URL_TO_SHARED_FOLDER> with the shared Dropbox link provided in ED.",
                "It should start with:",
                "  https://www.dropbox.com/...",
            ]))

        elif url is None:
            url = defaults.dropbox.url

        self.tkpaths.validate_dropbox()
        dst = _paths.dropbox_zip

        print(fmt_msg("Downloading files from Dropbox...", as_hdr=True))

        tmp = self.mk_tmp(dst) if dst.exists() else dst

        try:
            download(url, tmp)
        except Exception as e:
            if tmp.exists() and tmp != dst:
                tmp.unlink()
            raise e

        if tmp != dst:
            tmp.rename(dst)

    def copy_new_files(self):
        """
        Copy all new files from the shared Dropbox folder to the current
        PyCharm project folder. Only files that do not already exist will
        be copied. No files are overwritten.

        Prompts the user for confirmation before copying.
        """
        self.tkpaths.validate_tk_utils_init()
        self.tkpaths.validate_dropbox()
        _paths = self.tkpaths.paths
        src = _paths.dropbox_zip
        rsrc = src.relative_to(_paths.root)

        if not src.exists():
            raise FileNotFoundError(
                f"File {rsrc} does not exist. Run sync_dbox() first."
            )

        print(fmt_msg("Updating project with files from Dropbox", as_hdr=True))

        dst = self.mk_tmp(src)
        dst.mkdir(exist_ok=True)

        try:
            unzip(src=src, dst=dst)

            res = safe_copytree(src=dst, dst=_paths.root, dry_run=True)

            if len(res) == 0:
                print("\nAll Dropbox files are already in your project folder.")
                print("No files will be copied.\n")
                return

            from_paths, to_paths = zip(*res)

            notes = {str(p.relative_to(_paths.root)): "New File" for p in to_paths}
            all_paths = add_parents_to_paths(to_paths, _paths.root)

            tree = dirtree(
                root=_paths.root,
                paths=all_paths,
                dirs=None,
                notes=notes,
                note_align_width=defaults.pp.width,
            )

            msg = [
                "The following Dropbox files are NOT in your project folder:",
                "",
                tree,
                "",
                "Would you like to copy these files into your project folder?",
                "",
                "NOTE: Only NEW files will be copied!",
            ]

            confirmed = ask_yes("\n".join(msg))
            if confirmed:
                safe_copytree(src=dst, dst=_paths.root, dry_run=False)
                print("Done")

        finally:
            shutil.rmtree(dst)

    def backup(
            self,
            show_folder: bool = False, 
            quiet: bool = False,
            ) -> pathlib.Path | None:
        """
        Backup files under the PyCharm project folder

        This function will copy all (non-system) files under "toolkit" to a
        "dated" folder inside "toolkit/_backup". A new dated folder will be
        created every time this function is called.

        This function will exclude system files, hidden files (e.g., files
        starting with '.'),  and any folder starting with an underscore.

        Parameters
        ----------
        show_folder : bool
            If True, prints the location of the destination folder.
            Ignored if the "_backup" folder does not exist (will always be printed)
            Defaults to False

        quiet: bool, optional
            If True, do not display any messages.
            Defaults to False

        Usage
        -----
        >> import tk_utils
        >> tk_utils.backup()


        Example
        -------
        Suppose you only have the following files under toolkit:

         toolkit/               <- PyCharm project folder 
         |
         |__ toolkit_config.py
         |__ tk_utils/          <- this package
        
        After the backup, your toolkit folder will look like this:
        
         toolkit/               <- PyCharm project folder 
         |
         |__ _backup/                       <- Will be created 
         |  |__ <YYYY_MM_DD_HH_MM_SS>/          <- Represents the time of the backup
         |  |  |__ toolkit_config.py                <- backup
         |  |  |__ tk_utils/                        <- backup
         |
         |__ toolkit_config.py              <- original (not modified)
         |__ tk_utils/                      <- original (not modified)


        """
        self.tkpaths.validate_tk_utils_init()
        _paths = self.tkpaths.paths
        # Force showing folder if this is the first backup
        if not _paths.backup.exists():
            show_folder = True

        self.tkpaths.validate_backup()

        bk_dir = _paths.backup.joinpath(fmt_now())

        msg = ["Backing up PyCharm project folder..."]
        if show_folder is True:
            # TODO: This should be generated dynamically
            msg.extend([
                ' ',
                f"Destination:",
                ' ',
                f"{_paths.root.name}/                    <- PyCharm project folder",
                f"|__ {_paths.backup.name}/",
                f"|   |__ {bk_dir.name}/    <- New folder",
                ])
        print(fmt_msg(msg, as_hdr=True))

        for src in _paths.root.iterdir():
            if (src.name.startswith('_') 
                or src.name.startswith('.')
                or src.is_relative_to(_paths.backup)
                or src == _paths.backup):
                continue
            elif src.is_dir():
                safe_copytree(src, bk_dir.joinpath(src.name), 
                              raise_if_exists=True)
            elif src.is_file():
                safe_copy(src,
                          bk_dir.joinpath(src.name),
                          raise_if_exists=True)

        print("Done")
        return

    def create_venv(self, force: bool = False):
        """
        Create a new virtual environment inside PyCharm

        This function checks whether the specified environment is:
        - Already the active virtual environment (in which case, nothing is done).
        - An existing directory with a valid venv (raises unless `force=True`).
        - A non-existent path (creates a new virtual environment using `python -m venv`).

        Parameters
        ----------
        force : bool, default False
            If True, forcibly deletes an existing directory before creating a new venv.

        """
        self.tkpaths.validate_tk_utils_init()
        env_dir = self.tkpaths.venv.root
        create_venv(env_dir, force=force)

    def _update_tk_utils(self):
        """
        """
        _paths = self.tkpaths.paths
        tk_utils_base = github.cnts_url(
                    user=defaults.github.tk_utils.user, 
                    repo=defaults.github.tk_utils.repo, 
                    branch=defaults.github.tk_utils.base, 
                    )
        tk_utils_files = {
                x: f"{tk_utils_base}/{x}" 
                for x in defaults.github.tk_utils.modules}

        for name, url in tk_utils_files.items():
            dst = _paths.tk_utils.joinpath(name)
            try:
                tmp = self.mk_tmp(dst) if dst.exists() else dst
                download(url, tmp)
                tmp.rename(dst)
            finally:
                if dst != tmp and tmp.exists():
                    tmp.unlink()

    def _reinstall_tk_utils_core(self):
        """
        Reinstalls tk_utils_core
        """
        self.tkpaths.validate_tk_utils_init()
        self.tkpaths.validate_venv()
        _paths = self.tkpaths.paths
        tgt = github.git_url(
                    user=defaults.github.tk_utils_core.user, 
                    repo=defaults.github.tk_utils_core.repo, 
                    )
        opts = "--force-reinstall" 
        run(f"{_paths.venv.pip} install {opts} git+{tgt}")

    def update_tk_utils(self):
        """
        Forcibly update tk_utils and tk_utils_core
        """
        self.tkpaths.validate_tk_utils_init()
        self.tkpaths.validate_venv()
        self._update_tk_utils()
        self._reinstall_tk_utils_core()

def create_venv(
        env_dir: str | pathlib.Path,
        force: bool = False) -> bool:
    """
    Create a new virtual environment in the given directory if it does not exist.

    This function checks whether the specified environment is:
    - Already the active virtual environment (in which case, nothing is done).
    - An existing directory with a valid venv (raises unless `force=True`).
    - A non-existent path (creates a new virtual environment using `python -m venv`).

    Parameters
    ----------
    env_dir : str | pathlib.Path
        The path to the virtual environment directory.

    force : bool, default False
        If True, forcibly deletes an existing directory before creating a new venv.

    Returns
    -------
    bool
        True if the venv was created during this call, False if it already existed.

    Raises
    ------
    FileExistsError
        If the target directory exists but is not the active venv, and `force=False`.

    RuntimeError
        If the `python -m venv` command fails.

    Notes
    -----
    - A valid virtual environment must contain a `pyvenv.cfg` file.
    - Use `force=True` to recreate the environment from scratch.
    """
    env_dir = env_dir if isinstance(env_dir, pathlib.Path) else pathlib.Path(env_dir)
    is_active = sys.prefix == str(env_dir)

    if is_active:
        print(f"Virtual environment already active: {env_dir}")
        return False

    pyvenv_cfg = env_dir / "pyvenv.cfg"
    if env_dir.exists():
        if force and env_dir.name == '.venv':
            print(f"Warning: Forcibly removing existing venv at {env_dir}")
            shutil.rmtree(env_dir)
        elif pyvenv_cfg.exists():
            raise FileExistsError(
                f"Directory '{env_dir}' contains a venv but it is not active.\n"
                "Try restarting your IDE, or use force=True to recreate it."
            )
        else:
            raise FileExistsError(
                f"Directory '{env_dir}' exists but does not contain a venv.\n"
                "Use force=True to overwrite it."
            )

    print(f"Creating virtual environment at {env_dir}")
    run(
        [sys.executable, "-m", "venv", str(env_dir)],
        err_msg=f"Failed to create virtual environment at {env_dir}"
    )

    print(f"[done] Virtual environment created: {env_dir}")
    return True




