#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility functions helping conversion of metadata from
a python package to ebuild.

* Examples of what it can detect/convert:
    (See test_enamer.py for full capabilities)

    http://www.foo.com/pkgfoo-1.0.tbz2
    PN="pkgfoo"
    PV="1.0"
    Ebuild name: pkgfoo-1.0.ebuild
    SRC_URI="http://www.foo.com/${P}.tbz2"

    http://www.foo.com/PkgFoo-1.0.tbz2
    PN="pkgfoo"
    PV="1.0"
    Ebuild name: pkgfoo-1.0.ebuild
    MY_P="PkgFoo-${PV}"
    SRC_URI="http://www.foo.com/${MY_P}.tbz2"

    http://www.foo.com/pkgfoo_1.0.tbz2
    PN="pkgfoo"
    PV="1.0"
    Ebuild name: pkgfoo-1.0.ebuild
    MY_P="${PN}_${PV}"
    SRC_URI="http://www.foo.com/${MY_P}.tbz2"

    http://www.foo.com/PKGFOO_1.0.tbz2
    PN="pkgfoo"
    PV="1.0"
    Ebuild name: pkgfoo-1.0.ebuild
    MY_P="PKGFOO_${PV}"
    SRC_URI="http://www.foo.com/${MY_P}.tbz2"

    http://www.foo.com/pkg-foo-1.0_beta1.tbz2
    PN="pkg-foo"
    PV="1.0_beta1"
    Ebuild name: pkg-foo-1.0_beta1.ebuild
    SRC_URI="http://www.foo.com/${P}.tbz2"

