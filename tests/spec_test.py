# -*- coding: utf-8 -*-
from argparse import ArgumentParser

import pytest
import yapconf
from mock import patch, mock_open, Mock

from yapconf.exceptions import YapconfSpecError, YapconfLoadError, \
    YapconfItemNotFound
from yapconf.spec import YapconfSpec

import sys
import os
import json

# Hack so that tox works correctly in multiple
# versions of python
builtins_path = '__builtin__'
if sys.version_info > (3,):
    builtins_path = 'builtins'
    long = int
else:
    builtins_path = 'yapconf.spec'

original_env = None
original_yaml = yapconf.yaml


def setup_function(function):
    global original_env
    original_env = os.environ.copy()


def teardown_function(function):
    os.environ = original_env
    yapconf.yaml = original_yaml


@pytest.fixture
def basic_spec():
    """Most basic spec you can have"""
    return YapconfSpec({'foo': {'type': 'str', 'required': True}})


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
    return YapconfSpec({
        'file': {
            'type': 'str',
            'required': True,
            'default': '/default/path/to/file.yaml',
            'bootstrap': True,
            'env_name': 'MY_APP_CONFIG_FILE',
            'cli_short_name': 'f',
            'previous_defaults': ['./file.yaml']
        },
        'web_port': {
            'type': 'int',
            'required': True,
            'default': 3000,
            'previous_names': ['web.port'],
            'cli_short_name': 'p',
            'previous_defaults': [1234, 2345]
        },
        'ssl': {
            'type': 'dict',
            'required': True,
            'items': {
                'private_key': {
                    'type': 'str',
                    'required': True,
                    'default': '/etc/certs/private.key',
                    'previous_names': ['web.key']
                },
                'public_key': {
                    'type': 'str',
                    'required': True,
                    'default': '/etc/certs/public.crt',
                    'previous_names': ['web.crt']
                }
            }
        },
        'database': {
            'type': 'dict',
            'required': True,
            'items': {
                'name': {
                    'type': 'str',
                    'required': True,
                    'default': 'myapp',
                    'previous_names': ['db_name'],
                    'previous_defaults': ['test']
                },
                'host': {
                    'type': 'str',
                    'required': True,
                    'default': 'localhost',
                    'previous_names': ['db_host'],
                },
                'port': {
                    'type': 'int',
                    'required': True,
                    'default': 3306,
                    'previous_names': ['db_port']
                },
                'verbose': {
                    'type': 'bool',
                    'required': True,
                    'default': False,
                    'previous_defaults': [True],
                }
            }
        }
    }, env_prefix='MY_APP_')


def test_simple_load_config(simple_spec):
    config = simple_spec.load_config({'my_string': 'some value',
                                      'my_int': 123,
                                      'my_long': long(123),
                                      'my_float': 123.45,
                                      'my_bool': False,
                                      'my_complex': 2j,
                                      })
    assert config['my_string'] == 'some value'
    assert config['my_int'] == 123
    assert config['my_long'] == long(123)
    assert config['my_float'] == 123.45
    assert not config['my_bool']
    assert config['my_complex'] == 2j


def test_load_list_config(spec_with_lists):
    config = spec_with_lists.load_config({
        'simple_list': ['a', 'b', 'c'],
        'top_list': [[1, 2, 3], [4, 5, 6]],
        'list_of_dictionaries': [
            {'foo': 'foo_value', 'bar': 'bar_value'},
            {'foo': 'foo_value2', 'bar': 'bar_value2'}
        ]
    })

    assert len(config['simple_list']) == 3
    assert 'a' in config['simple_list']
    assert 'b' in config['simple_list']
    assert 'c' in config['simple_list']

    assert len(config['top_list']) == 2
    assert len(config['top_list'][0]) == 3
    assert len(config['top_list'][1]) == 3

    assert len(config['list_of_dictionaries']) == 2
    assert 'foo' in config['list_of_dictionaries'][0]
    assert 'bar' in config['list_of_dictionaries'][0]
    assert 'foo' in config['list_of_dictionaries'][1]
    assert 'bar' in config['list_of_dictionaries'][1]


