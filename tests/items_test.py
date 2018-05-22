# -*- coding: utf-8 -*-
from argparse import ArgumentParser

import pytest
import sys

import yapconf
from yapconf.exceptions import YapconfItemError, YapconfDictItemError, \
    YapconfListItemError, YapconfItemNotFound, YapconfValueError
from yapconf.items import YapconfItem, YapconfDictItem, YapconfListItem, \
    YapconfBoolItem, from_specification

if sys.version_info > (3,):
    long = int


@pytest.mark.parametrize('clazz,kwargs,env_names', [
    (
        YapconfItem,
        {'name': 'foo', 'env_name': None, 'alt_env_names': []},
        ['FOO']
    ),
    (
        YapconfItem,
        {'name': 'foo', 'env_name': None, 'alt_env_names': ['bar']},
        ['FOO', 'bar']
    ),
    (
        YapconfItem,
        {'name': 'foo', 'env_name': None, 'alt_env_names': ['bar'],
         'env_prefix': 'MY_APP_'},
        ['MY_APP_FOO', 'MY_APP_bar']
    ),
    (
        YapconfListItem,
        {
            'name': 'foos',
            'env_name': 'FOOS',
            'alt_env_names': ['BARS'],
            'children': {'foo': YapconfItem('foo')}
        },
        []
    )
])
def test_env_names(clazz, kwargs, env_names):
    item = clazz(**kwargs)
    item = clazz(**kwargs)
    assert item.all_env_names == env_names


@pytest.mark.parametrize('clazz,kwargs,error_clazz', [
    (
        YapconfItem,
        {'name': 'foo', 'item_type': 'INVALID_TYPE'},
        YapconfItemError
    ),
    (
        YapconfItem,
        {'name': 'foo', 'choices': ['a'], 'default': 'b'},
        YapconfValueError
    ),
    (
        YapconfItem,
        {'name': 'foo', 'cli_short_name': 'too_long'},
        YapconfItemError
    ),
    (
        YapconfItem,
        {'name': 'foo', 'cli_short_name': '-'},
        YapconfItemError
    ),
    (
        YapconfDictItem,
        {'name': 'foo', 'children': {}},
        YapconfDictItemError
    ),
    (
        YapconfDictItem,
        {
            'name': 'foo',
            'children': {'item1': YapconfItem('simple_item')},
            'choices': [{'foo': 'bar'}]
        },
        YapconfDictItemError
    ),
    (
        YapconfListItem,
        {
            'name': 'foo',
            'children': {
                'item1': YapconfItem('simple_item'),
                'item2': YapconfBoolItem('my_bool')}
        },
        YapconfListItemError
    )
])
def test_bad_specifications(clazz, kwargs, error_clazz):
    with pytest.raises(error_clazz):
        clazz(**kwargs)


def test_get_config_value_not_found_and_required(simple_item):
    with pytest.raises(YapconfItemNotFound):
        simple_item.get_config_value({})


def test_get_config_value_not_required(simple_item):
    simple_item.required = False
    assert simple_item.get_config_value({}) is None


@pytest.mark.parametrize('default,config,expected', [
    ('default', [('dict1', {})], 'default'),
    ('default', [('dict1', {'foo': None})], 'default')
])
def test_get_config_value_from_default(simple_item, default, config, expected):
    simple_item.default = default
    assert simple_item.get_config_value(config) == expected


def test_get_config_value_from_override(simple_item):
    simple_item.default = 'default'
    assert simple_item.get_config_value([('dict-1', {'foo': 'bar'})]) == 'bar'


@pytest.mark.parametrize('item_type,orig,expected', [
    ('str', 123, '123'),
    ('int', '123', 123),
    ('long', '123', long('123')),
    ('complex', '2j', 2j),
])
def test_convert_config_value(simple_item, item_type, orig, expected):
    simple_item.item_type = item_type
    assert simple_item.convert_config_value(orig, 'label') == expected


