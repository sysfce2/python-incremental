# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""Test handling of ``pyproject.toml`` configuration"""

import os
from twisted.trial.unittest import TestCase

from incremental import _load_pyproject_toml, _IncrementalConfig


class VerifyPyprojectDotTomlTests(TestCase):
    """Test the `_load_pyproject_toml` helper function"""

    def test_fileNotFound(self):
        """
        Verification fails when no ``pyproject.toml`` file exists.
        """
        path = os.path.join(self.mktemp(), "pyproject.toml")
        self.assertFalse(_load_pyproject_toml(path))

    def test_noToolIncrementalSection(self):
        """
        Verification fails when there isn't a ``[tool.incremental]`` section.
        """
        path = self.mktemp()
        for toml in [
            "\n",
            "[tool]\n",
            "[tool.notincremental]\n",
            '[project]\nname = "foo"\n',
        ]:
            with open(path, "w") as f:
                f.write(toml)
            self.assertIsNone(_load_pyproject_toml(path))

    def test_nameMissing(self):
        """
        `ValueError` is raised when ``[tool.incremental]`` is present but
        he project name isn't available.
        """
        path = self.mktemp()
        for toml in [
            "[tool.incremental]\n",
            "[project]\n[tool.incremental]\n",
        ]:
            with open(path, "w") as f:
                f.write(toml)

            self.assertRaises(ValueError, _load_pyproject_toml, path)

    def test_nameInvalid(self):
        """
        `TypeError` is raised when the project name isn't a string.
        """
        path = self.mktemp()
        for toml in [
            "[tool.incremental]\nname = -1\n",
            "[tool.incremental]\n[project]\nname = 1.0\n",
        ]:
            with open(path, "w") as f:
                f.write(toml)

            self.assertRaises(TypeError, _load_pyproject_toml, path)

    def test_toolIncrementalInvalid(self):
        """
        `ValueError` is raised when the ``[tool.incremental]`` section isn't
        a dict.
        """
        path = self.mktemp()
        for toml in [
            "[tool]\nincremental = false\n",
            "[tool]\nincremental = 123\n",
            "[tool]\nincremental = null\n",
        ]:
            with open(path, "w") as f:
                f.write(toml)

            self.assertRaises(ValueError, _load_pyproject_toml, path)

    def test_toolIncrementalUnexpecteKeys(self):
        """
        Raise `ValueError` when the ``[tool.incremental]`` section contains
        keys other than ``"name"``
        """
        path = self.mktemp()
        for toml in [
            "[tool.incremental]\nfoo = false\n",
            '[tool.incremental]\nname = "OK"\nother = false\n',
        ]:
            with open(path, "w") as f:
                f.write(toml)

            self.assertRaises(ValueError, _load_pyproject_toml, path)

    def test_ok(self):
        """
        The package has opted-in to Incremental version management when
        the ``[tool.incremental]`` section is an empty dict.
        """
        root = self.mktemp()
        path = os.path.join(root, "src", "foo")
        os.makedirs(path)
        toml_path = os.path.join(root, "pyproject.toml")

        for toml in [
            '[project]\nname = "Foo"\n[tool.incremental]\n',
            '[tool.incremental]\nname = "Foo"\n',
        ]:
            with open(toml_path, "w") as f:
                f.write(toml)

            self.assertEqual(
                _load_pyproject_toml(toml_path),
                _IncrementalConfig(package="Foo", path=path),
            )
