# -*- coding: utf-8 -*-
import logging
import os

import six

import yapconf
from box import Box
from yapconf.exceptions import (YapconfItemNotFound, YapconfLoadError,
                                YapconfSpecError)
from yapconf.items import from_specification, YapconfDictItem
from yapconf.sources import get_source


class YapconfSpec(object):
    """Object which holds your configuration's specification.

    The YapconfSpec item is the main interface into the yapconf package.
    It will help you load, migrate, update and add arguments for your
    application.

    Examples:
        >>> from yapconf import YapconfSpec

        First define a specification

        >>> my_spec = YapconfSpec(
        ...   {"foo": {"type": "str", "default": "bar"}},
        ...   env_prefix='MY_APP_'
        ... )

        Then load the configuration in whatever order you want!
        load_config will automatically look for the 'foo' value in
        '/path/to/config.yml', then the environment, finally
        falling back to the default if it was not found elsewhere

        >>> config = my_spec.load_config('/path/to/config.yml', 'ENVIRONMENT')
        >>> print(config.foo)
        >>> print(config['foo'])

    """

    def __init__(self, specification, file_type='json', env_prefix=None,
                 encoding='utf-8', separator='.'):
        self._file_type = file_type
        self._encoding = encoding

        if self._file_type not in yapconf.FILE_TYPES:
            raise YapconfSpecError(
                'Unsupported file type: {0}. Supported file types are: {1}'
                .format(self._file_type, yapconf.FILE_TYPES)
            )

        self._specification = self._load_specification(specification)
        self._env_prefix = env_prefix
        self._separator = separator
        self._yapconf_items = from_specification(self._specification,
                                                 self._env_prefix,
                                                 self._separator)
        self._logger = logging.getLogger(__name__)
        self._sources = {}

    def _load_specification(self, specification):
        if isinstance(specification, six.string_types):
            specification = yapconf.load_file(
                specification,
                file_type=self._file_type,
                klazz=YapconfSpecError
            )

        if not isinstance(specification, dict):
            raise YapconfSpecError(
                'Specification must be a dictionary or a filename which '
                'contains a loadable dictionary. Supported file types are {0}'
                .format(yapconf.FILE_TYPES)
            )

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
        """dict: All defaults for items in the specification."""
        return self._get_defaults(self._yapconf_items.values())

    def _get_defaults(self, items):
        defaults = {}
        for item in items:
            if isinstance(item, YapconfDictItem):
                defaults[item.name] = self._get_defaults(
                    item.children.values()
                )
            else:
                defaults[item.name] = item.default
        return defaults

    def add_arguments(self, parser, bootstrap=False):
        """Adds all items to the parser passed in.

        Args:
            parser (argparse.ArgumentParser): The parser to add all items to.
            bootstrap (bool): Flag to indicate whether you only want to mark
                bootstrapped items as required on the command-line.

        """
        [item.add_argument(parser, bootstrap)
         for item in self._get_items(bootstrap=False)]

    def add_source(self, label, source_type, **kwargs):
        """Add a source to the spec.

        Sources should have a unique label. This will help tracing where your
        configurations are coming from if you turn up the log-level.

        The keyword arguments are significant. Different sources require
        different keyword arguments. Required keys for each source_type are
        listed below, for a detailed list of all possible arguments, see the
        individual source's documentation.

        source_type: dict
            required keyword arguments:
                - data - A dictionary

        source_type: environment
            No required keyword arguments.

        source_type: etcd
            required keyword arguments:
                - client - A client from the python-etcd package.

        source_type: json
            required keyword arguments:
                - filename - A JSON file.
                - data - A string representation of JSON

        source_type: kubernetes
            required keyword arguments:
                - client - A client from the kubernetes package
                - name - The name of the ConfigMap to load

        source_type: yaml
            required keyword arguments:
                - filename - A YAML file.

        Args:
            label (str): A label for the source.
            source_type (str): A source type, available source types depend
            on the packages installed. See ``yapconf.ALL_SUPPORTED_SOURCES``
            for a complete list.

        """
        self._sources[label] = get_source(label, source_type, **kwargs)

    def get_item(self, name, bootstrap=False):
        """Get a particular item in the specification.

        Args:
            name (str): The name of the item to retrieve.
            bootstrap (bool): Only search bootstrap items

        Returns (YapconfItem):
            A YapconfItem if it is found, None otherwise.

        """
        for item in self._get_items(bootstrap):
            if item.name == name:
                return item
        return None

    def update_defaults(self, new_defaults, respect_none=False):
        """Update items defaults to the values in the new_defaults dict.

        Args:
            new_defaults (dict): A key-value pair of new defaults to be
                applied.
            respect_none (bool): Flag to indicate if ``None`` values should
                constitute an update to the default.

        """
        for key, value in six.iteritems(new_defaults):
            item = self.get_item(key)
            if item is None:
                raise YapconfItemNotFound("Cannot update default for {0}, "
                                          "there is no config item by the "
                                          "name of {1}".format(key, key), None)

            item.update_default(value, respect_none)

    def load_config(self, *args, **kwargs):
        """Load a config based on the arguments passed in.

        The order of arguments passed in as \*args is significant. It indicates
        the order of precedence used to load configuration values. Each
        argument can be a string, dictionary or a tuple. There is a special
        case string called 'ENVIRONMENT', otherwise it will attempt to load the
        filename passed in as a string.

        By default, if a string is provided, it will attempt to load the
        file based on the file_type passed in on initialization. If you
        want to load a mixture of json and yaml files, you can specify them
        as the 3rd part of a tuple.

        Examples:
            You can load configurations in any of the following ways:

            >>> my_spec = YapconfSpec({'foo': {'type': 'str'}})
            >>> my_spec.load_config('/path/to/file')
            >>> my_spec.load_config({'foo': 'bar'})
            >>> my_spec.load_config('ENVIRONMENT')
            >>> my_spec.load_config(('label', {'foo': 'bar'}))
            >>> my_spec.load_config(('label', '/path/to/file.yaml', 'yaml'))
            >>> my_spec.load_config(('label', '/path/to/file.json', 'json'))

            You can of course combine each of these and the order will be
            held correctly.

        Args:
            *args:
            **kwargs: The only supported keyword argument is 'bootstrap'
                which will indicate that only bootstrap configurations
                should be loaded.

        Returns:
            box.Box: A Box object which is subclassed from dict. It should
                behave exactly as a dictionary. This object is guaranteed to
                contain at least all of your required configuration items.

        Raises:
            YapconfLoadError: If we attempt to load your args and something
                goes wrong.
            YapconfItemNotFound: If an item is required but could not be found
                in the configuration.
            YapconfItemError: If a possible value was found but the type
                cannot be determined.
            YapconfValueError: If a possible value is found but during
                conversion, an exception was raised.
        """
        bootstrap = kwargs.get('bootstrap', False)
        overrides = self._generate_overrides(*args)
        config = self._generate_config_from_overrides(overrides, bootstrap)
        return Box(config)

    def migrate_config_file(
        self,
        config_file_path,
        always_update=False,
        current_file_type=None,
        output_file_name=None,
        output_file_type=None,
        create=True,
        update_defaults=True,
        dump_kwargs=None,
        include_bootstrap=True,
    ):
        """Migrates a configuration file.

        This is used to help you update your configurations throughout the
        lifetime of your application. It is probably best explained through
        example.

        Examples:
            Assume we have a JSON config file ('/path/to/config.json')
            like the following:
            ``{"db_name": "test_db_name", "db_host": "1.2.3.4"}``

            >>> spec = YapconfSpec({
            ...    'db_name': {
            ...        'type': 'str',
            ...        'default': 'new_default',
            ...        'previous_defaults': ['test_db_name']
            ...    },
            ...    'db_host': {
            ...        'type': 'str',
            ...        'previous_defaults': ['localhost']
            ...    }
            ... })

            We can migrate that file quite easily with the spec object:

            >>> spec.migrate_config_file('/path/to/config.json')

            Will result in /path/to/config.json being overwritten:
            ``{"db_name": "new_default", "db_host": "1.2.3.4"}``

        Args:
            config_file_path (str): The path to your current config
            always_update (bool): Always update values (even to None)
            current_file_type (str): Defaults to self._file_type
            output_file_name (str): Defaults to the current_file_path
            output_file_type (str): Defaults to self._file_type
            create (bool): Create the file if it doesn't exist (otherwise
                error if the file does not exist).
            update_defaults (bool): Update values that have a value set to
                something listed in the previous_defaults
            dump_kwargs (dict): A key-value pair that will be passed to dump
            include_bootstrap (bool): Include bootstrap items in the output

        Returns:
            box.Box: The newly migrated configuration.
        """

        current_file_type = current_file_type or self._file_type
        output_file_type = output_file_type or self._file_type
        output_file_name = output_file_name or config_file_path

        current_config = self._get_config_if_exists(config_file_path,
                                                    create,
                                                    current_file_type)

        migrated_config = {}

        if include_bootstrap:
            items = self._yapconf_items.values()
        else:
            items = [
                item for item in self._yapconf_items.values()
                if not item.bootstrap
            ]
        for item in items:
            item.migrate_config(current_config, migrated_config,
                                always_update, update_defaults)

        if create:
            yapconf.dump_data(migrated_config,
                              filename=output_file_name,
                              file_type=output_file_type,
                              klazz=YapconfLoadError,
                              dump_kwargs=dump_kwargs)

        return Box(migrated_config)

    def _get_config_if_exists(self, config_file_path, create, file_type):
        if not os.path.isfile(config_file_path) and create:
            return {}
        elif not os.path.isfile(config_file_path):
            raise YapconfLoadError("Error migrating config file {0}. "
                                   "File does not exist. If you would like "
                                   "to create the file, you need to pass "
                                   "the create flag.".format(config_file_path))

        return yapconf.load_file(config_file_path,
                                 file_type=file_type,
                                 klazz=YapconfLoadError)

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
            source = self._extract_source(index, override)
            overrides.append(source.generate_override(self._separator))

        # We manually generate defaults here so that it is easy to find out
        # if there are defaults for fallbacks that should be applied.
        overrides.append(
            (
                '__defaults__',
                yapconf.flatten(self.defaults, separator=self._separator)
            )
        )
        return overrides

    def _explode_override(self, override):
        label = None
        unpacked_value = override
        file_type = self._file_type

        # If they provided a tuple, they may have named their tuple
        # or given us a differing file_type. So we unpack it before
        # we look at the unpacked value.
        if isinstance(override, tuple):
            if len(override) < 2:
                raise YapconfLoadError(
                    'Invalid override tuple provided. The tuple must have a '
                    'name and value. Optionally, it can provide a third '
                    'argument specifying the file type if it is different '
                    'than the default file_type passed during initialization.'
                )

            label = override[0]
            unpacked_value = override[1]
            if len(override) > 2:
                file_type = override[2]

        return label, unpacked_value, file_type

    def _extract_string_source(self, label, value, file_type):
        if value in self._sources:
            return self._sources[value]
        elif value == 'ENVIRONMENT':
            return get_source(value, 'environment')
        elif file_type in ['json', 'yaml']:
            return get_source(
                value,
                file_type,
                filename=value,
                encoding=self._encoding
            )

        raise YapconfLoadError(
            'Invalid override given: %s. A string type was detected '
            'but no valid source could be generated. This should be '
            'a string which points to a label from the sources you added, '
            'the string "ENVIRONMENT" or have a file_type of "json" or "yaml"'
            'got a (value, file_type) of: (%s %s)' %
            (label, value, file_type)
        )

    def _extract_source(self, index, override):
        label, unpacked_value, file_type = self._explode_override(override)

        if isinstance(unpacked_value, six.string_types):
            return self._extract_string_source(
                label, unpacked_value, file_type
            )

        elif isinstance(unpacked_value, dict):
            label = label or 'dict-%d' % index
            return get_source(label, 'dict', data=unpacked_value)

        raise YapconfLoadError(
            'Invalid override given: %s overrides must be one of the '
            'following: a dictionary, a filename, a label for a source, or '
            '"ENVIRONMENT". Got: %s' % (label, unpacked_value)
        )
