# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""Test handling of ``pyproject.toml`` configuration"""

import os
from typing import cast, Optional, Union
from pathlib import Path
from twisted.trial.unittest import TestCase

from incremental import _load_pyproject_toml, _IncrementalConfig


class VerifyPyprojectDotTomlTests(TestCase):
    """Test the `_load_pyproject_toml` helper function"""

    def _loadToml(
        self, toml: str, opt_in: bool, *, path: Union[Path, str, None] = None
    ) -> Optional[_IncrementalConfig]:
        """
        Read a TOML snipped from a temporary file with `_load_pyproject_toml`

        @param toml: TOML content of the temporary file

        @param path: Path to which the TOML is written
        """
        path_: str
        if path is None:
            path_ = self.mktemp()  # type: ignore
        else:
            path_ = str(path)

        with open(path_, "w") as f:
            f.write(toml)

        try:
            return _load_pyproject_toml(path_, opt_in)
        except Exception as e:
            if hasattr(e, "add_note"):
                e.add_note(  # type: ignore[attr-defined]
                    f"While loading:\n\n{toml}"
                )  # pragma: no coverage
            raise

    def test_fileNotFound(self):
        """
        An absent ``pyproject.toml`` file produces no result unless
        there is opt-in.
        """
        path = os.path.join(cast(str, self.mktemp()), "pyproject.toml")
        self.assertIsNone(_load_pyproject_toml(path, False))
        self.assertRaises(FileNotFoundError, _load_pyproject_toml, path, True)

    def test_brokenToml(self):
        """
        Syntactially invalid TOML is ignored unless there's an opt-in.
        """
        toml = '[project]\nname = "abc'  # truncated

        self.assertIsNone(self._loadToml(toml, False))
        self.assertRaises(Exception, self._loadToml, toml, True)

    def test_configMissing(self):
        """
        A ``pyproject.toml`` that exists but provides no relevant configuration
        is ignored unless opted in.
        """
        for toml in [
            "\n",
            "[tool.notincremental]\n",
            "[project]\n",
        ]:
            self.assertIsNone(self._loadToml(toml, False))

    def test_nameMissing(self):
        """
        `ValueError` is raised when ``[tool.incremental]`` is present but
        the project name isn't available. The ``[tool.incremental]``
        section counts as opt-in.
        """
        for toml in [
            "[tool.incremental]\n",
            "[project]\n[tool.incremental]\n",
        ]:
            self.assertRaises(ValueError, self._loadToml, toml, False)
            self.assertRaises(ValueError, self._loadToml, toml, True)

    def test_nameInvalidNoOptIn(self):
        """
        An invalid project name is ignored when there's no opt-in.
        """
        self.assertIsNone(
            self._loadToml("[project]\nname = false\n", False),
        )

    def test_nameInvalidOptIn(self):
        """
        Once opted in, `TypeError` is raised when the project name
        isn't a string.
        """
        for toml in [
            "[project]\nname = false\n",
            "[tool.incremental]\nname = -1\n",
            "[tool.incremental]\n[project]\nname = 1.0\n",
        ]:
            self.assertRaises(TypeError, self._loadToml, toml, True)

    def test_toolIncrementalInvalid(self):
        """
        When ``[tool]`` or ``[tool.incremental]`` isn't a table the
        ``pyproject.toml`` it's an error if opted-in, otherwise the
        file is ignored.
        """
        for toml in [
            "tool = false\n",
            "[tool]\nincremental = false\n",
            "[tool]\nincremental = 123\n",
            "[tool]\nincremental = null\n",
        ]:
            self.assertIsNone(self._loadToml(toml, False))
            self.assertRaises(ValueError, self._loadToml, toml, True)

    def test_toolIncrementalUnexpecteKeys(self):
        """
        Raise `ValueError` when the ``[tool.incremental]`` section contains
        keys other than ``"name"``
        """
        for toml in [
            "[tool.incremental]\nfoo = false\n",
            '[tool.incremental]\nname = "OK"\nother = false\n',
        ]:
            self.assertRaises(ValueError, self._loadToml, toml, False)

    def test_setuptoolsOptIn(self):
        """
        The package has opted-in to Incremental version management when
        the ``[tool.incremental]`` section is a dict. The project name
        is taken from ``[tool.incremental] name`` or ``[project] name``.
        """
        root = Path(self.mktemp())
        pkg = root / "src" / "foo"
        pkg.mkdir(parents=True)

        for toml in [
            '[project]\nname = "Foo"\n[tool.incremental]\n',
            '[tool.incremental]\nname = "Foo"\n',
        ]:
            config = self._loadToml(toml, False, path=root / "pyproject.toml")

            self.assertEqual(
                config,
                _IncrementalConfig(
                    opt_in=True,
                    package="Foo",
                    path=str(pkg),
                ),
            )

    def test_noToolIncrementalSection(self):
        """
        We don't produce config unless we find opt-in.

        The ``[project]`` section doesn't imply opt-in, even if we can
        recover the project name from it.
        """
        root = Path(self.mktemp())
        pkg = root / "foo"  # A valid package directory.
        pkg.mkdir(parents=True)

        config = self._loadToml(
            '[project]\nname = "foo"\n',
            opt_in=False,
            path=root / "pyproject.toml",
        )

        self.assertIsNone(config)

    def test_pathNotFoundOptIn(self):
        """
        Once opted in, raise `ValueError` when the package root can't
        be resolved.
        """
        root = Path(self.mktemp())
        root.mkdir()  # Contains no package directory.

        with self.assertRaisesRegex(ValueError, "Can't find the directory of package"):
            self._loadToml(
                '[project]\nname = "foo"\n',
                opt_in=True,
                path=root / "pyproject.toml",
            )

    def test_noToolIncrementalSectionOptIn(self):
        """
        If opted in (i.e. in the Hatch plugin) then the [tool.incremental]
        table is completely optional.
        """
        root = Path(self.mktemp())
        pkg = root / "src" / "foo"
        pkg.mkdir(parents=True)

        config = self._loadToml(
            '[project]\nname = "Foo"\n',
            opt_in=True,
            path=root / "pyproject.toml",
        )

        self.assertEqual(
            config,
            _IncrementalConfig(
                opt_in=True,
                package="Foo",
                path=str(pkg),
            ),
        )
