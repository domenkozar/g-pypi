Development
===========


Workflow of creating an ebuild
******************************

    #. PyPi is queried for an package with coresponding version (if no version is given,
       highest available is used)

    #. PyPi metadata is collected, and :meth:`gpypi.enamer.Enamer.get_vars` is used to collect
       common ebuild variables

    #. Initial ebuild is written to overlay with :term:`SRC_URI`

    #. Ebuild in unpacked with Portage API through shell

    #. Unpacked dir is inspected for setup.py information

    #. Ebuild is rendered again and written to an overlay

    #. Possible dependencies from setup.py are resolved and whole process is repeated for each one.


How are :term:`PV`, :term:`PN`, :term:`MY_PV`, :term:`MY_PN` and :term:`SRC_URI` determined?
**********************************************************************************************

All the work is done by :meth:`gpypi.enamer.Enamer.get_vars`. Specifically:

    * :term:`PV` and :term:`MY_PV` in :meth:`gpypi.enamer.Enamer.parse_pv`
    * :term:`PN` and :term:`MY_PN` in :meth:`gpypi.enamer.Enamer.parse_pn`
    * :term:`SRC_URI` and :term:`HOMEPAGE` in :class:`gpypi.enamer.SrcUriNamer`


Tests against live PyPi -- :mod:`gpypi.tests.test_pypi`
*********************************************************

This module runs numerous tests against whole PyPI. It should be run manually, 
to detect new possible issues. All failures MUST be first written as unittests
and then fixed accordingly.

.. important:: 
    
    Issues should not be closed until there are appropriate tests
    and documentation for the changeset.


TODO
********************************************************

List of features that may be implemented in no particular order:

* atomic actions (cleanup on traceback/error)

* migrate to simpleindex and xmlrpc API provided by distutils2

* issue HEAD request to homepages (warn on failure)

* finish SrcUriNamer implementation

* implement setuptools Feature class

* SVN/GIT/HG support as SRC_URI

* implement homepage/src_uri as list (also includes config work)

* decide what to do with configuartion on dependency ebuilds

* search command

* use rewriting system instead of regex for pn/pv parsing
