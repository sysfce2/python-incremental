Incremental
===========

|pypi|
|calver|
|gha|
|coverage|

Incremental is a `CalVer <https://calver.org/>`_ version manager supports the future.

API documentation can be found `here <https://twisted.org/incremental/docs/>`_.
Narrative documentation follows.

.. contents::

Theory of Operation
-------------------

- A version number has the form YY.MM.PATCH.
- If your project is named "Shrubbery", its code is found in ``shrubbery/`` or ``src/shrubbery/``.
- Incremental stores your project's version number in ``{src/}shrubbery/_version.py``.
- To update the version, run ``incremental update Shrubbery``, passing ``--rc`` and/or ``--patch`` as appropriate (see `Updating`_, below).
- Changing the version also updates any `indeterminate versions`_ in your codebase, like "Shrubbery NEXT", so you can reference the upcoming release in documentation.
  That's how Incremental supports the future.


Quick Start
-----------

Using setuptools
~~~~~~~~~~~~~~~~

Add Incremental to your ``pyproject.toml``:

.. code-block:: toml

    [build-system]
    requires = [
        "setuptools",
        "incremental>=24.7.2",  # ← Add incremental as a build dependency
    ]
    build-backend = "setuptools.build_meta"

    [project]
    name = "<projectname>"
    dynamic = ["version"]       # ← Mark the version dynamic
    dependencies = [
        "incremental>=24.7.2",  # ← Depend on incremental at runtime
    ]
    # ...

    [tool.incremental]          # ← Activate Incremental's setuptools plugin

It's fine if the ``[tool.incremental]`` table is empty, but it must be present.

Remove any ``[project] version =`` entry and any ``[tool.setuptools.dynamic] version =`` entry.

Next, `initialize the project`_.

Using Hatchling
~~~~~~~~~~~~~~~

If you're using `Hatchling <https://hatch.pypa.io/>`_ to package your project,
activate Incremental's Hatchling plugin by altering your ``pyproject.toml``:

.. code:: toml

    [build-system]
    requires = [
        "hatchling",
        "incremental>=24.7.2",  # ← Add incremental as a build dependency
    ]
    build-backend = "hatchling.build"

    [project]
    name = "<projectname>"
    dynamic = ["version"]       # ← Mark the version dynamic
    dependencies = [
        "incremental>=24.7.2",  # ← Depend on incremental at runtime
    ]
    # ...

    [tool.hatch.version]
    source = "incremental"      # ← Activate Incremental's Hatchling plugin

Incremental can be configured as usual in an optional ``[tool.incremental]`` table.

The ``hatch version`` command will report the Incremental-managed version.
Use the ``incremental update`` command to change the version (setting it with ``hatch version`` is not supported).

Next, `initialize the project`_.


Using ``setup.py``
~~~~~~~~~~~~~~~~~~

Incremental may be used from ``setup.py`` instead of ``pyproject.toml``.
Add this to your ``setup()`` call, removing any other versioning arguments:

.. code:: python

   setup(
       use_incremental=True,
       setup_requires=['incremental'],
       install_requires=['incremental'], # along with any other install dependencies
       ...
   }

Then `initialize the project`_.


Initialize the project
~~~~~~~~~~~~~~~~~~~~~~

Install Incremental to your local environment with ``pipx install incremental``.
Then run ``incremental update <projectname> --create``.
It will create a file in your package named ``_version.py`` like this:

.. code:: python

   from incremental import Version

   __version__ = Version("<projectname>", 24, 1, 0)
   __all__ = ["__version__"]


Subsequent installations of your project will then use Incremental for versioning.


Runtime integration
~~~~~~~~~~~~~~~~~~~

You may expose the ``incremental.Version`` from ``_version.py`` in your package's API.
To do so, add to your root package's ``__init__.py``:

.. code:: python

   from ._version import __version__

