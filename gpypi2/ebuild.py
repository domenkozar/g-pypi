#!/usr/bin/env python
# pylint: disable-msg=C0103,C0301,E0611,W0511

# Reasons for pylint disable-msg's
#
# E0611 - No name 'resource_string' in module 'pkg_resources'
#         No name 'BashLexer' in module 'pygments.lexers'
#         No name 'TerminalFormatter' in module 'pygments.formatters'
#         (False positives ^^^)
# C0103 - Variable names too short (p, pn, pv etc.)
#         (These can be ignored individually with some in-line pylint-foo.)
"""

Creates an ebuild


.. currentmodule: gpypi2.ebuild

"""

import sys
import os
import imp
import logging
from datetime import date

from jinja2 import Environment, PackageLoader
from pygments import highlight
from pygments.lexers import BashLexer
from pygments.formatters import TerminalFormatter, HtmlFormatter
from pygments.formatters import BBCodeFormatter
from pkg_resources import parse_requirements
import setuptools
import distutils.core

from gpypi2 import __version__
from gpypi2.portage_utils import PortageUtils
from gpypi2.enamer import Enamer
from gpypi2.exc import *
#from g_pypi.config import MyConfig


log = logging.getLogger(__name__)


# TODO: dependency can ge a string or list of strings
class Ebuild(dict):
    """Contains ebuild

    :attr:`DOC_DIRS` -- Possible locations for documentation

    :attr:`EXAMPLES_DIRS` -- Possible locations for examples

    :attr:`EBUILD_TEMPLATE` -- Template name

    """
    DOC_DIRS = ['doc', 'docs', 'documentation']
    EXAMPLES_DIRS = ['example', 'examples', 'demo', 'demos']
    EBUILD_TEMPLATE = 'ebuild.tmpl'

    def __init__(self, up_pn, up_pv, download_url):
        """Setup ebuild variables"""
        self.pypi_pkg_name = up_pn
        self.metadata = None
        self.unpacked_dir = None
        self.ebuild_path = ""
        self.setup = []
        self.requires = set()
        self.has_tests = None

        # TODO: add possibility to override pn, pv, my_pn, my_pv
        ebuild_vars = Enamer.get_vars(download_url, up_pn, up_pv)

        # TODO: implement support for SCM download urls
        #if self.options.subversion:
            #self.options.pv = "9999"
            #self.vars['esvn_repo_uri'] = download_url
            #self.add_inherit("subversion")

        # Variables that will be passed to the Jinja template
        d = {
            'up_pn': up_pn,
            'up_pv': up_pv,
            'download_url': download_url,
            'need_python': '',
            'python_modname': '',
            'description': '',
            'homepage': set(),
            'rdepend': set(),
            'depend': set(),
            'use': set(),
            'warnings': set(),
            'slot': '0',
            's': '',
            'tests_method': '',
            'inherit': set(['distutils']),
            'gpypi_version': __version__,
            'year': date.today().year,
            'keywords': PortageUtils.get_keyword() or '',
        }
        d.update(ebuild_vars)
        super(Ebuild, self).__init__(d)
        self.set_ebuild_vars(download_url)

    def __repr__(self):
        return '<Ebuild (%s)>' % super(Ebuild, self).__repr__()

    def set_metadata(self, metadata):
        """Set metadata"""
        self.metadata = {}
        if metadata:
            for key, value in metadata.iteritems():
                new_key = key.lower().replace('-', '').replace('_', '')
                self.metadata[new_key] = value
        else:
            # TODO: convert error
            log.error("Package has no metadata.")

    def set_ebuild_vars(self, download_url):
        """Determine variables from SRC_URI
        """
        # TODO: docs
        d = Enamer.get_vars(download_url, self['up_pn'], self['up_pv'])
        self.update(d)

        if self['src_uri'].lower().endswith('.zip'):
            self.add_depend("app-arch/unzip")

    def add_metadata(self):
        """
        Extract DESCRIPTION, HOMEPAGE, LICENSE ebuild variables from metadata
        """
        if 'homepage' in self.metadata:
            self['homepage'].add(self.metadata['homepage'])

        # There doesn't seem to be any specification for case
        elif 'summary' in self.metadata:
            self['description'] = self.metadata['summary']
        if self['description'] is None:
            self['description'] = ""
        else:
            # Replace double quotes to keep bash syntax correct
            self['description'] = self['description'].replace('"', "'")

        my_license = ""
        if 'classifiers' in self.metadata:
            for data in self.metadata['classifiers']:
                if data.startswith("License :: "):
                    my_license = PortageUtils.get_portage_license(data)
        if not my_license:
            if 'license' in self.metadata:
                my_license = self.metadata['license']
            my_license = "%s" % my_license
        if not Enamer.is_valid_portage_license(my_license):
            if "LGPL" in my_license:
                my_license = "LGPL-2.1"
            elif "GPL" in my_license:
                my_license = "GPL-2"
            else:
                self['warnings'].add("Invalid LICENSE.")

        self['license'] = "%s" % my_license

    def post_unpack(self):
        """Perform finalization tasks:

            * determine if :term:`PYTHON_MODNAME` is not :term:`PN` -- We inspect `packages`, `py_module` and `package_dir`

            * get dependencies from `setup_requires`, `install_requires` and `extra_requires`

            * figure out if we need to :term:`DEPEND`/:term:`RDEPEND` on :mod:`setuptools` -- We inspect if setup.py imports setuptools or pkg_resources

            * calls :meth:`discover_docs_and_examples` and :meth:`discover_tests`

        """
        # save original functions to undo monkeypaching at the end
        temp_setup = setuptools.setup
        temp_distutils = distutils.core.setup

        # mock functions to get metadata
        keywords = {}

        def wrapper(**kw):
            keywords.update(kw)

        # monkeypatch setups
        setuptools.setup = wrapper
        distutils.core.setup = wrapper

        setup_file = os.path.join(self.unpacked_dir, "setup.py")
        if os.path.exists(self.unpacked_dir):
            if not os.path.exists(setup_file):
                raise GPyPiNoSetupFile("%s does not exists." % setup_file)
            else:
                # run setup file
                imp.load_source('setup', setup_file)
        else:
            raise GPyPiNoDistribution("Unpacked dir could not be found: %s" % self.unpacked_dir)

        # extract dependencies
        self.install_requires = keywords.get('install_requires', '')
        self.setup_requires = keywords.get('setup_requires', '')
        self.extras_require = keywords.get('extras_require', '')
        self.tests_require = keywords.get('tests_require', '')

        # dependencies resolving
        self.get_dependencies(self.install_requires)
        self.get_dependencies(self.setup_requires)
        # TODO: handle setup as depend instead of rdepend
        self.get_dependencies(self.extras_requires)
        self.discover_docs_and_examples()
        self.discover_tests()

        # check dependency on setuptools
        with open(setup_file) as f:
            contents = f.read()
            if 'setuptools' or 'pkg_resources' in contents:
                self.add_depend('dev-python/setuptools')
                self.add_rdepend('dev-python/setuptools')

        # handle PYTHON_MODNAME
        module_names = []
        module_names.extend(keywords.get('packages', []))
        module_names.extend(keywords.get('py_modules', []))
        module_names.extend(filter(None, keywords.get('package_dir', []).keys()))
        # TODO: extract $(S) from package_dir
        # TODO: support provides/requires keyword
        # http://docs.python.org/distutils/setupscript.html#relationships-between-distributions-and-packages

        # set modname only if needed
        if len(module_names) == 1 and module_names[0] != self['pn']:
            self['python_modname'] = module_names

        # undo monkeypatching
        setuptools.setup = temp_setup
        distutils.core.setup = temp_distutils

    def get_dependencies(self, vanilla_requirements, if_use=None):
        """
        Generate DEPEND/RDEPEND strings

        :param requirements:
        :param if_use: :term:`USE` that must be set to download dependencies
        :type requirements: string or list
        :type if_use: string

        * Run setup.py egg_info so we can get the setuptools requirements
          (dependencies)

        * Add the unpacked directory to the WorkingEnvironment

        * Get a Distribution object for package we are isntalling

        * Get Requirement object containing dependencies

          a) Determine if any of the requirements are installed

          b) If requirements aren't installed, see if we have a matching ebuild
          with adequate version available

        * Build DEPEND string based on either a) or b)

        """
        # TODO: enamer for determining category
        requirements = parse_requirements(vanilla_requirements)

        for req in requirements:
            added_dep = False
            extras = req.extras
            category = Enamer.convert_category(req.project_name, self.metadata)
            pn = Enamer.parse_pn(req.project_name)[0] or req.project_name
            log.debug('get_dependencies: pn(%s)' % pn)
            # add setuptools dependency for later dependency generating
            self.add_setuptools_depend(req)
            if not len(req.specs):
                # No version of requirement was specified so we only add
                # dev-python/pn
                self.add_rdepend(Enamer.construct_atom(pn, category, uses=extras, if_use=if_use))
                added_dep = True
            else:
                comparator, ver = req.specs[0]
                ver = Enamer.parse_pv(ver)[0] or ver
                log.debug('get_dependencies: pv(%s)' % ver)
                if len(req.specs) > 1:
                    # Some packages have more than one comparator, i.e. cherrypy
                    # for turbogears has cherrpy>=2.2,<3.0 which would translate to
                    # portage's =dev-python/cherrypy-2.2*
                    comparator1, ver1 = req.specs[0]
                    comparator2, ver2 = req.specs[1]
                    if comparator1.startswith(">") and \
                            comparator2.startswith("<"):
                        comparator = "="
                        # TODO: more specific info about req
                        # TODO: use blockers
                        self['warnings'].add("Couldn't resolve requirements. You will need to make sure the RDEPEND for %s is correct." % req)
                    else:
                        # TODO: more specific info about req
                        self['warnings'].add("Couldn't resolve requirements. You will need to make sure the RDEPEND for %s is correct." % req)
                        self.add_rdepend(Enamer.construct_atom(pn, category, uses=extras, if_use=if_use))
                        break
                # Requirement.specs is a list of (comparator,version) tuples
                if comparator == "==":
                    comparator = "="
                if PortageUtils.valid_cpn(Enamer.construct_atom(pn, category, ver, comparator, uses=extras)):
                    self.add_rdepend(Enamer.construct_atom(pn, category, ver, comparator, uses=extras, if_use=if_use))
                else:
                    log.debug("Invalid PV in dependency: (Requirement %s) %s" % (req, temp_cpn))
                    installed_pv = PortageUtils.\
                        get_installed_ver(Enamer.\
                        construct_atom(pn, category, uses=extras, if_use=if_use))
                    if installed_pv:
                        # If we have it installed, use >= installed version
                        self.add_rdepend(Enamer.construct_atom(pn, category, installed_pv, '>=', uses=extras, if_use=if_use))
                    else:
                        # If package has invalid version and we don't have
                        # an ebuild in portage, just add PN to DEPEND, no
                        # version. This means the dep ebuild will have to
                        # be created by adding --MY_? options using the CLI
                        self.add_rdepend(Enamer.construct_atom(pn, category, uses=extras, if_use=if_use))
                added_dep = True
            if not added_dep:
                self['warnings'].add("Could not determine dependency: %s" % req)

    def add_setuptools_depend(self, req):
        """
        Add dependency for setuptools requirement
        After current ebuild is created, we check if portage has an
        ebuild for the requirement, if not create it.

        :param req: requirement needed by ebuild
        :type req: pkg_resources `Requirement` object

        """
        log.debug("Found dependency: %s " % req)
        self.requires.add(req)

    def discover_docs_and_examples(self):
        """
        Add src_install for installing docs and examples if found
        and appropriate USE flags e.g. IUSE='doc examples'

        """
        # TODO: add support for sphinx

        for ddir in self.DOC_DIRS:
            if os.path.exists(os.path.join(self.unpacked_dir, ddir)):
                self['docs_dir'] = ddir
                self.add_use("doc")
                break

        for edir in self.EXAMPLES_DIRS:
            if os.path.exists(os.path.join(self.unpacked_dir, edir)):
                self['examples_dir'] = edir
                self.add_use("examples")
                break

    def discover_tests(self):
        """Determine :term:`DISTUTILS_SRC_TEST` if tests detected"""
        # TODO: py.test and trial

        for root, dirs, files in os.walk(self.unpacked_dir):
            if 'tests' in files or 'test' in files:
                self['tests_method'] = 'setup.py'

        for line in self.setup:
            if "nose.collector" in line:
                self['tests_method'] = 'nosetests'

        if self['tests_method']:
            self.get_dependencies(self.tests_require, 'test')

    def update_with_s(self):
        """Add ${S} to ebuild if needed"""
        log.debug("Trying to determine ${S}, unpacking...")
        unpacked_dir = find_s_dir(self['p'], self.options.category)
        if unpacked_dir == "":
            self["s"] = "${WORKDIR}"
            return

        self.unpacked_dir = os.path.join(get_workdir(self['p'],
            self.options.category), unpacked_dir)
        if unpacked_dir and unpacked_dir != self['p']:
            if unpacked_dir == self['my_p_raw']:
                unpacked_dir = '${MY_P}'
            elif unpacked_dir == self['my_pn']:
                unpacked_dir = '${MY_PN}'
            elif unpacked_dir == self['pn']:
                unpacked_dir = '${PN}'

            self["s"] = "${WORKDIR}/%s" % unpacked_dir

    def render(self):
        """Generate ebuild from template"""

        # Add homepage, license and description from metadata
        self.add_metadata()

        #if not self.options.pretend and self.unpacked_dir: # and \
        self.post_unpack()

        env = Environment(loader=PackageLoader('gpypi2', 'templates'))
        return env.get_template(self.EBUILD_TEMPLATE).render(self)

    def print_formatted(self):
        """Print ebuild with logging"""
        # No command-line set, config file says no formatting
        log.info("%s/%s-%s" % (self.options.category, self['pn'],
            self['pv']))
        if self.options.format == "none" or \
            (self.config['format'] == "none" and not self.options.format):
            log.info(self.ebuild_text)
            return

        # use pygments to print ebuild
        background = self.config['background']
        if self.options.format == "html":
            formatter = HtmlFormatter(full=True)
        elif self.config['format'] == "bbcode" or \
                self.options.format == "bbcode":
            formatter = BBCodeFormatter()
        elif self.options.format == "ansi" or self.config['format'] == "ansi":
            formatter = TerminalFormatter(bg=background)
        else:
            #Invalid formatter specified
            log.info(self.ebuild_text)
            print "ERROR - No formatter"
            print self.config['format'], self.options.format
            return
        log.info(highlight(self.ebuild_text,
                BashLexer(),
                formatter,
        ))
        self.show_warnings()

    def create(self):
        """Write ebuild and update it after unpacking and examining ${S}"""
        # Need to write the ebuild first so we can unpack it and check for $S
        if self.write(overwrite=self.options.overwrite):
            unpack_ebuild(self.ebuild_path)
            self.update_with_s()
            # Write ebuild again after unpacking and adding ${S}
            ebuild = self.render()
            # Run any tests if found
            #if self.has_tests:
            #    run_tests(self.ebuild_path)
            # We must overwrite initial skeleton ebuild
            self.write(ebuild, overwrite=True)
            self.print_formatted(ebuild)
            log.info("Your ebuild is here: " + self.ebuild_path)
        # If ebuild already exists, we don't unpack and get dependencies
        # because they must exist.
        # We should add an option to force creating dependencies or should
        # overwrite be used?
        return self.requires

    def write(self, overwrite=False):
        """Write ebuild file"""
        # Use command-line overlay if specified, else the one in .g-pyprc
        if self.options.overlay:
            overlay_name = self.options.overlay
            overlays = get_repo_names()
            if overlay_name in overlay:
                overlay_path = overlays[overlay_name]
            else:
                log.error("Couldn't find overylay/repository by that" +
                        " name. I know about these:")
                for repo in sorted(overlays.keys()):
                    log.error("  " + repo.ljust(18) + overlays[repo])
                sys.exit(1)
        else:
            overlay_path = self.config['overlay']
        ebuild_dir = make_overlay_dir(self.options.category, self['pn'], \
                overlay_path)
        if not ebuild_dir:
            log.error("Couldn't create overylay ebuild directory.")
            sys.exit(2)
        self.ebuild_path = os.path.join(ebuild_dir, "%s.ebuild" % \
                self['p'])
        if os.path.exists(self.ebuild_path) and not overwrite:
            # log.error("Ebuild exists. Use -o to overwrite.")
            log.warn("Ebuild exists, skipping: %s" % self.ebuild_path)
            return
        try:
            out = open(self.ebuild_path, "w")
        except IOError, err:
            log.error(err)
            sys.exit(2)
        out.write(self.ebuild_text)
        out.close()
        return True

    def show_warnings(self):
        """Print warnings for incorrect ebuild syntax"""
        for warning in self.warnings:
            log.warn("** Warning: %s" % warning)

    def add_use(self, use_flag):
        """Add USE flag"""
        self['use'].add(use_flag)

    def add_inherit(self, eclass):
        """Add inherit eclass"""
        self['inherit'].add(eclass)

    def add_depend(self, depend):
        """Add DEPEND ebuild variable"""
        self['depend'].add(depend)

    def add_rdepend(self, rdepend):
        """Add RDEPEND ebuild variable"""
        self['rdepend'].add(rdepend)
