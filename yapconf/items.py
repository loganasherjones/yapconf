# -*- coding: utf-8 -*-
import logging
import sys

import six

from yapconf.actions import MergeAction, AppendBoolean, AppendReplace
from yapconf.exceptions import YapconfItemError, YapconfItemNotFound, \
    YapconfValueError, YapconfListItemError, YapconfDictItemError

if sys.version_info > (3,):
    long = int

TYPES = ('str', 'int', 'long', 'float', 'bool', 'complex', 'dict', 'list', )


def from_specification(specification, env_prefix=None, separator='.',
                       use_env=True, parent_names=None):
    items = {}
    for item_name, item_info in six.iteritems(specification):
        names = parent_names or []
        items[item_name] = generate_item(item_name, item_info, env_prefix,
                                         separator, use_env, names)
    return items


def _get_item_cli_choices(item_type, item_dict):
    if item_type in ['list', 'dict']:
        return None
    else:
        return item_dict.get('cli_choices')


def _get_item_env_name(item_name, item_dict, item_type, env_prefix, use_env):
    if not use_env or item_type in ['list', 'dict']:
        return None

    default_env_name = item_name.upper()
    if env_prefix:
        default_env_name = env_prefix + default_env_name

    return item_dict.get('env_name', default_env_name)


def _get_item_children(item_name, item_dict, item_type, env_prefix,
                       use_env, env_name, parent_names, separator):
    if item_dict.get('items'):
        # We do not support getting list values from the environment at all.
        if item_type == 'list':
            use_env = False
            new_env_prefix = None
        else:
            parent_names.append(item_name)
            env_suffix = env_name or item_name.upper()
            if env_prefix:
                new_env_prefix = env_prefix + env_suffix + "_"
            else:
                new_env_prefix = env_suffix + "_"

        return from_specification(item_dict['items'],
                                  env_prefix=new_env_prefix,
                                  separator=separator,
                                  use_env=use_env,
                                  parent_names=parent_names)
    else:
        return None


def generate_item(name, item_dict, env_prefix,
                  separator, use_env, parent_names):
    init_args = {'name': name, 'separator': separator}

    item_type = item_dict.get('type', 'str')
    init_args['item_type'] = item_type
    init_args['bootstrap'] = item_dict.get('bootstrap', False)
    init_args['default'] = item_dict.get('default')
    init_args['description'] = item_dict.get('description')
    init_args['required'] = item_dict.get('required', True)
    init_args['cli_short_name'] = item_dict.get('cli_short_name')
    init_args['previous_names'] = item_dict.get('previous_names')
    init_args['previous_defaults'] = item_dict.get('previous_defaults')
    init_args['cli_expose'] = item_dict.get('cli_expose', True)

    if parent_names:
        init_args['prefix'] = separator.join(parent_names)
    else:
        init_args['prefix'] = None

    init_args['cli_choices'] = _get_item_cli_choices(item_type, item_dict)
    init_args['env_name'] = _get_item_env_name(item_name=name,
                                               item_dict=item_dict,
                                               item_type=item_type,
                                               env_prefix=env_prefix,
                                               use_env=use_env)
    init_args['children'] = _get_item_children(item_name=name,
                                               item_dict=item_dict,
                                               item_type=item_type,
                                               env_prefix=env_prefix,
                                               use_env=use_env,
                                               env_name=init_args['env_name'],
                                               parent_names=parent_names,
                                               separator=separator)

    if item_type == 'dict':
        return YapconfDictItem(**init_args)
    elif item_type == 'list':
        return YapconfListItem(**init_args)
    elif item_type == 'bool':
        return YapconfBoolItem(**init_args)
    else:
        return YapconfItem(**init_args)


