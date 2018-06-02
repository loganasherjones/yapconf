# -*- coding: utf-8 -*-
import abc
import copy
import hashlib
import json
import os
import threading

import six
import time
from watchdog.observers import Observer

import yapconf
from yapconf.exceptions import YapconfLoadError, YapconfSourceError
from yapconf.handlers import FileHandler


def get_source(label, source_type, **kwargs):
    """Get a config source based on type and keyword args.

    This is meant to be used internally by the spec via ``add_source``.

    Args:
        label (str): The label for this source.
        source_type: The type of source. See ``yapconf.SUPPORTED_SOURCES``

    Keyword Args:
        The keyword arguments are based on the source_type. Please see the
        documentation of the individual sources for a detailed list of all
        possible arguments.

    Returns (yapconf.sources.ConfigSource):
        A valid config source which can be used for generating an override.

    Raises:
        YapconfSourceError: If there is some kind of error with this source
        definition.

    """
    if source_type not in yapconf.ALL_SUPPORTED_SOURCES:
        raise YapconfSourceError(
            'Invalid source type %s. Supported types are %s.' %
            (source_type, yapconf.ALL_SUPPORTED_SOURCES)
        )
    if source_type not in yapconf.SUPPORTED_SOURCES:
        raise YapconfSourceError(
            'Unsupported source type "%s". If you want to use this type, you '
            'will need to install the correct client for it (try `pip install '
            'yapconf[%s]. Currently supported types are %s. All supported '
            'types are %s' %
            (source_type, source_type, yapconf.SUPPORTED_SOURCES,
             yapconf.ALL_SUPPORTED_SOURCES)
        )

    # We pop arguments from kwargs because the individual config sources
    # have better error messages if a keyword argument is missed.
    if source_type == 'dict':
        return DictConfigSource(label, data=kwargs.get('data'))

    elif source_type == 'json':
        return JsonConfigSource(label, **kwargs)

    elif source_type == 'yaml':
        filename = kwargs.get('filename')
        if 'filename' in kwargs:
            kwargs.pop('filename')
        return YamlConfigSource(label, filename, **kwargs)

    elif source_type == 'environment':
        return EnvironmentConfigSource(label)

    elif source_type == 'etcd':
        return EtcdConfigSource(
            label, kwargs.get('client'), kwargs.get('key', '/')
        )

    elif source_type == 'kubernetes':
        name = kwargs.get('name')
        if 'name' in kwargs:
            kwargs.pop('name')

        client = kwargs.get('client')
        if 'client' in kwargs:
            kwargs.pop('client')
        return KubernetesConfigSource(label, client, name, **kwargs)

    else:
        raise NotImplementedError(
            'No implementation for source type %s' % source_type
        )


@six.add_metaclass(abc.ABCMeta)
class ConfigSource(object):
    """Base class for a configuration source.

    Config sources will be used to generate overrides during configuration
    loading. In later iteration, it will also be used to migrate configs
    based on the configuration type.

    The act of loading configurations/migrating those configurations and
    especially watching those configuration is complicated enough to warrant
    its own data structure.

    Attributes:
          label: The label for this config source.
    """

    def __init__(self, label):
        self.label = label
        self.validate()
        self._continue = True

    @abc.abstractmethod
    def validate(self):
        """Validate that this ConfigSource can be used."""
        pass

    def generate_override(self, separator='.'):
        """Generate an override.

        Uses ``get_data`` which is expected to be implemented by each child
        class.

        Returns:
            A tuple of label, dict

        Raises:
            YapconfLoadError: If a known error occurs.

        """
        data = self.get_data()
        if not isinstance(data, dict):
            raise YapconfLoadError(
                'Invalid source (%s). The data was loaded successfully, but '
                'the result was not a dictionary. Got %s' %
                (self.label, type(data))
            )
        return self.label, yapconf.flatten(data, separator=separator)

    def watch(self, handler):
        """Watch a source for changes. When changes occur, call the handler.

        By default, watches a dictionary that is in memory.

        Args:
            handler: Must respond to handle_config_change

        Returns:
            The daemon thread that was spawned.

        """
        thread = threading.Thread(
            name=self.label + '-watcher',
            target=self._watch,
            args=(handler, self.get_data()),
            daemon=True,
        )
        thread.start()
        return thread

    def _hash_data(self, data):
        return hashlib.md5(repr(data).encode('utf-8')).hexdigest()

    def _watch(self, handler, data):
        current_hash = self._hash_data(data)
        while self._continue:
            new_hash = self._hash_data(self.get_data())
            if current_hash != new_hash:
                handler.handle_config_change(self.data)
                current_hash = new_hash
            time.sleep(1)

    @abc.abstractmethod
    def get_data(self):
        pass


