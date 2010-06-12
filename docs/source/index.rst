.. g-pypi2 documentation master file, created by
   sphinx-quickstart on Thu May 13 09:07:15 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

:mod:`gpypi2` -- Welcome to g-pypi2's documentation!
====================================================

.. moduleauthor:: Domen Kožar [iElectric] <domen@dev.si>
.. module:: gpypi2
    :platform: Everything that Gentoo supports.
    :synopsis: g-pypi2 manages ebuilds for Gentoo Linux using information in PyPi (Python Package Index)

:Author: Domen Kožar <domen@dev.si>
:Source code: `Bitbucket.org source browser <http://bitbucket.org/iElectric/g-pypi2/src>`_
:Bug tracker: `Bitbucket.org issues <http://bitbucket.org/iElectric/g-pypi2/issues?status=new&status=open>`_
:Version: |release|


.. topic:: Overview

   :mod:`gpypi2` is Python library and command line tool for ...

   :mod:`gpypi2` was started as part of `Google Summer of Code 2010 <http://code.google.com/soc>`_ by *Domen Kožar*, mentored by *Jesus Rivero*.


.. topic:: Features

   * use :term:`MY_P`, :term:`MY_PN`, :term:`MY_PV` when needed using Bash substitutions
   * extract metadata from PyPi like :term:`HOMEPAGE`, :term:`DESCRIPTION`, :term:`LICENSE`, :term:`AUTHOR`, etc.
   * determine dependencies from :mod:`setuptools` `install_requires`, `tests_require`, `setup_requires` and `extras_require`

.. note::
    :mod:`gpypi2` is not meant to be a developer replacment.
    It's goal is to make developers life easier.

.. toctree::
    :maxdepth: 3

    userguide
    development
    api
    changelog


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
* :ref:`glossary`
