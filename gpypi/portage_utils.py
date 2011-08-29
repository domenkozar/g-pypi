#!/usr/bin/env python
# pylint: disable-msg=C0301,W0613,W0612,C0103,E0611,W0511

"""

Various functions dealing with portage

"""

import sys
import os
import commands
import logging

from portage import config as portage_config
from portage import settings as portage_settings
try:
    # portage >= 2.2
    from portage import dep as portage_dep
except ImportError:
    # portage <= 2.1
    from portage import portage_dep

# TODO: find more clean way
sys.path.insert(0, "/usr/lib/gentoolkit/pym")
import gentoolkit
import gentoolkit.query

from gpypi.exc import *


log = logging.getLogger(__name__)
CONFIG = portage_config(clone=portage_settings)
ENV = CONFIG.environ()


class PortageUtils(object):
    """"""

    @classmethod
    def get_all_overlays(cls):
        """
        Return a dict of overlay names with their paths
        e.g.
        {'reponame': '/path/to/repo', ...}

        :returns: dict with repoman/paths

        """
        porttrees = [ENV['PORTDIR']] + \
            [os.path.realpath(t) for t in ENV["PORTDIR_OVERLAY"].split()]
        treemap = {}
        for path in porttrees:
            repo_name_path = os.path.join(path, 'profiles/repo_name')
            try:
                repo_name = open(repo_name_path, 'r').readline().strip()
                treemap[repo_name] = path
            except (OSError, IOError):
                log.warn("No '%s', skipping" % os.path.join(path, 'profiles/repo_name'))
        return treemap

    @classmethod
    def get_overlay_path(cls, overlay_name):
        """Return path mapped to overlay name.

        :param overlay_name: Name of the overlay
        :returns: Portage overlay path
        :rtype: string
        :raises: :exc:`gpypi.exc.GPyPiOverlayDoesNotExist`

        **Example:**
        """
        # TODO: example for local, main and third party overlay

        overlays = cls.get_all_overlays()
        if overlay_name in overlays:
            overlay_path = overlays[overlay_name]
        else:
            raise GPyPiOverlayDoesNotExist('"%s". Available: %s' \
                % (overlay_name, " ".join(overlays.keys())))
        return overlay_path

    @classmethod
    def get_installed_ver(cls, cpn):
        """
        Return PV for installed version of package

        :param cpn: cat/pkg-ver
        :type cpn: string
        :returns: string version or None if not pkg installed

        """
        try:
            #Return first version installed
            #XXX Log warning if more than one installed (SLOT)?
            pkg = gentoolkit.find_installed_packages(cpn, masked=True)[0]
            return pkg.get_version()
        except:
            return

    @classmethod
    def is_valid_atom(cls, atom):
        """
        Return True if atom is valid portage =category/pn-pv.

        :param atom: category/package-version
        :type atom: string
        :returns: bool

        **Example:**

        >>> PortageUtils.is_valid_atom('=dev-python/foobar-1.0')
        True
        >>> PortageUtils.is_valid_atom('=foobar-1.0')
        False

        """
        return bool(portage_dep.isvalidatom(atom))

    @classmethod
    def ebuild_exists(cls, cat_pkg):
        """
        Checks if an ebuild exists in portage tree or overlay

        :param cat_pkg: category/package_name
        :type cat_pkg: string
        :returns: bool

        **Example:**

        >>> PortageUtils.ebuild_exists('sys-devel/gcc')
        True

        """
        pkgs = gentoolkit.query.Query(cat_pkg).find()
        if len(pkgs):
            return True
        else:
            return False

    @classmethod
    def unpack_ebuild(cls, ebuild_path):
        """
        Use portage to unpack an ebuild.

        :param ebuild_path: full path to ebuild
        :type ebuild_path: string
        :returns: None if succeed, raises OSError if fails to unpack
        :raises: :exc:`gpypi.exc.GPyPiCouldNotUnpackEbuild`

        .. note::
            We are running "ebuild %s digest setup clean unpack" in bash
            subshell, since portage inner workings do not allow us to
            use Python API.

        """
        (status, output) = commands.getstatusoutput("ebuild %s digest setup clean unpack" % ebuild_path)
        if status:
            # Portage's error message, sometimes.
            # Couldn't determine PN or PV so we misnamed ebuild
            if 'does not follow correct package syntax' in output:
                log.error("Misnamed ebuild: %s" % ebuild_path)
                log.error("Try using -n or -v to force PN or PV")
                os.unlink(ebuild_path)
            raise GPyPiCouldNotUnpackEbuild(output)

    @classmethod
    def find_s_dir(cls, p, cat):
        """
        Try to get ${S} by determining what directories were unpacked

        :param p: portage ${P}
        :type p: string
        :param cat: valid portage category
        :type cat: string
        :returns: string with directory name if detected, empty string
                  if S=WORKDIR, None if couldn't find S

        """
        workdir = cls.get_workdir(p, cat)
        files = os.listdir(workdir)
        dirs = []
        for unpacked in files:
            if os.path.isdir(os.path.join(workdir, unpacked)):
                dirs.append(unpacked)
        if len(dirs) == 1:
            #Only one directory, must be it.
            return dirs[0]
        elif not len(dirs):
            #Unpacked in cwd
            return ""
        else:
            # TODO: Need to search whole tree for setup.py
            log.error("Can't determine ${S}")
            log.error("Unpacked multiple directories: %s" % dirs)

    @classmethod
    def get_workdir(cls, p, category):
        """
        Return WORKDIR

        :param p: portage ${P}
        :type p: string
        :param category: valid portage category
        :type category: string
        :returns: string of portage_tmpdir/cp

        **Example:**

        >>> PortageUtils.get_workdir('foobar-1.0', 'dev-python')
        u'/var/tmp/portage/dev-python/foobar-1.0/work'

        """
        return '%s/portage/%s/%s/work' % (cls.get_portage_tmpdir(), category, p)

    @classmethod
    def make_ebuild_dir(cls, category, pn, overlay):
        """
        Create directory(s) in overlay for ebuild.

        :param category: valid portage category
        :type category: string
        :param pn: :term:`PN`
        :type pn: string
        :param overlay: portage overlay directory
        :type overlay: string
        :returns: full directory name
        :rtype: string
        :raises: :exc:`gpypi.exc.GPyPiCouldNotCreateEbuildPath`

        **Example:**

        """
        ebuild_dir = os.path.join(overlay, category, pn)
        if not os.path.isdir(ebuild_dir):
            try:
                os.makedirs(ebuild_dir)
            except OSError, err:
                raise GPyPiCouldNotCreateEbuildPath(err)
        return ebuild_dir

    @classmethod
    def get_portage_tmpdir(cls):
        """Return PORTAGE_TMPDIR from /etc/make.conf
        """
        return ENV["PORTAGE_TMPDIR"]

    @classmethod
    def get_portdir(cls):
        """Return PORTDIR from /etc/make.conf
        """
        return ENV["PORTDIR"]

    @classmethod
    def get_keyword(cls):
        """Return ARCH from portage environment or None
        """
        arch = ENV.get('ARCH', None)

        if arch and not arch.startswith('~'):
            arch = "~%s" % arch
        return arch
