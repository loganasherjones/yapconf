# -*- coding: utf-8 -*-
"""Top-level package for Yapconf."""
import json
import re
import sys

import packaging.version
import six
from box import Box

if six.PY3:
    from collections.abc import MutableMapping

    unicode = str
else:
    from collections import MutableMapping
    from io import open

# Setup feature flags for use throughout the package.
yaml_support = True
etcd_support = True
kubernetes_support = True
redis_support = True
json_encode_support = True
if sys.version_info.major > 3 or (
    sys.version_info.major == 3 and sys.version_info.minor >= 9
):
    json_encode_support = False

try:
    # We set safe_load, to be load because otherwise ruamel.yaml
    # will throw warnings. Since we don't want that to happen, and
    # we want our code to be the same whether or not PyYaml or
    # ruamel.yaml is installed.
    import ruamel.yaml as yaml

    if packaging.version.parse(yaml.__version__) < packaging.version.parse("0.18.0"):
        # ruamel.yaml depricated support for safe_load in 0.17.0
        yaml.load = yaml.safe_load
    else:
        from ruamel.yaml import YAML

        yaml = YAML(typ="safe", pure=True)


except ImportError:
    try:
        import yaml
    except ImportError:
        yaml = None
        yaml_support = False

try:
    from etcd import client as etcd_client
except ImportError:
    etcd_client = None
    etcd_support = False


try:
    from kubernetes import client as kubernetes_client
except ImportError:
    kubernetes_client = None
    kubernetes_support = False

from yapconf.exceptions import YapconfError  # noqa: E402
from yapconf.spec import YapconfSpec  # noqa: E402

__author__ = """Logan Asher Jones"""
__email__ = "loganasherjones@gmail.com"
__version__ = "0.4.0"


FILE_TYPES = {
    "json",
}
SUPPORTED_SOURCES = {
    "dict",
    "environment",
    "json",
    "cli",
}
ALL_SUPPORTED_SOURCES = {
    "dict",
    "environment",
    "etcd",
    "json",
    "kubernetes",
    "yaml",
    "cli",
}

if yaml_support:
    FILE_TYPES.add("yaml")
    SUPPORTED_SOURCES.add("yaml")

if etcd_support:
    SUPPORTED_SOURCES.add("etcd")

if kubernetes_support:
    SUPPORTED_SOURCES.add("kubernetes")

__all__ = ["YapconfSpec", "dump_data"]


def change_case(s, separator="-"):
    """Changes the case to snake/kebab case depending on the separator.

    As regexes can be confusing, I'll just go through this line by line as an
    example with the following string: ' Foo2Boo_barBaz bat'

    1. Remove whitespaces from beginning/end. => 'Foo2Boo_barBaz bat-rat'
    2. Replace remaining spaces with underscores => 'Foo2Boo_barBaz_bat-rat'
    3. Add underscores before capital letters => 'Foo2_Boo_bar_Baz_bat-rat'
    4. Replace capital with lowercase => 'foo2_boo_bar_baz_bat-rat'
    5. Underscores & hyphens become the separator => 'foo2-boo-bar-baz-bat-rat'

    Args:
        s (str): The original string.
        separator: The separator you want to use (default '-' for kebab case).

    Returns:
        A snake_case or kebab-case (depending on separator)
    """
    s = s.strip()
    no_spaces = re.sub(" ", "_", s)
    add_underscores = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", no_spaces)
    lowercase = re.sub("([a-z0-9])([A-Z])", r"\1_\2", add_underscores).lower()
    return re.sub("[-_]", separator, lowercase)


def dump_data(
    data,
    filename=None,
    file_type="json",
    klazz=YapconfError,
    open_kwargs=None,
    dump_kwargs=None,
):
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

    open_kwargs = open_kwargs or {"encoding": "utf-8"}
    dump_kwargs = dump_kwargs or {}

    if filename:
        with open(filename, "w", **open_kwargs) as conf_file:
            _dump(data, conf_file, file_type, **dump_kwargs)
    else:
        _dump(data, sys.stdout, file_type, **dump_kwargs)


def _dump(data, stream, file_type, **kwargs):
    if not kwargs and file_type == "json":
        kwargs = {
            "sort_keys": True,
            "indent": 4,
            "ensure_ascii": False,
        }
    elif not kwargs and file_type == "yaml":
        kwargs = {"default_flow_style": False, "encoding": "utf-8"}

    if isinstance(data, Box):
        data = data.to_dict()

    if str(file_type).lower() == "json":
        dumped = json.dumps(data, **kwargs)
        if isinstance(dumped, unicode):
            stream.write(dumped)
        else:
            stream.write(six.u(dumped))
    elif str(file_type).lower() == "yaml":
        yaml.safe_dump(data, stream, **kwargs)
    else:
        raise NotImplementedError(
            "Someone forgot to implement dump for file " "type: %s" % file_type
        )


def load_file(
    filename,
    file_type="json",
    klazz=YapconfError,
    open_kwargs=None,
    load_kwargs=None,
):
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

    open_kwargs = open_kwargs or {"encoding": "utf-8"}
    load_kwargs = load_kwargs or {}

    data = None
    with open(filename, **open_kwargs) as conf_file:
        if str(file_type).lower() == "json":
            data = json.load(conf_file, **load_kwargs)
        elif str(file_type).lower() == "yaml":
            data = yaml.load(conf_file.read())
        else:
            raise NotImplementedError(
                "Someone forgot to implement how to load a %s file_type." % file_type
            )

    if not isinstance(data, dict):
        raise klazz(
            "Successfully loaded %s, but the result was not a dictionary." % filename
        )

    return data


def _check_file_type(file_type, klazz):
    if str(file_type).lower() == "yaml" and yaml is None:
        raise klazz(
            "You wanted to use a YAML file but the yaml module was "
            "not loaded. Please install the yaml dependency via `pip "
            "install yapconf[yaml]`."
        )

    if str(file_type).lower() not in FILE_TYPES:
        raise klazz(
            "Invalid file type %s. Valid file types are %s" % (file_type, FILE_TYPES)
        )


def flatten(dictionary, separator=".", prefix=""):
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
        if isinstance(value, MutableMapping):
            new_dict.update(flatten(value, separator, new_key))

        elif isinstance(value, list):
            new_value = []
            for item in value:
                if isinstance(item, MutableMapping):
                    new_value.append(flatten(item, separator, new_key))
                else:
                    new_value.append(item)
            new_dict[new_key] = new_value

        else:
            new_dict[new_key] = value

    return new_dict
