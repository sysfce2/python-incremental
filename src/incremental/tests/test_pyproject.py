# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""Test handling of ``pyproject.toml`` configuration"""

import os
from twisted.trial.unittest import TestCase

from incremental import _verify_pyproject_toml


class VerifyPyprojectDotTomlTests(TestCase):
    """Test the `_verify_pyproject_toml` helper function"""

    def test_fileNotFound(self):
        """
        Verification fails when no ``pyproject.toml`` file exists.
        """
        path = os.path.join(self.mktemp(), "pyproject.toml")
        self.assertFalse(_verify_pyproject_toml(path))

    def test_noToolIncrementalSection(self):
        """
        Verification fails when there isn't a ``[tool.incremental]`` section.
        """
        path = self.mktemp()
        for toml in [
            "\n",
            "[tool]\n",
            "[tool.notincremental]\n",
            "[tool.notincremental]\n",
        ]:
            with open(path, "w") as f:
                f.write(toml)
            self.assertFalse(_verify_pyproject_toml(path))

    def test_toolIncrementalNotEmpty(self):
        """
        `ValueError` is raised when the ``[tool.incremental]`` section isn't
        an empty dict.
        """
        path = self.mktemp()
        for toml in [
            '[tool.incremental]\nfoo = "bar"\n',
            "[tool]\nincremental = false\n",
        ]:
            with open(path, "w") as f:
                f.write(toml)

            self.assertRaises(ValueError, _verify_pyproject_toml, path)

    def test_ok(self):
        """
        The package has opted-in to Incremental version management when
        the ``[tool.incremental]`` section is an empty dict.
        """
        path = self.mktemp()
        for toml in [
            "[tool.incremental]\n",
            "[tool]\nincremental = {}\n",
        ]:
            with open(path, "w") as f:
                f.write(toml)

            self.assertTrue(_verify_pyproject_toml(path))
