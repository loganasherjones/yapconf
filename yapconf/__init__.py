# -*- coding: utf-8 -*-

"""Top-level package for Yapconf."""
import collections
import json
import re
import sys

import six

from yapconf.exceptions import YapconfError
from yapconf.spec import YapconfSpec

if sys.version_info.major < 3:
    from io import open
elif sys.version_info.major == 3:
    unicode = str

yaml_support = True

try:
    # We set safe_load, to be load because otherwise ruamel.yaml
    # will throw warnings. Since we don't want that to happen, and
    # we want our code to be the same whether or not PyYaml or
    # ruamel.yaml is installed.
    import ruamel.yaml as yaml
    yaml.load = yaml.safe_load
except ImportError:
    try:
        import yaml
    except ImportError:
        yaml = None
        yaml_support = False

__author__ = """Logan Asher Jones"""
__email__ = 'loganasherjones@gmail.com'
__version__ = '0.2.4'


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


def dump_data(data,
              filename=None,
              file_type='json',
              klazz=YapconfError,
              open_kwargs=None,
              dump_kwargs=None):
    """Dump data given to file or stdout in file_type.

    Args:
        data (dict): The dictionary to dump.
        filename (str, optional): Defaults to None. The filename to write
        the data to. If none is provided, it will be written to STDOUT.
        file_type (str, optional): Defaults to 'json'. Can be any of
        yapconf.FILE_TYPES
        klazz (optional): Defaults to YapconfError a special error to throw
        when something goes wrong.
        open_kwargs (dict, optional): Keyword arguments to open.
        dump_kwargs (dict, optional): Keyword arguments to dump.
    """

    _check_file_type(file_type, klazz)

    open_kwargs = open_kwargs or {'encoding': 'utf-8'}
    dump_kwargs = dump_kwargs or {}

    if filename:
        with open(filename, 'w', **open_kwargs) as conf_file:
            _dump(data, conf_file, file_type, **dump_kwargs)
    else:
        _dump(data, sys.stdout, file_type, **dump_kwargs)


def _dump(data, stream, file_type, **kwargs):
    if not kwargs and file_type == 'json':
        kwargs = {
            'sort_keys': True,
            'indent': 4,
            'ensure_ascii': False,
        }
    elif not kwargs and file_type == 'yaml':
        kwargs = {
            'default_flow_style': False,
            'encoding': 'utf-8'
        }

    if str(file_type).lower() == 'json':
        dumped = json.dumps(data, **kwargs)
        if isinstance(dumped, unicode):
            stream.write(dumped)
        else:
            stream.write(six.u(dumped))
    elif str(file_type).lower() == 'yaml':
        yaml.dump(data, stream, **kwargs)
    else:
        raise NotImplementedError('Someone forgot to implement dump for file '
                                  'type: %s' % file_type)


def load_file(filename,
              file_type='json',
              klazz=YapconfError,
              open_kwargs=None,
              load_kwargs=None):
    """Load a file with the given file type.

    Args:
        filename (str): The filename to load.
        file_type (str, optional): Defaults to 'json'. The file type for the
        given filename. Supported types are ``yapconf.FILE_TYPES```
        klazz (optional): The custom exception to raise if something goes
        wrong.
        open_kwargs (dict, optional): Keyword arguments for the open call.
        load_kwargs (dict, optional): Keyword arguments for the load call.

    Raises:
        klazz: If no klazz was passed in, this will be the ``YapconfError``

    Returns:
        dict: The dictionary from the file.
    """

    _check_file_type(file_type, klazz)

    open_kwargs = open_kwargs or {'encoding': 'utf-8'}
    load_kwargs = load_kwargs or {}

    data = None
    with open(filename, **open_kwargs) as conf_file:
        if str(file_type).lower() == 'json':
            data = json.load(conf_file, **load_kwargs)
        elif str(file_type).lower() == 'yaml':
            data = yaml.safe_load(conf_file.read())
        else:
            raise NotImplementedError('Someone forgot to implement how to '
                                      'load a %s file_type.' % file_type)

    if not isinstance(data, dict):
        raise klazz('Successfully loaded %s, but the result was '
                    'not a dictionary.' % filename)

    return data


def _check_file_type(file_type, klazz):
    if str(file_type).lower() == 'yaml' and yaml is None:
        raise klazz('You wanted to use a YAML file but the yaml module was '
                    'not loaded. Please install the yaml dependency via `pip '
                    'install yapconf[yaml]`.')

    if str(file_type).lower() not in FILE_TYPES:
        raise klazz('Invalid file type %s. Valid file types are %s' %
                    (file_type, FILE_TYPES))


def flatten(dictionary, separator='.', prefix=''):
    """Flatten the dictionary keys are separated by separator

    Arguments:
        dictionary {dict} -- The dictionary to be flattened.

    Keyword Arguments:
        separator {str} -- The separator to use (default is '.'). It will
        crush items with key conflicts.
        prefix {str} -- Used for recursive calls.

    Returns:
        dict -- The flattened dictionary.
    """
    new_dict = {}
    for key, value in dictionary.items():
        new_key = prefix + separator + key if prefix else key
        if isinstance(value, collections.MutableMapping):
            new_dict.update(flatten(value, separator, new_key))

        elif isinstance(value, list):
            new_value = []
            for item in value:
                if isinstance(item, collections.MutableMapping):
                    new_value.append(flatten(item, separator, new_key))
                else:
                    new_value.append(item)
            new_dict[new_key] = new_value

        else:
            new_dict[new_key] = value

    return new_dict
