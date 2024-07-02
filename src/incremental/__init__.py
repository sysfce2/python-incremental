# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Versions for Python packages.

See L{Version}.
"""

from __future__ import division, absolute_import

import sys
import warnings
from typing import TYPE_CHECKING, Any, TypeVar, Union, Optional, Dict, BinaryIO

#
# Compat functions
#

_T = TypeVar("_T", contravariant=True)


if TYPE_CHECKING:
    import io
    from typing_extensions import Literal
    from distutils.dist import Distribution as _Distribution


if sys.version_info > (3,):

    def _cmp(a, b):  # type: (Any, Any) -> int
        """
        Compare two objects.

        Returns a negative number if C{a < b}, zero if they are equal, and a
        positive number if C{a > b}.
        """
        if a < b:
            return -1
        elif a == b:
            return 0
        else:
            return 1


else:
    _cmp = cmp  # noqa: F821


#
# Versioning
#


class _Inf(object):
    """
    An object that is bigger than all other objects.
    """

    def __cmp__(self, other):  # type: (object) -> int
        """
        @param other: Another object.
        @type other: any

        @return: 0 if other is inf, 1 otherwise.
        @rtype: C{int}
        """
        if other is _inf:
            return 0
        return 1

    if sys.version_info >= (3,):

        def __lt__(self, other):  # type: (object) -> bool
            return self.__cmp__(other) < 0

        def __le__(self, other):  # type: (object) -> bool
            return self.__cmp__(other) <= 0

        def __gt__(self, other):  # type: (object) -> bool
            return self.__cmp__(other) > 0

        def __ge__(self, other):  # type: (object) -> bool
            return self.__cmp__(other) >= 0


_inf = _Inf()


class IncomparableVersions(TypeError):
    """
    Two versions could not be compared.
    """


class Version(object):
    """
    An encapsulation of a version for a project, with support for outputting
    PEP-440 compatible version strings.

    This class supports the standard major.minor.micro[rcN] scheme of
    versioning.
    """

    def __init__(
        self,
        package,  # type: str
        major,  # type: Union[Literal["NEXT"], int]
        minor,  # type: int
        micro,  # type: int
        release_candidate=None,  # type: Optional[int]
        prerelease=None,  # type: Optional[int]
        post=None,  # type: Optional[int]
        dev=None,  # type: Optional[int]
    ):
        """
        @param package: Name of the package that this is a version of.
        @type package: C{str}
        @param major: The major version number.
        @type major: C{int} or C{str} (for the "NEXT" symbol)
        @param minor: The minor version number.
        @type minor: C{int}
        @param micro: The micro version number.
        @type micro: C{int}
        @param release_candidate: The release candidate number.
        @type release_candidate: C{int}
        @param prerelease: The prerelease number. (Deprecated)
        @type prerelease: C{int}
        @param post: The postrelease number.
        @type post: C{int}
        @param dev: The development release number.
        @type dev: C{int}
        """
        if release_candidate and prerelease:
            raise ValueError("Please only return one of these.")
        elif prerelease and not release_candidate:
            release_candidate = prerelease
            warnings.warn(
                "Passing prerelease to incremental.Version was "
                "deprecated in Incremental 16.9.0. Please pass "
                "release_candidate instead.",
                DeprecationWarning,
                stacklevel=2,
            )

        if major == "NEXT":
            if minor or micro or release_candidate or post or dev:
                raise ValueError(
                    "When using NEXT, all other values except Package must be 0."
                )

        self.package = package
        self.major = major
        self.minor = minor
        self.micro = micro
        self.release_candidate = release_candidate
        self.post = post
        self.dev = dev

    @property
    def prerelease(self):  # type: () -> Optional[int]
        warnings.warn(
            "Accessing incremental.Version.prerelease was "
            "deprecated in Incremental 16.9.0. Use "
            "Version.release_candidate instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.release_candidate

    def public(self):  # type: () -> str
        """
        Return a PEP440-compatible "public" representation of this L{Version}.

        Examples:

          - 14.4.0
          - 1.2.3rc1
          - 14.2.1rc1dev9
          - 16.04.0dev0
        """
        if self.major == "NEXT":
            return self.major

        if self.release_candidate is None:
            rc = ""
        else:
            rc = ".rc%s" % (self.release_candidate,)

        if self.post is None:
            post = ""
        else:
            post = ".post%s" % (self.post,)

        if self.dev is None:
            dev = ""
        else:
            dev = ".dev%s" % (self.dev,)

        return "%r.%d.%d%s%s%s" % (self.major, self.minor, self.micro, rc, post, dev)

    base = public
    short = public
    local = public

    def __repr__(self):  # type: () -> str
        if self.release_candidate is None:
            release_candidate = ""
        else:
            release_candidate = ", release_candidate=%r" % (self.release_candidate,)

        if self.post is None:
            post = ""
        else:
            post = ", post=%r" % (self.post,)

        if self.dev is None:
            dev = ""
        else:
            dev = ", dev=%r" % (self.dev,)

        return "%s(%r, %r, %d, %d%s%s%s)" % (
            self.__class__.__name__,
            self.package,
            self.major,
            self.minor,
            self.micro,
            release_candidate,
            post,
            dev,
        )

    def __str__(self):  # type: () -> str
        return "[%s, version %s]" % (self.package, self.short())

    def __cmp__(self, other):  # type: (Version) -> int
        """
        Compare two versions, considering major versions, minor versions, micro
        versions, then release candidates, then postreleases, then dev
        releases. Package names are case insensitive.

        A version with a release candidate is always less than a version
        without a release candidate. If both versions have release candidates,
        they will be included in the comparison.

        Likewise, a version with a dev release is always less than a version
        without a dev release. If both versions have dev releases, they will
        be included in the comparison.

        @param other: Another version.
        @type other: L{Version}

        @return: NotImplemented when the other object is not a Version, or one
            of -1, 0, or 1.

        @raise IncomparableVersions: when the package names of the versions
            differ.
        """
        if not isinstance(other, self.__class__):
            return NotImplemented
        if self.package.lower() != other.package.lower():
            raise IncomparableVersions("%r != %r" % (self.package, other.package))

        if self.major == "NEXT":
            major = _inf  # type: Union[int, _Inf]
        else:
            major = self.major

        if self.release_candidate is None:
            release_candidate = _inf  # type: Union[int, _Inf]
        else:
            release_candidate = self.release_candidate

        if self.post is None:
            post = -1
        else:
            post = self.post

        if self.dev is None:
            dev = _inf  # type: Union[int, _Inf]
        else:
            dev = self.dev

        if other.major == "NEXT":
            othermajor = _inf  # type: Union[int, _Inf]
        else:
            othermajor = other.major

        if other.release_candidate is None:
            otherrc = _inf  # type: Union[int, _Inf]
        else:
            otherrc = other.release_candidate

        if other.post is None:
            otherpost = -1
        else:
            otherpost = other.post

        if other.dev is None:
            otherdev = _inf  # type: Union[int, _Inf]
        else:
            otherdev = other.dev

        x = _cmp(
            (major, self.minor, self.micro, release_candidate, post, dev),
            (othermajor, other.minor, other.micro, otherrc, otherpost, otherdev),
        )
        return x

    if sys.version_info >= (3,):

        def __eq__(self, other):  # type: (Any) -> bool
            c = self.__cmp__(other)
            if c is NotImplemented:
                return c  # type: ignore[return-value]
            return c == 0

        def __ne__(self, other):  # type: (Any) -> bool
            c = self.__cmp__(other)
            if c is NotImplemented:
                return c  # type: ignore[return-value]
            return c != 0

        def __lt__(self, other):  # type: (Version) -> bool
            c = self.__cmp__(other)
            if c is NotImplemented:
                return c  # type: ignore[return-value]
            return c < 0

        def __le__(self, other):  # type: (Version) -> bool
            c = self.__cmp__(other)
            if c is NotImplemented:
                return c  # type: ignore[return-value]
            return c <= 0

        def __gt__(self, other):  # type: (Version) -> bool
            c = self.__cmp__(other)
            if c is NotImplemented:
                return c  # type: ignore[return-value]
            return c > 0

        def __ge__(self, other):  # type: (Version) -> bool
            c = self.__cmp__(other)
            if c is NotImplemented:
                return c  # type: ignore[return-value]
            return c >= 0


def getVersionString(version):  # type: (Version) -> str
    """
    Get a friendly string for the given version object.

    @param version: A L{Version} object.
    @return: A string containing the package and short version number.
    """
    result = "%s %s" % (version.package, version.short())
    return result


def _get_distutils_version(dist, keyword, value):  # type: (_Distribution, object, object) -> None
    """
    Distutils integration: get the version from the package listed in the Distribution.

    This function is invoked when a ``setup.py`` calls `setup(use_incremental=True)`.

    See https://setuptools.pypa.io/en/latest/userguide/extension.html#adding-arguments
    """
    if not value:  # use_incremental=False
        return

    dist.metadata.version = _load_version(dist)


def _get_setuptools_version(dist):  # type: (_Distribution) -> None
    """
    Setuptools integration: get the version from the package

    This function is registered as a setuptools.finalize_distribution_options
    entry point [1]. It is a no-op unless there is a ``pyproject.toml`` containing
    a ``[tool.incremental]`` section.

    [1]: https://setuptools.pypa.io/en/latest/userguide/extension.html#customizing-distribution-options
    """
    if not _verify_pyproject_toml("pyproject.toml"):
        return

    dist.metadata.version = _load_version(dist)


def _load_version(dist):  # type: (_Distribution) -> str
    """
    Load the version from ``_version.py`` within the distribution.
    """
    from setuptools.command import build_py  # type: ignore

    sp_command = build_py.build_py(dist)
    sp_command.finalize_options()

    for item in sp_command.find_all_modules():
        if item[1] == "_version":
            version_file = {}  # type: Dict[str, Version]

            with open(item[2]) as f:
                exec(f.read(), version_file)

            return version_file["__version__"].public()

    raise Exception("No _version.py found.")


def _load_toml(f):  # type: (BinaryIO) -> Any
    """
    Read the content of a TOML file.
    """
    # This import is deferred to avoid a hard dependency on tomli
    # when no pyproject.toml is present.
    if sys.version_info > (3, 11):
        import tomllib
    else:
        import tomli as tomllib

    return tomllib.load(f)


def _verify_pyproject_toml(path):  # type: (str) -> bool
    """
    Does the ``pyproject.toml`` file contain an empty ``[tool.incremental]``
    section? This indicates that the package has opted-in to Incremental
    versioning.

    We enforce that the section is empty to allow for future extension.
    """
    try:
        with open(path, "rb") as f:
            data = _load_toml(f)
    except FileNotFoundError:
        return False

    if "tool" not in data:
        return False
    if "incremental" not in data["tool"]:
        return False
    if data["tool"]["incremental"] == {}:
        return True
    raise ValueError(
        "[tool.incremental] table must be empty. Do you need to upgrade Incremental?"
    )


from ._version import __version__  # noqa: E402


def _setuptools_version():  # type: () -> str
    return __version__.public()


__all__ = ["__version__", "Version", "getVersionString"]
