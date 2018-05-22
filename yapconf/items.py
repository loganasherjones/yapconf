# -*- coding: utf-8 -*-
import copy
import logging
import sys

import six

import yapconf
from yapconf.actions import MergeAction, AppendBoolean, AppendReplace
from yapconf.exceptions import YapconfItemError, YapconfItemNotFound, \
    YapconfValueError, YapconfListItemError, YapconfDictItemError

if sys.version_info > (3,):
    long = int

TYPES = ('str', 'int', 'long', 'float', 'bool', 'complex', 'dict', 'list', )


def from_specification(specification, env_prefix=None, separator='.',
                       parent_names=None):
    """Used to create YapconfItems from a specification dictionary.

    Args:
        specification (dict): The specification used to
            initialize ``YapconfSpec``
        env_prefix (str): Prefix to add to environment names
        separator (str): Separator for nested items
        parent_names (list): Parents names of any given item

    Returns:
        A dictionary of names to YapconfItems

    """
    items = {}
    for item_name, item_info in six.iteritems(specification):
        names = copy.copy(parent_names) if parent_names else []
        items[item_name] = _generate_item(item_name,
                                          item_info,
                                          env_prefix,
                                          separator,
                                          names)
    return items


def _get_item_cli_choices(item_type, item_dict):
    if item_type in ['list', 'dict']:
        return None
    else:
        return item_dict.get('cli_choices')


def _get_item_children(item_name, item_dict, env_prefix,
                       parent_names, separator, item_type):
    if item_dict.get('items'):
        if item_type == 'list':
            # List items are only allowed one child. This
            # child name is unused, so we just use the list
            # name. This helps the flattening process stay sane.
            child_key = list(item_dict['items'].keys())[0]
            child_items = {item_name: item_dict['items'][child_key]}
        else:
            child_items = item_dict['items']
            parent_names.append(item_name)

        return from_specification(child_items,
                                  env_prefix=env_prefix,
                                  separator=separator,
                                  parent_names=parent_names)
    else:
        return None


def _generate_item(name, item_dict, env_prefix,
                   separator, parent_names):
    init_args = {'name': name, 'separator': separator}

    item_type = item_dict.get('type', 'str')
    init_args['item_type'] = item_type
    init_args['bootstrap'] = item_dict.get('bootstrap', False)
    init_args['default'] = item_dict.get('default')
    init_args['description'] = item_dict.get('description')
    init_args['long_description'] = item_dict.get('long_description')
    init_args['required'] = item_dict.get('required', True)
    init_args['cli_short_name'] = item_dict.get('cli_short_name')
    init_args['previous_names'] = item_dict.get('previous_names')
    init_args['previous_defaults'] = item_dict.get('previous_defaults')
    init_args['cli_expose'] = item_dict.get('cli_expose', True)
    init_args['env_name'] = item_dict.get('env_name', None)
    init_args['format_cli'] = item_dict.get('format_cli', True)
    init_args['format_env'] = item_dict.get('format_env', True)
    init_args['apply_env_prefix'] = item_dict.get('apply_env_prefix', True)
    init_args['env_prefix'] = env_prefix
    init_args['choices'] = item_dict.get('choices', None)
    init_args['alt_env_names'] = item_dict.get('alt_env_names', [])
    init_args['validator'] = item_dict.get('validator')

    if parent_names:
        init_args['prefix'] = separator.join(parent_names)
    else:
        init_args['prefix'] = None

    init_args['cli_choices'] = _get_item_cli_choices(item_type, item_dict)
    init_args['children'] = _get_item_children(item_name=name,
                                               item_dict=item_dict,
                                               env_prefix=env_prefix,
                                               parent_names=parent_names,
                                               separator=separator,
                                               item_type=item_type)

    if item_type == 'dict':
        return YapconfDictItem(**init_args)
    elif item_type == 'list':
        return YapconfListItem(**init_args)
    elif item_type == 'bool':
        return YapconfBoolItem(**init_args)
    else:
        return YapconfItem(**init_args)


