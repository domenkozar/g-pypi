#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Configuration module

.. currentmodule:: gpypi2.config

"""

import os
import shutil
import logging
from ConfigParser import SafeConfigParser

from gpypi2.utils import asbool
from gpypi2.exc import *

# TODO: use Config.allowed_options in cli.py to avoid double information
# TODO: get rid of defaults in cli.py
# TODO: docs
log = logging.getLogger(__name__)
HERE = os.path.dirname(os.path.abspath(__file__))

class Config(dict):
    """Holds config values retrieved from various sources. Class
    also defines specification for supported options in :attr:`allowed_options`.

    Values are retrieved with help of validator methods.

    Example::

        >>> Config.from_pypi({'homepage': 'foobar'})
        <Config {'homepage': 'foobar'}>

    Attributes:

    :attr:`allowed_options` format::

        'name': ('Question ..', obj_type, default_value)

    """

    allowed_options = {
        'pn': ('Specify PN to use when naming ebuild', str, False),
        'pv': ('Specify PV to use when naming ebuild', str, False),
        'my_pv': ('Specify MY_PV used in ebuild', str, False),
        'my_pn': ('Specify MY_PN used in ebuild', str, False),
        'my_p': ('Specify MY_P used in ebuild', str, False),
        'uri': ('Specify SRC_URI of the package', str, False),
        'index_url': ('Base URL for PyPi', str, "http://pypi.python.org/pypi"),
        'overlay': ('Specify overlay to use by name (stored in $OVERLAY/profiles/repo_name)', str, "local"),
        'overwrite': ('Overwrite existing ebuild', bool, False),
        'no_deps': ("Don't create ebuilds for any needed dependencies", bool, False),
        'category': ("Specify portage category to use when creating ebuild", str, "dev-python"),
        'format': ("Format when printing to stdout (use pygments identifier)", str, "none"),
    }

    def __repr__(self):
        return "<Config %s>" % dict.__repr__(self)

    ##  from_config

    @classmethod
    def from_pypi(cls, metadata):
        return cls(metadata)

    @classmethod
    def from_ini(cls, path_to_ini, section='config'):
        """Retrieve dictionary from `path_to_ini` file, from `section`"""
        config = SafeConfigParser()
        config.read(path_to_ini)
        d = [lambda k, v: cls.validate(k, v), config.items(section).iteritems()]
        return cls(d)

    @classmethod
    def from_setup_py(cls, keywords):
        return cls(keywords)

    @classmethod
    def from_argparse(cls, options):
        return cls(options.__dict__)

    ## validate types

    @classmethod
    def validate(cls, name, value):
        """"""
        validator = cls.allowed_options[name][1]
        if isinstance(validator, type):
            f = getattr(cls, 'validate_%s' % validator.__name__)
        else:
            f = getattr(cls, 'validate_%s' % validator)
        return f(value)

    @classmethod
    def validate_bool(cls, value):
        """"""
        try:
            return asbool(value)
        except ValueError:
            raise GPyPiValidationError("Not a boolean (write y/n): %r" % value)

    @classmethod
    def validate_str(cls, value):
        """"""
        if isinstance(value, basestring):
            if isinstance(value, str):
                value = unicode(value, 'utf-8')
            return value
        else:
            raise GPyPiValidationError("Not a string: %r" % value)


class ConfigManager(object):
    """Holds multiple :class:`Config` instances and retrieves
    values from them.

    Example::

        >>> mgr = ConfigManager(['pypi', 'setup_py'])
        >>> mgr.configs['pypi'] = (Config.from_pypi({}))
        >>> mgr.configs['setup_py'] = (Config.from_setup_py({'overlay': 'foobar'}))
        >>> print mgr.overlay
        foobar

    :param use: Order of configuration taken in account
    :type use: list of strings
    :param questionnaire_options: What options will not use default if not
        given, but rather invoke interactive :class:`Questionnaire`
    :type questionnaire_options: list of strings
    :param questionnaire_class: class to be used for questionnaire,
        defaults to :class:`Questionnaire`
    :type questionnaire_class: class
    :raises: :exc:`gpypi2.exc.GPyPiConfigurationError` when:
        * no config is set
        * when option is retrieved that does not exist in :attr:`Config.allowed_options`
        * `use` does not have unique elements

    Attributes:

    :attr:`INI_TEMPLATE_PATH` -- Absolute path to .ini template file

    """
    INI_TEMPLATE_PATH = os.path.join(HERE, 'templates', 'gpypi2.config')

    def __init__(self, use, questionnaire_options=None, questionnaire_class=None):
        for config in use:
            if use.count(config) != 1:
                raise GPyPiConfigurationError("ConfigManager could not be setup"
                    ", config order has non-unique member: %s" % config)
        self.use = use
        self.questionnaire_options =  questionnaire_options or []
        self.q = (questionnaire_class or Questionnaire)()
        self.configs = {}

    def __repr__(self):
        return "<ConfigManager configs(%s) use(%s)>" % (self.configs.keys(), self.use)

    def __getattr__(self, name):
        if not self.configs:
            raise GPyPiConfigurationError("At least one config file must be used.")

        if name not in Config.allowed_options:
            raise GPyPiConfigurationError("No such option in Config.allowed_options: %s" % name)

        for config_name in self.use:
            value = self.configs.get(config_name, {}).get(name, None)
            log.debug("Got %r from %s", value, config_name)

            if value is not None:
                return value
            else:
                continue

        return self.default_or_question(name)

    def default_or_question(self, name):
        """"""
        if name in self.questionnaire_options:
            return self.q.ask(name)
        else:
            return Config.allowed_options[name][2]

    @classmethod
    def load_from_ini(cls, path_to_ini, section="config_manager"):
        """"""
        if not os.path.exists(path_to_ini):
            shutil.copy(cls.INI_TEMPLATE_PATH, path_to_ini)
            log.info('Config was generated at %s', path_to_ini)

        config = SafeConfigParser()
        config.read(path_to_ini)
        config_mgr = dict(config.items(section))

        use = config_mgr.get('use', '').split()
        q_options = config_mgr.get('questionnaire_options', '').split()
        return cls(use, q_options)


class Questionnaire(object):
    """"""
    IS_FIRST_QUESTION = True

    def ask(self, name, input_f=raw_input):
        """"""
        # TODO: colors and --nocolors
        if self.IS_FIRST_QUESTION:
            self.print_help()

        option = Config.allowed_options[name]
        answer = input_f("%s [%r]: " % (option[0].title(), option[2]))
        if not answer:
            answer = option[2]

        try:
            return Config.validate(name, answer)
        except GPyPiValidationError, e:
            log.error(e)
            return self.ask(name, input_f)

    def print_help(self):
        """"""
        log.info("You are using interactive mode for configuration.")
        log.info("Answer questions with configuration value or press enter")
        log.info("to use default value printed in brackets.")

        self.IS_FIRST_QUESTION = False
