"""
Comply with PEP 517's restictions on in-tree backends.

We use setuptools to package Incremental and want to activate
the in-tree Incremental plugin to manage its own version. To do
this we specify ``backend-path`` in our ``pyproject.toml``,
but PEP 517 requires that when ``backend-path`` is specified:

> The backend code MUST be loaded from one of the directories
> specified in backend-path (i.e., it is not permitted to
> specify backend-path and not have in-tree backend code).

We comply by re-publishing setuptools' ``build_meta``.
"""

import sys
from pathlib import Path

if sys.version_info > (3, 11):
    import tomllib
else:
    import tomli as tomllib

from importlib.metadata import Distribution, DistributionFinder

from setuptools import build_meta


def _entry_points_txt():
    """
    Format the entry points from ``pyproject.toml`` as the INI-style
    ``entry_points.txt`` used in package metadata.
    """
    with open(Path(__file__).parent / "pyproject.toml", "rb") as f:
        data = tomllib.load(f)

    lines = []
    for section, pairs in data["project"]["entry-points"].items():
        lines.append(f"[{section}]")
        for key, value in pairs.items():
            lines.append(f"{key} = {value}")
        lines.append("")
    return "\n".join(lines)


class IncrementalEntryPoints(Distribution):
    """
    A distribution that exposes the incremental entry points by by
    reading them from ``pyproject.toml``.
    """

    def read_text(self, filename):
        if filename == "METADATA":
            return None
        if filename == "PKG-INFO":
            return (
                "Metadata-Version: 2.1\n"
                "Name: incrementalbuildhack\n"
                "Version: 0.0.0\n"
            )
        if filename == "entry_points.txt":
            return _entry_points_txt()
        raise NotImplementedError(f"Can't synthesize {filename=}")

    def locate_file(self, path):
        raise NotImplementedError(f"Can't locate_file({path=})")


class EntryPointInjector(DistributionFinder):
    """
    Inject incremental's setuptools entry points so that
    setuptools can find Incremental's own version.
    """

    def find_distributions(self, context):
        if context.name is None:
            yield IncrementalEntryPoints()

    # No-op abstract methods from importlib.abc.MetaPathFinder:

    def find_spec(self, fullname, path, target=None):
        return None

    def invalidate_caches(self):
        pass


sys.meta_path.insert(0, EntryPointInjector())

__all__ = ["build_meta"]