class YapconfItem(object):
    """A simple configuration item for interacting with configurations.

    A ``YapconfItem`` represent the following types: (``str``, ``int``,
    ``long``, ``float``, ``complex``). It also acts as the base class
    for the other ``YapconfItem`` types. It provides several basic
    functions. It helps create CLI arguments to be used by
    ``argparse.ArgumentParser``. It also makes getting a particular
    configuration value simple.

    In general this class is expected to be used by the ``YapconfSpec``
    class to help manage your configuration.

    Attributes:
         name (str): The name of the config value.
         item_type (str): The type of config value you are expecting.
         default: The default value if no configuration value can be found.
         env_name: The name to search in the environment.
         description: The description of your configuration item.
         required: Whether or not the item is required to be present.
         cli_short_name: A short name (1-character) to identify your item
            on the command-line.
         cli_choices: A list of possible choices on the command-line.
         previous_names: A list of names that used to identify this item. This
            is useful for config migrations.
         previous_defaults: A list of previous default values given to this
            item. Again, useful for config migrations.
         children: Any children of this item. Not used by this base class.
         cli_expose: A flag to indicate if the item should be exposed from
            the command-line. It is possible for this value to be overwritten
            based on whether or not this item is part of a nested list.
         separator: A separator used to split apart parent names in the prefix.
         prefix: A delimited list of parent names
         bootstrap: A flag to determine if this item is required for
            bootstrapping the rest of your configuration.
         format_cli: A flag to determine if we should format the command-line
            arguments to be kebab-case.
         format_env: A flag to determine if environment variables will be all
            upper-case SNAKE_CASE.
         env_prefix: The env_prefix to apply to the environment name.
         apply_env_prefix: Apply the env_prefix even if the environment name
            was set manually. Setting format_env to false will override this
            behavior.
         choices: A list of valid choices for the item.
         alt_env_names: A list of alternate environment names.

    Raises:
        YapconfItemError: If any of the information given during
            initialization results in an invalid item.
    """

    def __init__(
        self,
        name,
        item_type='str',
        default=None,
        env_name=None,
        description=None,
        required=True,
        cli_short_name=None,
        cli_choices=None,
        previous_names=None,
        previous_defaults=None,
        children=None,
        cli_expose=True,
        separator='.',
        prefix=None,
        bootstrap=False,
        format_cli=True,
        format_env=True,
        env_prefix=None,
        apply_env_prefix=True,
        choices=None,
        alt_env_names=None,
        long_description=None,
        validator=None
    ):

        self.name = name
        self.item_type = item_type
        self.default = default
        self.description = description
        self.long_description = long_description
        self.required = required
        self.cli_short_name = cli_short_name
        self.cli_choices = cli_choices or []
        self.previous_names = previous_names or []
        self.previous_defaults = previous_defaults or []
        self.children = children or {}
        self.cli_expose = cli_expose
        self.separator = separator
        self.prefix = prefix
        self.bootstrap = bootstrap
        self.format_env = format_env
        self.format_cli = format_cli
        self.env_prefix = env_prefix or ''
        self.apply_env_prefix = apply_env_prefix
        self.choices = choices
        self.validator = validator

        if self.prefix:
            self.fq_name = self.separator.join([self.prefix, self.name])
        else:
            self.fq_name = self.name

        self.env_name = self._setup_env_name(env_name)
        self.alt_env_names = []
        for alt_env_name in alt_env_names or []:
            alt_name = self._setup_env_name(alt_env_name)
            if alt_name is not None:
                self.alt_env_names.append(alt_name)

        self.possible_names = [self.fq_name] + self.previous_names
        self.cli_support = self._has_cli_support()
        self.logger = logging.getLogger(__name__)

        if not self.cli_support and self.cli_expose:
            self.logger.info("Item {0} does not have cli_support, setting "
                             "cli_expose to False.".format(self.name))
            self.cli_expose = False

        self._validate()

    @property
    def all_env_names(self):
        if self.env_name is not None:
            return [self.env_name] + self.alt_env_names
        else:
            return []

    def update_default(self, new_default, respect_none=False):
        """Update our current default with the new_default.

        Args:
            new_default: New default to set.
            respect_none: Flag to determine if ``None`` is a valid value.

        """
        if new_default is not None:
            self.default = new_default
        elif new_default is None and respect_none:
            self.default = None

    def migrate_config(self, current_config, config_to_migrate,
                       always_update, update_defaults):
        """Migrate config value in current_config, updating config_to_migrate.

        Given the current_config object, it will attempt to find a value
        based on all the names given. If no name could be found, then it
        will simply set the value to the default.

        If a value is found and is in the list of previous_defaults, it will
        either update or keep the old value based on if update_defaults is
        set.

        If a non-default value is set it will either keep this value or update
        it based on if ``always_update`` is true.

        Args:
            current_config (dict): Current configuration.
            config_to_migrate (dict): Config to update.
            always_update (bool): Always update value.
            update_defaults (bool): Update values found in previous_defaults
        """
        value = self._search_config_for_possible_names(current_config)
        self._update_config(config_to_migrate, value,
                            always_update, update_defaults)

    def add_argument(self, parser, bootstrap=False):
        """Add this item as an argument to the given parser.

        Args:
            parser (argparse.ArgumentParser): The parser to add this item to.
            bootstrap: Flag to indicate whether you only want to mark this
                item as required or not
        """
        if self.cli_expose:
            args = self._get_argparse_names(parser.prefix_chars)
            kwargs = self._get_argparse_kwargs(bootstrap)
            parser.add_argument(*args, **kwargs)

    def get_config_value(self, overrides):
        """Get the configuration value from all overrides.

        Iterates over all overrides given to see if a value can be pulled
        out from them. It will convert each of these values to ensure they
        are the correct type.

        Args:
            overrides: A list of tuples where each tuple is a label and a
                dictionary representing a configuration.

        Returns:
            The converted configuration value.

        Raises:
            YapconfItemNotFound: If an item is required but could not be found
                in the configuration.
            YapconfItemError: If a possible value was found but the type
                cannot be determined.
            YapconfValueError: If a possible value is found but during
                conversion, an exception was raised.

        """
        label, override = self._find_label_and_override(overrides)

        if override is None and self.default is None and self.required:
            raise YapconfItemNotFound('Could not find config value for {0}'
                                      .format(self.fq_name), self)

        if override is None:
            self.logger.info('Config value not found for {0}, falling back '
                             'to default.'.format(self.name))
            value = self.default
        elif label == 'ENVIRONMENT':
            value = None
            for name in self.all_env_names:
                if (
                    name in override and
                    override[name] is not None and
                    override[name] != ''
                ):
                    value = override[name]
                    break
        else:
            value = override[self.fq_name]

        if value is None:
            return value

        converted_value = self.convert_config_value(value, label)
        self._validate_value(converted_value)
        return converted_value

    def _validate_value(self, value):
        if self.choices and value not in self.choices:
            raise YapconfValueError("Invalid value provided (%s) for %s."
                                    "Valid values are %s" %
                                    (value, self.fq_name, self.choices))
        if self.validator and not self.validator(value):
            raise YapconfValueError('Invalid value provided (%s) for %s.' %
                                    (value, self.fq_name))

    def convert_config_value(self, value, label):
        try:
            if self.item_type == 'str':
                return str(value)
            elif self.item_type == 'int':
                return int(value)
            elif self.item_type == 'long':
                return long(value)
            elif self.item_type == 'float':
                return float(value)
            elif self.item_type == 'complex':
                return complex(value)
            else:
                raise YapconfItemError("Do not know how to convert type {0} "
                                       "for {1} found in {2}"
                                       .format(self.item_type, self.name,
                                               label))
        except (TypeError, ValueError) as ex:
            raise YapconfValueError("Tried to convert {0} to {1} but got an "
                                    "error instead. Found in {2}. Error "
                                    "Message: {3}"
                                    .format(self.name, self.item_type, label,
                                            ex), ex)

    def _validate(self):
        if self.separator in self.name:
            raise YapconfItemError("Cannot have a name with {0} in it. Either "
                                   "choose a different name or choose a "
                                   "different separator."
                                   .format(self.separator))

        if self.item_type not in TYPES:
            raise YapconfItemError("Invalid type provided ({0}) valid types "
                                   "are: {1}"
                                   .format(self.item_type, TYPES))

        if self.cli_short_name and len(self.cli_short_name) != 1:
            raise YapconfItemError("CLI Short name ({0}) can only be a single "
                                   "character.".format(self.cli_short_name))
        elif self.cli_short_name == '-':
            raise YapconfItemError("CLI Short name cannot be '-'")

        if self.default:
            self._validate_value(self.default)

    def __repr__(self):
        return "Item(%s, %s)" % (self.fq_name, self.item_type)

    def _setup_env_name(self, env_name):
        if env_name is not None:
            if self.apply_env_prefix:
                return self.env_prefix + env_name
            return env_name

        if self.format_env:
            return yapconf.change_case(
                self.env_prefix +
                "_".join(self.fq_name.split(self.separator)), "_"
            ).upper()
        else:
            return "".join(self.fq_name.split(self.separator))

    def _has_cli_support(self, child_of_list=False):
        for child in self.children.values():
            if not child._has_cli_support(child_of_list):
                return False
        return True

    def _in_environment(self, env_dict):
        for name in self.all_env_names:
            if (
                name in env_dict and
                env_dict[name] is not None and
                env_dict[name] != ''
            ):
                return True
        return False

    def _find_label_and_override(self, overrides, skip_environment=False):
        for label, info in overrides:
            if label == 'ENVIRONMENT':
                if self._in_environment(info):
                    if skip_environment:
                        self.logger.info('Found possible value in the '
                                         'environment for {0}, but for {1} '
                                         'getting the value from the '
                                         'environment is currently '
                                         'unsupported. Skipping this entry.'
                                         .format(self.name, self.item_type))
                    else:
                        self.logger.info('Found config value for {0} in {1}'
                                         .format(self.name, label))
                        return label, info
            elif self.fq_name in info and info[self.fq_name] is not None:
                self.logger.info('Found config value for {0} in {1}'
                                 .format(self.fq_name, label))
                return label, info

        return None, None

    def _format_prefix_for_cli(self, chars):
        expected_prefix = "{0}{0}".format(chars)
        expected_suffix = "{0}".format(chars)

        if not self.prefix:
            return expected_prefix
        else:
            return expected_prefix + chars.join(
                self.prefix.split(self.separator)) + expected_suffix

    def _search_config_for_fq_name(self, fq_name, config_to_search):
        names = fq_name.split(self.separator)
        for index, name in enumerate(names):
            if index == len(names) - 1:
                return config_to_search.get(name, None)
            elif name in config_to_search:
                config_to_search = config_to_search[name]
            else:
                return None

    def _search_config_for_possible_names(self, config):
        for fq_name in self.possible_names:
            config_to_search = config
            value = self._search_config_for_fq_name(fq_name, config_to_search)
            if value is not None:
                return value

    def _update_config(self, config, value, always_update, update_defaults):
        if value is None:
            self.logger.debug("Key {0} was not found in the current config. "
                              "Setting to default value {1}"
                              .format(self.name, self.default))
            config[self.name] = self.default

        elif always_update:
            self.logger.debug("Key {0} was found, but always_update is set "
                              "to true so we will update the value to the "
                              "default from the specification. Old value: "
                              "{1}, New Value: {2}"
                              .format(self.name, value, self.default))
            config[self.name] = self.default

        elif value in self.previous_defaults and update_defaults:
            self.logger.debug("Key {0} was found, but it was a previous "
                              "default value; update_defaults was set to "
                              "true so we will update the value to the "
                              "newest default. Old Value: {1}, New Value: "
                              "{2}".format(self.name, value, self.default))
            config[self.name] = self.default

        else:
            self.logger.debug("Key {0} was found, not changing value from {1}"
                              .format(self.name, value))
            config[self.name] = value

    def _get_argparse_action(self, parent_action=True):
        if self.prefix and parent_action:
            return MergeAction
        else:
            return 'store'

    def _get_argparse_type(self):
        if self.item_type == 'str':
            return str
        elif self.item_type == 'int':
            return int
        elif self.item_type == 'long':
            return long
        elif self.item_type == 'float':
            return float
        elif self.item_type == 'complex':
            return complex
        else:
            raise YapconfItemError("Do not know how to generate CLI "
                                   "type for {0}".format(self.item_type))

    def _get_argparse_choices(self):
        return self.cli_choices or None

    def _get_argparse_names(self, prefix_chars):
        cli_prefix = self._format_prefix_for_cli(prefix_chars)
        if self.format_cli:
            cli_name = yapconf.change_case(self.name, prefix_chars)
        else:
            cli_name = self.name
        if self.cli_short_name:
            return ["{0}{1}".format(cli_prefix, cli_name),
                    "{0}{1}".format(prefix_chars, self.cli_short_name)]
        else:
            return ["{0}{1}".format(cli_prefix, cli_name)]

    def _get_argparse_kwargs(self, bootstrap):
        kwargs = {
            'action': self._get_argparse_action(),
            'default': None,
            'type': self._get_argparse_type(),
            'choices': self._get_argparse_choices(),
            'required': False,
            'help': self.description,
            'dest': self.fq_name,
        }

        if self.prefix:
            kwargs['child_action'] = self._get_argparse_action(False)
            kwargs['separator'] = self.separator

        return kwargs


