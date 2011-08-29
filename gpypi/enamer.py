#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Anything that needs to be converted from Python packaging
syntax to Gentoo ebuild syntax belongs to this module.

"""

import urlparse
import socket
import logging
import httplib
import re
import os

from portage import pkgsplit

from gpypi.portage_utils import PortageUtils
from gpypi.exc import *


log = logging.getLogger(__name__)


class Enamer(object):
    """Ebuild namer

       Collection of methods for metadata conversion
       from Python distribution syntax to ebuild syntax

       Most of utilities are classmethods, for purpose
       of customization support.

    """
    VALID_EXTENSIONS = [".zip", ".tgz", ".tar.gz", ".tar.bz2", ".tbz2"]

    @classmethod
    def get_filename(cls, uri):
        """
        Return file name minus extension from src_uri

        :param uri: URI to package with no variables substitution
        :type uri: string
        :returns: filename
        :rtype: string

        **Example:**

        >>> Enamer.get_filename('http://somesite.com/foobar-1.0.tar.gz')
        'foobar-1.0'

        """
        path = urlparse.urlparse(uri)[2]
        path = path.split('/')
        return cls.strip_ext(path[-1])

    @classmethod
    def strip_ext(cls, path):
        """Strip possible extensions from filename.

        Supported, valid extensions: zip, tgz, tar.gz, tar.bz2, tbz2

        :param path: Filesystem path to a file.
        :type path: string
        :returns: path minus extension
        :rtype: string

        **Example:**

        >>> Enamer.strip_ext('/home/user/filename.zip')
        '/home/user/filename'
        >>> Enamer.strip_ext('/home/user/filename.unknown')
        '/home/user/filename.unknown'

        """
        for ext in cls.VALID_EXTENSIONS:
            if path.endswith(ext):
                return path[: - len(ext)]
        return path

    @classmethod
    def is_valid_uri(cls, uri):
        """
        Check if URI's addressing scheme is valid

        :param uri: URI to package with no variable substitution
        :type uri: string
        :returns: boolean

        **Example:**

        >>> Enamer.is_valid_uri('http://...')
        True
        >>> Enamer.is_valid_uri('foobar://...')
        False

        """
        return uri.startswith("http:") or uri.startswith("ftp:") or \
                uri.startswith("mirror:") or uri.startswith("svn:")

    @classmethod
    def _is_good_filename(cls, uri):
        """If filename is sane enough to deduce PN & PV, return pkgsplit results"""
        if cls.is_valid_uri(uri):
            psplit = cls.split_uri(uri)
            if psplit and psplit[0].islower():
                return psplit

    @classmethod
    def split_uri(cls, uri):
        """Try to split a URI into PN, PV and REV

        :param uri: SRC_URI
        :type uri: string
        :returns: PN, PV, REV
        :rtype: tuple of strings

        **Example:**

        >>> Enamer.split_uri('http://www.foobar.com/foobar-1.0.tar.gz')
        ('foobar', '1.0', 'r0')
        >>> Enamer.split_uri('http://www.foobar.com/foo-2.3_beta3-r5.tar.gz')
        ('foo', '2.3_beta3', 'r5')

        """
        p = cls.get_filename(uri)
        return pkgsplit(p)

    @classmethod
    def _get_components(cls, uri):
        """Split uri into pn and pv and new uri"""
        p = cls.get_filename(uri)
        psplit = cls.split_uri(uri)
        uri_out = uri.replace(p, "${P}")
        pn = psplit[0].lower()
        pv = psplit[1]
        return uri_out, pn, pv

    @classmethod
    def _guess_components(cls, my_p):
        """Try to break up raw MY_P into PN and PV"""
        pn, pv = "", ""

        # Ok, we just have one automagical test here.
        # We should look at versionator.eclass for inspiration
        # and then come up with several functions.
        my_p = my_p.replace("_", "-")

        psplit = pkgsplit(my_p)
        if psplit:
            pn = psplit[0]
            pv = psplit[1]
        log.debug("guess_components got: pn(%s), pv(%s)", pn, pv)
        return pn, pv

    @classmethod
    def sanitize_uri(cls, uri):
        """
        Return URI without any un-needed extension.

        :param uri: URI to pacakge with no variable substitution
        :type uri: string
        :returns: URL without fragment, parameters and query
        :rtype: string

        **Example:**

        >>> Enamer.sanitize_uri('http://downloads.sourceforge.net/pythonreports/PythonReports-0.3.1.tar.gz?modtime=1182702645&big_mirror=0')
        'http://downloads.sourceforge.net/pythonreports/PythonReports-0.3.1.tar.gz'

        """
        skinned_uri = urlparse.urlparse(uri)
        return urlparse.urlunparse(skinned_uri[:3] + ('',) * 3)

    @classmethod
    def parse_setup_py(cls, distribution):
        """Parse metadata from :class:`Distribution` file.

        :param distribution:
        :type distirbution:
        :returns: Dictionary with extracted metadata

        """
        d = {}
        d['homepage'] = distribution.get_url()
        d['description'] = distribution.get_description()
        d['license'] = cls.convert_license(distribution.get_classifiers(), distribution.metadata.get_license())

        for key in dict(d).keys():
            if d[key] == 'UNKNOWN':
                del d[key]
        return d

    @classmethod
    def parse_pv(cls, up_pv, pv="", my_pv=None):
        """Convert PV to MY_PV if needed

        :param up_pv: Upstream package version
        :param pv: Converted Gentoo package version
        :param my_pv: Bash substitutions for original package version
        :type up_pv: string
        :type pv: string
        :type my_pv: list
        :returns: (:term:`PN`, :term:`PV`, :term:`MY_PN`, :term:`MY_PV`)
        :rtype: tuple of (string, string, list, list)

        Can't determine PV from upstream's version.
        Do our best with some well-known versioning schemes:

        * 1.0a1 (1.0_alpha1)
        * 1.0-a1 (1.0_alpha1)
        * 1.0b1 (1.0_beta1)
        * 1.0-b1 (1.0_beta1)
        * 1.0-r1234 (1.0_pre1234)
        * 1.0dev-r1234 (1.0_pre1234)
        * 1.0.dev-r1234 (1.0_pre1234)
        * 1.0dev-20091118 (1.0_pre20091118)
        * (for more examples look at test_enamer.py)

        Regex match.groups():
            * pkgfoo-1.0.dev-r1234
            * group 1 pv major (1.0)
            * group 2 replace this with portage suffix (.dev-r)
            * group 3 suffix version (1234)

        The order of the regexes is significant. For instance if you have
        .dev-r123, dev-r123 and -r123 you should order your regex's in
        that order.

        The chronological portage release versions are:

        * _alpha
        * _beta
        * _pre
        * _rc
        * release
        * _p

        **Example:**

        >>> Enamer.parse_pv('1.0b2')
        ('1.0_beta2', ['${PV/_beta/b}'])

        .. note::
            The number of regex's could have been reduced, but we use four
            number of match.groups every time to simplify the code

        """
        bad_suffixes = re.compile(
            r'((?:[._-]*)(?:dev|devel|final|stable|snapshot)$)', re.I)
        revision_suffixes = re.compile(
            r'(.*?)([\._-]*(?:r|patch|p)[\._-]*)([0-9]*)$', re.I)
        suf_matches = {
                '_pre': [
                    r'(.*?)([\._-]*dev[\._-]*r?)([0-9]+)$',
                    r'(.*?)([\._-]*(?:pre|preview)[\._-]*)([0-9]*)$',
                ],
                '_alpha': [
                    r'(.*?)([\._-]*(?:alpha|test)[\._-]*)([0-9]*)$',
                    r'(.*?)([\._-]*a[\._-]*)([0-9]*)$',
                    r'(.*[^a-z])(a)([0-9]*)$',
                ],
                '_beta': [
                    r'(.*?)([\._-]*beta[\._-]*)([0-9]*)$',
                    r'(.*?)([\._-]*b)([0-9]*)$',
                    r'(.*[^a-z])(b)([0-9]*)$',
                ],
                '_rc': [
                    r'(.*?)([\._-]*rc[\._-]*)([0-9]*)$',
                    r'(.*?)([\._-]*c[\._-]*)([0-9]*)$',
                    r'(.*[^a-z])(c[\._-]*)([0-9]+)$',
                ],
        }
        rs_match = None
        my_pv = my_pv or []
        additional_version = ""
        log.debug("parse_pv: up_pv(%s)", up_pv)

        rev_match = revision_suffixes.search(up_pv)
        if rev_match:
            pv = up_pv = rev_match.group(1)
            replace_me = rev_match.group(2)
            rev = rev_match.group(3)
            additional_version = '.' + rev
            my_pv.append("${PV: -%d}%s" % (len(additional_version), replace_me + rev))
            log.debug("parse_pv: new up_pv(%s), additional_version(%s), my_pv(%s)",
                up_pv, additional_version, my_pv)
            # TODO: if ALSO suf_matches succeeds, it's not implemented

        for this_suf in suf_matches.keys():
            if rs_match:
                break
            for regex in suf_matches[this_suf]:
                rsuffix_regex = re.compile(regex, re.I)
                rs_match = rsuffix_regex.match(up_pv)
                if rs_match:
                    log.debug("parse_pv: chosen regex: %s", regex)
                    portage_suffix = this_suf
                    break

        if rs_match:
            # e.g. 1.0.dev-r1234
            major_ver = rs_match.group(1)  # 1.0
            replace_me = rs_match.group(2)  # .dev-r
            rev = rs_match.group(3)  # 1234
            pv = major_ver + portage_suffix + rev
            my_pv.append("${PV/%s/%s}" % (portage_suffix, replace_me))
            log.debug("parse_pv: major_ver(%s) replace_me(%s), rev(%s)", major_ver, replace_me, rev)
        else:
            # Single suffixes with no numeric component are simply removed.
            match = bad_suffixes.search(up_pv)
            if match:
                suffix = match.groups()[0]
                my_pv.append("${PV}%s" % suffix)
                pv = up_pv[: - (len(suffix))]

        pv = pv + additional_version
        log.debug("parse_pv: pv(%s), my_pv(%s)", pv, my_pv)

        return pv, my_pv

    @classmethod
    def parse_pn(cls, up_pn, pn="", my_pn=None):
        """Convert PN to MY_PN if needed

        :params up_pn: Upstream package name
        :params pn: Gentoo package name
        :params my_pn: Bash substitutions to get original name
        :type up_pn: string
        :type pn: string
        :type my_pn: list
        :returns: (:term:`PN`, :term:`MY_PN`)
        :rtype: tuple of (string, list)

        **Example:**

        >>> Enamer.parse_pn('Test-Me')
        ('test-me', ['Test-Me'])
        >>> Enamer.parse_pn('test.me')
        ('test-me', ['${PN/-/.}'])

        """
        my_pn = my_pn or []
        if not up_pn.islower():
            # up_pn is lower but uri has upper-case
            log.debug('parse_pn: pn is not lowercase, converting to my_pn')
            if not my_pn:
                my_pn.append(up_pn)
            pn = up_pn.lower()

        if "." in up_pn:
            log.debug("parse_pn: dot found in pn")
            my_pn.append('${PN/-/.}')
            pn = up_pn.replace('.', '-')

        if " " in up_pn:
            log.debug("parse_pn: space found in pn")
            my_pn.append('${PN/-/ }')
            pn = up_pn.replace(' ', '-')

        #if not my_pn:
            #my_pn = "-".join(p.split("-")[:-1])
            #if (my_pn == pn) or (my_pn == "${PN}"):
                #my_pn = ""
            #log.debug("set my_on to %s", my_pn)

        log.debug("parse_pn: my_pn(%s) pn(%s)", my_pn, pn)
        return pn, my_pn

    @classmethod
    def get_vars(cls, uri, up_pn, up_pv, pn="", pv="", my_pn=None, my_pv=None):
        """
        Determine P* and MY_* ebuild variables

        :param uri: HTTP URL to download link for a package
        :param up_pn: Upstream package name
        :param up_pv: Upstream package version
        :param pn: Converted package name
        :param pv: Converted package version
        :param my_pn: Bash substitution for upstream package name
        :param my_pv: Bash substitution for upstream package version
        :type uri: string
        :type up_pn: string
        :type up_pv: string
        :type pn: string
        :type pv: string
        :type my_pn: list
        :type my_pv: list
        :raises: :exc:`GPyPiInvalidAtom` if version/name could not be parsed correctly
        :returns:
            * pn -- Ebuild Gentoo package name
            * pv -- Ebuild Gentoo package version
            * p -- Ebuild Gentoo package name + version
            * my_p -- Upstream whole package name (name + version)
            * my_pn -- Bash substitution for upstream package name
            * my_pv -- Bash substitution for upstream package version
            * my_p_raw -- my_p extracted from SRC_URI
            * src_uri -- Ebuild SRC_URI with MY_P variable
        :rtype: dict

        **Examples of what it can detect/convert** (see test_enamer.py for full capabilities)

        http://www.foo.com/pkgfoo-1.0.tbz2

        * PN="pkgfoo"
        * PV="1.0"
        * Ebuild name: pkgfoo-1.0.ebuild
        * SRC_URI="http://www.foo.com/${P}.tbz2"

        http://www.foo.com/PkgFoo-1.0.tbz2

        * PN="pkgfoo"
        * PV="1.0"
        * Ebuild name: pkgfoo-1.0.ebuild
        * MY_P="PkgFoo-${PV}"
        * SRC_URI="http://www.foo.com/${MY_P}.tbz2"

        http://www.foo.com/pkgfoo_1.0.tbz2

        * PN="pkgfoo"
        * PV="1.0"
        * Ebuild name: pkgfoo-1.0.ebuild
        * MY_P="${PN}_${PV}"
        * SRC_URI="http://www.foo.com/${MY_P}.tbz2"

        http://www.foo.com/PKGFOO_1.0.tbz2

        * PN="pkgfoo"
        * PV="1.0"
        * Ebuild name: pkgfoo-1.0.ebuild
        * MY_P="PKGFOO_${PV}"
        * SRC_URI="http://www.foo.com/${MY_P}.tbz2"

        http://www.foo.com/pkg-foo-1.0_beta1.tbz2

        * PN="pkg-foo"
        * PV="1.0_beta1"
        * Ebuild name: pkg-foo-1.0_beta1.ebuild
        * SRC_URI="http://www.foo.com/${P}.tbz2"

        **Example:**

        >>> d = Enamer.get_vars('http://www.foo.com/pkg.foo-1.0b1.tbz2', 'pkg.foo', '1.0b1')
        >>> assert d['pn'] == 'pkg-foo'
        >>> assert d['pv'] == '1.0_beta1'
        >>> assert d['p'] == 'pkg-foo-1.0_beta1'
        >>> assert d['my_pv'] == ['${PV/_beta/b}']
        >>> assert d['my_pn'] == ['${PN/-/.}']
        >>> assert d['my_p'] == '${MY_PN}-${MY_PV}'
        >>> assert d['my_p_raw'] == 'pkg.foo-1.0b1'
        >>> assert d['src_uri'] == 'http://www.foo.com/${MY_P}.tbz2'
        >>> assert len(d) == 8

        """
        log.debug("get_vars: %r" % locals())
        my_pn = my_pn or []
        my_pv = my_pv or []
        my_p = ""
        INVALID_VERSION = False
        uri = cls.sanitize_uri(uri)

        # Test for PV with -r1234 suffix
        # Portage uses -r suffixes for it's own ebuild revisions so
        # We have to convert it to _pre or _alpha etc.
        tail = up_pv.split("-")[-1][0]
        if tail == "r":
            INVALID_VERSION = True
            log.debug("We have a version with a -r### suffix")

        portage_atom = "=dev-python/%s-%s" % (up_pn, up_pv)
        if not PortageUtils.is_valid_atom(portage_atom):
            INVALID_VERSION = True
            log.debug("%s is not valid portage atom", portage_atom)

        if INVALID_VERSION:
            pv, my_pv = cls.parse_pv(up_pv, pv, my_pv)
        pn, my_pn = cls.parse_pn(up_pn, pn, my_pn)

        # No PN or PV given on command-line, try upstream's name/version
        if not pn and not pv:
            log.debug("pn and pv not given, trying upstream")
            # Try to determine pn and pv from uri
            parts = cls.split_uri(uri)
            if parts:
                # pylint: disable-msg=W0612
                # unused variable 'rev'
                # The 'rev' is never used because these are
                # new ebuilds being created.
                pn, pv, rev = parts
            else:
                pn = up_pn
                pv = up_pv
        # Try upstream's version if it could't be determined from uri or cli option
        elif pn and not pv:
            pv = up_pv
        elif not pn and pv:
            pn = up_pn

        p = "%s-%s" % (pn, pv)
        log.debug("get_vars: p(%s)", p)

        # Make sure we have a valid P
        atom = "=dev-python/%s-%s" % (pn, pv)
        if not PortageUtils.is_valid_atom(atom):
            log.debug(locals())
            raise GPyPiInvalidAtom("%s is not a valid portage atom. "
                "We could not determine it from upstream pn(%s) and pv(%s)." %
                (atom, up_pn, up_pv))

        # Check if we need to use MY_P based on src's uri
        src_uri, my_p_raw = cls.get_my_p(uri)
        log.debug("getting SRC_URI with ${MY_P}: %s %s %s", src_uri, my_p, my_p_raw)
        if my_p_raw == p:
            my_pn = []
            my_p_raw = ''
            src_uri = src_uri.replace("${MY_P}", "${P}")
        elif not (my_pn or my_pv):
            src_uri, my_p, my_pn, my_p_raw = cls._get_src_uri(uri, my_pn)
            log.debug("getting SRC_URI: %s %s %s", src_uri, my_p, my_p_raw)

        log.debug("before MY_P guessing: %r", locals())
        if my_pn or my_pv:
            my_p = "%s-%s" % ("${MY_PN}" if my_pn else "${PN}",
                "${MY_PV}" if my_pv else "${PV}")

        return {
            'pn': pn,
            'pv': pv,
            'p': p,
            'my_p': my_p,
            'my_pn': my_pn,
            'my_pv': my_pv,
            'my_p_raw': my_p_raw,
            'src_uri': src_uri,
        }

    @classmethod
    def _get_src_uri(cls, uri, my_pn):
        """
        """
        my_p = my_p_raw = ''
        if cls._is_good_filename(uri):
            src_uri, pn, pv = cls._get_components(uri)
        else:
            src_uri, my_p = cls.get_my_p(uri)
            pn, pv = cls._guess_components(my_p)
            if pn and pv:
                my_p_raw = my_p
                pn, my_pn = cls.parse_pn(pn)
                if my_pn and my_pn != pn:
                    for one_my_pn in my_pn:
                        my_p = my_p.replace(one_my_pn, "${MY_PN}")
                else:
                    my_p = my_p.replace(pn, "${PN}")
                my_p = my_p.replace(pv, "${PV}")

        log.debug("get_src_uri: src_uri(%s), my_p(%s), my_pn(%s), my_p_raw(%s)",
            src_uri, my_p, my_pn, my_p_raw)
        return src_uri, my_p, my_pn, my_p_raw

    @classmethod
    def get_my_p(cls, uri):
        """Return :term:`MY_P` and new :term:`SRC_URI` with :term:`MY_P` in it.

        :param uri: HTTP URL to a package
        :returns: (uri with ${MY_P}, ${MY_P_RAW})
        :rtype: tuple of strings

        **Example:**

        >>> Enamer.get_my_p('http://www.foobar.com/foobar-1.0.tar.gz')
        ('http://www.foobar.com/${MY_P}.tar.gz', 'foobar-1.0')

        """
        my_p_raw = cls.get_filename(uri)
        log.debug('get_my_p out of uri: %s', my_p_raw)
        return uri.replace(my_p_raw, "${MY_P}"), my_p_raw

    @classmethod
    def convert_license(cls, classifiers, setup_license=""):
        """
        Map defined classifier license to Portage license

        PyPi list of licences:
        http://pypi.python.org/pypi?:action=list_classifiers

        :param classifiers: PyPi (license) classifiers
        :type classifiers: list of string
        :param setup_license: license extracted from setup_py
        :type setup_license: string
        :returns: Portage license or ""
        :rtype: string

        **Example:**

        >>> Enamer.convert_license(["License :: OSI Approved :: BSD License"])
        'BSD-2'
        >>> Enamer.convert_license(["License :: OSI Approved :: foobar"])
        ''
        """

        if not isinstance(classifiers, list):
            raise ValueError("classifiers should be a list, not %s" % type(classifiers))
        if not isinstance(setup_license, basestring):
            raise ValueError("setup_license should be a string, not %s" % type(setup_license))

        my_license = ""
        for line in classifiers:
            if line.startswith("License :: "):
                my_license = line

        my_license = my_license.split(":: ")[-1]
        known_licenses = {
            "Academic Free License (AFL)": "AFL-3.0",
            "Aladdin Free Public License (AFPL)": "Aladdin",
            "Aladdin Free Public License (AFPL)": "Aladdin",
            "Apache Software License": "Apache-2.0",
            "Apple Public Source License": "Apple",
            "Artistic License": "Artistic-2",
            "BSD License": "BSD-2",
            "Common Public License": "CPL-1.0",
            "GNU Affero General Public License v3": "AGPL-3",
            "GNU Free Documentation License (FDL)": "FDL-3",
            "GNU General Public License (GPL)": "GPL-2",
            "GNU Library or Lesser General Public License (LGPL)": "LGPL-2.1",
            "IBM Public License": "IBM",
            "Intel Open Source License": "Intel",
            "ISC License (ISCL)": "ISC",
            "MIT License": "MIT",
            "Mozilla Public License 1.0 (MPL)": "MPL",
            "Mozilla Public License 1.1 (MPL 1.1)": "MPL-1.1",
            "Nethack General Public License": "nethack",
            "Netscape Public License (NPL)": "NPL-1.1",
            "Open Group Test Suite License": "OGTSL",
            "Public Domain": "public-domain",
            "Python License (CNRI Python License)": "CNRI",
            "Python Software Foundation License": "PSF-2.4",
            "Qt Public License (QPL)": "QPL",
            "Repoze Public License": "repoze",
            "Sleepycat License": "DB",
            "Sun Public License": "SPL",
            "University of Illinois/NCSA Open Source License": "ncsa-1.3",
            "W3C License": "WC3",
            "zlib/libpng License": "ZLIB",
            "Zope Public License": "ZPL",
        }
        guess_license = {
            'LGPL': 'LGPL-2.1',
            'GPL': 'GPL-2',
        }
        license = known_licenses.get(my_license, "")
        if license:
            return license
        else:
            if isinstance(setup_license, str) and not Enamer.is_valid_portage_license(setup_license):
                for guess, value in guess_license.iteritems():
                    if guess in setup_license:
                        return value
                return ""
            else:
                return setup_license

    @classmethod
    def is_valid_portage_license(cls, license):
        """
        Check if license string matches a valid one in ${PORTDIR}/licenses

        :param license: Portage license name
        :type license: string
        :returns: True if license is valid/exists
        :rtype: bool

        **Example:**

        >>> Enamer.is_valid_portage_license("KQEMU")
        True
        >>> Enamer.is_valid_portage_license("foobar")
        False

        """
        return os.path.exists(os.path.join(PortageUtils.get_portdir(), "licenses", license))

    @classmethod
    def construct_atom(cls, pn, category, pv=None, operator="", uses=None, if_use=None):
        """
        Construct atom from given parts.

        :param pn:
        :param category:
        :param pv:
        :param operator:
        :type pn: string
        :type category: string
        :type pv: string
        :type operator: string
        :returns: Portage Atom

        """
        atom = "%(operator)s%(category)s/%(pn)s" % locals()
        if pv:
            atom += '-%(pv)s' % locals()

        if uses:
            atom += '[%s]' % ",".join(uses)

        if if_use:
            atom = '%s? ( %s )' % (if_use, atom)

        return atom

    @classmethod
    def convert_category(cls, pn, metadata):
        """Determine Portage category for package

        :param pn:
        :param metadata:
        :type pn: string
        :type metadata: dict

        """
        return 'dev-python'


class SrcUriMetaclass(type):
    """Metaclass for SrcUriNamer.

    :attr:`providers` - list of plugins that subclass SrcUriNamer

    """
    providers = []

    def __new__(mcls, name, bases, dict):
        cls = type.__new__(mcls, name, bases, dict)
        if name != 'SrcUriNamer':
            mcls.providers.append(cls)
        return cls


class SrcUriNamer(object):
    """Base class for :term:`SRC_URI` providers.

    Main purpose of this class is to provide unique interface for
    determining :term:`SRC_URI` variable.

    Plugins should subclass this class and provide methods
    for conversion.

    :param uri: HTTP URI
    :type uri: string
    """
    __metaclass__ = SrcUriMetaclass
    BASE_HOMEPAGE = None
    BASE_URI = None

    def __init__(self, uri, enamer, up_pn, my_pn, up_pv, my_pv, my_p, p):
        self.uris = []
        self.homepages = []
        self.uri = uri
        self.up = urlparse.urlparse(uri)
        self.enamer = enamer
        self.up_pn = up_pn
        self.up_pv = up_pv
        self.my_pn = my_pn
        self.my_pv = my_pv
        self.my_p = my_p

        # bash substitution variables
        if my_pv:
            self.pv = "${MY_PV}"
        else:
            self.pv = "${PV}"
        if my_pn:
            self.pn = "${MY_PN}"
            self.pn0 = "${MY_PN:0:1}"
        else:
            self.pn = "${PN}"
            self.pn0 = "${PN:0:1}"
        self.p = my_p or "${P}"

    def __call__(self):
        """"""
        for provider in self.providers:
            p = provider(self.uri)
            self.uris.extend(p.convert_src_uri())
            if self.uris:
                self.homepages.extend(p.convert_homepage())
        return self.uris, self.homepages

    def is_uri_online(self, uri):
        """Issue HTTP HEAD request to confirm location of URI"""
        log.debug('is_uri_online: %s', uri)
        up = urlparse.urlparse(uri)
        conn = httplib.HTTPConnection(up.netloc, timeout=3)
        try:
            conn.request('HEAD', up.path)
            resp = conn.getresponse()
        except (httplib.HTTPException, socket.error):
            log.error('is_uri_online: timeout')
            return False
        log.error('is_uri_online: status(%r)' % resp.status)
        return resp.status in (302, 200)  # HEAD requests returns 302 FOUND when valid

    def convert_src_uri(self):
        """"""
        uris = []
        for ext in self.enamer.VALID_EXTENSIONS:
            if self.is_valid_for_uri():
                uri = self.BASE_URI % self.__dict__
                uris.append(uri)
        return uris

    def is_valid_for_uri(self):
        """
        Is plugin the right one for uri mirror?

        :rtype: bool
        """
        uri = self.BASE_URI % __dict__
        return self.is_uri_online(uri)

    def convert_homepage(self):
        """"""
        return [self.BASE_HOMEPAGE % self.__dict__]


class SourceForgeSrcUri(SrcUriNamer):
    """"""
    BASE_URI = 'mirror://sourceforge/%(pn)s/files/%(pn)s/%(pv)s/%(p)s.%(ext)s/download'
    BASE_HOMEPAGE = 'http://sourceforge.net/projects/%(up_pn)s/'


class PyPiSrcUri(SrcUriNamer):
    """"""
    BASE_URI = 'mirror://pypi/%(pn0)s/%(pn)s/%(p)s.%(ext)s'
    BASE_HOMEPAGE = 'http://pypi.python.org/pypi/%(up_pn)s/'
