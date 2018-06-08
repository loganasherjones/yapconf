# -*- coding: utf-8 -*-
import pytest
from etcd import EtcdWatchTimedOut
from mock import Mock, PropertyMock, patch

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


def test_k8s_watch():
    def apply_name(mock, name):
        p = PropertyMock(return_value=name)
        type(mock).name = p

    md_mock1 = Mock()
    apply_name(md_mock1, 'name')
    event_object1 = Mock(metadata=md_mock1)

    events = [
        {
            'object': event_object1,
            'type': 'MODIFIED'
        },
    ]

    mock_client = Mock(spec=yapconf.kubernetes_client.CoreV1Api)
    handler = Mock()
    source = get_source('label', 'kubernetes', client=mock_client, name='name')
    source.get_data = Mock(return_value="NEW DATA")
    with patch('yapconf.sources.watch.Watch') as WatchMock:
        mock_watch = Mock()
        WatchMock.return_value = mock_watch

        mock_watch.stream = Mock(return_value=events)
        source._watch(handler, {})

    handler.handle_config_change.assert_called_with("NEW DATA")


def test_k8s_watch_bomb_on_deletion():
    def apply_name(mock, name):
        p = PropertyMock(return_value=name)
        type(mock).name = p

    md_mock1 = Mock()
    apply_name(md_mock1, 'DOES_NOT_MATCH')
    event_object1 = Mock(metadata=md_mock1)

    md_mock2 = Mock()
    apply_name(md_mock2, 'name')
    event_object2 = Mock(metadata=md_mock2)
    events = [
        {
            'object': event_object1,
            'type': 'DELETED'
        },
        {
            'object': event_object2,
            'type': 'DELETED'
        }
    ]

    mock_client = Mock(spec=yapconf.kubernetes_client.CoreV1Api)
    mock_client.list_namespaced_config_map = Mock(return_value=[])
    handler = Mock()
    source = get_source('label', 'kubernetes', client=mock_client, name='name')
    with patch('yapconf.sources.watch.Watch') as WatchMock:
        mock_watch = Mock()
        WatchMock.return_value = mock_watch

        mock_watch.stream = Mock(return_value=events)
        with pytest.raises(YapconfSourceError):
            source._watch(handler, {})


def test_etcd_watch():

    mock_client = Mock(
        spec=yapconf.etcd_client.Client,
        read=Mock(side_effect=[EtcdWatchTimedOut, "result", ValueError])
    )
    handler = Mock()
    source = get_source('label', 'etcd', client=mock_client)
    source.get_data = Mock(return_value='NEW_DATA')
    with pytest.raises(ValueError):
        source._watch(handler, {})

    handler.handle_config_change('NEW_DATA')


def test_environment():
    source = get_source('label', 'environment')
    assert isinstance(source.get_data(), dict)
