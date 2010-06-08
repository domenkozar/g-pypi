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

"""

import re
import sys
import os
import logging
from datetime import date

from jinja2 import Environment, PackageLoader
from pygments import highlight
from pygments.lexers import BashLexer
from pygments.formatters import TerminalFormatter, HtmlFormatter
from pygments.formatters import BBCodeFormatter
from pkg_resources import resource_string, WorkingSet, Environment, Requirement

from gpypi2 import __version__
from gpypi2.portage_utils import PortageUtils
from gpypi2.enamer import Enamer
#from g_pypi.config import MyConfig


log = logging.getLogger(__name__)

class Ebuild(object):
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
        self.config = MyConfig.config
        self.options = MyConfig.options
        self.metadata = None
        self.unpacked_dir = None
        self.ebuild_text = ""
        self.ebuild_path = ""
        self.setup = []
        self.requires = set()
        self.has_tests = None

        # Variables that will be passed to the Jinja template
        self.vars = {
            'need_python': '',
            'python_modname': '',
            'description': '',
            'homepage': '',
            'rdepend': set(),
            'depend': set(),
            'use': set(),
            'warnings': set(),
            'slot': '0',
            's': '',
            'keywords': self.config['keyword'],
            'inherit': set(['distutils']),
            'gpypi_version': __version__,
            'year': date.today().year,
            'keywords': os.getenv('ACCEPT_KEYWORDS', ""),
            #'esvn_repo_uri': '',
        }
        # TODO: implement support for SCM download urls
        #if self.options.subversion:
            # Live svn version ebuild
            #self.options.pv = "9999"
            #self.vars['esvn_repo_uri'] = download_url
            #self.add_inherit("subversion")
        ebuild_vars = Enamer.get_vars(download_url, up_pn, up_pv, self.options.pn,
                self.options.pv, self.options.my_pn, self.options.my_pv)
        for key in ebuild_vars.keys():
            if not self.vars.has_key(key):
                self.vars[key] = ebuild_vars[key]
        self.vars['p'] = '%s-%s' % (self.vars['pn'], self.vars['pv'])

    def set_metadata(self, metadata):
        """Set metadata"""
        # TODO: convert error
        if metadata:
            self.metadata = metadata
        else:
            log.error("Package has no metadata.")
            sys.exit(2)

    def get_ebuild_vars(self, download_url):
        """Determine variables from SRC_URI"""
        # TODO: get rid of if/else
        if self.options.pn or self.options.pv:
            ebuild_vars = Enamer.get_vars(download_url, self.vars['pn'],
                    self.vars['pv'], self.options.pn, self.options.pv)
        else:
            ebuild_vars = Enamer.get_vars(download_url, self.vars['pn'],
                    self.vars['pv'])
        if self.options.my_p:
            ebuild_vars['my_p'] = self.options.my_p

        if self.options.my_pv:
            ebuild_vars['my_pv'] = self.options.my_pv

        if self.options.my_pn:
            ebuild_vars['my_pn'] = self.options.my_pn

        if ebuild_vars.has_key('my_p'):
            self.vars['my_p'] = ebuild_vars['my_p']
            self.vars['my_p_raw'] = ebuild_vars['my_p_raw']
        else:
            self.vars['my_p'] = ''
            self.vars['my_p_raw'] = ebuild_vars['my_p_raw']
        if ebuild_vars.has_key('my_pn'):
            self.vars['my_pn'] = ebuild_vars['my_pn']
        else:
            self.vars['my_pn'] = ''
        if ebuild_vars.has_key('my_pv'):
            self.vars['my_pv'] = ebuild_vars['my_pv']
        else:
            self.vars['my_pv'] = ''
        self.vars['src_uri'] = ebuild_vars['src_uri']

    def add_metadata(self):
        """
        Extract DESCRIPTION, HOMEPAGE, LICENSE ebuild variables from metadata
        """
        # Various spellings for 'homepage'
        homepages = ['Home-page', 'home_page', 'home-page']
        for hpage in homepages:
            if self.metadata.has_key(hpage):
                self.vars['homepage'] = self.metadata[hpage]

        # There doesn't seem to be any specification for case
        if self.metadata.has_key('Summary'):
            self.vars['description'] = self.metadata['Summary']
        elif self.metadata.has_key('summary'):
            self.vars['description'] = self.metadata['summary']
        # Replace double quotes to keep bash syntax correct
        if self.vars['description'] is None:
            self.vars['description'] = ""
        else:
            self.vars['description'] = self.vars['description'].replace('"', "'")

        my_license = ""
        if self.metadata.has_key('classifiers'):
            for data in self.metadata['classifiers']:
                if data.startswith("License :: "):
                    my_license = get_portage_license(data)
        if not my_license:
            if self.metadata.has_key('License'):
                my_license = self.metadata['License']
            elif self.metadata.has_key('license'):
                my_license = self.metadata['license']
            my_license = "%s" % my_license
        if not is_valid_license(my_license):
            if "LGPL" in my_license:
                my_license = "LGPL-2.1"
            elif "GPL" in my_license:
                my_license = "GPL-2"
            else:
                self.vars['warnings'].add("Invalid LICENSE.")

        self.vars['license'] = "%s" % my_license

    def post_unpack(self):
        """Check setup.py for:
           * PYTHON_MODNAME != $PN
           * setuptools install_requires or extra_requires
           # regex: install_requires[ \t]*=[ \t]*\[.*\],

        """
        # TODO: mock setup.py to extract data dynamic rather than with regex
        name_regex = re.compile('''.*name\s*=\s*[',"]([\w+,\-,\_]*)[',"].*''')
        module_regex = \
               re.compile('''.*packages\s*=\s*\[[',"]([\w+,\-,\_]*)[',"].*''')
        if os.path.exists(self.unpacked_dir):
            setup_file = os.path.join(self.unpacked_dir, "setup.py")
            if not os.path.exists(setup_file):
                self.vars['warnings'].add("No setup.py found!")
                self.setup = ""
                return
            self.setup = open(setup_file, "r").readlines()

        setuptools_requires = module_name = package_name = None
        for line in self.setup:
            name_match = name_regex.match(line)
            if name_match:
                package_name = name_match.group(1)
            elif "packages=" in line or "packages =" in line:
                #XXX If we have more than one and only one is a top-level
                #use it e.g. "module, not module.foo, module.bar"
                mods = line.split(",")[0]
                #if len(mods) > 1:
                #    self.warnings.add(line)
                module_match = module_regex.match(mods)
                if module_match:
                    module_name = module_match.group(1)
            elif ("setuptools" in line) and ("import" in line):
                setuptools_requires = True
                #It requires setuptools to install pkg
                self.add_depend("dev-python/setuptools")

        if setuptools_requires:
            self.get_dependencies(setup_file)
        else:
            log.warn("This package does not use setuptools so you will have to determine any dependencies if needed.")

        if module_name and package_name:
            #    if module_name != package_name:
            self.vars['python_modname'] = module_name

    def get_unpacked_dist(self, setup_file):
        """
        Return pkg_resources Distribution object from unpacked package
        """
        os.chdir(self.unpacked_dir)
        # TODO: executable
        os.system("/usr/bin/python %s egg_info" % setup_file)
        ws = WorkingSet([find_egg_info_dir(self.unpacked_dir)])
        env = Environment()
        return env.best_match(Requirement.parse(self.pypi_pkg_name), ws)

    def get_dependencies(self, setup_file):
        """
        Generate DEPEND/RDEPEND strings

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

        # `dist` is a pkg_resources Distribution object
        dist = self.get_unpacked_dist(setup_file)
        if not dist:
            # Should only happen if ebuild had 'install_requires' in it but
            # for some reason couldn't extract egg_info
            log.warn("Couldn't acquire Distribution obj for %s" % \
                    self.unpacked_dir)
            return

        for req in dist.requires():
            added_dep = False
            pkg_name = req.project_name.lower()
            if not len(req.specs):
                self.add_setuptools_depend(req)
                self.add_rdepend("dev-python/%s" % pkg_name)
                added_dep = True
                # No version of requirement was specified so we only add
                # dev-python/pkg_name
            else:
                comparator, ver = req.specs[0]
                self.add_setuptools_depend(req)
                if len(req.specs) > 1:
                    comparator1, ver = req.specs[0]
                    comparator2, ver = req.specs[1]
                    if comparator1.startswith(">") and \
                            comparator2.startswith("<"):
                        comparator = "="
                        self.vars['warnings'].add("Couldn't resolve requirements. You will need to make sure the RDEPEND for %s is correct." % req)
                    else:
                        # Some packages have more than one comparator, i.e. cherrypy
                        # for turbogears has >=2.2,<3.0 which would translate to
                        # portage's =dev-python/cherrypy-2.2*
                        log.warn(" **** Requirement %s has multi-specs ****" % req)
                        self.add_rdepend("dev-python/%s" % pkg_name)
                        break
                # Requirement.specs is a list of (comparator,version) tuples
                if comparator == "==":
                    comparator = "="
                if valid_cpn("%sdev-python/%s-%s" % (comparator, pkg_name, ver)):
                    self.add_rdepend("%sdev-python/%s-%s" % (comparator, pkg_name, ver))
                else:
                    log.info(\
                            "Invalid PV in dependency: (Requirement %s) %sdev-python/%s-%s" \
                            % (req, comparator, pkg_name, ver)
                            )
                    installed_pv = get_installed_ver("dev-python/%s" % pkg_name)
                    if installed_pv:
                        self.add_rdepend(">=dev-python/%s-%s" % \
                                (pkg_name, installed_pv))
                    else:
                        # If we have it installed, use >= installed version
                        # If package has invalid version and we don't have
                        # an ebuild in portage, just add PN to DEPEND, no 
                        # version. This means the dep ebuild will have to
                        # be created by adding --MY_? options using the CLI
                        self.add_rdepend("dev-python/%s" % pkg_name)
                added_dep = True
            if not added_dep:
                self.vars['warnings'].add("Couldn't determine dependency: %s" % req)

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

    def get_docs(self):
        """
        Add src_install for installing docs and examples if found
        and appropriate USE flags e.g. IUSE='doc examples'

        """
        have_docs = False
        have_examples = False

        # TODO: add support for sphinx

        for ddir in self.DOC_DIRS:
            if os.path.exists(os.path.join(self.unpacked_dir, ddir)):
                docs_dir = ddir
                self.add_use("doc")
                break

        for edir in self.EXAMPLES_DIRS:
            if os.path.exists(os.path.join(self.unpacked_dir, edir)):
                examples_dir = edir
                self.add_use("examples")
                break

    def get_src_test(self):
        """Create src_test if tests detected"""
        for line in self.setup:
            if "nose.collector" in line:
                self.add_depend("test? ( dev-python/nose )")
                self.add_use("test")
                self.has_tests = True
                return nose_test

        # TODO: Search for sub-directories
        if os.path.exists(os.path.join(self.unpacked_dir,
            "tests")) or os.path.exists(os.path.join(self.unpacked_dir,
                "test")):
            self.has_tests = True
            return regular_test

    def add_use(self, use_flag):
        """Add USE flag"""
        self.vars['use'].add(use_flag)

    def add_inherit(self, eclass):
        """Add inherit eclass"""
        self.vars['inherit'].add(eclass)

    def add_depend(self, depend):
        """Add DEPEND ebuild variable"""
        self.vars['depend'].add(depend)

    def add_rdepend(self, rdepend):
        """Add RDEPEND ebuild variable"""
        self.vars['rdepend'].add(rdepend)

    def get_ebuild(self):
        """Generate ebuild from template"""
        self.set_variables()
        functions = {
            'src_unpack': "",
            'src_compile': "",
            'src_install': "",
            'src_test': ""
        }
        if not self.options.pretend and self.unpacked_dir: # and \
            # not self.options.subversion:
            self.post_unpack()
            self.get_src_test()
            self.get_docs()

        # *_f variables are formatted text ready for ebuild
        # TODO: format_depend to filter
        self.vars['depend_f'] = format_depend(self.vars['depend'])
        self.vars['rdepend_f'] = format_depend(self.vars['rdepend'])

        env = Environment(loader=PackageLoader('gpypi2', 'templates'))
        self.ebuild_text = env.get_template(self.EBUILD_TEMPLATE).render(self.vars)

    def set_variables(self):
        """
        Ensure all variables needed for ebuild template are set and formatted

        """
        if self.vars['src_uri'].endswith('.zip') or \
                self.vars['src_uri'].endswith('.ZIP'):
            self.add_depend("app-arch/unzip")
        if self.vars['python_modname'] == self.vars['pn']:
            self.vars['python_modname'] = ""
        # Add homepage, license and description from metadata
        self.add_metadata()

    def print_ebuild(self):
        """Print ebuild to stdout"""
        # No command-line set, config file says no formatting
        log.info("%s/%s-%s" % \
                (self.options.category, self.vars['pn'],
        self.vars['pv']))
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

    def create_ebuild(self):
        """Write ebuild and update it after unpacking and examining ${S}"""
        # Need to write the ebuild first so we can unpack it and check for $S
        if self.write_ebuild(overwrite=self.options.overwrite):
            unpack_ebuild(self.ebuild_path)
            self.update_with_s()
            # Write ebuild again after unpacking and adding ${S}
            self.get_ebuild()
            # Run any tests if found
            #if self.has_tests:
            #    run_tests(self.ebuild_path)
            # We must overwrite initial skeleton ebuild
            self.write_ebuild(overwrite=True)
            self.print_ebuild()
            log.info("Your ebuild is here: " + self.ebuild_path)
        # If ebuild already exists, we don't unpack and get dependencies 
        # because they must exist.
        # We should add an option to force creating dependencies or should
        # overwrite be used?
        return self.requires

    def write_ebuild(self, overwrite=False):
        """Write ebuild file"""
        # Use command-line overlay if specified, else the one in .g-pyprc
        if self.options.overlay:
            overlay_name = self.options.overlay
            overlays = get_repo_names()
            if overlays.has_key(overlay_name):
                overlay_path = overlays[overlay_name]
            else:
                log.error("Couldn't find overylay/repository by that"+
                        " name. I know about these:")
                for repo in sorted(overlays.keys()):
                    log.error("  " + repo.ljust(18) + overlays[repo])
                sys.exit(1)
        else:
            overlay_path = self.config['overlay']
        ebuild_dir = make_overlay_dir(self.options.category, self.vars['pn'], \
                overlay_path)
        if not ebuild_dir:
            log.error("Couldn't create overylay ebuild directory.")
            sys.exit(2)
        self.ebuild_path = os.path.join(ebuild_dir, "%s.ebuild" % \
                self.vars['p'])
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

    def update_with_s(self):
        """Add ${S} to ebuild if needed"""
        #if self.options.subversion:
        #    return
        log.debug("Trying to determine ${S}, unpacking...")
        unpacked_dir = find_s_dir(self.vars['p'], self.options.category)
        if unpacked_dir == "":
            self.vars["s"] = "${WORKDIR}"
            return

        self.unpacked_dir = os.path.join(get_workdir(self.vars['p'],
            self.options.category), unpacked_dir)
        if unpacked_dir and unpacked_dir != self.vars['p']:
            if unpacked_dir == self.vars['my_p_raw']:
                unpacked_dir = '${MY_P}'
            elif unpacked_dir == self.vars['my_pn']:
                unpacked_dir = '${MY_PN}'
            elif unpacked_dir == self.vars['pn']:
                unpacked_dir = '${PN}'

            self.vars["s"] = "${WORKDIR}/%s" % unpacked_dir