def test_nested_load_config(spec_with_dicts):
    config = spec_with_dicts.load_config(
        {
            'database': {
                'name': 'dbname',
                'host': 'dbhost',
                'port': 1234
            },
            'foo': {
                'bar': {'baz': 'baz_value'},
                'bat': True
            }
        }
    )
    assert config['database']['name'] == 'dbname'
    assert config['database']['host'] == 'dbhost'
    assert config['database']['port'] == 1234

    assert config['foo']['bar']['baz'] == 'baz_value'
    assert config['foo']['bat']


def test_spec_bad_file_type():
    with pytest.raises(YapconfSpecError):
        YapconfSpec({}, file_type='INVALID')


@pytest.mark.parametrize('bad_data', [
    (['THIS SHOULD BE A DICT']),
    ({'name': 'THIS SHOULD BE A DICT'}),
    ({'name': {'type': 'str', 'items': {'name2': {'type': 'str'}}}}),
    ({'name': {'type': 'list', 'error': 'it has not items entry'}}),
])
def test_invalid_specification(bad_data):
    with pytest.raises(YapconfSpecError):
        YapconfSpec(bad_data)


def test_load_config_fallbacks(simple_spec):
    config = simple_spec.load_config(
        {'my_string': 'some value'},
        {'my_int': 123},
        {'my_long': long(123)},
        {'my_float': 123.45},
        {'my_bool': False},
        {'my_complex': 2j}
    )
    assert config['my_string'] == 'some value'
    assert config['my_int'] == 123
    assert config['my_long'] == long(123)
    assert config['my_float'] == 123.45
    assert not config['my_bool']
    assert config['my_complex'] == 2j


@pytest.mark.parametrize('file_type,file_data,overrides,expected_value', [
    ('json', '{"foo": {"type": "str"}}', {"foo": "bar"}, {"foo": "bar"}),
    ('yaml',
     '''foo:
        type: str''',
     {'foo': 'bar'},
     {'foo': 'bar'})
])
def test_load_specification_from_file(file_type, file_data,
                                      overrides, expected_value):
    open_path = 'yapconf.open'
    with patch(open_path, mock_open(read_data=file_data)):
        spec = YapconfSpec('/path/to/specification', file_type=file_type)
        assert spec.load_config(overrides) == expected_value


def test_load_bad_specification_from_file():
    open_path = 'yapconf.open'
    with patch(open_path, mock_open(read_data="[]")):
        with pytest.raises(YapconfSpecError):
            YapconfSpec('/path/to/bad/spec', file_type='json')


def test_load_from_env(basic_spec):
    os.environ['FOO'] = 'foo_value'
    config = basic_spec.load_config('ENVIRONMENT')
    assert config['foo'] == 'foo_value'


@pytest.mark.parametrize('override', [
    ("Need another item",),
    ("label", "file", "invalid_file_type"),
    (["THIS SHOULD BE A DICT"])
])
def test_load_config_invalid_override(basic_spec, override):
    with pytest.raises(YapconfLoadError):
        basic_spec.load_config(override)


def test_load_config_yaml_not_supported(basic_spec):
    yapconf.yaml = None
    with pytest.raises(YapconfLoadError):
        basic_spec.load_config(('label', 'path/to/file', 'yaml'))


def test_load_config_nested_from_environment(spec_with_dicts):
    os.environ['FOO_BAR_BAZ'] = 'baz_value'
    config = spec_with_dicts.load_config(
        {
            'database': {'name': 'dbname', 'host': 'dbhost', 'port': 1234},
            'foo': {'bat': True}
        },
        'ENVIRONMENT'
    )
    value = spec_with_dicts.load_config(config)
    assert value['foo']['bar']['baz'] == 'baz_value'


def test_load_config_multi_part_dictionary(spec_with_dicts):
    config = spec_with_dicts.load_config(
        {'database': {'name': 'dbname'}},
        {'database': {'host': 'dbhost'}},
        {'database': {'port': 1234}},
        {'foo': {'bar': {'baz': 'baz_value'}, 'bat': True}}
    )
    value = spec_with_dicts.load_config(config)
    assert value['database'] == {'name': 'dbname',
                                 'host': 'dbhost',
                                 'port': 1234}


@patch('os.path.isfile', Mock(return_value=True))
def test_migrate_config_file_no_changes(basic_spec):
    open_path = 'yapconf.open'
    current_config = '{"foo": "bar"}'
    with patch(open_path, mock_open(read_data=current_config)):
        new_config = basic_spec.migrate_config_file('/path/to/file',
                                                    create=False)

    assert new_config == {"foo": "bar"}