@pytest.mark.parametrize('orig,expected', [
    (True, True),
    (False, False),
    ('t', True),
    ('TrUe', True),
    ('y', True),
    ('yes', True),
    ('f', False),
    ('False', False),
    ('n', False),
    ('no', False),
    (1, True),
    (0, False),
    ('1', True),
    ('0', False),
])
def test_convert_bool_config_value(bool_item, orig, expected):
    assert bool_item.convert_config_value(orig, 'label') == expected


@pytest.mark.parametrize('item_type,value,exc_clazz', [
    ('int', [], YapconfValueError),
    ('INVALID_TYPE', 'value', YapconfItemError),
    ('int', object, YapconfValueError),
])
def test_convert_config_value_error(simple_item, item_type, value, exc_clazz):
    simple_item.item_type = item_type
    with pytest.raises(exc_clazz):
        simple_item.convert_config_value(value, 'label')


def test_convert_config_value_invalid_bool(bool_item):
    with pytest.raises(YapconfValueError):
        bool_item.convert_config_value('INVALID_VALUE', 'label')


@pytest.mark.parametrize('env_name,alt_names, default,config,expected', [
    ('FOO', [], None, {'FOO': 'foo_value', 'foo': 'should not be this'},
     'foo_value'),
    ('FOO', [], 'default', {'FOO': 'foo_value', 'foo': 'should not be this'},
     'foo_value'),
    ('FOO', [], 'default', {'FOO': None}, 'default'),
    ('FOO', [], 'default', {'FOO': ''}, 'default'),
    ('FOO', ['FOO_BACKUP'], None, {'FOO_BACKUP': 'foo_backup_value'},
     'foo_backup_value')
])
def test_get_config_value_from_environment(simple_item, env_name, alt_names,
                                           default, config, expected):
    simple_item.alt_env_names = alt_names
    simple_item.env_name = env_name
    simple_item.default = default
    value = simple_item.get_config_value([('ENVIRONMENT', config)])
    assert value == expected


def test_get_config_value_unformatted_env(unformatted_item):
    value = unformatted_item.get_config_value(
        [('ENVIRONMENT', {unformatted_item.name: 'value'})])
    assert value == 'value'


def test_get_config_value_for_list(list_item):
    value = list_item.get_config_value([('label', {'foos': ['foo1', 'foo2']})])
    assert value == ['foo1', 'foo2']


def test_get_config_value_for_list_not_there(list_item):
    with pytest.raises(YapconfItemNotFound):
        list_item.get_config_value({})


def test_get_config_value_with_default(list_item):
    list_item.default = ['foo1', 'foo2']
    value = list_item.get_config_value({})
    assert value == ['foo1', 'foo2']


def test_get_config_list_value_not_required(list_item):
    list_item.required = False
    assert list_item.get_config_value({}) is None


def test_get_config_value_not_a_list(list_item):
    with pytest.raises(YapconfValueError):
        list_item.get_config_value([('label', {'foos': 123})])


def test_convert_config_value_not_a_list(list_item):
    with pytest.raises(YapconfValueError):
        list_item.convert_config_value(123, 'label')


def test_get_config_ignore_environment(list_item):
    list_item.env_name = 'FOOS'
    value = list_item.get_config_value(
        [
            ('ENVIRONMENT', {'FOOS': ['foo1', 'foo2']}),
            ('label', {'foos': ['foo3', 'foo4']})
        ]
    )
    assert value == ['foo3', 'foo4']


def test_dict_get_config_value(dict_item):
    value = dict_item.get_config_value(
        [
            ('label1', yapconf.flatten({'foo_dict': {'foo': 'bar'}}))
        ]
    )
    assert value == {'foo': 'bar'}


def test_dict_get_config_value_ignore_environment(dict_item):
    dict_item.env_name = 'FOO_DICT'
    value = dict_item.get_config_value([
        ('ENVIRONMENT', {'FOO_DICT': {'foo': 'bar'}}),
        ('label1', yapconf.flatten({'foo_dict': {'foo': 'baz'}}))
    ])
    assert value == {'foo': 'baz'}


