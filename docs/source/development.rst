Development
===========


Workflow of creating an ebuild
******************************

    #. PyPi is queried for an package with coresponding version (if no version is given,
       highest available is used)

    #. PyPi metadata is collected, and :meth:`gpypi2.enamer.Enamer.get_vars` is used to collect
       common ebuild variables

    #. Initial ebuild is written to overlay with :term:`SRC_URI`

    #. Ebuild in unpacked.


How are :term:`PV`, :term:`PN`, :term:`MY_PV`, :term:`MY_PN` and :term:`SRC_URI` determined?
**********************************************************************************************

All the work is done by :meth:`gpypi2.enamer.Enamer.get_vars`. Specifically:

    * :term:`PV` and :term:`MY_PV` in :meth:`gpypi2.enamer.Enamer.parse_pv`
    * :term:`PN` and :term:`MY_PN` in :meth:`gpypi2.enamer.Enamer.parse_pn`
    * :term:`SRC_URI` and :term:`HOMEPAGE` in :class:`gpypi2.enamer.SrcUriNamer`


Tests against live PyPi -- :mod:`gpypi2.tests.test_pypi`
*********************************************************

This module runs numerous tests against whole PyPI. It should be run manually, 
to detect new possible issues. All failures MUST be first written as unittests
and then fixed accordingly.

.. important:: 
    
    Issues should not be closed until there are appropriate tests
    and documentation for the changeset.