class YapconfItem(object):

    def __init__(self, name, item_type='str',
                 default=None, env_name=None,
                 description=None, required=True, cli_short_name=None,
                 cli_choices=None, previous_names=None, previous_defaults=None,
                 children=None, cli_expose=True, separator='.', prefix=None,
                 bootstrap=False):

        self.name = name
        self.item_type = item_type
        self.default = default
        self.env_name = env_name
        self.description = description
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

        if self.prefix:
            self.fq_name = self.separator.join([self.prefix, self.name])
        else:
            self.fq_name = self.name

        self.possible_names = [self.fq_name] + self.previous_names
        self.cli_support = self.has_cli_support()
        self.logger = logging.getLogger(__name__)

        if not self.cli_support and self.cli_expose:
            self.logger.info("Item {0} does not have cli_support, setting "
                             "cli_expose to False.".format(self.name))
            self.cli_expose = False

        self._validate()

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

    def _find_label_and_override(self, overrides, skip_environment=False):
        for label, info in overrides:
            if label == 'ENVIRONMENT':
                if self.env_name and self.env_name in info:
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
            elif self.name in info:
                self.logger.info('Found config value for {0} in {1}'
                                 .format(self.name, label))
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

    def update_default(self, new_default, respect_none=False):
        if new_default is not None:
            self.default = new_default
        elif new_default is None and respect_none:
            self.default = None

    def has_cli_support(self, child_of_list=False):
        for child in self.children.values():
            if not child.has_cli_support(child_of_list):
                return False
        return True

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

    def migrate_config(self, current_config, config_to_migrate,
                       always_update, update_defaults):
        value = self._search_config_for_possible_names(current_config)
        self._update_config(config_to_migrate, value,
                            always_update, update_defaults)

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

    def _get_argparse_required(self, bootstrap):
        if bootstrap is True and not self.bootstrap:
            return False
        elif self.default is None:
            return self.required
        else:
            return False

    def _get_argparse_choices(self):
        return self.cli_choices or None

    def _get_argparse_names(self, prefix_chars):
        cli_prefix = self._format_prefix_for_cli(prefix_chars)
        if self.cli_short_name:
            return ["{0}{1}".format(cli_prefix, self.name),
                    "{0}{1}".format(prefix_chars, self.cli_short_name)]
        else:
            return ["{0}{1}".format(cli_prefix, self.name)]

    def _get_argparse_kwargs(self, bootstrap):
        kwargs = {
            'action': self._get_argparse_action(),
            'default': None,
            'type': self._get_argparse_type(),
            'choices': self._get_argparse_choices(),
            'required': self._get_argparse_required(bootstrap),
            'help': self.description,
            'dest': self.fq_name,
        }

        if self.prefix:
            kwargs['child_action'] = self._get_argparse_action(False)
            kwargs['separator'] = self.separator

        return kwargs

    def add_argument(self, parser, bootstrap=False):
        if self.cli_expose:
            args = self._get_argparse_names(parser.prefix_chars)
            kwargs = self._get_argparse_kwargs(bootstrap)
            parser.add_argument(*args, **kwargs)

    def get_config_value(self, overrides):
        label, override = self._find_label_and_override(overrides)

        if override is None and self.default is None and self.required:
            raise YapconfItemNotFound('Could not find config value for {0}'
                                      .format(self.name))

        if override is None:
            self.logger.info('Config value not found for {0}, falling back '
                             'to default.'.format(self.name))
            value = self.default
        elif label == 'ENVIRONMENT':
            value = override[self.env_name]
        else:
            value = override[self.name]

        if value is None:
            return value

        return self.convert_config_value(value, label)

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


class YapconfBoolItem(YapconfItem):

    TRUTHY_VALUES = ('y', 'yes', 't', 'true', '1', 1, True, )
    FALSY_VALUES = ('n', 'no', 'f', 'false', '0', 0, False, )

    def __init__(self, name, item_type='bool',
                 default=None, env_name=None,
                 description=None, required=True, cli_short_name=None,
                 cli_choices=None, previous_names=None, previous_defaults=None,
                 children=None, cli_expose=True, separator='.', prefix=None,
                 bootstrap=False):
        super(YapconfBoolItem, self).__init__(
            name, item_type, default, env_name, description, required,
            cli_short_name, cli_choices, previous_names, previous_defaults,
            children, cli_expose, separator, prefix, bootstrap)

    def _get_argparse_action(self, parent_action=True):

        if self.prefix and parent_action:
            return MergeAction
        elif self.default:
            return 'store_false'
        else:
            return 'store_true'

    def _get_argparse_names(self, prefix_chars):
        cli_prefix = self._format_prefix_for_cli(prefix_chars)
        if self.default:
            full_name = "{0}no{1}{2}".format(cli_prefix,
                                             prefix_chars,
                                             self.name)
        else:
            full_name = "{0}{1}".format(cli_prefix, self.name)

        if self.cli_short_name:
            return [full_name, "{0}{1}".format(prefix_chars,
                                               self.cli_short_name)]
        else:
            return [full_name]

    def _get_argparse_kwargs(self, bootstrap):
        kwargs = {
            'action': self._get_argparse_action(),
            'default': None,
            'required': self._get_argparse_required(bootstrap),
            'help': self.description,
            'dest': self.fq_name,
        }

        if self.prefix:
            kwargs['child_action'] = self._get_argparse_action(False)
            kwargs['separator'] = self.separator
            kwargs['nargs'] = 0

        return kwargs

    def add_argument(self, parser, bootstrap=False):
        # If we do not have a default we need to add the positive
        # and negative flags so that the user can specify either.
        # so we simply change the default and add the arguments to
        # an exclusive group. We can't just call add_argument again
        # because we need to add them to the exclusive group not
        # the parser.
        if self.default is None and self.cli_expose:
            exclusive_grp = parser.add_mutually_exclusive_group()
            self.default = True
            args = self._get_argparse_names(parser.prefix_chars)
            kwargs = self._get_argparse_kwargs(bootstrap)
            exclusive_grp.add_argument(*args, **kwargs)

            self.default = False
            args = self._get_argparse_names(parser.prefix_chars)
            kwargs = self._get_argparse_kwargs(bootstrap)
            exclusive_grp.add_argument(*args, **kwargs)

            self.default = None
        elif self.cli_expose:
            super(YapconfBoolItem, self).add_argument(parser, bootstrap)

    def convert_config_value(self, value, label):
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


