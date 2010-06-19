#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Command-line code for :mod:`gpypi2`

"""

import os
import sys
import inspect
import logging

import argparse
from pkg_resources import Requirement

from yolk.pypi import CheeseShop
from yolk.yolklib import get_highest_version
from yolk.setuptools_support import get_download_uri

from gpypi2.ebuild import Ebuild
from gpypi2.portage_utils import PortageUtils
from gpypi2 import __version__
from gpypi2.exc import *


log = logging.getLogger(__name__)

class GPyPI(object):
    """
    Main class for command-line interface

    :param package_name: case-insensitive package name
    :type package_name: string

    :param version: package version
    :type version: string

    :param options: command-line options
    :type options: OptParser config object

    """

    def __init__(self, package_name, version, options):

        self.package_name = package_name
        self.version = version
        self.options = options
        self.tree = [(package_name, version)]
        self.pypi = CheeseShop()
        self.create_ebuilds()

    def create_ebuilds(self):
        """
        Create ebuild for given package_name and any ebuilds for dependencies
        if needed. If no version is given we use the highest available.

        """
        #Create first ebuild then turn off overwrite in case a dependency
        #ebuild already exists
        #self.logger.debug("Creating dep tree...")
        while len(self.tree):
            (project_name, version) = self.tree.pop(0)
            #self.logger.debug(self.tree)
            #self.logger.debug("%s %s" % (project_name, version))
            self.package_name = project_name
            self.version = version
            requires = self.do_ebuild()
            if requires:
                for req in requires:
                    # TODO: category
                    if self.options.no_deps or ebuild_exists("dev-python/%s" % req.project_name.lower()):
                        if not self.options.no_deps:
                            log.info("Skipping dependency (exists): %s" % req.project_name)
                    else:
                        self.add_dep(req.project_name)
            #Only force overwriting and category on first ebuild created, not dependencies
            self.options.overwrite = False
            self.options.category = None

    def add_dep(self, project_name):
        """Add dependency"""
        pkgs = []
        if len(self.tree):
            for deps in self.tree:
                pkgs.append(deps[0])

        if project_name not in pkgs:
            self.tree.append((project_name, None))
            log.info("Dependency needed: %s" % project_name)

    def url_from_pypi(self):
        """
        Query PyPI for package's download URL

        :returns: source URL string

        """

        try:
            return self.pypi.get_download_urls(self.package_name, self.version, pkg_type="source")[0]
        except IndexError:
            return None

    def find_uri(self, method="setuptools"):
        """
        Returns download URI for package
        If no package version was given it returns highest available
        Setuptools should find anything xml-rpc can and more.

        :param method: download method can be 'xml-rpc', 'setuptools', or 'all'
        :type method: string

        :returns download_url string

        """
        download_url = None

        if method == "all" or method == "xml-rpc":
            download_url = self.url_from_pypi()

        if (method == "all" or method == "setuptools") and not download_url:
            #Sometimes setuptools can find a package URI if PyPI doesn't have it
            download_url = self.uri_from_setuptools()
        return download_url

    def get_uri(self, svn=False):
        """
        Attempt to find a package's download URI

        :returns: download_url string

        """
        download_url = self.find_uri()

        if not download_url:
            self.raise_error("Can't find SRC_URI for '%s'." %  self.package_name)

        log.debug("Package URI: %s " % download_url)
        return download_url

    def uri_from_setuptools(self):
        """
        Use setuptools to find a package's URI

        """
        try:
            req = Requirement.parse(self.package_name)
        except ValueError:
            self.raise_error("The package seems to have a ridiculous name or version, can't proceed.")

        #if self.options.subversion:
        #    src_uri = get_download_uri(self.package_name, "dev", "source")
        #else:
        src_uri = get_download_uri(self.package_name, self.version, "source")
        if not src_uri:
            self.raise_error("The package has no source URI available.")
        return src_uri

    def verify_pkgver(self):
        """
        Query PyPI to make sure we have correct case for package name
        """
        pass

    def do_ebuild(self):
        """
        Get SRC_URI using PyPI and attempt to create ebuild

        :returns: tuple with exit code and pkg_resources requirement

        """
        #Get proper case for project name:
        (self.package_name, versions) = self.pypi.query_versions_pypi(self.package_name)

        if self.version and (self.version not in versions):
            log.error("Can't find package for version:'%s'." %  self.version)
            return
        else:
            self.version = get_highest_version(versions)

        if self.options.uri:
            download_url = self.options.uri
        else:
            download_url = self.get_uri()
        #try:
        ebuild = Ebuild(self.package_name, self.version, download_url, self.options)
        # TODO: convert exceptions to ours
        #except portage_exception.InvalidVersionString:
            #log.error("Can't determine PV, use -v to set it: %s-%s" % \
                    #(self.package_name, self.version))
            #return
        #except portage_exception.InvalidPackageName:
            #log.error("Can't determine PN, use -n to set it: %s-%s" % \
                    #(self.package_name, self.version))
            #return

        ebuild.set_metadata(self.query_metadata())

        if self.options.pretend:
            ebuild.print_formatted()
        else:
            ebuild.create()

    def query_metadata(self):
        """
        Get package metadata from PyPI

        :returns: metadata text

        """

        if self.version:
            return self.pypi.release_data(self.package_name, self.version)
        else:
            (pn, vers) = self.pypi.query_versions_pypi(self.package_name)
            return self.pypi.release_data(self.package_name, get_highest_version(vers))


def main():
    """Parse command-line options and do it.
    Core function for gpypi2 command.
    """
    main_parser = argparse.ArgumentParser(prog='gpypi2')

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-P", "--PN", action='store', dest="pn",
        default=False, help="Specify PN to use when naming ebuild.")
    parser.add_argument("-V", "--PV", action='store', dest="pv",
        default=False, help="Specify PV to use when naming ebuild.")
    parser.add_argument("--MY_PV", action='store', dest="my_pv",
        default=False, help="Specify MY_PV")
    parser.add_argument("--MY_PN", action='store', dest="my_pn",
        default=False, help="Specify MY_PN")
    parser.add_argument("--MY_P", action='store', dest="my_p",
        default=False, help="Specify MY_P")
    parser.add_argument("-u", "--uri", action='store', dest="uri",
        default=False, help="Specify URI of package if PyPI doesn't have it.")
    parser.add_argument("-q", "--quiet", action='store_true',
        dest="quiet", default=False, help="Show less output.")
    parser.add_argument("-d", "--debug", action='store_true',
        dest="debug", default=False, help="Show debug information.")
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)

    # subcommands
    subparsers = main_parser.add_subparsers(title="commands", dest="command")

    parser_create = subparsers.add_parser('create', help="Write  to an overlay.", parents=[parser])
    parser_create.add_argument('package', action='store')
    parser_create.add_argument('version', nargs='?', default=None)
    parser_create.add_argument("-l", "--overlay", action='store', dest='overlay',
        metavar='OVERLAY_NAME', default=None,
        help='Specify overy to use by name ($OVERLAY/profiles/repo_name)')
    parser_create.add_argument("-o", "--overwrite", action='store_true',
        dest="overwrite", default=False, help= "Overwrite existing ebuild.")
    parser_create.add_argument("--no-deps", action='store_true', dest="no_deps",
        default=False, help="Don't create ebuilds for any needed dependencies.")
    parser_create.add_argument("-c", "--portage-category", action='store',
        dest="category", default="dev-python",
        help="Specify category to use when creating ebuild. Default is dev-python")
    parser_create.add_argument("-p", "--pretend", action='store_true',
        dest="pretend", default=False, help="Print ebuild to stdout, "
        "don't write ebuild file, don't download SRC_URI.")

    parser_echo = subparsers.add_parser('echo', help="Echo ebuild to stdout.", parents=[parser])
    parser_echo.add_argument('package', action='store')
    parser_echo.add_argument('version', nargs='?', default=None)
    parser_echo.add_argument("--format", action='store', dest="format",
        default=None, help="Format when printing to stdout: console, "
        "html, bbcode, or none")

    args = main_parser.parse_args()

    if args.debug and args.quiet:
        main_parser.error('Can\'t use --debug and --quiet altogether.')

    # TODO: config
    logger = logging.getLogger()
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(ch)

    if args.debug:
        logger.setLevel(logging.DEBUG)
    elif args.quiet:
        logger.setLevel(logging.WARN)
    else:
        logger.setLevel(logging.INFO)

    if os.geteuid() != 0:
        main_parser.error('Must be run as root.')

    gpypi = GPyPI(args.package, args.version, args)

if __name__ == "__main__":
    main()
