# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

import os
import shlex
from typing import TypedDict

from hatchling.version.source.plugin.interface import VersionSourceInterface
from hatchling.plugin import hookimpl

from incremental import _load_pyproject_toml, _existing_version


class _VersionData(TypedDict):
    version: str


class IncrementalVersionSource(VersionSourceInterface):
    PLUGIN_NAME = "incremental"

    def get_version_data(self) -> _VersionData:
        config = _load_pyproject_toml(os.path.join(self.root, "./pyproject.toml"))
        return {"version": _existing_version(config.path).public()}

    def set_version(self, version: str, version_data: dict):
        raise NotImplementedError(
            f"Run `python -m incremental.version --newversion"
            f" {shlex.quote(version)}` to set the version.\n\n"
            f" See `python -m incremental.version --help` for more options."
        )


@hookimpl
def hatch_register_version_source():
    return [IncrementalVersionSource]
