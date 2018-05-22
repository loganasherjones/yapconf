=======
History
=======

0.2.4 (2018-05-21)
------------------
* Flattened configs before loading (#54)
* Fixed bug where the ``fq_name`` was not correctly set for complex objects
* Added ``dump_kwargs`` to ``migrate_config`` (#53)
* Better error message when validation fails (#55)
* Made all argparse items optional (#42)
* Added support for ``long_description`` on config items (#44)
* Added support for ``validator`` on config items (#43)

0.2.3 (2018-04-03)
------------------
* Fixed Python2 unicode error (#41)

0.2.1 (2018-03-11)
0.2.2 (2018-03-28)
------------------
* Fixed Python2 compatibility error (#35)

0.2.1 (2018-03-11)
------------------
* Added item to YapconfItemNotFound (#21)
* Removed pytest-runner from setup_requires (#22)

0.2.0 (2018-03-11)
------------------

* Added auto kebab-case for CLI arguments (#7)
* Added the flag to apply environment prefixes (#11)
* Added ``choices`` to item specification (#14)
* Added ``alt_env_names`` to item specification (#13)

0.1.1 (2018-02-08)
------------------

* Fixed bug where ``None`` was a respected value.

0.1.0 (2018-02-01)
------------------

* First release on PyPI.
