=======
Yapconf
=======


.. image:: https://img.shields.io/pypi/v/yapconf.svg
        :target: https://pypi.python.org/pypi/yapconf

.. image:: https://img.shields.io/travis/loganasherjones/yapconf.svg
        :target: https://travis-ci.org/loganasherjones/yapconf

.. image:: https://codecov.io/gh/loganasherjones/yapconf/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/loganasherjones/yapconf

.. image:: https://readthedocs.org/projects/yapconf/badge/?version=latest
        :target: https://yapconf.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://pyup.io/repos/github/loganasherjones/yapconf/shield.svg
     :target: https://pyup.io/repos/github/loganasherjones/yapconf/
     :alt: Updates


Yet Another Python Configuration. A simple way to manage configurations for python applications.


Yapconf allows you to easily manage your python application's configuration. It handles everything involving your
application's configuration. Often times exposing your configuration in sensible ways can be difficult. You have to
consider loading order, and lots of boilerplate code to update your configuration correctly. Now what about CLI
support? Migrating old configs to the new config? Yapconf can help you.


Features
--------
Yapconf helps manage your python application's configuration

* JSON/YAML config file support
* Argparse integration
* Environment Loading
* Bootstrapping
* Migrate old configurations to new configurations


Quick Start
-----------

To install Yapconf, run this command in your terminal:

.. code-block:: console

    $ pip install yapconf

Then you can use Yapconf yourself!

.. code-block:: python

    from yapconf import YapconfSpec

    # First define a specification
    my_spec = YapconfSpec({"foo": {"type": "str", "default": "bar"}}, env_prefix='MY_APP_')

    # Then load the configuration in whatever order you want!
    # load_config will automatically look for the 'foo' value in
    # '/path/to/config.yml', then the environment, finally
    # falling back to the default if it was not found elsewhere
    config = my_spec.load_config('/path/to/config.yml', 'ENVIRONMENT')

    print(config.foo)
    print(config['foo'])

You can also add these arguments to the command line very easily

.. code-block:: python

    import argparse

    parser = argparse.ArgumentParser()

    # This will add --foo as an argument to your python program
    my_spec.add_arguments(parser)

    cli_args = vars(parser.parse_args(sys.argv[1:]))

    # Now you can load these via load_config:
    config = my_spec.load_config(cli_args, '/path/to/config.yml', 'ENVIRONMENT')

For more detailed information and better walkthroughs, checkout the documentation!

Documentation
-------------
Documentation is available at https://yapconf.readthedocs.io


Credits
---------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

