.. g-pypi documentation master file, created by
   sphinx-quickstart on Thu May 13 09:07:15 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

:mod:`gpypi` -- Welcome to g-pypi's documentation!
====================================================

.. moduleauthor:: Domen Kožar [iElectric] <domen@dev.si>
.. module:: gpypi
    :platform: Everything that Gentoo supports.
    :synopsis: g-pypi manages ebuilds for Gentoo Linux using information in PyPi (Python Package Index)

:Author: Domen Kožar <domen@dev.si>
:Source code: `Github.com source browser <https://github.com/iElectric/g-pypi>`_
:Bug tracker: `Github.com issues <https://github.com/iElectric/g-pypi/issues>`_
:Generated: |today|
:License: Simplified BSD (2-clause)
:Version: |release|


.. sidebar:: Features

   * write ebuilds to overlay or stdout (formatted in ansi color, html and bbcode)
   * install ebuilds through portage
   * use :term:`MY_P`, :term:`MY_PN`, :term:`MY_PV` when needed using Bash substitutions
   * extract metadata from :term:`PyPi` like :term:`HOMEPAGE`, :term:`DESCRIPTION`, :term:`LICENSE`, :term:`AUTHOR`, etc.
   * determine :term:`RDEPEND` / :term:`DEPEND` from :mod:`setuptools`: ``install_requires``, ``tests_require``, ``setup_requires`` and ``extras_require``
   * determine :term:`PYTHON_MODNAME` from :mod:`setuptools`: `packages`, `py_modules` and `package_dir`
   * determine :term:`S` by unpacking ebuild
   * discovers `Sphinx documentation <http://sphinx.pocoo.org/>`_
   * discovers examples
   * discovers :mod:`nosetests` and ``setup.py test``
   * generates ebuilds for dependencies
   * uses Portage-alike colorful output
   * offers :ref:`customizable configuration <configuration>`
   * support for ``python setup.py sdist_ebuild``
   * updates ``Manifest`` file
   * generates ``metadata.xml`` file
   * appends ``ChangeLog`` file


.. topic:: Overview

    :command:`gpypi` is a command line tool for creating `Gentoo portage ebuilds <http://en.wikipedia.org/wiki/Ebuild>`_
    from `Python Package Index <http://pypi.python.org/pypi>`_.

    :command:`gpypi` was started as part of `Google Summer of Code 2010 <http://code.google.com/soc>`_
    by *Domen Kožar*, mentored by *Jesus Rivero*.

    :command:`gpypi` is not meant to be a `Gentoo developer replacement <http://www.gentoo.org/proj/en/devrel/roll-call/userinfo.xml>`_.
    On the contrary, it's goal is to make his (hers) life easier.

.. toctree::
    :maxdepth: 3

    userguide
    development
    api
    changelog

.. toctree::
   :hidden:

   glossary


Indices and tables
==================

* :ref:`glossary`
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
