# -*- coding: utf-8 -*-
import os

import pytest

import yapconf
from yapconf import YapconfSpec
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


@pytest.fixture
def basic_spec(simple_item_spec):
    """Most basic spec you can have"""
    return YapconfSpec(simple_item_spec)


@pytest.fixture
def simple_spec():
    """Simple YapconfSpec for all YapconfItem variations"""
    return YapconfSpec(
        {
            'my_string': {'type': 'str', 'required': True, },
            'my_int': {'type': 'int', 'required': True, },
            'my_long': {'type': 'long', 'required': True, },
            'my_float': {'type': 'float', 'required': True, },
            'my_bool': {'type': 'bool', 'required': True, },
            'my_complex': {'type': 'complex', 'required': True, },
        }
    )


@pytest.fixture
def spec_with_lists():
    """YapconfSpec for testing YapconfListItem variations"""
    return YapconfSpec(
        {
            'simple_list': {
                'type': 'list',
                'required': True,
                'items': {
                    'list_item': {
                        'type': 'str', 'required': True
                    }
                }
            },
            'top_list': {
                'type': 'list',
                'required': True,
                'items': {
                    'nested_list': {
                        'type': 'list',
                        'required': True,
                        'items': {
                            'nested_list_items': {
                                'type': 'int',
                                'required': True
                            }
                        }
                    }
                }
            },
            'list_of_dictionaries': {
                'type': 'list',
                'required': True,
                'items': {
                    'list_item': {
                        'type': 'dict',
                        'required': True,
                        'items': {
                            'foo': {'type': 'str', 'required': True, },
                            'bar': {'type': 'str', 'required': False, }
                        }
                    }
                }
            }
        }
    )


@pytest.fixture
def spec_with_dicts():
    """YapconfSpec for testing YapconfDictItem variations"""
    return YapconfSpec({
        'database': {
            'type': 'dict',
            'required': True,
            'items': {
                'name': {'type': 'str', 'required': True, },
                'host': {'type': 'str', 'required': True, },
                'port': {'type': 'int', 'required': True, },
            }
        },
        'foo': {
            'type': 'dict',
            'required': True,
            'items': {
                'bar': {
                    'type': 'dict',
                    'required': True,
                    'items': {
                        'baz': {
                            'type': 'str', 'required': True,
                        },
                    },
                },
                'bat': {
                    'type': 'bool',
                }
            },
        },
    })


@pytest.fixture
def real_world_spec():
    """YapconfSpec based on a 'real-world' example"""
    current_dir = os.path.abspath(os.path.dirname(__file__))
    filename = os.path.join(current_dir, 'files', 'real_world', 'spec.yaml')
    return YapconfSpec(filename, file_type='yaml', env_prefix='MY_APP_')


@pytest.fixture
def current_config():
    current_dir = os.path.abspath(os.path.dirname(__file__))
    filename = os.path.join(
        current_dir,
        'files',
        'real_world',
        'current_config.yaml'
    )
    return yapconf.load_file(filename, 'yaml')


@pytest.fixture
def previous_config():
    current_dir = os.path.abspath(os.path.dirname(__file__))
    filename = os.path.join(
        current_dir,
        'files',
        'real_world',
        'previous_config.yaml'
    )
    return yapconf.load_file(filename, 'yaml')


@pytest.fixture
def default_current_config():
    current_dir = os.path.abspath(os.path.dirname(__file__))
    filename = os.path.join(
        current_dir,
        'files',
        'real_world',
        'default_current_config.yaml'
    )
    return yapconf.load_file(filename, 'yaml')


@pytest.fixture
def default_previous_config():
    current_dir = os.path.abspath(os.path.dirname(__file__))
    filename = os.path.join(
        current_dir,
        'files',
        'real_world',
        'default_previous_config.yaml'
    )
    return yapconf.load_file(filename, 'yaml')


@pytest.fixture
def example_spec():
    return YapconfSpec(
        {
            'foo': {},
            'emoji': {},
            u'💩': {},
            'db': {
                'type': 'dict',
                'items': {
                    'name': {},
                    'port': {'type': 'int'}
                }
            },
            'items': {
                'type': 'list',
                'items': {
                    'item': {'type': 'int'},
                },
            },
        }
    )


@pytest.fixture
def example_data():
    return {
        "foo": "bar",
        "emoji": u"💩",
        u"💩": u"🐍",
        "db": {
            "name": "db_name",
            "port": 123
        },
        "items": [1, 2, 3]
    }


@pytest.fixture
def fallback_spec():
    return YapconfSpec({
        'defaults': {
            'type': 'dict',
            'items': {
                'str': {'type': 'str', 'default': 'default_str'},
                'int': {'type': 'int', 'default': 123},
                'long': {'type': 'long', 'default': 123},
                'float': {'type': 'float', 'default': 123.123},
                'bool': {'type': 'bool', 'default': True},
                'complex': {'type': 'complex', 'default': 1j},
                'list': {
                    'type': 'list',
                    'default': [1, 2, 3],
                    'items': {
                        'list_item': {'type': 'int', 'default': 1}
                    },
                },
                'dict': {
                    'type': 'dict',
                    'default': {'foo': 'dict_default'},
                    'items': {
                        'foo': {'type': 'str', 'default': 'item_default'}
                    },
                },
            },
        },
        'str': {'type': 'str', 'fallback': 'defaults.str'},
        'int': {'type': 'int', 'fallback': 'defaults.int'},
        'long': {'type': 'long', 'fallback': 'defaults.long'},
        'float': {'type': 'float', 'fallback': 'defaults.float'},
        'bool': {'type': 'bool', 'fallback': 'defaults.bool'},
        'complex': {'type': 'complex', 'fallback': 'defaults.complex'},
        'list': {
            'type': 'list',
            'fallback': 'defaults.list',
            'items': {
                'list_item': {
                    'type': 'int',
                    'fallback': 'defaults.list.list_item'
                },
            },
        },
        'dict': {
            'type': 'dict',
            'fallback': 'defaults.dict',
            'items': {
                'foo': {
                    'type': 'str',
                    'fallback': 'defaults.dict.foo'
                },
            },
        },
    })
