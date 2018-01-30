# -*- coding: utf-8 -*-
import logging
import json
import six
import os

from box import Box
from yapconf import FILE_TYPES, yaml, yaml_support
from yapconf.exceptions import YapconfSpecError, YapconfLoadError, \
    YapconfItemNotFound
from yapconf.items import from_specification


class YapconfSpec(object):

    def __init__(self, specification, file_type='json', env_prefix=None,
                 encoding='utf-8', separator='.'):
        self._file_type = file_type
        self._encoding = encoding

        if self._file_type not in FILE_TYPES:
            raise YapconfSpecError('Unsupported file type: {0}.'
                                   'Supported file types are: {1}'
                                   .format(self._file_type, FILE_TYPES))

        self._specification = self._load_specification(specification)
        self._env_prefix = env_prefix
        self._separator = separator
        self._yapconf_items = from_specification(self._specification,
                                                 self._env_prefix,
                                                 self._separator)
        self._logger = logging.getLogger(__name__)

    def _load_specification(self, specification):
        if isinstance(specification, six.string_types):
            specification = self._load_file_to_dict(specification,
                                                    self._file_type,
                                                    YapconfSpecError)

        if not isinstance(specification, dict):
            raise YapconfSpecError('Specification must be a dictionary or a '
                                   'filename which contains a loadable '
                                   'dictionary. Supported file types are {0}'
                                   .format(FILE_TYPES))

        self._validate_specification(specification)
        return specification

    def _validate_specification(self, specification):
        for item_name, item_info in six.iteritems(specification):
            if not isinstance(item_info, dict):
                raise YapconfSpecError("Invalid specification. {0} is not a "
                                       "dictionary.".format(item_name))

            item_type = item_info.get('type', 'str')
            nested_items = item_info.get('items', {})
            if nested_items and item_type not in ['list', 'dict']:
                raise YapconfSpecError("Invalid specification. {0} is a {1} "
                                       "type item, but it has children. "
                                       "Maybe you meant to set type to either"
                                       "'list' or 'dict'?"
                                       .format(item_name, item_type))
            elif item_type in ['list', 'dict'] and not nested_items:
                raise YapconfSpecError("Invalid specification. {0} is a {1} "
                                       "type item, but it has no children. "
                                       "This is not allowed."
                                       .format(item_name, item_type))
            elif item_type in ['list', 'dict']:
                self._validate_specification(nested_items)

    @property
    def defaults(self):
        return {item.name: item.default
                for item in self._yapconf_items.values()}

    def add_arguments(self, parser, bootstrap=False):
        [item.add_argument(parser, bootstrap)
         for item in self._get_items(bootstrap=False)]

    def get_item(self, name, bootstrap=False):
        for item in self._get_items(bootstrap):
            if item.name == name:
                return item
        return None

    def update_defaults(self, new_defaults, respect_none=False):
        for key, value in six.iteritems(new_defaults):
            item = self.get_item(key)
            if item is None:
                raise YapconfItemNotFound("Cannot update default for {0}, "
                                          "there is no config item by the "
                                          "name of {1}".format(key, key))

            item.update_default(value, respect_none)

    def load_config(self, *args, **kwargs):
        bootstrap = kwargs.get('bootstrap', False)
        overrides = self._generate_overrides(*args)
        config = self._generate_config_from_overrides(overrides, bootstrap)
        return Box(config)

    def migrate_config_file(self, config_file_path,
                            always_update=False,
                            current_file_type=None,
                            output_file_name=None,
                            output_file_type=None,
                            create=True,
                            update_defaults=True):

        current_file_type = current_file_type or self._file_type
        output_file_type = output_file_type or self._file_type
        output_file_name = output_file_name or config_file_path

        current_config = self._get_config_if_exists(config_file_path,
                                                    create,
                                                    current_file_type)

        migrated_config = {}
        for item in self._yapconf_items.values():
            item.migrate_config(current_config, migrated_config,
                                always_update, update_defaults)

        if create:
            self._write_dict_to_file(migrated_config, output_file_name,
                                     output_file_type)

        return Box(migrated_config)

    def _get_config_if_exists(self, config_file_path, create, file_type):
        if not os.path.isfile(config_file_path) and create:
            return {}
        elif not os.path.isfile(config_file_path):
            raise YapconfLoadError("Error migrating config file {0}. "
                                   "File does not exist. If you would like "
                                   "to create the file, you need to pass "
                                   "the create flag.".format(config_file_path))
        else:
            return self._load_file_to_dict(config_file_path,
                                           file_type, YapconfLoadError)

    @staticmethod
    def _get_key_if_exists(config_dict, item):
        for name in item.possible_names:
            if name in config_dict:
                return name
        return None

    def _get_items(self, bootstrap):
        if not bootstrap:
            return self._yapconf_items.values()
        else:
            return [item for item in self._yapconf_items.values()
                    if item.bootstrap]

    def _generate_config_from_overrides(self, overrides, bootstrap):
        return {
            item.name: item.get_config_value(overrides) for item in
            self._get_items(bootstrap)
        }

    def _generate_overrides(self, *args):
        # An override is a tuple of label, dictionary
        # we cannot use a dictionary because we need to preserve
        # the order of the arguments passed in as they are significant
        overrides = []
        for index, override in enumerate(args):
            label, info = self._generate_override(index, override)
            overrides.append((label, info))
        return overrides

    def _generate_override(self, index, value):

        # If they provided a tuple, they may have named their tuple
        # or given us a differing file_type. So we unpack it before
        # we look at the unpacked value.
        if isinstance(value, tuple):
            if len(value) < 2:
                raise YapconfLoadError('Invalid override tuple provided. The '
                                       'tuple must have a name and value. '
                                       'Optionally, it can provide a third '
                                       'argument specifying the file type if '
                                       'it is different than the default '
                                       'file_type passed during '
                                       'initialization.')
            label = value[0]
            unpacked_value = value[1]
            file_type = self._file_type
            if len(value) > 2:
                file_type = value[2]

        else:
            label = None
            unpacked_value = value
            file_type = self._file_type

        if isinstance(unpacked_value, six.string_types):
            label = label or unpacked_value

            # Special String called "ENVIRONMENT" tells us to load
            # the override as the current environment. Otherwise
            # a string is a file name.
            if unpacked_value == 'ENVIRONMENT':
                override_dict = os.environ.copy()
            else:
                override_dict = self._load_file_to_dict(unpacked_value,
                                                        file_type,
                                                        YapconfLoadError)
        elif isinstance(unpacked_value, dict):
            label = label or "dict-{0}".format(index)
            override_dict = unpacked_value

        else:
            raise YapconfLoadError("Invalid override given: {0} Overrides "
                                   "must be either a dictionary or a filename."
                                   .format(unpacked_value))

        return label, override_dict

    def _write_dict_to_file(self, dictionary, filename, file_type):
        self._logger.debug("Writing config: {0}".format(dictionary))
        self._logger.debug("To ({0}) file: {1}".format(file_type, filename))

        if file_type == 'yaml' and not yaml_support:
            raise YapconfLoadError('Cannot output a YAML file because the '
                                   'yaml module was not loaded. Please '
                                   'install either PyYaml or ruamel.yaml')
        elif file_type not in FILE_TYPES:
            raise YapconfLoadError('Unsupported file type: {0}'
                                   .format(file_type))

        with open(filename, 'w', encoding=self._encoding) as conf_file:
            if file_type == 'json':
                json.dump(dictionary, conf_file, sort_keys=True, indent=4)
            elif file_type == 'yaml':
                yaml.dump(dictionary, conf_file)

    def _load_file_to_dict(self, filename, file_type, exc_clazz):
        # Loads file, validates that the file, after loading is a dict
        data = None

        if file_type == 'yaml' and not yaml_support:
            raise exc_clazz('You wanted to load a YAML file but '
                            'the yaml module was not loaded. Please '
                            'install either PyYaml or ruamel.yaml')
        elif file_type not in FILE_TYPES:
            raise exc_clazz('Unsupported file type: {0}'.format(file_type))

        with open(filename, encoding=self._encoding) as conf_file:
            if file_type == 'json':
                data = json.load(conf_file)
            elif file_type == 'yaml':
                data = yaml.load(conf_file.read())

        if not isinstance(data, dict):
            raise exc_clazz("File: {0} when parsed did not result "
                            "in a dictionary.".format(filename))
        return data
