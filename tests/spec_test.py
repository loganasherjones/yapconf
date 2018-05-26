# -*- coding: utf-8 -*-
import json
import os
import sys
from argparse import ArgumentParser

import pytest
from mock import Mock, mock_open, patch
from ruamel import yaml

import yapconf
from yapconf.exceptions import (YapconfItemNotFound, YapconfLoadError,
                                YapconfSourceError, YapconfSpecError)
from yapconf.spec import YapconfSpec

if sys.version_info > (3,):
    long = int

original_env = None
original_yaml = yapconf.yaml
current_dir = os.path.abspath(os.path.dirname(__file__))


def setup_function(function):
    global original_env
    original_env = os.environ.copy()


def teardown_function(function):
    os.environ = original_env
    yapconf.yaml = original_yaml
    tmp_path = os.path.join(current_dir, 'files', 'real_world', 'tmp')
    if os.path.exists(tmp_path):
        os.remove(tmp_path)


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
    with pytest.raises(YapconfSourceError):
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


@pytest.mark.usefixtures('basic_spec')
@pytest.mark.parametrize('config', [
    ({'foo': None}),
    ({'foo': 'bar'}),
    ({'foo': u'bar'}),
    ({'foo': u'\U0001F4A9'}),
    ({'foo': u'💩'}),
    ({u'\U0001F4A9': 'foo'}),
    ({u'💩': 'foo'}),
    ({u'💩': u'💩'}),
])
def test_migrate_config_no_mock_existing_file(tmpdir, basic_spec, config):
    new_path = tmpdir.join('config.json')
    new_path.ensure()

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


@patch('os.path.isfile', Mock(return_value=True))
@pytest.mark.parametrize(
    'filename,expected,always_update,update_defaults,output_file_type', [
        (
            'default_current_config.yaml',
            pytest.lazy_fixture('default_current_config'),
            False,
            True,
            'yaml',
        ),
        (
            'default_previous_config.yaml',
            pytest.lazy_fixture('default_current_config'),
            False,
            True,
            'yaml',
        ),
        (
            'previous_config.yaml',
            {
                'emoji': u'🐍',
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
            },
            False,
            True,
            'json',
        ),
    ]
)
def test_real_world_migrations(
    real_world_spec,
    filename,
    expected,
    always_update,
    update_defaults,
    output_file_type
):
    real_world_path = os.path.join(current_dir, 'files', 'real_world')
    full_path = os.path.join(real_world_path, filename)
    tmp_config = os.path.join(real_world_path, 'tmp')

    new_config = real_world_spec.migrate_config_file(
        full_path,
        create=True,
        update_defaults=update_defaults,
        always_update=always_update,
        output_file_type=output_file_type,
        output_file_name=tmp_config
    )

    assert new_config == expected

    assert real_world_spec.load_config(tmp_config) == expected


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


@pytest.mark.usefixtures('simple_spec')
@pytest.mark.parametrize('key', [
    '/',
    '/foo/bar/',
])
def test_load_etcd(simple_spec, key):
    children = [
        Mock(key='%smy_string' % key, value='str_val'),
        Mock(key='%smy_int' % key, value='123'),
        Mock(key='%smy_long' % key, value='12341234'),
        Mock(key='%smy_float' % key, value='123.123'),
        Mock(key='%smy_bool' % key, value='true'),
        Mock(key='%smy_complex' % key, value='1j'),
    ]

    etcd_result = Mock(dir=True)
    etcd_result.__iter__ = Mock(return_value=iter(children))
    client = Mock(spec=yapconf.etcd_client.Client)
    client.read = Mock(return_value=etcd_result)
    simple_spec.add_source('etcd', 'etcd', client=client)
    config = simple_spec.load_config('etcd')
    assert config == {
        'my_string': 'str_val',
        'my_int': 123,
        'my_long': 12341234,
        'my_float': 123.123,
        'my_bool': True,
        'my_complex': 1j,
    }


@pytest.mark.parametrize('data,filename,file_type', [
    (None, 'unicode.json', 'json'),
    (None, 'unicode.yaml', 'yaml'),
    (pytest.lazy_fixture('example_data'), None, 'json'),
])
def test_load_from_source(
    example_spec,
    example_data,
    data,
    filename,
    file_type
):
    example_path = os.path.join(current_dir, 'files')
    if filename is not None:
        full_path = os.path.join(example_path, filename)
    else:
        full_path = None

    if data is not None:
        data = json.dumps(data)

    example_spec._file_type = file_type
    example_spec.add_source(
        'example',
        file_type,
        filename=full_path,
        data=data
    )

    config = example_spec.load_config('example')
    assert config == example_data


@pytest.mark.usefixtures('simple_spec')
@pytest.mark.parametrize('key,config_type,formatter', [
    (None, None, None),
    ('file.yaml', 'yaml', yaml.dump),
    ('file.json', 'json', json.dumps),
])
def test_load_kubernetes(simple_spec, key, config_type, formatter):
    data = {
        'my_string': 'str_val',
        'my_int': '123',
        'my_long': '12341234',
        'my_float': '123.123',
        'my_bool': 'True',
        'my_complex': '1j',
    }
    if formatter:
        data = formatter(data)

    if key:
        to_return = {key: data}
    else:
        to_return = data

    client = Mock(spec=yapconf.kubernetes_client.CoreV1Api)
    client.read_namespaced_config_map = Mock(return_value=Mock(data=to_return))
    simple_spec.add_source('kubernetes',
                           'kubernetes',
                           client=client,
                           config_type=config_type,
                           key=key)
    config = simple_spec.load_config('kubernetes')
    assert config == {
        'my_string': 'str_val',
        'my_int': 123,
        'my_long': 12341234,
        'my_float': 123.123,
        'my_bool': True,
        'my_complex': 1j,
    }