class DictConfigSource(ConfigSource):
    """A basic config source with just a dictionary as the data.

    Keyword Args:
        data (dict): A dictionary that represents the data.
    """

    def __init__(self, label, data):
        self.data = data
        self.type = 'dict'
        super(DictConfigSource, self).__init__(label)

    def validate(self):
        if not isinstance(self.data, dict):
            raise YapconfSourceError(
                'Invalid source provided. %s provided data but it was not a '
                'dictionary. Got: %s' % (self.label, self.data)
            )

    def get_data(self):
        return self.data


class JsonConfigSource(ConfigSource):
    """JSON Config source.

    Needs either a filename or data keyword arg to work.

    Keyword Args:
        data (str): If provided, will be loaded via ``json.loads``
        filename (str): If provided, will be loaded via ``yapconf.load_file``
        kwargs: All other keyword arguments will be provided as keyword args
        to the ``load`` calls above.
    """

    def __init__(self, label, data=None, filename=None, **kwargs):
        self.type = 'json'
        self.data = data
        self.filename = filename
        self._load_kwargs = kwargs
        if 'encoding' not in self._load_kwargs:
            self._load_kwargs['encoding'] = 'utf-8'
        super(JsonConfigSource, self).__init__(label)

    def validate(self):
        if self.data is None and self.filename is None:
            raise YapconfSourceError(
                'Invalid source (%s). No data or filename was provided for a '
                'JSON config source.' % self.label
            )

    def _watch(self, handler, data):
        if self.filename:
            file_handler = FileHandler(
                filename=self.filename,
                handler=handler,
                file_type='json'
            )
            observer = Observer()
            directory = os.path.dirname(self.filename)
            observer.schedule(file_handler, directory, recursive=False)
            observer.start()
            observer.join()
        else:
            raise YapconfSourceError(
                'Cannot watch a string json source. Strings are immutable.'
            )

    def get_data(self):
        if self.data is not None:
            return json.loads(self.data, **self._load_kwargs)

        return yapconf.load_file(
            self.filename,
            file_type='json',
            klazz=YapconfSourceError,
            load_kwargs=self._load_kwargs
        )


class YamlConfigSource(ConfigSource):
    """YAML Config source.

    Needs a filename to work.

    Keyword Args:
        filename (str): Will be loaded via ``yapconf.load_file``
        encoding (str): The encoding of the filename.
    """

    def __init__(self, label, filename, **kwargs):
        self.type = 'yaml'
        self.filename = filename
        self._encoding = kwargs.get('encoding', 'utf-8')
        super(YamlConfigSource, self).__init__(label)

    def validate(self):
        if self.filename is None:
            raise YapconfSourceError(
                'Invalid source (%s). No filename was provided for a YAML '
                'config source.' % self.label
            )

    def _watch(self, handler, data):
        file_handler = FileHandler(
            filename=self.filename,
            handler=handler,
            file_type='yaml'
        )
        observer = Observer()
        directory = os.path.dirname(self.filename)
        observer.schedule(file_handler, directory, recursive=False)
        observer.start()
        observer.join()

    def get_data(self):
        return yapconf.load_file(
            self.filename,
            file_type='yaml',
            klazz=YapconfSourceError,
            open_kwargs={'encoding': self._encoding}
        )