class YapconfBoolItem(YapconfItem):
    """A YapconfItem specifically for Boolean behavior"""

    # Values to interpret as True (not case sensitive)
    TRUTHY_VALUES = ('y', 'yes', 't', 'true', '1', 1, True, )

    # Values to interpret as False (not case sensitive)
    FALSY_VALUES = ('n', 'no', 'f', 'false', '0', 0, False, )

    def __init__(
        self,
        name,
        item_type='bool',
        default=None,
        env_name=None,
        description=None,
        required=True,
        cli_short_name=None,
        cli_choices=None,
        previous_names=None,
        previous_defaults=None,
        children=None,
        cli_expose=True,
        separator='.',
        prefix=None,
        bootstrap=False,
        format_cli=True,
        format_env=True,
        env_prefix=None,
        apply_env_prefix=True,
        choices=None,
        alt_env_names=None,
        long_description=None,
        validator=None
    ):
        super(YapconfBoolItem, self).__init__(
            name,
            item_type,
            default,
            env_name,
            description,
            required,
            cli_short_name,
            cli_choices,
            previous_names,
            previous_defaults,
            children,
            cli_expose,
            separator,
            prefix,
            bootstrap,
            format_cli,
            format_env,
            env_prefix,
            apply_env_prefix,
            choices,
            alt_env_names,
            long_description,
            validator
        )

    def add_argument(self, parser, bootstrap=False):
        """Add boolean item as an argument to the given parser.

        An exclusive group is created on the parser, which will add
        a boolean-style command line argument to the parser.

        Examples:
            A non-nested boolean value with the name 'debug' will result
            in a command-line argument like the following:

            '--debug/--no-debug'

        Args:
            parser (argparse.ArgumentParser): The parser to add this item to.
            bootstrap (bool): Flag to indicate whether you only want to mark
                this item as required or not.
        """
        tmp_default = self.default
        exclusive_grp = parser.add_mutually_exclusive_group()
        self.default = True
        args = self._get_argparse_names(parser.prefix_chars)
        kwargs = self._get_argparse_kwargs(bootstrap)
        exclusive_grp.add_argument(*args, **kwargs)

        self.default = False
        args = self._get_argparse_names(parser.prefix_chars)
        kwargs = self._get_argparse_kwargs(bootstrap)
        exclusive_grp.add_argument(*args, **kwargs)

        self.default = tmp_default

    def convert_config_value(self, value, label):
        """Converts all 'Truthy' values to True and 'Falsy' values to False.

        Args:
            value: Value to convert
            label: Label of the config which this item was found.

        Returns:

        """
        if isinstance(value, six.string_types):
            value = value.lower()

        if value in self.TRUTHY_VALUES:
            return True
        elif value in self.FALSY_VALUES:
            return False
        else:
            raise YapconfValueError("Cowardly refusing to interpret "
                                    "config value as a boolean. Name: "
                                    "{0}, Value: {1}"
                                    .format(self.name, value))

    def _get_argparse_action(self, parent_action=True):

        if self.prefix and parent_action:
            return MergeAction
        elif self.default:
            return 'store_false'
        else:
            return 'store_true'

    def _get_argparse_names(self, prefix_chars):
        cli_prefix = self._format_prefix_for_cli(prefix_chars)
        if self.format_cli:
            cli_name = yapconf.change_case(self.name, prefix_chars)
        else:
            cli_name = self.name

        if self.default:
            full_prefix = "{0}no{1}".format(cli_prefix, prefix_chars)
        else:
            full_prefix = cli_prefix

        full_name = "{0}{1}".format(full_prefix, cli_name)

        if self.cli_short_name:
            return [full_name, "{0}{1}".format(full_prefix,
                                               self.cli_short_name)]
        else:
            return [full_name]

    def _get_argparse_kwargs(self, bootstrap):
        kwargs = {
            'action': self._get_argparse_action(),
            'default': None,
            'required': False,
            'help': self.description,
            'dest': self.fq_name,
        }

        if self.prefix:
            kwargs['child_action'] = self._get_argparse_action(False)
            kwargs['separator'] = self.separator
            kwargs['nargs'] = 0

        return kwargs


