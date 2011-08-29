#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This module implements Gentoo developers workflows::

    # repoman QA
    # metadata generation
    # manifest calculation
    # echangelog population

"""

import os
import logging
from subprocess import Popen, PIPE, STDOUT

from metagen import metagenerator
from metagen.main import parse_echangelog_variable

# TODO: depend on gentoolkit-dev and metagen
# TODO: cleanup on failures
# TODO: argparse params
log = logging.getLogger(__name__)


class Workflow(object):
    """Abstract class for workflow actions.

    :param config_manager: Options to be used
    :type config_manager: :class:`gpypi.config.ConfigManager` instance
    :param ebuild_dir: Path to ebuilds directory
    :type ebuild_dir: string

    """

    def __init__(self, config_manager, ebuild_dir):
        self.options = config_manager
        self.path = ebuild_dir

    def __call__(self):
        """"""
        raise NotImplemented

    def command(self, cmd):
        """Execute command in a subshell

        :param cmd: Command to execute
        :type cmd: string
        :returns: If return code was 0
        :rtype: bool

        """
        self.p = Popen(cmd.split(), cwd=self.path, stderr=STDOUT, stdout=PIPE)
        self.output = self.p.communicate()[0]
        if self.p.returncode == 0:
            return True
        else:
            log.error('Error while running $(%s):', cmd)
            log.error(self.output)
            return False


class Metadata(Workflow):
    """Class for generating metadata.xml file by metagen. Supports:

    * herds
    * maintainers
    * long description

    """

    def __call__(self):
        """"""
        if self.options.metadata_disable:
            log.warning('Skipping metadata.xml ...')
            return
        metadata = metagenerator.MyMetadata()

        if self.options.metadata_herd:
            herds = self.options.metadata_herd.split(",")
        else:
            herds = ["no-herd"]
        metadata.set_herd(herds)

        if self.options.metadata_use_echangelog_user:
            (name, email) = parse_echangelog_variable(
                self.options.metadata_maintainer_name,
                self.options.metadata_maintainer_email)
        else:
            (name, email) = self.options.metadata_maintainer_name, self.options.metadata_maintainer_email

        if email:
            names, descs = [], []
            if name:
                names = name.split(",")
            if self.options.metadata_maintainer_description:
                descs = self.options.metadata_maintainer_description.split(",")
            metadata.set_maintainer(email.split(","), names, descs)

        metadata.set_longdescription(self.options.long_description)

        filename = os.path.join(self.path, 'metadata.xml')
        if os.path.exists(filename):
            log.warning('metadata.xml already exists.')
            return

        f = open(filename, 'w')
        try:
            f.write(str(metadata))
        finally:
            f.close()
            log.info('Added metadata.xml file')


class Echangelog(Workflow):
    """Update changelog by echangelog."""

    def __call__(self):
        """"""
        if self.options.echangelog_disable:
            log.warning('Skipping echangelog...')
            return
        # TODO: add files to SCM
        msg = self.options.echangelog_message
        if self.command('echangelog %s' % msg):
            log.info('Created echangelog: %s', msg)


class Repoman(Workflow):
    """Run repoman with atleast manifest command."""

    def __call__(self):
        """"""
        if self.command('repoman %s' % self.options.repoman_commands):
            if 'manifest' in self.options.repoman_commands:
                log.info('Updated manifest file')
            # TODO: output