class YapconfListItem(YapconfItem):
    def __init__(self, name, item_type='list', default=None, env_name=None,
                 description=None, required=True, cli_short_name=None,
                 cli_choices=None, previous_names=None, previous_defaults=None,
                 children=None, cli_expose=True, separator='.', prefix=None,
                 bootstrap=False):

        super(YapconfListItem, self).__init__(
            name, item_type, default, env_name, description, required,
            cli_short_name, cli_choices, previous_names, previous_defaults,
            children, cli_expose, separator, prefix, bootstrap)

        if len(self.children) != 1:
            raise YapconfListItemError("List Items can only have a "
                                       "single child item. Got {0} children"
                                       .format(len(self.children)))

        self.child = list(children.values())[0]

    def get_config_value(self, overrides):
        label, override = self._find_label_and_override(overrides,
                                                        skip_environment=True)

        if override is None and self.default is None and self.required:
            raise YapconfItemNotFound('Could not find config value for {0}'
                                      .format(self.name))

        if override is None:
            values = self.default
        else:
            values = override[self.name]

        if values is None:
            return None

        try:
            return [
                self.child.convert_config_value(value, label)
                for value in values
            ]
        except TypeError:
            raise YapconfValueError('{0} was found in {1} but we expected the '
                                    'item to be a list'
                                    .format(self.name, label))

    def convert_config_value(self, value, label):
        try:
            return [self.child.convert_config_value(v, label) for v in value]
        except (TypeError, ValueError) as ex:
            raise YapconfValueError('Tried to convert "{0}" to a list but '
                                    'could not iterate over the value. '
                                    'Invalid item found in {1}'
                                    .format(self.name, label), ex)

    def has_cli_support(self, child_of_list=False):
        if child_of_list:
            return False
        else:
            return super(YapconfListItem, self).has_cli_support(True)

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

    def add_argument(self, parser, bootstrap=False):
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


class YapconfDictItem(YapconfItem):
    def __init__(self, name, item_type='dict',
                 default=None, env_name=None,
                 description=None, required=True, cli_short_name=None,
                 cli_choices=None, previous_names=None, previous_defaults=None,
                 children=None, cli_expose=True, separator='.', prefix=None,
                 bootstrap=False):

        super(YapconfDictItem, self).__init__(
            name, item_type, default, env_name, description, required,
            cli_short_name, cli_choices, previous_names, previous_defaults,
            children, cli_expose, separator, prefix, bootstrap)

        if len(self.children) < 1:
            raise YapconfDictItemError('Dict item {0} must have children'
                                       .format(self.name))

    def has_cli_support(self, child_of_list=False):
        if child_of_list:
            return False
        else:
            return super(YapconfDictItem, self).has_cli_support()

    def add_argument(self, parser, bootstrap=False):
        if self.cli_expose:
            for child in self.children.values():
                child.add_argument(parser, bootstrap)

    def get_config_value(self, overrides):
        nested_overrides = self._find_all_overrides(overrides)

        return {
            child_name: child_item.get_config_value(nested_overrides)
            for child_name, child_item in six.iteritems(self.children)
        }

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
