.. highlight:: bash

User Guide
##########

Installation
**************

Stable version
----------------

The most recommended way of installing :command:`gpypi` is through portage.
Portage will handle all of dependencies and make sure you install stable version.

::
    
    # sudo emerge -av gpypi

Download and install directly through :term:`PyPi`::

    $ sudo easy_install gpypi

or::

    $ sudo pip install gpypi


Development version
---------------------------

::

    $ sudo pip install https://github.com/iElectric/g-pypi/zipball/master

or::

    $ sudo easy_install https://github.com/iElectric/g-pypi/zipball/master


Getting started
***************

:command:`gpypi` is a command line tool with vision to make
Gentoo developers life easier. To create an ebuild and its dependencies::

    $ sudo gpypi create --overlay sunrise pylons
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

    $ sudo gpypi -h
    usage: gpypi [-h] [-v] {create,sync,install,echo} ...

    Builds ebuilds from PyPi.

    optional arguments:
      -h, --help            show this help message and exit
      -v, --version

    commands:
      {create,sync,install,echo}
        create              Write ebuild and it's dependencies to an overlay
        echo                Echo ebuild to stdout
        install             Install ebuild and it's dependencies
        sync                Populate all packages from pypi into an overlay


and most of the time one will use the :command:`gpypi create` command::

    $ sudo gpypi create -h
    usage: gpypi create [-h] [-P PN] [-V PV] [--MY-PV MY_PV] [--MY-PN MY_PN]
                         [--MY-P MY_P] [--homepage HOMEPAGE] [--keywords KEYWORDS]
                         [--license LICENSE] [--description DESCRIPTION]
                         [--long-description LONG_DESCRIPTION] [-u URI]
                         [-i INDEX_URL] [--nocolors] [--config-file CONFIG_FILE]
                         [-q | -d] [-l OVERLAY_NAME] [-o] [--no-deps]
                         [-c CATEGORY] [--metadata-disable]
                         [--metadata-disable-echangelog-user]
                         [--metadata-herd METADATA_HERD]
                         [--metadata-maintainer-description METADATA_MAINTAINER_DESCRIPTION]
                         [--metadata-maintainer-email METADATA_MAINTAINER_EMAIL]
                         [--metadata-maintainer-name METADATA_MAINTAINER_NAME]
                         [--echangelog-disable]
                         [--echangelog-message ECHANGELOG_MESSAGE]
                         [--repoman-commands REPOMAN_COMMANDS]
                         package name [package version]

    Write ebuild and it's dependencies to an overlay

    positional arguments:
      package name
      package version

    optional arguments:
      -h, --help            show this help message and exit
      -P PN, --PN PN        Specify PN to use when naming ebuild
      -V PV, --PV PV        Specify PV to use when naming ebuild
      --MY-PV MY_PV         Specify MY_PV used in ebuild
      --MY-PN MY_PN         Specify MY_PN used in ebuild
      --MY-P MY_P           Specify MY_P used in ebuild
      --homepage HOMEPAGE   Homepage of the package
      --keywords KEYWORDS   Portage keywords for ebuild masking
      --license LICENSE     Portage license for the ebuild
      --description DESCRIPTION
                            Short description of the package
      --long-description LONG_DESCRIPTION
                            Long description of the package
      -u URI, --uri URI     Specify SRC_URI of the package
      -i INDEX_URL, --index-url INDEX_URL
                            Base URL for PyPi
      --nocolors            Disable colorful output
      --config-file CONFIG_FILE
                            Absolute path to a config file
      -q, --quiet           Show less output.
      -d, --debug           Show debug information.
      -l OVERLAY_NAME, --overlay OVERLAY_NAME
                            Specify overlay to use by name (stored in
                            $OVERLAY/profiles/repo_name)
      -o, --overwrite       Overwrite existing ebuild
      --no-deps             Don't create ebuilds for any needed dependencies
      -c CATEGORY, --category CATEGORY
                            Specify portage category to use when creating ebuild

    Workflow control:
      Generate metadata, manifest, changelog ...

      --metadata-disable    Disable metadata generation
      --metadata-disable-echangelog-user
                            Don't use ECHANGELOG_USER
      --metadata-herd METADATA_HERD
                            Herd for ebuild metadata
      --metadata-maintainer-description METADATA_MAINTAINER_DESCRIPTION
                            Maintainer descriptions for ebuild metadata (comma
                            separated)
      --metadata-maintainer-email METADATA_MAINTAINER_EMAIL
                            Maintainer emails for ebuild metadata (comma
                            separated)
      --metadata-maintainer-name METADATA_MAINTAINER_NAME
                            Maintainer names for ebuild metadata (comma separated)
      --echangelog-disable  Disable echangelog
      --echangelog-message ECHANGELOG_MESSAGE
                            Echangelog commit message
      --repoman-commands REPOMAN_COMMANDS
                            List of repoman commands to issue on each ebuild
                            (separated by space)


Creating ebuild from source of Python package with distutils
****************************************************************

:mod:`gpypi` supports not also querying :term:`PyPi` but also creating an ebuild with
help of distutils. Configuration is done when you first run :mod:`gpypi`. ``cd`` to
your package and just do::

    python setup.py sdist_ebuild


.. _configuration:

Configuration
**************************

.. currentmodule:: gpypi.config
.. highlight:: ini

:mod:`gpypi` offers configuration based on multiple sources. Currently supported sources are: :meth:`Config.from_pypi`, :meth:`Config.from_setup_py`, :meth:`Config.from_argparse` and :meth:`Config.from_ini`.

Configuration API lets you choose what source is used and what priority it has relative to other source providers. Here is a complete list of supported configuration options that :class:`Config` can provide:

.. literalinclude:: ../../gpypi/config.py
    :language: python
    :start-after: allowed_options = {
    :end-before: }

.. todo:: write a reST table

:class:`Config` is basically a `dict` with few additional classmethods for validation and source processing. Each :class:`Config` represents configuration values retrieved from specific source.

:class:`ConfigManager` is a class that handles multiple :class:`Config` instances. When a value is retrieved from :class:`ConfigManager`, it is loaded from :class:`Config` instances located in :attr:`ConfigManager.configs` `(dict)`. Order is specified as ``use`` parameter to :class:`ConfigManager`.


When :mod:`gpypi` is first time used, it will create ``.ini`` configuration file at ``/etc/gpypi``. Further usage will load the file with :meth:`ConfigManager.load_from_ini`. Default configuration file will look something like this::


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

Most of :attr:`ConfigManager.configs` are populated in :mod:`gpypi.cli` module.

.. note::
    
    For example usage of classes, following linked API definition.