@patch('os.path.isfile', Mock(return_value=False))
def test_migrate_config_file_does_not_exist_do_not_create(basic_spec):
    with pytest.raises(YapconfLoadError):
        basic_spec.migrate_config_file('/path/to/file', create=False)


@patch('os.path.isfile', Mock(return_value=False))
def test_migrate_config_file_does_not_exist_create(basic_spec):
    open_path = 'yapconf.open'
    with patch(open_path, mock_open()):
        new_config = basic_spec.migrate_config_file('/path/to/file',
                                                    create=True)

    assert new_config == {"foo": None}


@patch('os.path.isfile', Mock(return_value=False))
def test_migrate_config_file_create_yaml(basic_spec):
    open_path = 'yapconf.open'
    with patch('yapconf.yaml.dump') as dump_mock:
        with patch(open_path, mock_open()) as mock_file:
            new_config = basic_spec.migrate_config_file(
                '/path/to/file', create=True, output_file_type='yaml')
            dump_mock.assert_called_with(
                {"foo": None},
                mock_file(),
                default_flow_style=False,
                encoding='utf-8')

    assert new_config == {"foo": None}


@patch('os.path.isfile', Mock(return_value=True))
def test_migrate_config_file_always_update(basic_spec):
    open_path = 'yapconf.open'
    current_config = '{"foo": "bar"}'
    with patch(open_path, mock_open(read_data=current_config)):
        new_config = basic_spec.migrate_config_file('/path/to/file',
                                                    create=False,
                                                    always_update=True)

    assert new_config == {"foo": None}


@patch('os.path.isfile', Mock(return_value=True))
def test_migrate_config_file_update_previous_default():
    spec = YapconfSpec({'foo': {'default': 'baz',
                                'previous_defaults': ['bar']}})
    open_path = 'yapconf.open'
    current_config = '{"foo": "bar"}'
    with patch(open_path, mock_open(read_data=current_config)):
        new_config = spec.migrate_config_file('/path/to/file',
                                              create=False,
                                              update_defaults=True)
    assert new_config == {'foo': 'baz'}


def test_migrate_config_no_mock(tmpdir, basic_spec):
    new_path = tmpdir.join('config.json')
    with pytest.raises(YapconfLoadError):
        basic_spec.migrate_config_file(str(new_path), create=False)


def test_migrate_config_no_mock_create_file(tmpdir, basic_spec):
    new_path = tmpdir.join('config.json')
    basic_spec.migrate_config_file(str(new_path), create=True)
    assert json.load(new_path) == {"foo": None}


def test_migrate_config_no_mock_existing_file(tmpdir, basic_spec):
    new_path = tmpdir.join('config.json')
    new_path.ensure()
    config = {"foo": None}

    with new_path.open(mode='w') as fp:
        json.dump(config, fp)

    basic_spec.migrate_config_file(str(new_path), create=False)

    with new_path.open(mode='r') as fp:
        assert json.load(fp) == config


def test_get_item(basic_spec):
    assert basic_spec.get_item('foo') is not None
    assert basic_spec.get_item('no name match') is None


def test_update_defaults(basic_spec):
    assert basic_spec.defaults == {'foo': None}
    basic_spec.update_defaults({'foo': 'bar'})
    assert basic_spec.defaults == {'foo': 'bar'}


def test_update_defaults_bad_key(basic_spec):
    with pytest.raises(YapconfItemNotFound):
        basic_spec.update_defaults({"INVALID_KEY": "bar"})


