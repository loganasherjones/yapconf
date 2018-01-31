# -*- coding: utf-8 -*-

"""Top-level package for Yapconf."""
from yapconf.spec import YapconfSpec

yaml_support = True

try:
    import yaml
except ImportError:
    try:
        import ruamel.yaml as yaml
    except ImportError:
        yaml = None
        yaml_support = False

__author__ = """Logan Asher Jones"""
__email__ = 'loganasherjones@gmail.com'
__version__ = '0.0.1'


FILE_TYPES = ('json',)
if yaml_support:
    FILE_TYPES += ('yaml', )

__all__ = ['YapconfSpec']
