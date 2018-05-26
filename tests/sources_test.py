# -*- coding: utf-8 -*-
import pytest
from mock import Mock

import yapconf
from yapconf.exceptions import YapconfSourceError
from yapconf.sources import (DictConfigSource, EnvironmentConfigSource,
                             EtcdConfigSource, JsonConfigSource,
                             KubernetesConfigSource, YamlConfigSource,
                             get_source)

original_sources = yapconf.SUPPORTED_SOURCES.copy()


def teardown_function(function):
    yapconf.SUPPORTED_SOURCES = original_sources


@pytest.mark.parametrize('source_type,sources,kwargs', [
    ('invalid_source', yapconf.SUPPORTED_SOURCES, {}),
    ('yaml', [], {}),
    ('dict', yapconf.SUPPORTED_SOURCES, {'data': 'NOT_A_DICT'}),
    ('json', yapconf.SUPPORTED_SOURCES, {}),
    ('yaml', yapconf.SUPPORTED_SOURCES, {}),
    ('etcd', yapconf.SUPPORTED_SOURCES, {'client': 'NOT_A_ETCD_CLIENT'}),
    ('kubernetes', yapconf.SUPPORTED_SOURCES, {'client': 'NOT_A_K8S_CLIENT'}),
])
def test_get_source_error(source_type, sources, kwargs):
    yapconf.SUPPORTED_SOURCES = sources
    with pytest.raises(YapconfSourceError):
        get_source('label', source_type, **kwargs)


@pytest.mark.parametrize('source_type,kwargs,klazz', [
    ('dict', {'data': {}}, DictConfigSource),
    ('json', {'filename': 'path/to/config'}, JsonConfigSource),
    ('yaml', {'filename': 'path/to/config'}, YamlConfigSource),
    ('environment', {}, EnvironmentConfigSource),
    (
        'etcd',
        {'client': Mock(spec=yapconf.etcd_client.Client)},
        EtcdConfigSource),
    (
        'kubernetes',
        {
            'name': 'configMap',
            'client': Mock(spec=yapconf.kubernetes_client.CoreV1Api)
        },
        KubernetesConfigSource
    ),
])
def test_get_source(source_type, kwargs, klazz):
    source = get_source('label', source_type, **kwargs)
    assert isinstance(source, klazz)