def test_load_config_real_world(real_world_spec):
    parser = ArgumentParser(conflict_handler='resolve')
    real_world_spec.add_arguments(parser, bootstrap=True)
    cli_args = ['--file', '/path/to/file.yaml',
                '--web-port', '1234',
                '--ssl-public-key', '/path/to/public.crt',
                '--ssl-private-key', '/path/to/private.key',
                '--database-verbose'
                ]
    cli_values = vars(parser.parse_args(cli_args))
    bootstrap_config = real_world_spec.load_config(
        ('boostrap_cli', cli_values), 'ENVIRONMENT',
        bootstrap=True
    )
    os.environ['MY_APP_DATABASE_HOST'] = 'db_host_from_env'

    # Pretend we load this from bootstrap_config.file
    # Normally, you could just specify bootstrap_config.file
    # but because we are in a test, I'm not doing that.
    config_file_dict = {
        'ssl': {
            'public_key': '/path/to/public/from/file.crt',
            'private_key': '/path/to/private/from/file.key'
        },
        'database': {
            'name': 'name_from_config_file',
        },
        'web_port': 8080,
    }

    real_world_spec.add_arguments(parser, bootstrap=False)
    cli_values = vars(parser.parse_args(cli_args))

    config = real_world_spec.load_config(*[
        ('command line', cli_values),
        (bootstrap_config['file'], config_file_dict),
        'ENVIRONMENT'])

    assert config['file'] == '/path/to/file.yaml'
    assert config['web_port'] == 1234
    assert config['ssl']['public_key'] == '/path/to/public.crt'
    assert config['ssl']['private_key'] == '/path/to/private.key'
    assert config['database']['name'] == 'name_from_config_file'
    assert config['database']['host'] == 'db_host_from_env'
    assert config['database']['port'] == 3306
    assert config['database']['verbose']


current_config = {
    'file': '/path/to/file.yaml',
    'web_port': 443,
    'ssl': {
        'private_key': '/path/to/private.key',
        'public_key': '/path/to/public.crt',
    },
    'database': {
        'name': 'myapp_prod',
        'host': '1.2.3.4',
        'port': 3306,
        'verbose': False
    }
}

previous_config = {
    'file': './file.yaml',
    'web': {
        'port': 1234,
        'key': '/previous/path/to/private.key',
        'crt': '/previous/path/to/public.crt',
    },
    'db_name': 'test',
    'db_host': 'localhost',
    'database': {
        'port': 1234
    }
}

default_current_config = {
    'file': '/default/path/to/file.yaml',
    'web_port': 3000,
    'ssl': {
        'private_key': '/etc/certs/private.key',
        'public_key': '/etc/certs/public.crt',
    },
    'database': {
        'name': 'myapp',
        'host': 'localhost',
        'port': 3306,
        'verbose': False
    }
}

previous_default_config = {
    'file': './file.yaml',
    'web': {
        'port': 2345,
        'key': '/etc/certs/private.key',
        'crt': '/etc/certs/public.crt'
    },
    'db_name': 'test',
    'db_host': 'localhost',
    'db_port': 3306,
    'database': {
        'verbose': True
    }
}


@patch('os.path.isfile', Mock(return_value=True))
@pytest.mark.parametrize('current,expected,always_update,update_defaults', [
    (current_config, current_config, False, True),
    (default_current_config, default_current_config, False, True),
    (previous_default_config, default_current_config, False, True),
    (previous_config,
     {
         'file': '/default/path/to/file.yaml',
         'web_port': 3000,
         'ssl': {
             'private_key': '/previous/path/to/private.key',
             'public_key': '/previous/path/to/public.crt'
         },
         'database': {
             'name': 'myapp',
             'host': 'localhost',
             'port': 1234,
             'verbose': False
         }
     }, False, True)
])
def test_real_world_migrations(real_world_spec, current, expected,
                               always_update, update_defaults):
    open_path = 'yapconf.open'
    with patch(open_path, mock_open(read_data=json.dumps(current))):
        new_config = real_world_spec.migrate_config_file(
            'file', create=False, update_defaults=update_defaults,
            always_update=always_update)

        assert new_config == expected


@pytest.mark.parametrize('env_name,apply_prefix,env_prefix,key', [
    ('BG_HOST', True, 'BG_', 'BG_BG_HOST'),
    ('BG_HOST', False, 'BG_', 'BG_HOST'),
    ('HOST', True, 'BG_', 'BG_HOST'),
])
def test_env_names_with_prefixes(env_name, apply_prefix, env_prefix, key):
    spec = YapconfSpec(
        {
            'bg_host': {
                'type': 'str',
                'env_name': env_name,
                'apply_env_prefix': apply_prefix,
            }
        }, env_prefix=env_prefix)

    config = spec.load_config(('ENVIRONMENT', {key: 'host_value'}))
    assert config.bg_host == 'host_value'