class YapconfListItem(YapconfItem):
    """A YapconfItem for capture list-specific behavior"""

    def __init__(
        self,
        name,
        item_type='list',
        default=None,
        env_name=None,
        description=None,
        required=True,
        cli_short_name=None,
        cli_choices=None,
        previous_names=None,
        previous_defaults=None,
        children=None,
        cli_expose=True,
        separator='.',
        prefix=None,
        bootstrap=False,
        format_cli=True,
        format_env=True,
        env_prefix=None,
        apply_env_prefix=True,
        choices=None,
        alt_env_names=None,
        long_description=None,
        validator=None
    ):

        super(YapconfListItem, self).__init__(
            name,
            item_type,
            default,
            env_name,
            description,
            required,
            cli_short_name,
            cli_choices,
            previous_names,
            previous_defaults,
            children,
            cli_expose,
            separator,
            prefix,
            bootstrap,
            format_cli,
            format_env,
            env_prefix,
            apply_env_prefix,
            choices,
            alt_env_names,
            long_description,
            validator
        )

        if len(self.children) != 1:
            raise YapconfListItemError("List Items can only have a "
                                       "single child item. Got {0} children"
                                       .format(len(self.children)))

        self.child = list(children.values())[0]

    def _setup_env_name(self, env_name):
        return None

    def get_config_value(self, overrides):
        label, override = self._find_label_and_override(overrides,
                                                        skip_environment=True)

        if override is None and self.default is None and self.required:
            raise YapconfItemNotFound('Could not find config value for {0}'
                                      .format(self.fq_name), self)

        if override is None:
            values = self.default
        else:
            values = override[self.fq_name]

        if values is None:
            return None

        converted_value = self.convert_config_value(values, label)
        self._validate_value(converted_value)
        return converted_value

    def convert_config_value(self, value, label):
        try:
            value_to_return = []
            for v in value:
                converted_value = self.child.convert_config_value(v, label)
                self.child._validate_value(converted_value)
                value_to_return.append(converted_value)
            return value_to_return
        except (TypeError, ValueError) as ex:
            raise YapconfValueError('Tried to convert "{0}" to a list but '
                                    'could not iterate over the value. '
                                    'Invalid item found in {1}'
                                    .format(self.name, label), ex)

    def add_argument(self, parser, bootstrap=False):
        """Add list-style item as an argument to the given parser.

        Generally speaking, this works mostly like the normal append
        action, but there are special rules for boolean cases. See the
        AppendReplace action for more details.

        Examples:
            A non-nested list value with the name 'values' and a child name of
            'value' will result in a command-line argument that will correctly
            handle arguments like the following:

            ['--value', 'VALUE1', '--value', 'VALUE2']

        Args:
            parser (argparse.ArgumentParser): The parser to add this item to.
            bootstrap (bool): Flag to indicate whether you only want to mark
                this item as required or not.
        """
        if self.cli_expose:
            if isinstance(self.child, YapconfBoolItem):
                original_default = self.child.default

                self.child.default = True
                args = self.child._get_argparse_names(parser.prefix_chars)
                kwargs = self._get_argparse_kwargs(bootstrap)
                parser.add_argument(*args, **kwargs)

                self.child.default = False
                args = self.child._get_argparse_names(parser.prefix_chars)
                kwargs = self._get_argparse_kwargs(bootstrap)
                parser.add_argument(*args, **kwargs)

                self.child.default = original_default
            else:
                super(YapconfListItem, self).add_argument(parser, bootstrap)

    def _has_cli_support(self, child_of_list=False):
        if child_of_list:
            return False
        else:
            return super(YapconfListItem, self)._has_cli_support(True)

    def _get_argparse_action(self, parent_action=True):
        if self.prefix and parent_action:
            return MergeAction
        elif isinstance(self.child, YapconfBoolItem):
            return AppendBoolean
        else:
            return AppendReplace

    def _get_argparse_type(self):
        return self.child._get_argparse_type()

    def _get_argparse_kwargs(self, bootstrap):
        child_kwargs = self.child._get_argparse_kwargs(bootstrap)
        child_kwargs['action'] = self._get_argparse_action()
        child_kwargs['dest'] = self.fq_name
        child_kwargs['default'] = None

        if self.prefix:
            child_kwargs['child_action'] = self._get_argparse_action(False)
            child_kwargs['child_const'] = not self.child.default

        if isinstance(self.child, YapconfBoolItem):
            child_kwargs['const'] = not self.child.default

        return child_kwargs


