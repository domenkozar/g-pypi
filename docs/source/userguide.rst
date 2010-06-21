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
Gentoo developers life easier. It's usage should be pretty
self explainatory through command's help::

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


.. warning::
    
    Root login must be used for populating overlays and unpacking ebuilds.
