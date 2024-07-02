# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Tests for the packaging examples.
"""

from twisted.trial.unittest import TestCase


class ExampleTests(TestCase):
    def test_setuppy_version(self):
        """
        example_setuppy has a version of 1.2.3.
        """
        import example_setuppy

        self.assertEqual(example_setuppy.__version__.base(), "1.2.3")

    def test_setuptools_version(self):
        """
        example_setuptools has a version of 2.3.4.
        """
        import example_setuptools

        self.assertEqual(example_setuptools.__version__.base(), "2.3.4")
