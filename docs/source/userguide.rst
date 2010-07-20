.. highlight:: console

User Guide
##########

Installation
**************

Stable version
----------------

The most recommended way of installing :command:`gpypi2` is through portage.
Portage will handle all of dependencies and make sure you install stable version.

::
    
    # sudo emerge -av gpypi2

Download and install directly through :term:`PyPi`::

    $ sudo easy_install gpypi2

or::

    $ sudo pip install gpypi2


Development version
---------------------------

::

    $ sudo pip install http://bitbucket.org/iElectric/g-pypi2/get/tip.zip

or::

    $ sudo easy_install http://bitbucket.org/iElectric/g-pypi2/get/tip.zip


Getting started
***************

:command:`gpypi2` is a command line tool with vision to make
Gentoo developers life easier. To create an ebuild and its dependencies::

    $ sudo gpypi2 create --overlay sunrise pylons
    * Generating ebuild: Jinja2 2.5
    * Your ebuild is here: /usr/local/portage/dev-python/jinja2/jinja2-2.5.ebuild
    * Dependency needed: Babel
    * Generating ebuild: Babel 0.9.5
    * Your ebuild is here: /usr/local/portage/dev-python/babel/babel-0.9.5.ebuild
    * Dependency needed: pytz
    * Generating ebuild: pytz 2010h
    * Your ebuild is here: /usr/local/portage/dev-python/pytz/pytz-2010h.ebuild

.. warning::
    
    Root login must be used for populating overlays and unpacking ebuilds.

Usage should be pretty self explanatory through help::

    $ sudo gpypi2 -h
    usage: gpypi2 [-h] {create,echo} ...

    optional arguments:
      -h, --help     show this help message and exit

    commands:
      {create,echo}
        create       Write ebuild to an overlay.
        echo         Echo ebuild to stdout.

and most of the time one will use the :command:`pypi2 create` command::

    $ sudo gpypi2 create -h
    usage: gpypi2 create [-h] [-P PN] [-V PV] [--MY_PV MY_PV] [--MY_PN MY_PN]
                         [--MY_P MY_P] [-u URI] [-q] [-d] [-v] [--nocolor]
                         [-l OVERLAY_NAME] [-o] [--no-deps] [-c CATEGORY] [-p]
                         package [version]

    positional arguments:
      package
      version

    optional arguments:
      -h, --help            show this help message and exit
      -P PN, --PN PN        Specify PN to use when naming ebuild.
      -V PV, --PV PV        Specify PV to use when naming ebuild.
      --MY_PV MY_PV         Specify MY_PV
      --MY_PN MY_PN         Specify MY_PN
      --MY_P MY_P           Specify MY_P
      -u URI, --uri URI     Specify URI of package if PyPI doesn't have it.
      -q, --quiet           Show less output.
      -d, --debug           Show debug information.
      -v, --version
      --nocolor
      -l OVERLAY_NAME, --overlay OVERLAY_NAME
                            Specify overy to use by name
                            ($OVERLAY/profiles/repo_name)
      -o, --overwrite       Overwrite existing ebuild.
      --no-deps             Don't create ebuilds for any needed dependencies.
      -c CATEGORY, --portage-category CATEGORY
                            Specify category to use when creating ebuild. Default
                            is dev-python
      -p, --pretend         Print ebuild to stdout, don't write ebuild file, don't
                            download SRC_URI.

.. _configuration:

Configuration
**************************

.. currentmodule:: gpypi2.config
.. highlight:: ini

:mod:`gpypi2` offers configuration based on multiple sources. Currently supported sources are: :meth:`Config.from_pypi`, :meth:`Config.from_setup_py`, :meth:`Config.from_argparse` and :meth:`Config.from_ini`.

Configuration API lets you choose what source is used and what priority it has relative to other source providers. Here is a complete list of supported configuration options that :class:`Config` can provide:

.. literalinclude:: ../../gpypi2/config.py
    :language: python
    :start-after: allowed_options = {
    :end-before: }

.. todo:: write a reST table

:class:`Config` is basically a `dict` with few additional classmethods for validation and source processing. Each :class:`Config` represents configuration values retrieved from specific source.

:class:`ConfigManager` is a class that handles multiple :class:`Config` instances. When a value is retrieved from :class:`ConfigManager`, it is loaded from :class:`Config` instances located in :attr:`ConfigManager.configs` `(dict)`. Order is specified as ``use`` parameter to :class:`ConfigManager`.


When :mod:`gpypi2` is first time used, it will create ``.ini`` configuration file at ``/etc/gpypi2``. Further usage will load the file with :meth:`ConfigManager.load_from_ini`. Default configuration file will look something like this::


    [config]
    # main option defaults go here:
    # overlay = Personal
    # ...

    [config_manager]
    # list the order of configurations
    use = argparse ini pypi setup_py
    # list of what options will invoke interactive questions when missing
    questionnaire_options = overlay

You will notice the ``use`` parameter in ``config_manager`` section. As already said, it specifies what :class:`Config` sources are used and in what order. ``config_manager`` section is loaded on :meth:`ConfigManager.load_from_ini` call, creating the :class:`ConfigManager` instance.

``config`` section is used as ``ini`` source provider, populated by :class:`Config.from_ini` also called in :class:`ConfigManager.load_from_ini`. Another non-foobared example of configuration file::

    [config]
    format = html
    overlay = iElectric
    index_url = http://eggs.mycompany.com

    [config_manager]
    use = pypi ini argparse
    questionnaire_options = uri category

The last option not yet mentioned is ``questionnaire_options``. The question is, what happens when none of :class:`Config` sources provide the config value we need? The behavior is specified with ``questionnaire_options``. If configuration option is listed in ``questionnaire_options``, :class:`Questionnaire` is used to interactively request developer for input through shell. Otherwise, default is used (specified in :attr:`Config.allowed_options` tuple).

Most of :attr:`ConfigManager.configs` are populated in :mod:`gpypi2.cli` module.

.. note::
    
    For example usage of classes, following linked API definition.
