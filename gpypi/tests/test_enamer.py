#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

Test ``get_vars`` with all types of URI's we can come up with.

.. note::

    up_pn and up_pv are upstream's package name and package version respectively
    and not actually used in an ebuild. These are the names returned
    from yolklib/PyPI.

"""

import unittest2

from gpypi.enamer import *
from gpypi.tests import *


class TestEnamer(BaseTestCase):
    """"""

    def test_sanitize_uri(self):
        self.assertEqual(Enamer.sanitize_uri("http://www.domain.org/library/urlparse.html?highlight=split%20url"),
            "http://www.domain.org/library/urlparse.html")
        self.assertEqual(Enamer.sanitize_uri("http://www.domain.org/library/urlparse.html#test"),
            "http://www.domain.org/library/urlparse.html")
        self.assertEqual(Enamer.sanitize_uri("http://www.domain.org/library/urlparse.html;test?highlight=split%20ur#test"),
            "http://www.domain.org/library/urlparse.html")

    def test_get_filename(self):
        """Return filename minus extension from src_uri"""
        self.assertEqual(Enamer.get_filename("http://www.foo.com/pkgfoo-1.0.tbz2"), "pkgfoo-1.0")
        self.assertEqual(Enamer.get_filename("http://www.foo.com/PKGFOO-1.0.tbz2"), "PKGFOO-1.0")
        self.assertEqual(Enamer.get_filename("http://www.foo.com/pkgfoo_1.0.tbz2"), "pkgfoo_1.0")
        self.assertEqual(Enamer.get_filename("http://www.foo.com/PKGFOO_1.0.tbz2"), "PKGFOO_1.0")
        self.assertEqual(Enamer.get_filename("http://www.foo.com/pkg-foo-1.0_beta1.tbz2"), "pkg-foo-1.0_beta1")
        self.assertEqual(Enamer.get_filename("http://www.foo.com/pkg_foo-1.0lawdy.tbz2"), "pkg_foo-1.0lawdy")
        self.assertEqual(Enamer.get_filename("http://internap.dl.sourceforge.net/sourceforge/abeni/abeni-0.0.22.tar.gz"),
            "abeni-0.0.22")
        self.assertEqual(Enamer.get_filename("http://internap.dl.sourceforge.net/sourceforge/dummy/StupidName_0.2.tar.gz"),
            "StupidName_0.2")

    def test_strip_ext(self):
        """Strip extension tests"""
        self.assertEqual(Enamer.strip_ext("test.txt"), 'test.txt')
        self.assertEqual(Enamer.strip_ext("test.zip"), 'test')
        self.assertEqual(Enamer.strip_ext("/path/test.zip"), '/path/test')
        self.assertEqual(Enamer.strip_ext("/path/test.zip.tar.gz"), '/path/test.zip')
        self.assertEqual(Enamer.strip_ext("/path/test.zip.tar.out"), '/path/test.zip.tar.out')

    def test_is_valid_uri(self):
        """Check if URI's addressing scheme is valid"""
        self.assertTrue(Enamer.is_valid_uri('http://foo.com/foo-1.0.tbz2'))
        self.assertTrue(Enamer.is_valid_uri('ftp://foo.com/foo-1.0.tbz2'))
        self.assertTrue(Enamer.is_valid_uri('mirror://sourceforge/foo-1.0.tbz2'))
        self.assertTrue(Enamer.is_valid_uri('http://foo.com/foo-1.0.tbz2#md5=2E3AF09'))
        self.assertTrue(Enamer.is_valid_uri('svn://foo.com/trunk/foo'))
        self.assertTrue(Enamer.is_valid_uri('http://www.themarkedmen.com/'))

        self.assertFalse(Enamer.is_valid_uri('The Marked Men'))

    def test_convert_license(self):
        """Convert classifier license to known portage license"""
        self.assertEqual(Enamer.convert_license(["License :: OSI Approved :: Zope Public License"]), "ZPL")
        self.assertEqual(Enamer.convert_license(["License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)"]),  "LGPL-2.1")
        self.assertEqual(Enamer.convert_license(["License :: Public Domain"]), "public-domain")
        self.assertEqual(Enamer.convert_license([]), "")
        self.assertEqual(Enamer.convert_license([], 'GPL alike'), 'GPL-2')

    def test_is_valid_license(self):
        """Check if license string matches a valid one in ${PORTDIR}/licenses"""
        self.assertFalse(Enamer.is_valid_portage_license("GPL"))
        self.assertTrue(Enamer.is_valid_portage_license("GPL-2"))

    def test_get_vars1(self):
        """
        Absolute best-case scenario determines $P from up_pn, up_pv
        We have a sanely named package and URI is perfect.

        """
        up_pn = "pkgfoo"
        up_pv = "1.0"
        uri = "http://www.foo.com/pkgfoo-1.0.tbz2"
        correct = \
            {'pn': 'pkgfoo',
             'pv': '1.0',
             'p': 'pkgfoo-1.0',
             'my_pn': [],
             'my_pv': [],
             'my_p': '',
             'my_p_raw': '',
             'src_uri': 'http://www.foo.com/${P}.tbz2',
             }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    @unittest2.expectedFailure # TODO: compare MY_P and MY_P_RAW
    def test_get_vars2(self):
        """
        (up_pn == pn) but URI has wrong case

        """
        up_pn = "pkgfoo"
        up_pv = "1.0"
        uri = "http://www.foo.com/PkgFoo-1.0.tbz2"
        correct = \
            {'pn': 'pkgfoo',
             'pv': '1.0',
             'p': 'pkgfoo-1.0',
             'my_pn': ['PkgFoo'],
             'my_pv': [],
             'my_p': '${MY_PN}-${PV}',
             'my_p_raw': 'PkgFoo-1.0',
             'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
             }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars3(self):
        """
        (up_pn != pn) URI has correct case

        """
        up_pn = "PKGFoo"
        up_pv = "1.0"
        uri = "http://www.foo.com/pkgfoo-1.0.tbz2"
        correct = \
            {'pn': 'pkgfoo',
             'pv': '1.0',
             'p': 'pkgfoo-1.0',
             'my_pn': [],
             'my_pv': [],
             'my_p': '',
             'my_p_raw': '',
             'src_uri': 'http://www.foo.com/${P}.tbz2',
             }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars4(self):
        """
        up_pn is not lower case but matches uri pn
        """
        pn = "pkgfoo"
        up_pn = "PKGFoo"
        up_pv = "1.0"
        uri = "http://www.foo.com/PKGfoo-1.0.tbz2"
        correct =\
            {'pn': 'pkgfoo',
             'pv': '1.0',
             'p': 'pkgfoo-1.0',
             'my_pn': ['PKGFoo'],
             'my_pv': [],
             'my_p': '${MY_PN}-${PV}',
             'my_p_raw': 'PKGfoo-1.0',
             'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
             }
        results = Enamer.get_vars(uri, up_pn, up_pv, pn)
        self.assertEqual(correct, results)

    @unittest2.expectedFailure # TODO: compare MY_P and MY_P_RAW
    def test_get_vars5(self):
        """
        up_pn is not lower case and doesn't match uri case
        """
        pn = "pkgfoo"
        up_pn = "PKGFoo"
        up_pv = "1.0"
        uri = "http://www.foo.com/pkgFOO-1.0.tbz2"
        correct =\
            {'pn': 'pkgfoo',
             'pv': '1.0',
             'p': 'pkgfoo-1.0',
             'my_pn': ['pkgFOO'],
             'my_pv': [],
             'my_p': '${MY_PN}-${PV}',
             'my_p_raw': 'pkgFOO-1.0',
             'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
             }
        results = Enamer.get_vars(uri, up_pn, up_pv, pn)
        self.assertEqual(correct, results)

    def test_get_vars6(self):
        """
        pn has uppercase
        """
        pn = "pkgfoo"
        up_pn = "PkgFoo"
        up_pv = "1.0"
        pv = "1.0"
        my_pn = [up_pn]
        my_pv = []
        uri = "http://www.foo.com/PkgFoo-1.0.tbz2"
        correct =\
            {'pn': 'pkgfoo',
             'pv': '1.0',
             'p': 'pkgfoo-1.0',
             'my_pn': ['PkgFoo'],
             'my_pv': [],
             'my_p': '${MY_PN}-${PV}',
             'my_p_raw': 'PkgFoo-1.0',
             'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
             }
        results = Enamer.get_vars(uri, up_pn, up_pv, pn, pv, my_pn, my_pv)
        self.assertEqual(correct, results)

    def test_get_vars7(self):
        """
        up_pn has uppercase, no PN given
        """
        up_pn = "PkgFoo"
        up_pv = "1.0"
        pn = ""
        pv = "1.0"
        my_pv = []
        my_pn = []
        uri = "http://www.foo.com/PkgFoo-1.0.tbz2"
        correct =\
            {'pn': 'pkgfoo',
             'pv': '1.0',
             'p': 'pkgfoo-1.0',
             'my_pn': ['PkgFoo'],
             'my_pv': [],
             'my_p': '${MY_PN}-${PV}',
             'my_p_raw': 'PkgFoo-1.0',
             'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
             }
        results = Enamer.get_vars(uri, up_pn, up_pv, pn, pv, my_pn, my_pv)
        self.assertEqual(correct, results)

    def test_get_vars8(self):
        """
        Bad suffix on PV that can be removed
        """
        up_pn = "pkgfoo"
        up_pv = "1.0dev"
        uri = "http://www.foo.com/pkgfoo-1.0dev.tbz2"
        correct = \
            {'pn': 'pkgfoo',
             'pv': '1.0',
             'p': 'pkgfoo-1.0',
             'my_pn': [],
             'my_pv': ['${PV}dev'],
             'my_p': '${PN}-${MY_PV}',
             'my_p_raw': 'pkgfoo-1.0dev',
             'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
             }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars9(self):
        """
        An existing -r123 suffix on upstream version
        is changed to _pre123
        """
        # TODO: my_pv shouldn't include revision number
        up_pn = "pkgfoo"
        up_pv = "1.0-r123"
        uri = "http://www.foo.com/pkgfoo-1.0-r123.tbz2"
        correct = \
            {'pn': 'pkgfoo',
             'pv': '1.0.123',
             'p': 'pkgfoo-1.0.123',
             'my_pn': [],
             'my_pv': ['${PV: -4}-r123'],
             'my_p': '${PN}-${MY_PV}',
             'my_p_raw': 'pkgfoo-1.0-r123',
             'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
             }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars10(self):
        """
        -r1234 suffix on PV that can be removed
        """
        up_pn = "pkgfoo"
        up_pv = "1.0.dev-r1234"
        uri = "http://www.foo.com/pkgfoo-1.0.dev-r1234.tbz2"
        correct = \
            {'pn': 'pkgfoo',
             'pv': '1.0.1234',
             'p': 'pkgfoo-1.0.1234',
             'my_pn': [],
             'my_pv': ['${PV: -5}-r1234', '${PV}.dev'],
             'my_p': '${PN}-${MY_PV}',
             'my_p_raw': 'pkgfoo-1.0.dev-r1234',
             'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
             }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars11(self):
        """
        -r1234 suffix on PV that can be removed
        """
        up_pn = "pkgfoo"
        up_pv = "1.0dev-r1234"
        uri = "http://www.foo.com/pkgfoo-1.0dev-r1234.tbz2"
        correct = \
            {'pn': 'pkgfoo',
             'pv': '1.0.1234',
             'p': 'pkgfoo-1.0.1234',
             'my_pn': [],
             'my_pv': ['${PV: -5}-r1234', '${PV}dev'],
             'my_p': '${PN}-${MY_PV}',
             'my_p_raw': 'pkgfoo-1.0dev-r1234',
             'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
             }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars12(self):
        """
        a4 suffix -> _alpha4
        """
        up_pn = "pkgfoo"
        up_pv = "1.0a4"
        uri = "http://www.foo.com/pkgfoo-1.0a4.tbz2"
        correct = \
            {'pn': 'pkgfoo',
             'pv': '1.0_alpha4',
             'p': 'pkgfoo-1.0_alpha4',
             'my_pn': [],
             'my_pv': ['${PV/_alpha/a}'],
             'my_p': '${PN}-${MY_PV}',
             'my_p_raw': 'pkgfoo-1.0a4',
             'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
             }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars13(self):
        """
        b1 suffix -> _beta1
        """
        up_pn = "pkgfoo"
        up_pv = "1.0b1"
        uri = "http://www.foo.com/pkgfoo-1.0b1.tbz2"
        correct = \
            {'pn': 'pkgfoo',
             'pv': '1.0_beta1',
             'p': 'pkgfoo-1.0_beta1',
             'my_pn': [],
             'my_pv': ['${PV/_beta/b}'],
             'my_p': '${PN}-${MY_PV}',
             'my_p_raw': 'pkgfoo-1.0b1',
             'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
             }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars14(self):
        """
        -b1 suffix -> _beta1
        """
        up_pn = "pkgfoo"
        up_pv = "1.0-b1"
        uri = "http://www.foo.com/pkgfoo-1.0-b1.tbz2"
        correct = \
            {'pn': 'pkgfoo',
             'pv': '1.0_beta1',
             'p': 'pkgfoo-1.0_beta1',
             'my_pn': [],
             'my_pv': ['${PV/_beta/-b}'],
             'my_p': '${PN}-${MY_PV}',
             'my_p_raw': 'pkgfoo-1.0-b1',
             'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
             }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars15(self):
        """
        -a4 suffix -> _alpha4
        """
        up_pn = "pkgfoo"
        up_pv = "1.0-a4"
        uri = "http://www.foo.com/pkgfoo-1.0-a4.tbz2"
        correct = \
            {'pn': 'pkgfoo',
             'pv': '1.0_alpha4',
             'p': 'pkgfoo-1.0_alpha4',
             'my_pn': [],
             'my_pv': ['${PV/_alpha/-a}'],
             'my_p': '${PN}-${MY_PV}',
             'my_p_raw': 'pkgfoo-1.0-a4',
             'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
             }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars16(self):
        """
        -rc3 suffix -> _rc3
        """
        up_pn = "pkgfoo"
        up_pv = "1.0-rc3"
        uri = "http://www.foo.com/pkgfoo-1.0-rc3.tbz2"
        input_test = (uri, up_pn, up_pv)
        correct = \
            {'pn': 'pkgfoo',
             'pv': '1.0_rc3',
             'p': 'pkgfoo-1.0_rc3',
             'my_pn': [],
             'my_pv': ['${PV/_rc/-rc}'],
             'my_p': '${PN}-${MY_PV}',
             'my_p_raw': 'pkgfoo-1.0-rc3',
             'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
             }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars17(self):
        """
        rc3 suffix -> _rc3
        """
        up_pn = "pkgfoo"
        up_pv = "1.0rc3"
        uri = "http://www.foo.com/pkgfoo-1.0rc3.tbz2"
        correct = \
            {'pn': 'pkgfoo',
             'pv': '1.0_rc3',
             'p': 'pkgfoo-1.0_rc3',
             'my_pn': [],
             'my_pv': ['${PV/_rc/rc}'],
             'my_p': '${PN}-${MY_PV}',
             'my_p_raw': 'pkgfoo-1.0rc3',
             'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
             }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars18(self):
        """
        .rc3 suffix -> _rc3
        """
        up_pn = "pkgfoo"
        up_pv = "1.0.rc3"
        uri = "http://www.foo.com/pkgfoo-1.0.rc3.tbz2"
        correct = \
            {'pn': 'pkgfoo',
             'pv': '1.0_rc3',
             'p': 'pkgfoo-1.0_rc3',
             'my_pn': [],
             'my_pv': ['${PV/_rc/.rc}'],
             'my_p': '${PN}-${MY_PV}',
             'my_p_raw': 'pkgfoo-1.0.rc3',
             'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
             }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars19(self):
        """
        uppercase package name
        .rc3 suffix -> _rc3
        """
        up_pn = "PkgFoo"
        up_pv = "1.0.rc3"
        uri = "http://www.foo.com/PkgFoo-1.0.rc3.tbz2"
        input_test = (uri, up_pn, up_pv)
        correct = \
            {'pn': 'pkgfoo',
             'pv': '1.0_rc3',
             'p': 'pkgfoo-1.0_rc3',
             'my_pn': ['PkgFoo'],
             'my_pv': ['${PV/_rc/.rc}'],
             'my_p': '${MY_PN}-${MY_PV}',
             'my_p_raw': 'PkgFoo-1.0.rc3',
             'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
             }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars20(self):
        """
        -c3 suffix -> _rc3
        """
        up_pn = "PkgFoo"
        up_pv = "1.0-c3"
        uri = "http://www.foo.com/PkgFoo-1.0-c3.tbz2"
        correct = \
            {'pn': 'pkgfoo',
             'pv': '1.0_rc3',
             'p': 'pkgfoo-1.0_rc3',
             'my_pn': ['PkgFoo'],
             'my_pv': ['${PV/_rc/-c}'],
             'my_p': '${MY_PN}-${MY_PV}',
             'my_p_raw': 'PkgFoo-1.0-c3',
             'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
             }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars21(self):
        """
        uppercase package name
        .c3 suffix -> _rc3
        """
        up_pn = "PkgFoo"
        up_pv = "1.0.c3"
        uri = "http://www.foo.com/PkgFoo-1.0.c3.tbz2"
        correct = \
            {'pn': 'pkgfoo',
             'pv': '1.0_rc3',
             'p': 'pkgfoo-1.0_rc3',
             'my_pn': ['PkgFoo'],
             'my_pv': ['${PV/_rc/.c}'],
             'my_p': '${MY_PN}-${MY_PV}',
             'my_p_raw': 'PkgFoo-1.0.c3',
             'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
             }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars22(self):
        """
        uppercase package name
        c3 suffix -> _rc3
        """
        up_pn = "PkgFoo"
        up_pv = "1.0c3"
        uri = "http://www.foo.com/PkgFoo-1.0c3.tbz2"
        correct = \
            {'pn': 'pkgfoo',
             'pv': '1.0_rc3',
             'p': 'pkgfoo-1.0_rc3',
             'my_pn': ['PkgFoo'],
             'my_pv': ['${PV/_rc/c}'],
             'my_p': '${MY_PN}-${MY_PV}',
             'my_p_raw': 'PkgFoo-1.0c3',
             'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
             }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars23(self):
        """
        package name with a '.' in it, Zope packages have this often

        Problem:
             We can't have a '.' in PN

        Solution:
            We convert the . to a -

        Note: We also may need to use PYTHON_MODNAME='pkg.foo'

        Example:
            zope.foo -> zope-foo
        """
        up_pn = "pkg.foo"
        up_pv = "1.0"
        uri = "http://www.foo.com/pkg.foo-1.0.tbz2"
        correct = \
            {'pn': 'pkg-foo',
             'pv': '1.0',
             'p': 'pkg-foo-1.0',
             'my_pn': ['${PN/-/.}'],
             'my_pv': [],
             'my_p': '${MY_PN}-${PV}',
             'my_p_raw': 'pkg.foo-1.0',
             'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
             }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars24(self):
        """0.1a3 -> 0.1_alpha3"""
        up_pn = "3to2"
        up_pv = "0.1a3"
        uri = "http://pypi.python.org/packages/source/3/3to2/3to2-0.1a3.tar.gz"
        correct = \
            {'pn': '3to2',
             'pv': '0.1_alpha3',
             'p': '3to2-0.1_alpha3',
             'my_pn': [],
             'my_pv': ['${PV/_alpha/a}'],
             'my_p': '${PN}-${MY_PV}',
             'my_p_raw': '3to2-0.1a3',
             'src_uri': 'http://pypi.python.org/packages/source/3/3to2/${MY_P}.tar.gz',
             }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars25(self):
        """0.1dev-20091118 -> 0.1_pre20091118"""
        up_pn = "airspeed"
        up_pv = "0.1dev-20091118"
        uri = "http://pypi.python.org/packages/any/a/airspeed/airspeed-0.1dev_20091118.tar.gz"
        correct = \
            {'pn': 'airspeed',
             'pv': '0.1_pre20091118',
             'p': 'airspeed-0.1_pre20091118',
             'my_pn': [],
             'my_pv': ['${PV/_pre/dev-}'],
             'my_p': '${PN}-${MY_PV}',
             'my_p_raw': 'airspeed-0.1dev_20091118',
             'src_uri': 'http://pypi.python.org/packages/any/a/airspeed/${MY_P}.tar.gz',
             }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars26(self):
        """1.0beta1 -> 1.0_beta1"""
        up_pn = "atreal.cmfeditions.unlocker"
        up_pv = "1.0beta1"
        uri = "http://pypi.python.org/packages/2.4/a/atreal.cmfeditions.unlocker/atreal.cmfeditions.unlocker-1.0beta1.tar.gz"
        correct = {
             'pn': 'atreal-cmfeditions-unlocker',
             'pv': '1.0_beta1',
             'p': 'atreal-cmfeditions-unlocker-1.0_beta1',
             'my_pn': ['${PN/-/.}'],
             'my_pv': ['${PV/_beta/beta}'],
             'my_p': '${MY_PN}-${MY_PV}',
             'my_p_raw': 'atreal.cmfeditions.unlocker-1.0beta1',
             'src_uri': 'http://pypi.python.org/packages/2.4/a/atreal.cmfeditions.unlocker/${MY_P}.tar.gz',
             }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars27(self):
        """0.10alpha2 -> 0.10_alpha2"""
        up_pn = "zif.sedna"
        up_pv = "0.10alpha2"
        uri = "http://pypi.python.org/packages/2.5/z/zif.sedna/zif.sedna-0.10alpha2.tar.gz"
        correct = \
            {'pn': 'zif-sedna',
             'pv': '0.10_alpha2',
             'p': 'zif-sedna-0.10_alpha2',
             'my_pn': ['${PN/-/.}'],
             'my_pv': ['${PV/_alpha/alpha}'],
             'my_p': '${MY_PN}-${MY_PV}',
             'my_p_raw': 'zif.sedna-0.10alpha2',
             'src_uri': 'http://pypi.python.org/packages/2.5/z/zif.sedna/${MY_P}.tar.gz',
             }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars28(self):
        """1.1.3beta -> 1.1.3_beta"""
        up_pn = "xapian-haystack"
        up_pv = "1.1.3beta"
        uri = "http://pypi.python.org/packages/source/x/xapian-haystack/xapian-haystack-1.1.3beta.tar.gz"
        correct = {
            'pn': 'xapian-haystack',
            'pv': '1.1.3_beta',
            'p': 'xapian-haystack-1.1.3_beta',
            'my_pn': [],
            'my_pv': ['${PV/_beta/beta}'],
            'my_p': '${PN}-${MY_PV}',
            'my_p_raw': 'xapian-haystack-1.1.3beta',
            'src_uri': 'http://pypi.python.org/packages/source/x/xapian-haystack/${MY_P}.tar.gz',
        }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars29(self):
        """0.6.2-test3 -> 0.6.2_alpha3"""
        up_pn = "wtop"
        up_pv = "0.6.2-test3"
        uri = "http://pypi.python.org/packages/source/w/wtop/wtop-0.6.2-test3.tar.gz"
        correct = {
            'pn': 'wtop',
            'pv': '0.6.2_alpha3',
            'p': 'wtop-0.6.2_alpha3',
            'my_pn': [],
            'my_pv': ['${PV/_alpha/-test}'],
            'my_p': '${PN}-${MY_PV}',
            'my_p_raw': 'wtop-0.6.2-test3',
            'src_uri': 'http://pypi.python.org/packages/source/w/wtop/${MY_P}.tar.gz',
        }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    @unittest2.expectedFailure
    def test_get_vars30(self):
        """"0.3.0b2.1 -> UNKNOWN"""
        up_pn = "zw.schema"
        up_pv = "0.3.0b2.1"
        # TODO: parse b2.1
        uri = "http://pypi.python.org/packages/source/z/zw.schema/zw.schema-0.3.0b2.1.tar.gz"
        correct = {
            'pn': 'zw.schema',
            'pv': '0.3.0_beta2',
            'p': 'zw.schema-0.3.0_beta2',
            'my_pn': [],
            'my_pv': ['${PV/_beta/b}'],
            'my_p': '${PN}-${MY_PV}',
            'my_p_raw': 'zw.schema-0.3.0b2.1',
            'src_uri': 'http://pypi.python.org/packages/source/z/zw.schema/${MY_P}.tar.gz',
        }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars31(self):
        """1.2-devel -> 1.2"""
        up_pn = "optcomplete"
        up_pv = "1.2-devel"
        uri = "http://pypi.python.org/packages/source/o/optcomplete/optcomplete-1.2-devel.tar.gz"
        correct = {
            'pn': 'optcomplete',
            'pv': '1.2',
            'p': 'optcomplete-1.2',
            'my_pn': [],
            'my_pv': ['${PV}-devel'],
            'my_p': '${PN}-${MY_PV}',
            'my_p_raw': 'optcomplete-1.2-devel',
            'src_uri': 'http://pypi.python.org/packages/source/o/optcomplete/${MY_P}.tar.gz',
        }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars32(self):
        """1.1.56-STABLE -> 1.1.56"""
        up_pn = "django-plus"
        up_pv = "1.1.56-STABLE"
        uri = "http://pypi.python.org/packages/source/d/django-plus/django-plus-1.1.56-stable.tar.gz#md5=e788af64f1dfa643bb614a9e0453c1cd"
        correct = {
            'pn': 'django-plus',
            'pv': '1.1.56',
            'p': 'django-plus-1.1.56',
            'my_pn': [],
            'my_pv': ['${PV}-STABLE'],
            'my_p': '${PN}-${MY_PV}',
            'my_p_raw': 'django-plus-1.1.56-stable',
            'src_uri': 'http://pypi.python.org/packages/source/d/django-plus/${MY_P}.tar.gz',
        }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    @unittest2.expectedFailure
    def test_get_vars33(self):
        """Community Codeswarm-0.2.1 -> community-codeswarm-0.2.1"""
        up_pn = "Community Codeswarm"
        up_pv = "0.2.1"
        uri = "http://pypi.python.org/packages/source/C/Community%20Codeswarm/Community%20Codeswarm-0.2.1.tar.gz"
        correct = {
            'pn': 'community-codeswarm',
            'pv': '0.2.1',
            'p': 'community-codeswarm-0.2.1',
            'my_pn': ['lowercase', '${PN/ /-}'],
            'my_pv': [],
            'my_p': '${MY_PN}-${PV}',
            'my_p_raw': 'Community%20Codeswarm-0.2.1',
            'src_uri': 'http://pypi.python.org/packages/source/C/Community%20Codeswarm/${MY_P}.tar.gz',
        }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars34(self):
        """1.1.56-STABLE -> 1.1.56"""
        up_pn = "django-plus"
        up_pv = "1.1.56-STABLE"
        uri = "http://pypi.python.org/packages/source/d/django-plus/django-plus-1.1.56-stable.tar.gz#md5=e788af64f1dfa643bb614a9e0453c1cd"
        correct = {
            'pn': 'django-plus',
            'pv': '1.1.56',
            'p': 'django-plus-1.1.56',
            'my_pn': [],
            'my_pv': ['${PV}-STABLE'],
            'my_p': '${PN}-${MY_PV}',
            'my_p_raw': 'django-plus-1.1.56-stable',
            'src_uri': 'http://pypi.python.org/packages/source/d/django-plus/${MY_P}.tar.gz',
        }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars35(self):
        """2.0.1-pre1 -> 2.0.1_pre1"""
        up_pn = "django-articles"
        up_pv = "2.0.1-pre1"
        uri = "http://pypi.python.org/packages/source/d/django-articles/django-articles-2.0.1-pre1.tar.gz"
        correct = {
            'pn': 'django-articles',
            'pv': '2.0.1_pre1',
            'p': 'django-articles-2.0.1_pre1',
            'my_pn': [],
            'my_pv': ['${PV/_pre/-pre}'],
            'my_p': '${PN}-${MY_PV}',
            'my_p_raw': 'django-articles-2.0.1-pre1',
            'src_uri': 'http://pypi.python.org/packages/source/d/django-articles/${MY_P}.tar.gz',
        }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars36(self):
        """0.1.4pre -> 2.0.1_pre"""
        up_pn = "django-mako"
        up_pv = "0.1.4pre"
        uri = "http://pypi.python.org/packages/source/d/django-mako/django-mako-0.1.4pre.tar.gz"
        correct = {
            'pn': 'django-mako',
            'pv': '0.1.4_pre',
            'p': 'django-mako-0.1.4_pre',
            'my_pn': [],
            'my_pv': ['${PV/_pre/pre}'],
            'my_p': '${PN}-${MY_PV}',
            'my_p_raw': 'django-mako-0.1.4pre',
            'src_uri': 'http://pypi.python.org/packages/source/d/django-mako/${MY_P}.tar.gz',
        }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars37(self):
        """2.0.1-pre1 -> 2.0.1_pre1"""
        up_pn = "django-mako"
        up_pv = "0.1.4pre"
        uri = "http://pypi.python.org/packages/source/d/django-mako/django-mako-0.1.4pre.tar.gz"
        correct = {
            'pn': 'django-mako',
            'pv': '0.1.4_pre',
            'p': 'django-mako-0.1.4_pre',
            'my_pn': [],
            'my_pv': ['${PV/_pre/pre}'],
            'my_p': '${PN}-${MY_PV}',
            'my_p_raw': 'django-mako-0.1.4pre',
            'src_uri': 'http://pypi.python.org/packages/source/d/django-mako/${MY_P}.tar.gz',
        }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars38(self):
        """1.0.0-preview2 -> 1.0.0_pre2"""
        up_pn = "mrv"
        up_pv = "1.0.0-preview2"
        uri = "http://pypi.python.org/packages/source/M/MRV/mrv-1.0.0-Preview2.zip"
        correct = {
            'pn': 'mrv',
            'pv': '1.0.0_pre2',
            'p': 'mrv-1.0.0_pre2',
            'my_pn': [],
            'my_pv': ['${PV/_pre/-preview}'],
            'my_p': '${PN}-${MY_PV}',
            'my_p_raw': 'mrv-1.0.0-Preview2',
            'src_uri': 'http://pypi.python.org/packages/source/M/MRV/${MY_P}.zip',
        }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars39(self):
        """0.2.0RC5 -> 0.2.0_rc5"""
        up_pn = "irssinotifier"
        up_pv = "0.2.0RC5"
        uri = "http://pypi.python.org/packages/source/I/IrssiNotifier/IrssiNotifier-0.2.0RC5.tar.bz2"
        correct = {
            'pn': 'irssinotifier',
            'pv': '0.2.0_rc5',
            'p': 'irssinotifier-0.2.0_rc5',
            'my_pn': [],
            'my_pv': ['${PV/_rc/RC}'],
            'my_p': '${PN}-${MY_PV}',
            'my_p_raw': 'IrssiNotifier-0.2.0RC5',
            'src_uri': 'http://pypi.python.org/packages/source/I/IrssiNotifier/${MY_P}.tar.bz2',
        }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars40(self):
        """3.0.rc.8 -> 3.0_rc8"""
        up_pn = "pydap"
        up_pv = "3.0.rc.8"
        uri = "http://pypi.python.org/packages/source/P/Pydap/Pydap-3.0.rc.8.tar.gz"
        correct = {
            'pn': 'pydap',
            'pv': '3.0_rc8',
            'p': 'pydap-3.0_rc8',
            'my_pn': [],
            'my_pv': ['${PV/_rc/.rc.}'],
            'my_p': '${PN}-${MY_PV}',
            'my_p_raw': 'Pydap-3.0.rc.8',
            'src_uri': 'http://pypi.python.org/packages/source/P/Pydap/${MY_P}.tar.gz',
        }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars41(self):
        """0.1-beta-3 -> 0.1_beta3"""
        up_pn = "clyther"
        up_pv = "0.1-beta-3"
        uri = "http://pypi.python.org/packages/source/c/clyther/clyther-0.1-beta-3.tar.gz"
        correct = {
            'pn': 'clyther',
            'pv': '0.1_beta3',
            'p': 'clyther-0.1_beta3',
            'my_pn': [],
            'my_pv': ['${PV/_beta/-beta-}'],
            'my_p': '${PN}-${MY_PV}',
            'my_p_raw': 'clyther-0.1-beta-3',
            'src_uri': 'http://pypi.python.org/packages/source/c/clyther/${MY_P}.tar.gz',
        }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars42(self):
        """0.1.5.-beta -> 0.1.5_beta"""
        up_pn = "django-projector"
        up_pv = "0.1.5.-beta"
        uri = "http://pypi.python.org/packages/source/d/django-projector/django-projector-0.1.5.-beta.tar.gz"
        correct = {
            'pn': 'django-projector',
            'pv': '0.1.5_beta',
            'p': 'django-projector-0.1.5_beta',
            'my_pn': [],
            'my_pv': ['${PV/_beta/.-beta}'],
            'my_p': '${PN}-${MY_PV}',
            'my_p_raw': 'django-projector-0.1.5.-beta',
            'src_uri': 'http://pypi.python.org/packages/source/d/django-projector/${MY_P}.tar.gz',
        }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    @unittest2.expectedFailure
    def test_get_vars43(self):
        """v1.0.0 -> 1.0.0"""
        up_pn = "bdflib"
        up_pv = "v1.0.0"
        uri = "http://pypi.python.org/packages/source/b/bdflib/bdflib-v1.0.0.tar.gz"
        correct = {
            'pn': 'bdflib',
            'pv': '1.0.0',
            'p': 'bdflib-1.0.0',
            'my_pn': [],
            'my_pv': ['v${PV}'],
            'my_p': '${PN}-${MY_PV}',
            'my_p_raw': 'bdflib-v1.0.0',
            'src_uri': 'http://pypi.python.org/packages/source/b/bdflib/${MY_P}.tar.gz',
        }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars44(self):
        """0.1r1 -> 0.1.1"""
        up_pn = "flamboyantsshd"
        up_pv = "0.1r1"
        uri = "http://pypi.python.org/packages/source/f/flamboyantsshd/flamboyantsshd-0.1r1.tar.gz"
        correct = {
            'pn': 'flamboyantsshd',
            'pv': '0.1.1',
            'p': 'flamboyantsshd-0.1.1',
            'my_pn': [],
            'my_pv': ['${PV: -2}r1'],
            'my_p': '${PN}-${MY_PV}',
            'my_p_raw': 'flamboyantsshd-0.1r1',
            'src_uri': 'http://pypi.python.org/packages/source/f/flamboyantsshd/${MY_P}.tar.gz',
        }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars45(self):
        """1.0.r39 -> 1.0.39"""
        up_pn = "fusepy"
        up_pv = "1.0.r39"
        uri = "http://pypi.python.org/packages/source/f/fusepy/fusepy-1.0.r39.tar.gz"
        correct = {
            'pn': 'fusepy',
            'pv': '1.0.39',
            'p': 'fusepy-1.0.39',
            'my_pn': [],
            'my_pv': ['${PV: -3}.r39'],
            'my_p': '${PN}-${MY_PV}',
            'my_p_raw': 'fusepy-1.0.r39',
            'src_uri': 'http://pypi.python.org/packages/source/f/fusepy/${MY_P}.tar.gz',
        }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars46(self):
        """0.3.0patch1 -> 0.3.0.1"""
        up_pn = "pymage"
        up_pv = "0.3.0patch1"
        uri = "http://pypi.python.org/packages/source/p/pymage/pymage-0.3.0patch1.tar.gz"
        correct = {
            'pn': 'pymage',
            'pv': '0.3.0.1',
            'p': 'pymage-0.3.0.1',
            'my_pn': [],
            'my_pv': ['${PV: -2}patch1'],
            'my_p': '${PN}-${MY_PV}',
            'my_p_raw': 'pymage-0.3.0patch1',
            'src_uri': 'http://pypi.python.org/packages/source/p/pymage/${MY_P}.tar.gz',
        }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars47(self):
        """1.3p3 -> 1.3.3"""
        # TODO: uri and my_p do not match
        up_pn = "pyshipping"
        up_pv = "1.3p3"
        uri = "http://pypi.python.org/packages/source/p/pyShipping/pyShipping-1.3p3.tar.gz"
        correct = {
            'pn': 'pyshipping',
            'pv': '1.3.3',
            'p': 'pyshipping-1.3.3',
            'my_pn': [],
            'my_pv': ['${PV: -2}p3'],
            'my_p': '${PN}-${MY_PV}',
            'my_p_raw': 'pyShipping-1.3p3',
            'src_uri': 'http://pypi.python.org/packages/source/p/pyShipping/${MY_P}.tar.gz',
        }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

