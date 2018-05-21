# -*- coding: utf-8 -*-
import os
import pytest
import yapconf


@pytest.fixture
def ascii_data():
    return {
        'foo': 'bar',
        'db': {'name': 'db_name', 'port': 123},
        'items': [1, 2, 3]
    }


@pytest.fixture
def unicode_data():
    return {
        'foo': 'bar',
        'db': {'name': 'db_name', 'port': 123},
        'items': [1, 2, 3],
        u'💩': u'🐍',
        'emoji': u'💩'
    }


@pytest.mark.parametrize('orig,expected', [
    ('CamelCase', 'camel-case'),
    ('CamelCamelCase', 'camel-camel-case'),
    ('Camel2Camel2Case', 'camel2-camel2-case'),
    ('getHTTPResponseCode', 'get-http-response-code'),
    ('get2HTTPResponseCode', 'get2-http-response-code'),
    ('HTTPResponseCode', 'http-response-code'),
    ('HTTPResponseCodeXYZ', 'http-response-code-xyz'),
    ('snake_case', 'snake-case'),
    ('snake_snake_case', 'snake-snake-case'),
    ('snake2_snake2_case', 'snake2-snake2-case'),
    (' CamelGetHTTPResponse_code_snake2_case is a pain',
     'camel-get-http-response-code-snake2-case-is-a-pain')
])
def test_convert_camel_to_kebab(orig, expected):
    assert expected == yapconf.change_case(orig)


@pytest.mark.parametrize('filename,file_type,expected', [
    (
        'ascii.yaml',
        'yaml',
        pytest.lazy_fixture('ascii_data')
    ),
    (
        'unicode.yaml',
        'yaml',
        pytest.lazy_fixture('unicode_data')
    ),
    (
        'ascii.json',
        'json',
        pytest.lazy_fixture('ascii_data')
    ),
    (
        'unicode.json',
        'json',
        pytest.lazy_fixture('unicode_data')
    ),
])
def test_load_file(filename, file_type, expected):
    current_dir = os.path.abspath(os.path.dirname(__file__))
    full_path = os.path.join(current_dir, 'files', filename)
    data = yapconf.load_file(full_path, file_type=file_type)
    assert data == expected


@pytest.mark.parametrize('filename,file_type', [
    ('bad.json', 'json'),
    ('ascii.json', 'INVALID_TYPE'),
])
def test_load_file_error(filename, file_type):
    current_dir = os.path.abspath(os.path.dirname(__file__))
    full_path = os.path.join(current_dir, 'files', filename)
    with pytest.raises(ValueError):
        yapconf.load_file(full_path,
                          file_type=file_type,
                          klazz=ValueError)


@pytest.mark.parametrize('data,file_type', [
    (
        pytest.lazy_fixture('ascii_data'),
        'yaml'
    ),
    (
        pytest.lazy_fixture('unicode_data'),
        'yaml'
    ),
    (
        pytest.lazy_fixture('unicode_data'),
        'json'
    ),
    (
        pytest.lazy_fixture('ascii_data'),
        'json'
    )
])
def test_dump_data(tmpdir, data, file_type):
    path = tmpdir.join('test.%s' % file_type)
    filename = os.path.join(path.dirname, path.basename)
    yapconf.dump_data(data, filename, file_type)
    assert data == yapconf.load_file(filename, file_type)


@pytest.mark.parametrize('original,expected', [
    ({}, {}),
    ({'foo': 'bar'}, {'foo': 'bar'}),
    ({'foo': {'bar': 'baz'}}, {'foo.bar': 'baz'}),
    (
        {'foo': {'bar': {'baz': 'bat', 'bax': 'bat'}, 'bat': 'bar'}},
        {'foo.bar.baz': 'bat', 'foo.bar.bax': 'bat', 'foo.bat': 'bar'}
    ),
    (
        {
            'list': [
                {'foo': 'foo_value', 'bar': 'bar_value'},
                {'foo': 'foo_value2', 'bar': 'bar_value2'},
            ]
        },
        {
            'list': [
                {'list.foo': 'foo_value', 'list.bar': 'bar_value'},
                {'list.foo': 'foo_value2', 'list.bar': 'bar_value2'}
            ]
        }
    ),
    (
        {
            'foo': {'list1': [1], 'list2': [{'bar': 'baz'}]}
        },
        {
            'foo.list1': [1], 'foo.list2': [{'foo.list2.bar': 'baz'}]
        }
    ),
    (
        {
            'foo': {
                'list1': [
                    {
                        'bar': {
                            'list2': [1, 2, 3],
                            'bar2': 'bar2_value',
                            'bat': {
                                'bat2': 'bat2_value',
                                'bat_list_dict': [
                                    {
                                        'baz': 'baz_value',
                                        'bazl': [4, 5, 6],
                                        'bazd': {'bazd_key': 'bazd_value'}
                                    }
                                ]
                            }
                        }
                    }
                ]
            }
        },
        {
            'foo.list1': [
                {
                    'foo.list1.bar.list2': [1, 2, 3],
                    'foo.list1.bar.bar2': 'bar2_value',
                    'foo.list1.bar.bat.bat2': 'bat2_value',
                    'foo.list1.bar.bat.bat_list_dict': [
                        {
                            'foo.list1.bar.bat.bat_list_dict.baz': 'baz_value',
                            'foo.list1.bar.bat.bat_list_dict.bazl': [4, 5, 6],
                            'foo.list1.bar.bat.bat_list_dict.bazd.bazd_key':
                                'bazd_value'
                        }
                    ]

                }
            ]
        }
    )
])
def test_flatten(original, expected):
    assert yapconf.flatten(original) == expected
