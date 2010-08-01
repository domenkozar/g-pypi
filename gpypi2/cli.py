#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Command-line code for :mod:`gpypi2`

"""

import os
import sys
import pdb
import inspect
import logging

import argparse

from yolk.pypi import CheeseShop
from yolk.yolklib import get_highest_version
from yolk.setuptools_support import get_download_uri

from gpypi2 import __version__
from gpypi2.exc import *
from gpypi2.enamer import Enamer
from gpypi2.sdist_ebuild import sdist_ebuild
from gpypi2.config import Config, ConfigManager
from gpypi2.ebuild import Ebuild
from gpypi2.portage_utils import PortageUtils
from gpypi2.utils import PortageFormatter, PortageStreamHandler


log = logging.getLogger(__name__)

class GPyPI(object):
    """
    Main class for GPyPi interface

    :param package_name: case-insensitive package name
    :type package_name: string

    :param version: package version
    :type version: string

    :param options: command-line options
    :type options: ArgParse options

    """

    def __init__(self, package_name, version, options):
        self.package_name = package_name
        self.version = version
        self.options = options
        self.tree = [(package_name, version)]
        self.pypi = CheeseShop()

    def create_ebuilds(self):
        """
        Create ebuild for given package_name and any ebuilds for dependencies
        if needed. If no version is given we use the highest available.

        """
        while len(self.tree):
            (project_name, version) = self.tree.pop(0)
            self.package_name = project_name
            self.version = version
            requires = self.do_ebuild()
            if requires:
                for req in requires:
                    if self.options.no_deps:
                        pass
                    else:
                        self.handle_dependencies(req.project_name)
            # TODO: disable some options after first ebuild is created
            #self.options.overwrite = False
            #self.options.category = None

    def handle_dependencies(self, project_name):
        """Add dependency if not already in self.tree"""
        pkgs = []
        if len(self.tree):
            for deps in self.tree:
                pkgs.append(deps[0])

        if project_name not in pkgs:
            # TODO: document that we can not query pypi with version spec or use distutils2
            # for dependencies
            self.tree.append((project_name, None))
            log.info("Dependency needed: %s" % project_name)

    def url_from_pypi(self):
        """
        Query PyPI to find a package's URI

        :returns: source URL string

        """
        try:
            return self.pypi.get_download_urls(self.package_name, self.version, pkg_type="source")[0]
        except IndexError:
            return None

    def url_from_setuptools(self):
        """
        Use setuptools to find a package's URI

        :returns: source URL string or None

        """
        #if self.options.subversion:
        #    src_uri = get_download_uri(self.package_name, "dev", "source")
        #else:
        return get_download_uri(self.package_name, self.version, "source", self.options.index_url)

    def find_uri(self, method="all"):
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
            download_url = self.url_from_setuptools()

        if not download_url:
            log.error("Can't find SRC_URI for '%s'." %  self.package_name)

        # TODO: configuratior
        log.debug("Package URI: %s " % download_url)

        return download_url

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

        # TODO: self.options.uri only for first ebuild
        # TODO: make find_uri method configurable
        download_url = self.find_uri()

        log.info('Generating ebuild: %s %s', self.package_name, self.version)
        log.debug('URI from PyPi: %s', download_url)

        #try:
        self.options.configs['argparse']['uri'] = download_url
        self.options.configs['argparse']['up_pn'] = self.package_name
        self.options.configs['argparse']['up_pv'] = self.version
        ebuild = Ebuild(self.options)
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

        if self.options.command == 'echo' or self.options.pretend:
            ebuild.print_formatted()
        else:
            ebuild.create()
        return ebuild.requires

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


class CLI(object):
    """
    Dispatcher based on parsed arguments. Holds
    all commands methods.

    :param config: Options to be used when making ebuilds
    :type config: :class:`gpypi2.config.ConfigManager`
    :param command: Command name to execute
    :type command: string

    """

    def __init__(self, config):
        self.config = config
        getattr(self, config.command)()

    def create(self):
        """"""
        gpypi = GPyPI(self.config.up_pn, self.config.up_pv, self.config)
        gpypi.create_ebuilds()
        # TODO: atomic cleanup

    def install(self):
        """"""
        self.create()
        package = Enamer.parse_pn(self.config.up_pn)[0]
        os.execvp('emerge', ['emerge', '-av', package or self.config.up_pn])
        # TODO: support for emerge arguments
        # TODO: install exact version

    def echo(self):
        """"""
        gpypi = GPyPI(self.config.up_pn, self.config.up_pv, self.config)
        gpypi.do_ebuild()
        # TODO: cleanup

    def sync(self):
        """"""
        pypi = CheeseShop()
        all_packages = []
        for package in pypi.list_packages():
            (pn, vers) = pypi.query_versions_pypi(package)
            for version in vers:
                # TODO: parse_* will not return anything for correct atoms
                atom = Enamer.construct_atom(Enamer.parse_pn(pn)[0], self.config.category, Enamer.parse_pv(version[0]))

                # we skip existing ebuilds
                if PortageUtils.ebuild_exists(atom):
                    continue
                try:
                    url = pypi.get_download_urls(pn, version)[0]
                    # TODO: use setuptools way also
                except IndexError:
                    log.warn('Skipping %s, no download url', atom)
                else:
                    try:
                        gpypi = GPyPI(pn, version, self.config)
                        gpypi.create_ebuilds()
                    except GPyPiException, e:
                        log.warn(e)
                    except KeyboardInterrupt:
                        raise
                    except:
                        log.exception('Unexpected error occured during ebuild creation:')


def main(args=sys.argv[1:]):
    """Parse command-line options and do it.
    Core function for gpypi2 command.

    Dispatches commands to :class:`gpypi2.cli.CLI`
    """
    main_parser = argparse.ArgumentParser(prog='gpypi2',
        description="Builds ebuilds from PyPi.")
    main_parser.add_argument('-v', '--version', action='version',
        version='%(prog)s ' + __version__)

    # global options
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-P", "--PN", action='store', dest="pn",
        help=Config.allowed_options['pn'][0])
    parser.add_argument("-V", "--PV", action='store', dest="pv",
        help=Config.allowed_options['pv'][0])
    parser.add_argument("--MY-PV", action='store', dest="my_pv",
        help=Config.allowed_options['my_pv'][0])
    parser.add_argument("--MY-PN", action='store', dest="my_pn",
        help=Config.allowed_options['my_pn'][0])
    parser.add_argument("--MY-P", action='store', dest="my_p",
        help=Config.allowed_options['my_p'][0])
    parser.add_argument("-u", "--uri", action='store', dest="uri",
        help=Config.allowed_options['uri'][0])
    parser.add_argument("-i", "--index-url", action='store', dest="index_url",
        help=Config.allowed_options['index_url'][0])
    # TODO: release yolk with support to query third party PyPi
    # TODO: test --index-url is always taken in account
    parser.add_argument('--nocolors', action='store_true', dest='nocolors',
        help=Config.allowed_options['nocolors'][0])
    parser.add_argument("--config-file", action='store', dest="config_file",
        default="/etc/gpypi2", help="Absolute path to a config file")

    logging_group = parser.add_mutually_exclusive_group()
    logging_group.add_argument("-q", "--quiet", action='store_true',
        dest="quiet", default=False, help="Show less output.")
    logging_group.add_argument("-d", "--debug", action='store_true',
        dest="debug", default=False, help="Show debug information.")

    # ebuild handling options
    ebuild_parser = argparse.ArgumentParser(add_help=False)
    ebuild_parser.add_argument('up_pn', action='store', metavar="package name")
    ebuild_parser.add_argument('up_pv', nargs='?', default=None, metavar="package version")

    # create & install options
    create_install_parser = argparse.ArgumentParser(add_help=False)
    create_install_parser.add_argument("-l", "--overlay", action='store', dest='overlay',
        metavar='OVERLAY_NAME', help=Config.allowed_options['overlay'][0])
    create_install_parser.add_argument("-o", "--overwrite", action='store_true',
        dest="overwrite", help=Config.allowed_options['overwrite'][0])
    create_install_parser.add_argument("--no-deps", action='store_true', dest="no_deps",
        help=Config.allowed_options['no_deps'][0])
    create_install_parser.add_argument("-c", "--category", action='store',
        dest="category", help=Config.allowed_options['category'][0])
    # TODO: pretend
    #create_install_parser.add_argument("-p", "--pretend", action='store_true',
        #dest="pretend", default=False, help="Print ebuild to stdout, "
        #"don't write ebuild file, don't download SRC_URI.")

    ## subcommands
    subparsers = main_parser.add_subparsers(title="commands", dest="command")

    parser_create = subparsers.add_parser('create', help="Write ebuild and it's dependencies to an overlay",
        description="Write ebuild and it's dependencies to an overlay",
        parents=[parser, ebuild_parser, create_install_parser])

    parser_echo = subparsers.add_parser('echo', help="Echo ebuild to stdout",
        description="Echo ebuild to stdout",
        parents=[parser, ebuild_parser])
    parser_echo.add_argument("--format", action='store', dest="format",
        help=Config.allowed_options['format'][0])

    parser_install = subparsers.add_parser('install', help="Install ebuild and it's dependencies",
        description="Install ebuild and it's dependencies",
        parents=[parser, ebuild_parser, create_install_parser])

    parser_pypi = subparsers.add_parser('sync', help="Populate all packages from pypi into an overlay",
        description="Populate all packages from pypi into an overlay",
        parents=[parser, create_install_parser])

    # register sdist_ebuild command
    sdist_ebuild.register()

    args = main_parser.parse_args(args)

    # TODO: configurable logging
    if args.nocolors:
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter("%(message)s"))
    else:
        ch = PortageStreamHandler()
        ch.setFormatter(PortageFormatter("%(message)s"))
    logger = logging.getLogger()
    logger.addHandler(ch)

    if args.debug:
        logger.setLevel(logging.DEBUG)
    elif args.quiet:
        logger.setLevel(logging.WARN)
    else:
        logger.setLevel(logging.INFO)

    # root must be used for write permission in overlay and for
    # unpacking of ebuilds
    if os.geteuid() != 0:
        main_parser.error('Must be run as root.')

    config_mgr = ConfigManager.load_from_ini(args.config_file)
    config_mgr.configs['argparse'] = Config.from_argparse(args)

    # handle command
    try:
        CLI(config_mgr)
    except:
        # enter pdb debugger when debugging is enabled
        if args.debug:
            pdb.post_mortem()
        else:
            raise

if __name__ == "__main__":
    main()
