# -*- coding: utf-8 -*-
import argparse


class AppendReplace(argparse.Action):
    """argparse.Action used for appending values on the command-line"""

    def __call__(self, parser, namespace, values, option_string=None):
        # if we find an attribute and it is equal to the default,
        # then we need to completely replace the value
        current_value = getattr(namespace, self.dest, [])
        if current_value == self.default:
            setattr(namespace, self.dest, [values])
        else:
            current_value.append(values)
            setattr(namespace, self.dest, current_value)


class AppendBoolean(argparse.Action):
    """Action used for appending boolean values on the command-line"""

    def __init__(self,
                 option_strings,
                 dest,
                 const,
                 default=None,
                 required=False,
                 help=None,
                 metavar=None):
        super(AppendBoolean, self).__init__(
            option_strings=option_strings,
            dest=dest,
            nargs=0,
            const=const,
            default=default,
            required=required,
            help=help,
            metavar=metavar)

    def __call__(self, parser, namespace, values, option_string=None):
        # if we find an attribute and it is equal to the default,
        # then we need to completely replace the value
        current_value = getattr(namespace, self.dest, [])
        if current_value == self.default:
            setattr(namespace, self.dest, [self.const])
        else:
            current_value.append(self.const)
            setattr(namespace, self.dest, current_value)


class MergeAction(argparse.Action):
    """Merges command-line values into a single dictionary based on separator.

    Each MergeAction has a child_action that indicates what should happen
    for each value. It uses the separator to determine the eventual
    location for each of its values.

    The dest is split up by separator and each string is in turn used to
    determine the key that should be used to store this value in the
    dictionary that will get created.

    Attributes:
        child_action: The action that determines which value is stored
        child_const: For booleans, this is the value used
        separator: A separator to split up keys in the dictionary
    """

    def __init__(self,
                 option_strings,
                 dest,
                 nargs=None,
                 const=None,
                 default=None,
                 type=None,
                 choices=None,
                 required=False,
                 help=None,
                 metavar=None,
                 child_action=None,
                 separator='.',
                 child_const=None):
        super(MergeAction, self).__init__(option_strings=option_strings,
                                          dest=dest,
                                          nargs=nargs,
                                          const=const,
                                          default=default,
                                          type=type,
                                          choices=choices,
                                          required=required,
                                          help=help,
                                          metavar=metavar,
                                          )
        self.child_action = child_action
        self.child_const = child_const
        self.separator = separator
        self.parent_names = self.dest.split(self.separator)

    def _get_leaf_dict_and_key(self, namespace):
        # Traverse the namespace down to the lowest dict and return
        # a dictionary and key that represents the "leaf" node
        if not hasattr(namespace, self.parent_names[0]):
            setattr(namespace, self.parent_names[0], {})

        current_dict = getattr(namespace, self.parent_names[0])

        for index, parent_name in enumerate(self.parent_names[1:]):
            if index == len(self.parent_names) - 2:
                return current_dict, parent_name
            elif parent_name not in current_dict:
                current_dict[parent_name] = {}

            current_dict = current_dict[parent_name]

        return current_dict, self.parent_names[-1]

    def _merge_value(self, leaf_dict, name, value):
        if self.child_action == 'store_true':
            leaf_dict[name] = True

        elif self.child_action == 'store_false':
            leaf_dict[name] = False

        elif self.child_action == AppendBoolean:
            if name in leaf_dict:
                leaf_dict[name].append(self.child_const)
            else:
                leaf_dict[name] = [self.child_const]

        elif self.child_action == 'store':
            leaf_dict[name] = value

        elif self.child_action == AppendReplace:
            if name in leaf_dict:
                leaf_dict[name].append(value)
            else:
                leaf_dict[name] = [value]

        else:
            raise ValueError("Don't know how to do action: {0}"
                             .format(self.child_action))

    def __call__(self, parser, namespace, values, option_string=None):
        if hasattr(namespace, self.dest):
            delattr(namespace, self.dest)
        leaf_dict, name = self._get_leaf_dict_and_key(namespace)
        self._merge_value(leaf_dict, name, values)
