# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Tests for the packaging examples.
"""

import os
from importlib import metadata
from subprocess import run

from build import ProjectBuilder
from twisted.python.filepath import FilePath
from twisted.trial.unittest import TestCase

from incremental import Version


TEST_DIR = FilePath(os.path.abspath(os.path.dirname(__file__)))


def build_and_install(path):  # type: (FilePath) -> None
    builder = ProjectBuilder(path.path)
    pkgfile = builder.build("wheel", output_directory=os.environ["PIP_FIND_LINKS"])

    # Force reinstall in case tox reused the venv.
    run(["pip", "install", "--force-reinstall", pkgfile], check=True)


class ExampleTests(TestCase):
    def test_setuppy_version(self):
        """
        example_setuppy has a version of 1.2.3.
        """
        build_and_install(TEST_DIR.child("example_setuppy"))

        import example_setuppy

        self.assertEqual(example_setuppy.__version__.base(), "1.2.3")
        self.assertEqual(metadata.version("example_setuppy"), "1.2.3")

    def test_setuptools_version(self):
        """
        example_setuptools has a version of 2.3.4.
        """
        build_and_install(TEST_DIR.child("example_setuptools"))

        import example_setuptools

        self.assertEqual(example_setuptools.__version__.base(), "2.3.4")
        self.assertEqual(metadata.version("example_setuptools"), "2.3.4")

    def test_hatchling_get_version(self):
        """
        example_hatchling has a version of 24.7.0.
        """
        build_and_install(TEST_DIR.child("example_hatchling"))

        import example_hatchling

        self.assertEqual(
            example_hatchling.__version__,
            Version("example_hatchling", 24, 7, 0),
        )
        self.assertEqual(metadata.version("example_hatchling"), "24.7.0")

    def test_hatch_version(self):
        """
        The ``hatch version`` command reports the version of a package
        packaged with hatchling.
        """
        proc = run(
            ["hatch", "version"],
            cwd=TEST_DIR.child("example_hatchling").path,
            check=True,
            capture_output=True,
        )

        self.assertEqual(proc.stdout, b"24.7.0\n")

    def test_hatch_version_set(self):
        """
        The ``hatch version`` command can't set the version so its output
        tells the user to use ``incremental.update`` instead.
        """
        proc = run(
            ["hatch", "--no-color", "version", "24.8.0"],
            cwd=TEST_DIR.child("example_hatchling").path,
            check=False,
            capture_output=True,
        )
        suggestion = b"Run `python -m incremental.version --newversion 24.8.0` to set the version."

        self.assertGreater(proc.returncode, 0)
        self.assertRegex(
            proc.stdout,
            # Hatch may wrap the output, so we are flexible about the specifics of whitespace.
            suggestion.replace(b".", rb"\.").replace(b" ", b"\\s+"),
        )

    def test_noop(self):
        """
        The Incremental setuptools hook is a silent no-op when there is no Incremental
        configuration to be found.
        """
        build_and_install(TEST_DIR.child("example_noop"))

        import example_noop

        self.assertEqual(example_noop.__version__, "100")
        self.assertEqual(metadata.version("example_noop"), "100")