.. note::

    Providing a ``__version__`` attribute is falling out of fashion following the introduction of `importlib.metadata.version() <https://docs.python.org/3/library/importlib.metadata.html#distribution-versions>`_ in Python 3.6, which can retrieve an installed package's version.

If you don't expose this object publicly, nor make use of it within your package,
then there is no need to depend on Incremental at runtime.
You can remove it from your project's ``dependencies`` array (or, in ``setup.py``, from ``install_requires``).


Incremental Versions
--------------------

``incremental.Version`` is a class that represents a version of a given project.
It is made up of the following elements (which are given during instantiation):

- ``package`` (required), the name of the package this ``Version`` represents.
- ``major``, ``minor``, ``micro`` (all required), the X.Y.Z of your project's ``Version``.
- ``release_candidate`` (optional), set to 0 or higher to mark this ``Version`` being of a release candidate (also sometimes called a "prerelease").
- ``post`` (optional), set to 0 or higher to mark this ``Version`` as a postrelease.
- ``dev`` (optional), set to 0 or higher to mark this ``Version`` as a development release.

You can extract a PEP-440 compatible version string by using the ``.public()`` method, which returns a ``str`` containing the full version. This is the version you should provide to users, or publicly use. An example output would be ``"13.2.0"``, ``"17.1.2dev1"``, or ``"18.8.0rc2"``.

Calling ``repr()`` with a ``Version`` will give a Python-source-code representation of it, and calling ``str()`` on a ``Version`` produces a string like ``'[Incremental, version 16.10.1]'``.


Updating
--------

Incremental includes a tool to automate updating your Incremental-using project's version called ``incremental``.
It updates the ``_version.py`` file and automatically updates some uses of Incremental versions from an indeterminate version to the current one.
It requires ``click`` from PyPI.

``incremental update <projectname>`` will perform updates on that package.
The commands that can be given after that determine what the next version is.

- ``--newversion=<version>``, to set the project version to a fully-specified version (like 1.2.3, or 17.1.0dev1).
- ``--rc``, to set the project version to ``<year-2000>.<month>.0rc1`` if the current version is not a release candidate, or bump the release candidate number by 1 if it is.
- ``--dev``, to set the project development release number to 0 if it is not a development release, or bump the development release number by 1 if it is.
- ``--patch``, to increment the patch number of the release. This will also reset the release candidate number, pass ``--rc`` at the same time to increment the patch number and make it a release candidate.
- ``--post``, to set the project postrelease number to 0 if it is not a postrelease, or bump the postrelease number by 1 if it is. This will also reset the release candidate and development release numbers.

If you give no arguments, it will strip the release candidate number, making it a "full release".

Indeterminate Versions
----------------------

Incremental supports "indeterminate" versions, as a stand-in for the next "full" version. This can be used when the version which will be displayed to the end-user is unknown (for example "introduced in" or "deprecated in"). Incremental supports the following indeterminate versions:

- ``Version("<projectname>", "NEXT", 0, 0)``
- ``<projectname> NEXT``

When you run ``incremental update <projectname> --rc``, these will be updated to real versions (assuming the target final version is 17.1.0):

- ``Version("<projectname>", 17, 1, 0, release_candidate=1)``
- ``<projectname> 17.1.0rc1``

Once the final version is made, it will become:

- ``Version("<projectname>", 17, 1, 0)``
- ``<projectname> 17.1.0``


.. |pypi| image:: http://img.shields.io/pypi/v/incremental.svg
    :alt: PyPI
    :target: https://pypi.org/project/incremental/

.. |calver| image:: https://img.shields.io/badge/calver-YY.MM.MICRO-22bfda.svg
    :alt: calver: YY.MM.MICRO
    :target: https://calver.org/

.. |gha| image:: https://github.com/twisted/incremental/actions/workflows/tests.yaml/badge.svg
    :alt: Tests
    :target: https://github.com/twisted/incremental/actions/workflows/tests.yaml

.. |coverage| image:: https://img.shields.io/badge/Coverage-100%25-green
    :alt: Coverage: 100%
