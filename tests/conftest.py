# -*- coding: utf-8 -*-
import pytest

from yapconf.items import from_specification


@pytest.fixture
def simple_item_spec():
    """A specification for a string item."""
    return {'foo': {}}


@pytest.fixture
def bool_item_spec():
    """A specification for a boolean item."""
    return {'my_bool': {'type': 'bool', 'required': True}}


@pytest.fixture
def unformatted_item_spec():
    """A specification for an unformatted string item."""
    return {
        'weirdName-Cool_stuff lol': {
            'required': True,
            'format_env': False,
            'format_cli': False,
        }
    }


@pytest.fixture
def unformatted_bool_item_spec():
    """A specification for an unformatted boolean item."""
    return {
        'weirdName-Cool_stuff lol': {
            'type': 'bool',
            'required': True,
            'format_env': False,
            'format_cli': False,
        }
    }


@pytest.fixture
def list_item_spec(simple_item_spec):
    """A specification for a list item."""
    return {
        'foos': {
            'required': True,
            'items': {'simple_item': simple_item_spec}
        }
    }


@pytest.fixture
def bool_list_item_spec(bool_item_spec):
    """A specification for a list of boolean items."""
    return {
        'my_bools': {
            'required': True,
            'items': bool_item_spec
        }
    }


@pytest.fixture
def simple_item(simple_item_spec):
    """A YacponfItem for a string config value."""
    return from_specification(simple_item_spec)['foo']


@pytest.fixture
def bool_item(bool_item_spec):
    """A YacponfItem for a boolean config value."""
    return from_specification(bool_item_spec)['my_bool']


@pytest.fixture
def unformatted_item(unformatted_item_spec):
    """A YapconfItem for an unformatted string value."""
    items = from_specification(unformatted_item_spec)
    return items['weirdName-Cool_stuff lol']


@pytest.fixture
def unformatted_bool_item(unformatted_bool_item_spec):
    """A YapconfItem for an unformatted boolean value."""
    # unformatted_item_spec['type'] = 'bool'
    items = from_specification(unformatted_bool_item_spec)
    return items['weirdName-Cool_stuff lol']


@pytest.fixture
def list_item(simple_item_spec):
    """A YapconfItem for a list value."""
    return from_specification({
        'foos': {
            'type': 'list',
            'items': {
                'simple_item': simple_item_spec
            }
        }
    })['foos']


@pytest.fixture
def bool_list_item(bool_item_spec):
    """A YapconfItem for a list of boolean values."""
    return from_specification({
        'my_bools': {
            'type': 'list',
            'items': bool_item_spec
        }
    })['my_bools']


@pytest.fixture
def dict_item(simple_item_spec):
    """A YapconfItem for a dictionary."""
    return from_specification({
        'foo_dict': {
            'type': 'dict',
            'items': {'foo': simple_item_spec}
        }
    })['foo_dict']


@pytest.fixture
def db_item():
    """A YapconfItem for a dictionary that represents a db config."""
    return from_specification(
        {
            'db': {
                'type': 'dict',
                'items': {
                    'name': {
                        'required': True,
                        'alt_env_names': ['ALT_NAME'],
                    },
                    'port': {
                        'required': True,
                        'type': 'int',
                    },
                    'verbose': {
                        'required': True,
                        'type': 'bool',
                    },
                    'users': {
                        'type': 'list',
                        'required': True,
                        'items': {
                            'user': {
                                'required': True,
                                'type': 'str',
                            },
                        },
                    },
                    'log': {
                        'type': 'dict',
                        'required': True,
                        'items': {
                            'level': {
                                'required': True,
                                'type': 'str'
                            },
                            'file': {
                                'required': True,
                                'type': 'str'
                            },
                        },
                    },
                },
            },
        },
    )['db']
