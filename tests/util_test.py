# -*- coding: utf-8 -*-
import pytest
import yapconf


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
