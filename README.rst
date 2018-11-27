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
* Etcd config support
* Kubernetes ConfigMap support
* Argparse integration
* Environment Loading
* Configuration watching
* Migrate old configurations to new configurations
* Generate documentation for your configuration


Quick Start
-----------

To install Yapconf, run this command in your terminal:

.. code-block:: console

    $ pip install yapconf

Then you can use Yapconf yourself!


**Load your first config**

.. code-block:: python

    from yapconf import YapconfSpec

    # First define a specification
    spec_def = {
        "foo": {"type": "str", "default": "bar"},
    }
    my_spec = YapconfSpec(spec_def)

    # Now add your source
    my_spec.add_source('my yaml config', 'yaml', filename='./config.yaml')

    # Then load the configuration!
    config = my_spec.load_config('config.yaml')

    print(config.foo)
    print(config['foo'])

In this example ``load_config`` will look for the 'foo' value in the file
./config.yaml and will fall back to the default from the specification
definition ("bar") if it's not found there.

Try running with an empty file at ./config.yaml, and then try running with

.. code-block:: yaml
   :caption: config.yaml:

   foo: baz


**Load from Environment Variables**

.. code-block:: python

    from yapconf import YapconfSpec

    # First define a specification
    spec_def = {
        "foo-dash": {"type": "str", "default": "bar"},
    }
    my_spec = YapconfSpec(spec_def, env_prefix='MY_APP_')

    # Now add your source
    my_spec.add_source('env', 'environment')

    # Then load the configuration!
    config = my_spec.load_config('env')

    print(config.foo)
    print(config['foo'])

In this example ``load_config`` will look for the 'foo' value in the
environment and will fall back to the default from the specification
definition ("bar") if it's not found there.

Try running once, and then run ``export MY_APP_FOO_DASH=BAZ`` in the shell
and run again.

Note that the name yapconf is searching the environment for has been modified.
The env_prefix ``MY_APP_`` as been applied to the name, and the name itself has
been capitalized and converted to snake-case.


**Load from CLI arguments**

.. code-block:: python

    import argparse
    from yapconf import YapconfSpec

    # First define a specification
    spec_def = {
        "foo": {"type": "str", "default": "bar"},
    }
    my_spec = YapconfSpec(spec_def)

    # This will add --foo as an argument to your python program
    parser = argparse.ArgumentParser()
    my_spec.add_arguments(parser)

    # Now you can load these via load_config:
    cli_args = vars(parser.parse_args(sys.argv[1:]))
    config = my_spec.load_config(cli_args)

    print(config.foo)
    print(config['foo'])


**Load from multiple sources**

.. code-block:: python

    from yapconf import YapconfSpec

    # First define a specification
    spec_def = {
        "foo": {"type": "str", "default": "bar"},
    }
    my_spec = YapconfSpec(spec_def, env_prefix='MY_APP_')

    # Now add your sources (order does not matter)
    my_spec.add_source('env', 'environment')
    my_spec.add_source('my yaml file', 'yaml', filename='./config.yaml')

    # Now load your configuration using the sources in the order you want!
    config = my_spec.load_config('my yaml file', 'env')

    print(config.foo)
    print(config['foo'])

In this case ``load_config`` will look for 'foo' in ./config.yaml. If not
found it will look for ``MY_APP_FOO`` in the environment, and if stil not
found it will fall back to the default.
Since the 'my yaml file' label comes first in the load_config arguments
yapconf will look there for values first, even though add_source was
called with 'env' first.


**Watch your config for changes**

.. code-block:: python

    def my_handler(old_config, new_config):
        print("TODO: Something interesting goes here.")

    my_spec.spawn_watcher('config.yaml', target=my_handler)


**Generate documentation for your config**

.. code-block:: python

    # Show me some sweet Markdown documentation
    my_spec(spec.generate_documentation())

    # Or write it to a file
    spec.generate_documentation(output_file_name='configuration_docs.md')


For more detailed information and better walkthroughs, checkout the documentation!

Documentation
-------------
Documentation is available at https://yapconf.readthedocs.io


Credits
---------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