@pytest.mark.parametrize('current_default,new_default,respect_flag,expected', [
    (None, 'foo', False, 'foo'),
    (None, None, False, None),
    ('foo', None, False, 'foo'),
    ('foo', None, True, None)
])
def test_update_default(simple_item, current_default, new_default,
                        respect_flag, expected):
    simple_item.default = current_default
    simple_item.update_default(new_default, respect_none=respect_flag)
    assert simple_item.default == expected


@pytest.mark.parametrize('type,required,default,short,args,expected', [
    ('str', True, 'default_value', None, ['--foo', 'foo_value'], 'foo_value'),
    ('str', True, 'default_value', None, [], None),
    ('str', False, None, None, [], None),
    ('str', True, None, 'f', ['-f', 'foo_value'], 'foo_value'),
    ('int', True, None, 'f', ['-f', '1'], 1),
    ('long', True, None, 'f', ['-f', '1'], long(1)),
    ('float', True, None, 'f', ['-f', '1.23'], 1.23),
    ('complex', True, None, 'f', ['-f', '2j'], 2j),
])
def test_add_argument(simple_item, type, required,
                      default, short, args, expected):
    simple_item.item_type = type
    simple_item.required = required
    simple_item.default = default
    simple_item.cli_short_name = short
    parser = ArgumentParser()
    simple_item.add_argument(parser)
    values = vars(parser.parse_args(args))
    assert values[simple_item.name] == expected


@pytest.mark.parametrize('default,short_name,args,expected', [
    (True, None, ['--no-my-bool'], False),
    (False, None, ['--my-bool'], True),
    (None, None, ['--my-bool'], True),
    (None, None, ['--no-my-bool'], False),
    (None, 'b', ['--no-b'], False),
    (None, 'b', ['--b'], True),
    (True, None, [], None),
    (False, None, [], None),
])
def test_add_bool_argument(bool_item, default, short_name, args, expected):
    bool_item.default = default
    bool_item.cli_short_name = short_name
    parser = ArgumentParser()
    bool_item.add_argument(parser)
    values = vars(parser.parse_args(args))
    assert values[bool_item.name] == expected


def test_add_argument_unformatted(unformatted_item):
    parser = ArgumentParser()
    unformatted_item.add_argument(parser)
    args = ['--%s' % unformatted_item.name, 'value']
    values = vars(parser.parse_args(args))
    assert values[unformatted_item.name] == 'value'


def test_add_argument_unformatted_bool(unformatted_bool_item):
    parser = ArgumentParser()
    unformatted_bool_item.add_argument(parser)
    args = ['--no-%s' % unformatted_bool_item.name]
    values = vars(parser.parse_args(args))
    assert values[unformatted_bool_item.name] is False


@pytest.mark.parametrize('list_default,child_default,args,expected', [
    (None, True, ['--my-bool', '--no-my-bool'], [True, False]),
    (None, False, ['--no-my-bool', '--my-bool'], [False, True]),
    ([True, False], False, [], None),
    ([True, False], None, [], None),
    ([True, False], None, ['--my-bool'], [True]),
    ([True, False], None, ['--no-my-bool'], [False]),
])
def test_add_list_boolean_arguments(bool_list_item,
                                    list_default,
                                    child_default,
                                    args,
                                    expected):
    bool_list_item.default = list_default
    bool_list_item.child.default = child_default
    parser = ArgumentParser()
    bool_list_item.add_argument(parser)
    values = vars(parser.parse_args(args))

    assert values[bool_list_item.name] == expected


@pytest.mark.parametrize('list_default,child_default,args,expected', [
    (None, None, ['--foo', 'foo1', '--foo', 'foo2'], ['foo1', 'foo2']),
    (None, "foo", ['--foo', 'foo1', '--foo', 'foo2'], ['foo1', 'foo2']),
    (['foo1', 'foo2'], 'foo', [], None),
    ([], 'foo', [], None),
    (['foo1', 'foo2'], None, ['--foo', 'foo'], ['foo']),
])
def test_add_list_arguments(list_item,
                            list_default,
                            child_default,
                            args,
                            expected):
    list_item.default = list_default
    list_item.child.default = child_default
    parser = ArgumentParser()
    list_item.add_argument(parser)
    values = vars(parser.parse_args(args))
    assert values[list_item.name] == expected