class YapconfDictItem(YapconfItem):
    """A YapconfItem for capture dict-specific behavior"""

    def __init__(
        self,
        name,
        item_type='dict',
        default=None,
        env_name=None,
        description=None,
        required=True,
        cli_short_name=None,
        cli_choices=None,
        previous_names=None,
        previous_defaults=None,
        children=None,
        cli_expose=True,
        separator='.',
        prefix=None,
        bootstrap=False,
        format_cli=True,
        format_env=True,
        env_prefix=None,
        apply_env_prefix=True,
        choices=None,
        alt_env_names=None,
        long_description=None,
        validator=None
    ):

        super(YapconfDictItem, self).__init__(
            name,
            item_type,
            default,
            env_name,
            description,
            required,
            cli_short_name,
            cli_choices,
            previous_names,
            previous_defaults,
            children,
            cli_expose,
            separator,
            prefix,
            bootstrap,
            format_cli,
            format_env,
            env_prefix,
            apply_env_prefix,
            choices,
            alt_env_names,
            long_description,
            validator
        )

        if self.choices is not None:
            raise YapconfDictItemError('Dict items {0} cannot have choices '
                                       'because they are not hashable.'
                                       .format(self.name))
        if len(self.children) < 1:
            raise YapconfDictItemError('Dict item {0} must have children'
                                       .format(self.name))

    def _setup_env_name(self, env_name):
        self.env_name = None

    def add_argument(self, parser, bootstrap=False):
        """Add dict-style item as an argument to the given parser.

        The dict item will take all the nested items in the dictionary and
        namespace them with the dict name, adding each child item as
        their own CLI argument.

        Examples:
            A non-nested dict item with the name 'db' and children named
            'port' and 'host' will result in the following being valid
            CLI args:

            ['--db-host', 'localhost', '--db-port', '1234']

        Args:
            parser (argparse.ArgumentParser): The parser to add this item to.
            bootstrap (bool): Flag to indicate whether you only want to mark
                this item as required or not.
        """
        if self.cli_expose:
            for child in self.children.values():
                child.add_argument(parser, bootstrap)

    def get_config_value(self, overrides):
        converted_value = {
            child_name: child_item.get_config_value(overrides)
            for child_name, child_item in six.iteritems(self.children)
        }
        self._validate_value(converted_value)
        return converted_value

    def migrate_config(self, current_config, config_to_migrate,
                       always_update, update_defaults):

        if self.name not in config_to_migrate:
            config_to_migrate[self.name] = {}

        child_config = config_to_migrate[self.name]

        for child_item in self.children.values():
            child_item.migrate_config(current_config, child_config,
                                      always_update, update_defaults)

    def convert_config_value(self, value, label):
        return {
            child_name: child_item.get_config_value([(label, value)])
            for child_name, child_item in six.iteritems(self.children)
        }

    def _has_cli_support(self, child_of_list=False):
        if child_of_list:
            return False
        else:
            return super(YapconfDictItem, self)._has_cli_support()

    def _find_all_overrides(self, overrides):
        nested_overrides = []
        for label, info in overrides:
            if label == 'ENVIRONMENT':
                if self.env_name in info:
                    self.logger.info('Found possible value in the '
                                     'environment for {0}, but the item is '
                                     'a dict. Getting dict values from the '
                                     'environment is currently '
                                     'unsupported. Skipping this entry.'
                                     .format(self.name))
                nested_overrides.append((label, info))
            elif self.name in info:
                if not isinstance(info[self.name], dict):
                    raise YapconfValueError("Invalid override found in {0}. "
                                            "It contained a key {1} which we "
                                            "expected to be a dictionary."
                                            .format(label, self.name))
                nested_overrides.append((label, info[self.name]))
        return nested_overrides