# TODO: URLs don't actually match MY_P (case sensitivity, special chars..., SRC_URI class should handle this)

class TestSrcUriNamer(BaseTestCase):
    """"""

    def test_is_valid_for_uri(self):
        pass
        #out = PyPiSrcUri('').is_valid_for_uri('pytz', '2010h', 'tar.bz2')
        #self.assertTrue(out)

    #def test_parse_sourceforge_uri(self):
        #""" Convert sourceforge URI to portage mirror URI """
        #for url, mirror in (
            #("http://internap.dl.sourceforge.net/sourceforge/pythonreports/PythonReports-0.3.0.tar.gz",
                #("mirror://sourceforge/pythonreports/PythonReports-0.3.0.tar.gz",
                        #"http://sourceforge.net/projects/pythonreports/")
            #),
            #("http://downloads.sourceforge.net/pythonreports/PythonReports-0.3.0.tar.gz",
                #("mirror://sourceforge/pythonreports/PythonReports-0.3.0.tar.gz",
                        #"http://sourceforge.net/projects/pythonreports/")
            #),
            ## Test abbreviated sf.net domain
            #("http://downloads.sf.net/pythonreports/PythonReports-0.3.0.tar.gz",
                #("mirror://sourceforge/pythonreports/PythonReports-0.3.0.tar.gz",
                        #"http://sourceforge.net/projects/pythonreports/")
            #),
            ## Non-sourceforge URI
            #("http://yahoo.com/pythonReports-0.3.0.tar.gz",
                #('', '')
            #),
        #):
            #self.assertEqual(Enamer.parse_sourceforge_uri(url), mirror)