"""

import urlparse
import re
import os

from portage import pkgsplit

try:
    # portage >=2.2
    from portage import dep as portage_dep
    from portage import exception as portage_exception
except ImportError:
    # portage <=2.1
    from portage import portage_dep
    from portage import portage_exception


def get_filename(uri):
    """
    Return file name minus extension from src_uri
    e.g. http://somesite.com/foobar-1.0.tar.gz will yield foobar-1.0

    :param uri: URI to package with no variables substitution
    :type uri: string
    :returns: string

    """
    path = urlparse.urlparse(uri)[2]
    path = path.split('/')
    return strip_ext(path[-1])

def strip_ext(path):
    """Strip possible extensions from filename.

    Supported extensions: zip, tgz, tar.gz, tar.bz2, tbz2

    :param path: Filesystem path to a file.
    :type path: string
    :returns: string

    """
    valid_extensions = [".zip", ".tgz", ".tar.gz", ".tar.bz2", ".tbz2"]
    for ext in valid_extensions:
        if path.endswith(ext):
            return path[:-len(ext)]
    return path

def is_valid_uri(uri):
    """
    Check if URI's addressing scheme is valid

    :param uri: URI to pacakge with no variable substitution
    :type uri: string

    :returns: boolean
    """
    if uri.startswith("http:") or uri.startswith("ftp:") or \
            uri.startswith("mirror:") or uri.startswith("svn:"):
        return True
    else:
        return False

def parse_sourceforge_uri(uri):
    """
    Change URI to mirror://sourceforge format.
    Also determines a homepage string which can be used if the metadata
    doesn't have Home_page.

    :param uri: URI to pacakage with no variable substitution
    :type uri: string
    :returns: tuple: (uri string, homepage string)
    """
    uri_out = homepage = ""
    tst_uri = urlparse.urlparse(uri)

    host = tst_uri[1]
    upath = tst_uri[2]
    if upath.startswith("/sourceforge"):
        upath = upath[12:]
    if ("sourceforge" in host) or (host.endswith("sf.net")):
        uri_out = 'mirror://sourceforge%s' % upath
        homepage = "http://sourceforge.net/projects/%s/" % \
                   upath.split("/")[1]
    return uri_out, homepage

def is_good_filename(uri):
    """If filename is sane enough to deduce PN & PV, return pkgsplit results"""
    if is_valid_uri(uri):
        psplit = split_p(uri)
        if psplit and psplit[0].islower():
            return psplit

def split_p(uri):
    """Try to split a URI into PN, PV"""
    p = get_filename(uri)
    return pkgsplit(p)

def get_components(uri):
    """Split uri into pn and pv and new uri"""
    p = get_filename(uri)
    psplit = split_p(uri)
    uri_out = uri.replace(p, "${P}")
    pn = psplit[0].lower()
    pv = psplit[1]
    return uri_out, pn, pv

def get_myp(uri):
    """Return MY_P and new uri with MY_P in it"""
    my_p = get_filename(uri)
    uri_out = uri.replace(my_p, "${MY_P}")
    return uri_out, my_p

def guess_components(my_p):
    """Try to break up raw MY_P into PN and PV"""
    pn, pv = "", ""

    # Ok, we just have one automagical test here.
    # We should look at versionator.eclass for inspiration
    # and then come up with several functions.
    my_p = my_p.replace("_", "-")

    psplit = pkgsplit(my_p)
    if psplit:
        pn = psplit[0].lower()
        pv = psplit[1]
    return pn, pv


def bad_pv(up_pn, up_pv, pn="", pv="", my_pn="", my_pv=""):
    """
    Can't determine PV from upstream's version.
    Do our best with some well-known versioning schemes:

    1.0a1 (1.0_alpha1)
    1.0-a1 (1.0_alpha1)
    1.0b1 (1.0_beta1)
    1.0-b1 (1.0_beta1)
    1.0-r1234 (1.0_pre1234)
    1.0dev-r1234 (1.0_pre1234)
    1.0.dev-r1234 (1.0_pre1234)

    regex match.groups:
    pkgfoo-1.0.dev-r1234
    group 1 pv major (1.0)
    group 2 entire suffix (.dev-r1234)
    group 3 replace this with portage suffix (.dev-r)
    group 4 suffix version (1234)

    The order of the regex's is significant. For instance if you have
    .dev-r123, dev-r123 and -r123 you should order your regex's in
    that order.

    The number of regex's could have been reduced, but we use four
    number of match.groups every time to simplify the code

    The _pre suffix is most-likely incorrect. There is no 'dev'
    prefix used by portage, the 'earliest' there is is '_alpha'.
    The chronological portage release versions are:
    _alpha
    _beta
    _pre
    _rc
    release
    _p
    """
    my_p = ""
    suf_matches = {
            '_pre': ['(.*)((\.dev-r)([0-9]+))$',
                     '(.*)((dev-r)([0-9]+))$',
                     '(.*)((-r)([0-9]+))$'],
            '_alpha': ['(.*)((-a)([0-9]+))$', '(.*)((a)([0-9]+))$'],
            '_beta': ['(.*)((-b)([0-9]+))$', '(.*)((b)([0-9]+))$'],
            '_rc': ['(.*)((\.rc)([0-9]+))$', '(.*)((-rc)([0-9]+))$',
                    '(.*)((rc)([0-9]+))$', '(.*)((-c)([0-9]+))$',
                    '(.*)((\.c)([0-9]+))$', '(.*)((c)([0-9]+))$'],
            }
    sufs = suf_matches.keys()
    rs_match = None
    for this_suf in sufs:
        if rs_match:
            break
        for regex in suf_matches[this_suf]:
            rsuffix_regex = re.compile(regex)
            rs_match = rsuffix_regex.match(up_pv)
            if rs_match:
                portage_suffix = this_suf
                break
    if rs_match:
        #e.g. 1.0.dev-r1234
        major_ver = rs_match.group(1) # 1.0
        #whole_suffix = rs_match.group(2) #.dev-r1234
        replace_me = rs_match.group(3) #.dev-r
        rev = rs_match.group(4) #1234
        if not up_pn.islower():
            my_pn = up_pn
            pn = up_pn.lower()
        pv = major_ver + portage_suffix + rev
        if my_pn:
            my_p = "${MY_PN}-${MY_PV}"
        else:
            my_p = "${PN}-${MY_PV}"
        my_pv = "${PV/%s/%s}" % (portage_suffix, replace_me)

    #Single suffixes with no numeric component are simply removed.
    else:
        bad_suffixes = [".dev", "-dev", "dev", ".final", "-final", "final"]
        for suffix in bad_suffixes:
            if up_pv.endswith(suffix):
                my_pv = "${PV}%s" % suffix
                my_p = "${PN}-${MY_PV}"
                pn = up_pn
                pv = up_pv[:-(len(suffix))]
                if not pn.islower():
                    if not my_pn:
                        my_pn = pn
                    pn = pn.lower()
                break
    return pn, pv, my_p, my_pn, my_pv

def sanitize_uri(uri):
    """
    Return URI without any un-needed extension.
    e.g. http://downloads.sourceforge.net/pythonreports/PythonReports-0.3.1.tar.gz?modtime=1182702645&big_mirror=0
    would have everything after '?' stripped

    :param uri: URI to pacakge with no variable substitution
    :type uri: string
    :returns: string

    """
    # TODO: ?
    return uri

def get_vars(uri, up_pn, up_pv, pn="", pv="", my_pn="", my_pv=""):
    """
    Determine P* and MY_* variables

    Don't modify this to accept new URI schemes without writing new
    test_enamer unit tests

    This function makes me weep and gives me nightmares.

    :param uri:
    :param up_pn:
    :param up_pv:
    :param pn:
    :param pv:
    :param my_pn:
    :param my_pv:
    :param my_pv:
    :type uri: string
    :type up_pn:
    :type up_pv:
    :type pn:
    :type pv:
    :type my_pn:
    :type my_pv:
    :type my_pv:
    :returns: dict


    """
    my_p = my_p_raw = ""
    uri = sanitize_uri(uri)
    sf_uri, _sf_homepage = parse_sourceforge_uri(uri)
    if sf_uri:
        uri = sf_uri
        #XXX _sf_homepage can be used if package metadata doesn't have one


    #Make sure we have a valid PV

    #Test for PV with -r1234 suffix
    #Portage uses -r suffixes for it's own ebuild revisions so
    #we have to convert it to _pre or _alpha etc.
    try:
        tail = up_pv.split("-")[-1:][0][0]
        #we have a version with a -r[nnn] suffix
        if tail == "r":
            pn, pv, my_p, my_pn, my_pv = \
                bad_pv(up_pn, up_pv, pn, pv, my_pn, my_pv)
    except:
        pass

    if not portage_dep.isvalidatom("=dev-python/%s-%s" % (up_pn, up_pv)):
        pn, pv, my_p, my_pn, my_pv = \
            bad_pv(up_pn, up_pv, pn, pv, my_pn, my_pv)

    #No PN or PV given on command-line, try upstream's name/version
    if not pn and not pv:
        #Try to determine pn and pv from uri
        parts = split_p(uri)
        if parts:
            # pylint: disable-msg=W0612
            # unused variable 'rev'
            # The 'rev' is never used because these are
            # new ebuilds being created.
            pn, pv, rev = parts
        else:
            pn = up_pn
            pv = up_pv
    #Try upstream's version if it could't be determined from uri or cli option
    elif pn and not pv:
        pv = up_pv
    elif not pn and pv:
        pn = up_pn.lower()

    if not pn.islower():
        #up_pn is lower but uri has upper-case
        if not my_pn:
            my_pn = pn
        pn = pn.lower()

    if "." in pn:
        my_pn = '${PN/./-}'
        pn = pn.replace('.', '-')
        my_p = "${MY_PN}-${PV}"

    p = "%s-%s" % (pn, pv)

    #Check if we need to use MY_P based on src's uri
    if my_p:
        src_uri, my_p_raw = get_myp(uri)
    else:
        src_uri, my_p, my_p_raw = get_src_uri(uri)

    #Make sure we have a valid P
    if not portage_dep.isvalidatom("=dev-python/%s-%s" % (pn, pv)):
        if not portage_dep.isjustname("dev-python/%s-%s" % (pn, pv)):
            raise portage_exception.InvalidPackageName(pn)
        else:
            raise portage_exception.InvalidVersionString(pv)

    if not my_pn:
        my_pn = "-".join(my_p.split("-")[:-1])
        if (my_pn == pn) or (my_pn == "${PN}"):
            my_pn = ""

    if my_p:
        if my_p == "%s-%s" % (my_pn, "${PV}"):
            my_p = "${MY_PN}-${PV}"
        elif my_p == "%s-%s" % (my_pn, my_pv):
            my_p = "${MY_PN}-${MY_PV}"
        elif my_p == "%s-%s" % ("${PN}", my_pv):
            my_p = "${PN}-${MY_PV}"
        else:
            my_p = my_p.replace(pn, "${PN}")
            my_p = my_p.replace(pv, "${PV}")

    return {'pn': pn,
            'pv': pv,
            'p': p,
            'my_p': my_p,
            'my_pn': my_pn,
            'my_pv': my_pv,
            'my_p_raw': my_p_raw,
            'src_uri': src_uri,
            }

def get_src_uri(uri):
    """Return src_uri

    :param uri:
    :type uri:
    :returns: tuple (src_uri, my_p, my_p_raw)
    """
    my_p = my_p_raw = ''
    if is_good_filename(uri):
        src_uri, pn, pv = get_components(uri)
    else:
        src_uri, my_p = get_myp(uri)
        pn, pv = guess_components(my_p)
        if pn and pv:
            my_p_raw = my_p
            my_p = my_p.replace(pn, "${PN}")
            my_p = my_p.replace(pv, "${PV}")

    return src_uri, my_p, my_p_raw
