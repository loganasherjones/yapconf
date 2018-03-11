# -*- coding: utf-8 -*-

"""Top-level package for Yapconf."""
import re
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
__version__ = '0.2.0'


FILE_TYPES = ('json',)
if yaml_support:
    FILE_TYPES += ('yaml', )

__all__ = ['YapconfSpec']


def change_case(s, separator='-'):
    """Changes the case to snake/kebab case depending on the separator.

    As regexes can be confusing, I'll just go through this line by line as an
    example with the following string: ' Foo2Boo_barBaz bat'

    1. Remove whitespaces from beginning/end. => 'Foo2Boo_barBaz bat'
    2. Replace all remaining spaces with underscores => 'Foo2Boo_barBaz_bat'
    3. Add underscores before capital letters => 'Foo2_Boo_bar_Baz_bat'
    4. Replace capital with lowercase => 'foo2_boo_bar_baz_bat'
    5. Replace underscores with the separator => 'foo2-boo-bar-baz-bat'

    Args:
        s (str): The original string.
        separator: The separator you want to use (default '-' for kebab case).

    Returns:
        A snake_case or kebab-case (depending on separator)
    """
    s = s.strip()
    no_spaces = re.sub(' ', '_', s)
    add_underscores = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', no_spaces)
    snake_case = re.sub('([a-z0-9])([A-Z])', r'\1_\2', add_underscores).lower()
    return re.sub('_', separator, snake_case)
