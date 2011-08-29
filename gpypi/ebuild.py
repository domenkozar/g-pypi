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


.. currentmodule: gpypi.ebuild

"""

import os
import logging
import tempfile
import shutil
import string

from pprint import pformat
from datetime import date
import distutils.core

from jinja2 import Environment, PackageLoader
from pygments import highlight
from pygments.lexers import BashLexer
from pygments.formatters import get_formatter_by_name
from pkg_resources import parse_requirements
import setuptools

from gpypi import __version__
from gpypi import utils
from gpypi.portage_utils import PortageUtils
from gpypi.enamer import Enamer
from gpypi.workflow import Repoman, Echangelog, Metadata
from gpypi.exc import *
from gpypi.trove_map import topic_dict

log = logging.getLogger(__name__)


# TODO: dependency can be a string or list of strings
class Ebuild(dict):
    """Contains, populates and renders an ebuild.

    :param options: Configuration for ebuild
    :type options: :class:`gpypi.config.ConfigManager` instance

    :attr:`DOC_DIRS` -- Possible locations for documentation

    :attr:`EXAMPLES_DIRS` -- Possible locations for examples

    :attr:`EBUILD_TEMPLATE` -- Template name

    :attr:`requires` -- set of packages that this ebuild depends on

    """
    # TODO: __init__ attrs
    DOC_DIRS = ['doc', 'docs', 'documentation']
    EXAMPLES_DIRS = ['example', 'examples', 'demo', 'demos']
    EBUILD_TEMPLATE = 'ebuild.jinja'
    EBUILD_TEMPLATE_PACKAGE = 'gpypi'

    def __init__(self, options):
        self.setup_keywords = {}
        self.metadata = {}
        self.unpacked_dir = None
        self.ebuild_path = None
        self.requires = set()
        self.has_tests = None
        self.options = options

        # init stuff
        self.env = Environment(
            loader=PackageLoader(self.EBUILD_TEMPLATE_PACKAGE, 'templates'),
            trim_blocks=True)
        self.template = self.env.get_template(self.EBUILD_TEMPLATE)

        # Variables that will be passed to the Jinja template
        d = {
            'python_modname': None,
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
            'gentoo_keywords': PortageUtils.get_keyword(),
        }
        super(Ebuild, self).__init__(d)
        # TODO: use Config rather
        self.options.configs['setup_py'] = self
        self.set_ebuild_vars()

    def __repr__(self):
        return '<Ebuild (%s)>' % pformat(dict.__repr__(self))

    def set_metadata(self, metadata):
        """Set metadata from :term:`PyPi`.

        :param metadata: Meta information about ebuild
        :type metadata: dict

        """
        d = {}
        if metadata and 'pypi' in self.options.use:
            for key, value in metadata.iteritems():
                new_key = key.lower().replace('-', '').replace('_', '')
                d[new_key] = value
            self.update(d)
            self.parse_metadata()
        else:
            log.error("No metadata or pypi configuration is disabled.")

        if self.options.category == "":
            # Unless given on the command line,
            # default category is 'dev-python'
            self.options.category = 'dev-python'

            topics = [i for i in self.get('classifiers', []) if i[:5] == 'Topic']
            # Other wise set the category to the one paired with the
            # most detailed classifier.
            topic_classifiers = [tuple(i.split(' :: ')) for i in topics]
            if len(topic_classifiers) > 0:
                length = 0
                for i in topic_classifiers:
                    if len(i) > length:
                        length = len(i)
                        tc = i
                self.options.category = topic_dict[string.join(tc, ' :: ')]

    def set_ebuild_vars(self):
        """Calls :meth:`gpypi.enamer.Enamer.get_vars` and
        updates instance variables.

        """
        d = Enamer.get_vars(self.options.uri, self.options.up_pn, self.options.up_pv)
        self.update(d)

        if filter(None, [src_uri.lower().endswith('.zip') for src_uri in self['src_uri']]):
            self.add_depend("app-arch/unzip")

    def parse_metadata(self):
        """Extract :term:`DESCRIPTION`, :term:`HOMEPAGE`,
        :term:`LICENSE` ebuild variables from :term:`PyPi` metadata.

        """
        # There doesn't seem to be any specification for case
        if 'summary' in self:
            self['description'] = self.get('summary', "")
            # Replace double quotes to keep bash syntax correct
            self['description'] = self['description'].replace('"', "'")

        my_license = Enamer.convert_license(self.get('classifiers', []), self.get('license', ""))

        if Enamer.is_valid_portage_license(my_license):
            self['license'] = my_license
        else:
            if 'license' in self:
                del self['license']

        self.options.configs['setup_py'].update(self)

    def post_unpack(self):
        """Perform finalization tasks. Dynamically imports *setup.py*
        file and extracts it's kwargs.

            * determine if :term:`PYTHON_MODNAME` is not
              :term:`PN` -- We inspect `packages`, `py_module` and `package_dir`

            * get dependencies from `setup_requires`,
              `install_requires` and `extra_requires`

            * figure out if we need to :term:`DEPEND` / :term:`RDEPEND` on
              :mod:`setuptools` -- We inspect if `setup.py` imports
              :mod:`setuptools` or :mod:`pkg_resources`

            * calls :meth:`Ebuild.discover_docs_and_examples`
              and :meth:`Ebuild.discover_tests`

            * determines :term:`DEPEND` / :term:`RDEPEND` on :mod:`setuptools`

        :raises: :exc:`gpypi.exc.GPyPiNoSetupFile`
        :raises: :exc:`gpypi.exc.GPyPiNoDistribution`

        """
        # save original functions to undo monkeypaching at the end
        temp_setup = setuptools.setup
        temp_distutils = distutils.core.setup

        # mock functions to get metadata
        self.setup_keywords = {}

        def wrapper(**kw):
            self.setup_keywords.update(kw)

        # monkeypatch setups
        setuptools.setup = wrapper
        distutils.core.setup = wrapper

        setup_file = os.path.join(self.unpacked_dir, "setup.py")
        if os.path.exists(self.unpacked_dir):
            if not os.path.exists(setup_file):
                raise GPyPiNoSetupFile("%s does not exists." % setup_file)
            else:
                # run setup file from unpacked_dir
                cwd = os.getcwdu()
                try:
                    os.chdir(self.unpacked_dir)
                    utils.import_path(setup_file)
                finally:
                    os.chdir(cwd)
        else:
            raise GPyPiNoDistribution("Unpacked dir could not be found: %s"\
                % self.unpacked_dir)

        # extract dependencies
        self.install_requires = self.setup_keywords.get('install_requires', '')
        self.setup_requires = self.setup_keywords.get('setup_requires', '')
        self.extras_require = self.setup_keywords.get('extras_require', {})
        self.tests_require = self.setup_keywords.get('tests_require', '')

        # dependencies resolving
        self.get_dependencies(self.install_requires)
        self.get_dependencies(self.setup_requires)
        # TODO: handle setup as depend instead of rdepend
        for use_flag, dependency in self.extras_require.iteritems():
            self.get_dependencies(dependency, if_use=use_flag)

        self.discover_docs_and_examples()
        self.discover_tests()

        # check dependency on setuptools
        with open(setup_file) as f:
            contents = f.read()
            if ('setuptools' in contents) or ('pkg_resources' in contents):
                self.add_depend('dev-python/setuptools')
                self.add_rdepend('dev-python/setuptools')

        # handle PYTHON_MODNAME
        module_names = []
        module_names.extend(self.setup_keywords.get('packages', []))
        module_names.extend(self.setup_keywords.get('py_modules', []))
        module_names.extend(filter(None, self.setup_keywords.get('package_dir', {}).keys()))

        # set modname only if needed
        if len(module_names) == 1 and module_names[0] != self['pn']:
            self['python_modname'] = module_names

        # undo monkeypatching
        setuptools.setup = temp_setup
        distutils.core.setup = temp_distutils

        # extract metadata
        if 'setup_py' in self.options.use:
            d = distutils.core.Distribution(self.setup_keywords)
            metadata = Enamer.parse_setup_py(d)
            self.update(metadata)

    def get_dependencies(self, vanilla_requirements, if_use=None):
        """
        Generate :term:`DEPEND` / :term:`RDEPEND` strings.

        :param vanilla_requirements: **require_\*** contents from `setup.py`
        :param if_use: :term:`USE` flag that must be set
            to download dependencies
        :type vanilla_requirements: string or list
        :type if_use: string

        """
        # TODO: DOC: steps to acquire deps
        requirements = parse_requirements(vanilla_requirements)

        for req in requirements:
            extras = req.extras
            # TODO: extend configuration to support callable configs
            # TODO: pass metadata from the project_name
            #category = Enamer.convert_category(req.project_name, {})
            category = self.options.category
            pn = Enamer.parse_pn(req.project_name)[0] or req.project_name

            # add setuptools dependency for later dependency generating
            self.add_setuptools_depend(req)

            log.debug('get_dependencies: pn(%s) category(%s)', pn, category)

            if not len(req.specs):
                # No version of requirement was specified so we only add
                # dev-python/pn
                self.add_rdepend(Enamer.construct_atom(pn, category,
                    uses=extras, if_use=if_use))
            else:
                comparator, ver = req.specs[0]
                ver = Enamer.parse_pv(ver)[0] or ver
                log.debug('get_dependencies: pv(%s)' % ver)
                if len(req.specs) > 1:
                    # Some packages have more than one comparator, i.e. cherrypy
                    # for turbogears has cherrpy>=2.2,<3.0 which would translate
                    # to portage's =dev-python/cherrypy-2.2*
                    comparator1, ver1 = req.specs[0]
                    comparator2, ver2 = req.specs[1]
                    # TODO: this is a total mess, refactor
                    if comparator1.startswith(">") and \
                            comparator2.startswith("<"):
                        # we set blocker for <*
                        self.add_rdepend(Enamer.construct_atom(pn, category, ver1,
                            comparator1, uses=extras, if_use=if_use))
                        self.add_rdepend(Enamer.construct_atom(pn, category, ver2,
                            "!" + comparator2, uses=extras, if_use=if_use))
                    elif comparator2.startswith(">") and \
                            comparator1.startswith("<"):
                        self.add_rdepend(Enamer.construct_atom(pn, category, ver2,
                            comparator2, uses=extras, if_use=if_use))
                        self.add_rdepend(Enamer.construct_atom(pn, category, ver1,
                            "!" + comparator1, uses=extras, if_use=if_use))
                    else:
                        self['warnings'].add("Couldn't resolve requirements. "
                            "You will need to make sure the RDEPEND for %s is "
                            "correct." % req)
                        self.add_rdepend(Enamer.construct_atom(pn, category,
                            uses=extras, if_use=if_use))
                        self['warnings'].add("Could not determine dependency: %s" % req)
                    break
                # Requirement.specs is a list of (comparator,version) tuples
                if comparator == "==":
                    comparator = "="
                atom = Enamer.construct_atom(pn, category, ver, comparator,
                    uses=extras)
                if PortageUtils.is_valid_atom(atom):
                    self.add_rdepend(Enamer.construct_atom(pn, category, ver,
                        comparator, uses=extras, if_use=if_use))
                else:
                    log.debug("Invalid PV in dependency: (Requirement %s) %s",
                        req, atom)
                    installed_pv = PortageUtils.get_installed_ver(Enamer.\
                        construct_atom(pn, category, uses=extras, if_use=if_use))
                    if installed_pv:
                        # If we have it installed, use >= installed version
                        self.add_rdepend(Enamer.construct_atom(pn, category,
                            installed_pv, '>=', uses=extras, if_use=if_use))
                    else:
                        # If package has invalid version and we don't have
                        # an ebuild in portage, just add PN to DEPEND, no
                        # version.
                        self['warnings'].add("Could not determine dependency: %s" % req)
                        self.add_rdepend(Enamer.construct_atom(pn, category,
                            uses=extras, if_use=if_use))

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
        # TODO: deep introspection
        # TODO: add support for sphinx
        # TODO: remove the DOCS searching, already handles by portage

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
        """Determine :term:`DISTUTILS_SRC_TEST` if tests are detected"""
        # TODO: py.test and trial
        # TODO: deep introspection and merge with docs/examples

        for root, dirs, files in os.walk(self.unpacked_dir):
            if 'tests' in dirs or 'test' in dirs:
                self['tests_method'] = 'setup.py'

        if self.setup_keywords.get('test_suite', '') == 'nose.collector':
            self['tests_method'] = 'nosetests'

        self.get_dependencies(self.tests_require, 'test')

    def update_with_s(self):
        """Add ${:term:`S`} to ebuild if needed."""
        log.debug("Trying to determine ${S}, unpacking...")
        if self.unpacked_dir is None:
            unpacked_dir = PortageUtils.find_s_dir(self['p'], self.options.category)
            if unpacked_dir == "":
                self["s"] = "${WORKDIR}"

            self.unpacked_dir = os.path.join(PortageUtils.get_workdir(self['p'],
                self.options.category), unpacked_dir)

        if self.get('my_p', None):
            self["s"] = "${WORKDIR}/${MY_P}"
        else:
            pass  # ${WORKDIR}/${P}

    def render(self):
        """Generate ebuild from template"""
        self.output = self.template.render(self, options=self.options)
        self.output = self.output.replace('    ', '\t')
        return self.output

    def print_formatted(self):
        """Print formatted ebuild
        """
        formatting = self.options.format
        background = self.options.background

        d = tempfile.mkdtemp()
        try:
            ebuild_path = self.find_path_to_ebuild(d)
            self.create(ebuild_path)
        finally:
            shutil.rmtree(d)

        self.show_warnings()
        if formatting == "none":
            print self.output
        else:
            # use pygments to print ebuild
            formatter = get_formatter_by_name(formatting, background=background)
            print highlight(self.output, BashLexer(), formatter)

    def create(self, ebuild_path=None):
        """Write ebuild and update it after unpacking and examining ${S}"""
        # Need to write the ebuild first so we can unpack it and check for $S
        if ebuild_path:
            self.ebuild_path = ebuild_path

        if self.write(overwrite=self.options.overwrite):
            if self.unpacked_dir is None:
                PortageUtils.unpack_ebuild(self.ebuild_path)
            self.update_with_s()
            self.post_unpack()

            # Write ebuild again after unpacking and adding ${S}
            self.write(overwrite=True)

            if self.options.command != 'echo':
                # apply workflows
                Metadata(self.options, os.path.dirname(self.ebuild_path))()
                Echangelog(self.options, os.path.dirname(self.ebuild_path))()
                Repoman(self.options, os.path.dirname(self.ebuild_path))()

                log.info("Your ebuild is here: " + self.ebuild_path)

        # TODO: If ebuild already exists, we don't unpack and get dependencies
        # because they must exist.
        # We should add an option to force creating dependencies or should
        # overwrite be used?
        return self.requires

    def find_path_to_ebuild(self, overlay_path):
        """"""
        ebuild_dir = PortageUtils.make_ebuild_dir(self.options.category,
            self['pn'], overlay_path)
        if not os.path.isdir(ebuild_dir or ""):
            raise GPyPiCouldNotCreateEbuildPath('Couldn not create ebuild directory %s' % ebuild_dir)
        return os.path.join(ebuild_dir, self['p'] + ".ebuild")

    def write(self, overwrite=False):
        """Write ebuild file

        :param overwrite: Overwrite ebuild if it already exists.
        :type overwrite: bool

        """

        # get ebuild path
        if not self.ebuild_path:
            overlay_name = self.options.overlay
            overlay_path = PortageUtils.get_overlay_path(overlay_name)
            self.ebuild_path = self.find_path_to_ebuild(overlay_path)

        log.debug('Ebuild.write: build_path(%s)', self.ebuild_path)

        # see if we want to overwrite
        if (not self.options.command == 'echo') and os.path.exists(self.ebuild_path) and not overwrite:
            log.warn("Ebuild exists (use -o to overwrite), skipping: %s" % self.ebuild_path)
            return False

        # write ebuild
        out = open(self.ebuild_path, "w")
        try:
            out.write(self.render())
        finally:
            out.close()
        return True

    def show_warnings(self):
        """Log warnings for incorrect ebuild syntax."""
        for warning in self['warnings']:
            log.warn(warning)

    def add_use(self, use_flag):
        """Add :term:`USE` flag."""
        self['use'].add(use_flag)

    def add_inherit(self, eclass):
        """Add inherit :term:`eclass`."""
        self['inherit'].add(eclass)

    def add_depend(self, depend):
        """Add :term:`DEPEND` ebuild variable."""
        self['depend'].add(depend)

    def add_rdepend(self, rdepend):
        """Add :term:`RDEPEND` ebuild variable."""
        self['rdepend'].add(rdepend)
    # TODO: get rid of add_*
