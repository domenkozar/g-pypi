#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

Test ``get_vars`` with all types of URI's we can come up with.

Note:
-----

up_pn and up_pv are upstream's package name and package version respectively
and not actually used in an ebuild. These are the names returned
from yolklib/PyPI.


"""

from gpypi2.enamer import *
from gpypi2.tests import *


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

    def test_parse_sourceforge_uri(self):
        """ Convert sourceforge URI to portage mirror URI """
        for url, mirror in (
            ("http://internap.dl.sourceforge.net/sourceforge/pythonreports/PythonReports-0.3.0.tar.gz",
                ("mirror://sourceforge/pythonreports/PythonReports-0.3.0.tar.gz",
                        "http://sourceforge.net/projects/pythonreports/")
            ),
            ("http://downloads.sourceforge.net/pythonreports/PythonReports-0.3.0.tar.gz",
                ("mirror://sourceforge/pythonreports/PythonReports-0.3.0.tar.gz",
                        "http://sourceforge.net/projects/pythonreports/")
            ),
            # Test abbreviated sf.net domain
            ("http://downloads.sf.net/pythonreports/PythonReports-0.3.0.tar.gz",
                ("mirror://sourceforge/pythonreports/PythonReports-0.3.0.tar.gz",
                        "http://sourceforge.net/projects/pythonreports/")
            ),
            # Non-sourceforge URI
            ("http://yahoo.com/pythonReports-0.3.0.tar.gz",
                ('', '')
            ),
        ):
            self.assertEqual(Enamer.parse_sourceforge_uri(url), mirror)

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
             'my_pn': '',
             'my_pv': '',
             'my_p': '',
             'my_p_raw': '',
             'src_uri': 'http://www.foo.com/${P}.tbz2',
             }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

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
             'my_pn': 'PkgFoo',
             'my_pv': '',
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
             'my_pn': '',
             'my_pv': '',
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
             'my_pn': 'PKGfoo',
             'my_pv': '',
             'my_p': '${MY_PN}-${PV}',
             'my_p_raw': 'PKGfoo-1.0',
             'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
             }
        results = Enamer.get_vars(uri, up_pn, up_pv, pn)
        self.assertEqual(correct, results)

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
             'my_pn': 'pkgFOO',
             'my_pv': '',
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
        my_pn = up_pn
        my_pv = ""
        uri = "http://www.foo.com/PkgFoo-1.0.tbz2"
        correct =\
            {'pn': 'pkgfoo',
             'pv': '1.0',
             'p': 'pkgfoo-1.0',
             'my_pn': 'PkgFoo',
             'my_pv': '',
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
        my_pv = ""
        my_pn = "PkgFoo"
        uri = "http://www.foo.com/PkgFoo-1.0.tbz2"
        correct =\
            {'pn': 'pkgfoo',
             'pv': '1.0',
             'p': 'pkgfoo-1.0',
             'my_pn': 'PkgFoo',
             'my_pv': '',
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
             'my_pn': '',
             'my_pv': '${PV}dev',
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
        up_pn = "pkgfoo"
        up_pv = "1.0-r123"
        uri = "http://www.foo.com/pkgfoo-1.0-r123.tbz2"
        correct = \
            {'pn': 'pkgfoo',
             'pv': '1.0_pre123',
             'p': 'pkgfoo-1.0_pre123',
             'my_pn': '',
             'my_pv': '${PV/_pre/-r}',
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
             'pv': '1.0_pre1234',
             'p': 'pkgfoo-1.0_pre1234',
             'my_pn': '',
             'my_pv': '${PV/_pre/.dev-r}',
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
             'pv': '1.0_pre1234',
             'p': 'pkgfoo-1.0_pre1234',
             'my_pn': '',
             'my_pv': '${PV/_pre/dev-r}',
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
             'my_pn': '',
             'my_pv': '${PV/_alpha/a}',
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
             'my_pn': '',
             'my_pv': '${PV/_beta/b}',
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
             'my_pn': '',
             'my_pv': '${PV/_beta/-b}',
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
             'my_pn': '',
             'my_pv': '${PV/_alpha/-a}',
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
             'my_pn': '',
             'my_pv': '${PV/_rc/-rc}',
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
             'my_pn': '',
             'my_pv': '${PV/_rc/rc}',
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
             'my_pn': '',
             'my_pv': '${PV/_rc/.rc}',
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
             'my_pn': 'PkgFoo',
             'my_pv': '${PV/_rc/.rc}',
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
             'my_pn': 'PkgFoo',
             'my_pv': '${PV/_rc/-c}',
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
             'my_pn': 'PkgFoo',
             'my_pv': '${PV/_rc/.c}',
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
             'my_pn': 'PkgFoo',
             'my_pv': '${PV/_rc/c}',
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
             'my_pn': '${PN/./-}',
             'my_pv': '',
             'my_p': '${MY_PN}-${PV}',
             'my_p_raw': 'pkg.foo-1.0',
             'src_uri': 'http://www.foo.com/${MY_P}.tbz2',
             }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars24(self):
        up_pn = "3to2"
        up_pv = "0.1a3"
        uri = "http://pypi.python.org/packages/source/3/3to2/3to2-0.1a3.tar.gz"
        correct = \
            {'pn': '3to2',
             'pv': '0.1_alpha3',
             'p': '3to2-0.1_alpha3',
             'my_pn': '',
             'my_pv': '${PV/_alpha/a}',
             'my_p': '${PN}-${MY_PV}',
             'my_p_raw': '3to2-0.1a3',
             'src_uri': 'http://pypi.python.org/packages/source/3/3to2/${MY_P}.tar.gz',
             }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars25(self):
        up_pn = "airspeed"
        up_pv = "0.1dev-20091118"
        uri = "http://pypi.python.org/packages/any/a/airspeed/airspeed-0.1dev_20091118.tar.gz"
        correct = \
            {'pn': 'airspeed',
             'pv': '0.1_pre20091118',
             'p': 'airspeed-0.1_pre20091118',
             'my_pn': '',
             'my_pv': '${PV/_pre/dev-}',
             'my_p': '${PN}-${MY_PV}',
             'my_p_raw': 'airspeed-0.1dev_20091118',
             'src_uri': 'http://pypi.python.org/packages/any/a/airspeed/${MY_P}.tar.gz',
             }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

    def test_get_vars25(self):
        up_pn = "atreal.cmfeditions.unlocker"
        up_pv = "1.0beta1"
        uri = "http://pypi.python.org/packages/2.4/a/atreal.cmfeditions.unlocker/atreal.cmfeditions.unlocker-1.0beta1.tar.gz"
        correct = {
             'pn': 'atreal-cmfeditions-unlocker',
             'pv': '1.0_beta1',
             'p': 'atreal-cmfeditions-unlocker-1.0_beta1',
             'my_pn': '${PN/./-}',
             'my_pv': '${PV/_beta/beta}',
             'my_p': '${MY_PN}-${MY_PV}',
             'my_p_raw': 'atreal.cmfeditions.unlocker-1.0beta1',
             'src_uri': 'http://pypi.python.org/packages/2.4/a/atreal.cmfeditions.unlocker/${MY_P}.tar.gz',
             }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

#gpypi2.enamer: ERROR: {'up_pv': '1.0beta1', 'pv': '1.0bet_alpha1', 'my_pn':
#'${PN/./-}', 'my_p_raw': 'atreal.cmfeditions.unlocker-1.0beta1-py2.4.egg',
#'cls': <class 'gpypi2.enamer.Enamer'>, 'uri':
#'http://pypi.python.org/packages/2.4/a/atreal.cmfeditions.unlocker/atreal.cmfeditions.unlocker-1.0beta1-py2.4.egg',
#'sf_uri': '', 'p': 'atreal-cmfeditions-unlocker-1.0bet_alpha1', 'tail': '1',
#'my_pv': '${PV/_alpha/a}', 'src_uri':
#'http://pypi.python.org/packages/2.4/a/atreal.cmfeditions.unlocker/${MY_P}',
#'up_pn': 'atreal.cmfeditions.unlocker', 'my_p': '${MY_PN}-${PV}', 'pn':
#'atreal-cmfeditions-unlocker', '_sf_homepage': ''}

    def test_get_vars26(self):
        up_pn = "zif.sedna"
        up_pv = "0.10alpha2"
        uri = "http://pypi.python.org/packages/2.5/z/zif.sedna/zif.sedna-0.10alpha2.tar.gz"
        correct = \
            {'pn': 'zif-sedna',
             'pv': '0.10_alpha2',
             'p': 'zif-sedna-0.10_alpha2',
             'my_pn': '${PN/./-}',
             'my_pv': '${PV/_alpha/alpha}',
             'my_p': '${MY_PN}-${MY_PV}',
             'my_p_raw': 'zif.sedna-0.10alpha2',
             'src_uri': 'http://pypi.python.org/packages/2.5/z/zif.sedna/${MY_P}.tar.gz',
             }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

#gpypi2.enamer: ERROR: {'up_pv': '0.10alpha2', 'pv': '0.10alph_alpha2', 'my_pn': '${PN/./-}', 'my_p_raw': 'zif.sedna-0.10alpha2-py2.5.egg', 'cls': <class 'gpypi2.enamer.Enamer'>, 'uri': 'http://pypi.python.org/packages/2.5/z/zif.sedna/zif.sedna-0.10alpha2-py2.5.egg', 'sf_uri': '', 'p': 'zif-sedna-0.10alph_alpha2', 'tail': '0', 'my_pv': '${PV/_alpha/a}', 'src_uri': 'http://pypi.python.org/packages/2.5/z/zif.sedna/${MY_P}', 'up_pn': 'zif.sedna', 'my_p': '${MY_PN}-${PV}', 'pn': 'zif-sedna', '_sf_homepage': ''}

    def test_get_vars27(self):
        up_pn = "xapian-haystack"
        up_pv = "1.1.3beta"
        uri = "http://pypi.python.org/packages/source/x/xapian-haystack/xapian-haystack-1.1.3beta.tar.gz"
        correct = {
            'pn': 'xapian-haystack',
            'pv': '1.1.3_beta',
            'p': 'xapian-haystack-1.1.3_beta',
            'my_pn': '',
            'my_pv': '${PV/_beta/beta}',
            'my_p': '${PN}-${MY_PV}',
            'my_p_raw': 'xapian-haystack-1.1.3beta',
            'src_uri': 'http://pypi.python.org/packages/source/x/xapian-haystack/${MY_P}.tar.gz',
        }
        results = Enamer.get_vars(uri, up_pn, up_pv)
        self.assertEqual(correct, results)

# TODO: test 0.1a; 0.1beta, 0.1rc

#gpypi2.enamer: ERROR: {'up_pv': '1.1.3beta', 'pv': '1.1.3beta', 'my_pn': '', 'my_p_raw': '', 'cls': <class 'gpypi2.enamer.Enamer'>, 'uri': 'http://pypi.python.org/packages/source/x/xapian-haystack/xapian-haystack-1.1.3beta.tar.gz', 'sf_uri': '', 'p': 'xapian-haystack-1.1.3beta', 'tail': '1', 'parts': None, 'my_pv ': '', 'src_uri': 'http://pypi.python.org/packages/source/x/xapian-haystack/${MY_P}.tar.gz', 'up_pn': 'xapian-haystack', 'my_p': 'xapian-haystack-1.1.3beta', 'pn': 'xapian-haystack', '_sf_homepage': ''}

#gpypi2.enamer: ERROR: {'up_pv': '3.5.0-1', 'pv': '3.5.0-1', 'my_pn': '${PN/./-}', 'my_p_raw': 'zope.event-3.5.0-1', 'cls': <class 'gpypi2.enamer.Enamer'>, 'uri': 'http://pypi.python.org/packages/source/z/zope.event/zope.event-3.5.0-1.tar.gz', 'sf_uri': '', 'p': 'zope-event-3.5.0-1', 'tail': '1', 'parts': None, 'my_pv': '', 'src_uri': 'http://pypi.python.org/packages/source/z/zope.event/${MY_P}.tar.gz', 'up_pn': 'zope.event', 'my_p': '${MY_PN}-${PV}', 'pn': 'zope-event', '_sf_homepage': ''}
#gpypi2.enamer: ERROR: {'up_pv': '0.1-1', 'pv': '0.1-1', 'my_pn': '', 'my_p_raw': '', 'cls': <class 'gpypi2.enamer.Enamer'>, 'uri': 'http://pypi.python.org/packages/source/w/wsgixhtml2html/wsgixhtml2html-0.1-1.tar.gz', 'sf_uri': '', 'p': 'wsgixhtml2html-0.1-1', 'tail': '1', 'parts': None, 'my_pv': '', 'src_uri': ' http://pypi.python.org/packages/source/w/wsgixhtml2html/${MY_P}.tar.gz', 'up_pn': 'wsgixhtml2html', 'my_p': 'wsgixhtml2html-0.1-1', 'pn': 'wsgixhtml2html', ' _sf_homepage': ''}
#gpypi2.enamer: ERROR: {'up_pv': '0.6.2-test3', 'pv': '0.6.2-test3', 'my_pn': '', 'my_p_raw': '', 'cls': <class 'gpypi2.enamer.Enamer'>, 'uri': 'http://pypi.p ython.org/packages/source/w/wtop/wtop-0.6.2-test3.tar.gz', 'sf_uri': '', 'p': 'wtop-0.6.2-test3', 'tail': 't', 'parts': None, 'my_pv': '', 'src_uri': 'http:/ /pypi.python.org/packages/source/w/wtop/${MY_P}.tar.gz', 'up_pn': 'wtop', 'my_p': 'wtop-0.6.2-test3', 'pn': 'wtop', '_sf_homepage': ''}
# TODO: gpypi2.enamer: ERROR: {'up_pv': '0.3.0b2.1', 'pv': '0.3.0b2.1', 'my_pn': '${PN/./-}', 'my_p_raw': 'zw.schema-0.3.0b2.1', 'cls': <class 'gpypi2.enamer.Enamer'>, 'uri': 'http://pypi.python.org/packages/source/z/zw.schema/zw.schema-0.3.0b2.1.tar.gz', 'sf_uri': '', 'p': 'zw-schema-0.3.0b2.1', 'tail': '0', 'parts': None, 'my_pv': '', 'src_uri': 'http://pypi.python.org/packages/source/z/zw.schema/${MY_P}.tar.gz', 'up_pn': 'zw.schema', 'my_p': '${MY_PN}-${PV}', 'pn': 'zw-schema', '_sf_homepage': ''}