class EnvironmentConfigSource(DictConfigSource):
    """Special dict config which gets its value from the environment."""

    def __init__(self, label):
        super(EnvironmentConfigSource, self).__init__(label, os.environ.copy())
        self.type = 'environment'

    def get_data(self):
        return copy.deepcopy(os.environ)


class EtcdConfigSource(ConfigSource):
    """Etcd config source (requires python-etcd package).

    If your keys have '/'s in them, you're going to have a bad time.

    Keyword Args:
        client: An etcd client from the python-etcd package.
        key (str): The key to fetch in etcd. Defaults to "/"
    """

    def __init__(self, label, client, key='/'):
        self.type = 'etcd'
        self.client = client
        self.key = key
        super(EtcdConfigSource, self).__init__(label)

    def validate(self):
        if not isinstance(self.client, yapconf.etcd_client.Client):
            raise YapconfSourceError(
                'Invalid source (%s). Client must be supplied and must be of '
                'type %s. Got type: %s' %
                (self.label,
                 type(yapconf.etcd_client.Client),
                 type(self.client))
            )

    def get_data(self):
        result = self.client.read(key=self.key, recursive=True)
        if not result.dir:
            raise YapconfLoadError(
                'Loaded key %s, but it was not a directory according to etcd.'
                % self.key
            )

        data = {}
        for child in result.children:
            keys = self._extract_keys(child.key)
            self._add_value(data, keys, child.value)

        return data

    def _add_value(self, data, keys, value):
        for i, key in enumerate(keys):
            if i == len(keys) - 1:
                data[key] = value
            else:
                data[key] = {}

    def _extract_keys(self, fq_key):
        return fq_key.lstrip(self.key).split('/')


class KubernetesConfigSource(ConfigSource):
    """A kubernetes config data source.

    This is meant to load things directly from the kubernetes API.
    Specifically, it can load things from config maps.

    Keyword Args:
        client: A kubernetes client from the kubernetes package.
        name (str): The name of the ConfigMap to load.
        namespace (str): The namespace for the ConfigMap
        key (str): A key for the given ConfigMap data object.
        config_type (str): Used in conjunction with 'key', if 'key' points to
        a data blob, this will specify whether to use json or yaml to load
        the file.
    """

    def __init__(self, label, client, name, **kwargs):
        self.type = 'kubernetes'
        self.client = client
        self.name = name
        self.namespace = kwargs.get('namespace') or 'default'
        self.key = kwargs.get('key')
        self.config_type = kwargs.get('config_type') or 'json'
        super(KubernetesConfigSource, self).__init__(label)

    def validate(self):
        if (yapconf.kubernetes_client and
                not isinstance(self.client,
                               yapconf.kubernetes_client.CoreV1Api)):
            raise YapconfSourceError(
                'Invalid source (%s). Client must be supplied and must be of '
                'type %s. Got type: %s' %
                (self.label,
                 type(yapconf.kubernetes_client.CoreV1Api),
                 type(self.client))
            )

        if self.config_type == 'yaml' and not yapconf.yaml_support:
            raise YapconfSourceError(
                'Kubernetes config source specified that the configmap '
                'contained a yaml config. In order to support yaml loading, '
                'you will need to `pip install yapconf[yaml]`.'
            )

        if self.config_type not in yapconf.FILE_TYPES:
            raise YapconfSourceError(
                'Invalid config type specified for a kubernetes config. %s is '
                'not supported. Supported types are %s' %
                (self.name, yapconf.FILE_TYPES)
            )

    def get_data(self):
        result = self.client.read_namespaced_config_map(self.name,
                                                        self.namespace)
        if self.key is None:
            return result.data

        if self.key not in result.data:
            raise YapconfLoadError(
                'Loaded configmap %s, but could not find key %s in the data '
                'portion of the configmap.' % self.key
            )

        nested_config = result.data[self.key]
        if self.config_type == 'json':
            return json.loads(nested_config, )
        elif self.config_type == 'yaml':
            return yapconf.yaml.load(nested_config)
        else:
            raise NotImplementedError('Cannot load config with type %s' %
                                      self.config_type)