@pytest.mark.parametrize('dict_default,args,expected', [
    (
        None,
        ['--db-name', 'db_name', '--db-port', '123', '--db-verbose',
         '--db-users', 'user1', '--db-users', 'user2',
         '--db-log-level', 'INFO',
         '--db-log-file', '/path/to/file'],
        {
            'name': 'db_name',
            'port': 123,
            'verbose': True,
            'users': ['user1', 'user2'],
            'log': {
                'level': 'INFO',
                'file': '/path/to/file'
            }
        }
    )
])
def test_basic_dict_add_argument(db_item,
                                 dict_default,
                                 args,
                                 expected):
    db_item.default = dict_default
    parser = ArgumentParser()
    db_item.add_argument(parser)
    values = vars(parser.parse_args(args))
    assert values[db_item.name] == expected


def test_basic_dict_get_config_value_from_env(db_item):
    value = db_item.get_config_value(
        [
            (
                'ENVIRONMENT',
                {
                    'ALT_NAME': 'db_name',
                    'DB_PORT': '1234',
                    'DB_VERBOSE': 'True'
                }
            ),
            (
                'dict1',
                yapconf.flatten({
                    'db': {
                        'users': ['user1', 'user2'],
                        'log': {'level': 'INFO', 'file': '/some/file'}
                    }
                })
            )
        ]
    )
    assert value['name'] == 'db_name'
    assert value['port'] == 1234


@pytest.mark.parametrize('item,config', [
    (
        YapconfItem("foo", choices=['a', 'b', 'c']),
        {'foo': 'd'}
    ),
    (
        YapconfListItem("foos",
                        children={
                            'foo': YapconfItem('foo',
                                               choices=['a', 'b', 'c'])
                        }),
        {'foos': ['d']},
    ),
    (
        YapconfListItem("foos",
                        choices=[['a', 'a'], ['a', 'b'], ['c']],
                        children={
                            'foo': YapconfItem('foo',
                                               choices=['a', 'b', 'c'])
                        }),
        {'foos': ['a']}
    ),
    (
        YapconfDictItem("foo_dict",
                        children={
                            "foo": YapconfItem('foo',
                                               choices=['bar', 'baz'],
                                               prefix='foo_dict')
                        }),
        yapconf.flatten({'foo_dict': {'foo': 'invalid'}})
    ),
])
def test_choices(item, config):
    with pytest.raises(YapconfValueError):
        item.get_config_value([('test', config)])


def test_from_spec_list_fq_names():
    spec = {
        'list1': {
            'type': 'list',
            'required': True,
            'items': {
                'list_item': {
                    'type': 'str',
                    'required': True
                },
            },
        },
        'list2': {
            'type': 'list',
            'required': True,
            'items': {
                'list_dict_item': {
                    'type': 'dict',
                    'required': True,
                    'items': {
                        'foo': {},
                        'bar': {},
                    },
                },
            },
        },
    }
    items = from_specification(spec)
    assert items['list1'].fq_name == 'list1'
    assert items['list1'].children['list1'].fq_name == 'list1'
    assert items['list2'].children['list2'].fq_name == 'list2'
    assert (
        items['list2'].children['list2'].children['foo'].fq_name ==
        'list2.foo'
    )
    assert (
        items['list2'].children['list2'].children['bar'].fq_name ==
        'list2.bar'
    )


def test_from_specification_check_fq_names():
    spec = {
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
    }
    items = from_specification(spec)
    assert items['foo'].fq_name == 'foo'
    assert items['foo'].children['bar'].fq_name == 'foo.bar'
    assert (
        items['foo'].children['bar'].children['baz'].fq_name == 'foo.bar.baz'
    )
    assert items['foo'].children['bat'].fq_name == 'foo.bat'


def test_invalid_value():
    def always_invalid(value):
        return False
    item = from_specification({'foo': {'validator': always_invalid}})['foo']
    with pytest.raises(YapconfValueError):
        item.get_config_value([('label', {'foo': 'bar'})])
