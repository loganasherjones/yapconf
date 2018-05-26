.. _sources:

=======
Sources
=======

Yapconf supports a variety of different sources for configuration. Some of these sources require
third-party libraries to be installed. Each of the sources should be loaded with the ``add_source``
method call on a specification. The ``add_source`` may require differing keyword arguments
depending on which source you wish to add.

dict
----

The ``dict`` source type is just a dictionary.


**Example**:

.. code-block:: python

    my_spec.add_source('label', 'dict', data={'foo': 'bar'})




+-------------------+----------+------------------------+
| Keyword Arguments | Required | Description            |
+===================+==========+========================+
| ``data``          | ``Y``    | The dictionary to use. |
+-------------------+----------+------------------------+

environment
-----------

The ``environment`` source type is a dictionary, but we will copy the
environment for you. There are no required keyword arguments.

**Example**:

.. code-block:: python

    my_spec.add_source('label', 'environment')


etcd
----

The ``etcd`` source type specifies that yapconf should load the configuration
from an etcd.  In order to use the ``etcd`` capabilities in yapconf, you need
to install the package yapconf uses for etcd:

.. code-block:: console

    $ pip install yapconf[etcd]

**Example**

.. code-block:: python

    import etcd
    client = etcd.Client()

    my_spec.add_source('label', 'etcd', client=client, key='/')


+-------------------+----------+--------------------------------------------------------------------+
| Keyword Arguments | Required | Description                                                        |
+===================+==========+====================================================================+
| ``client``        | ``Y``    | Etcd client to use.                                                |
+-------------------+----------+--------------------------------------------------------------------+
| ``key``           | ``N``    | Key to use, default is '/'. Key in etcd where your config resides. |
+-------------------+----------+--------------------------------------------------------------------+

json
----

The ``json`` source type can specify either a JSON string or a JSON file to load.


**Example**

.. code-block:: python

    # Load from JSON file
    filename = '/path/to/config.json'
    my_spec.add_source('label1', 'json', filename=filename)

    # You can also load from a JSON string
    json_string = json.loads(some_info)
    my_spec.add_source('label2', 'json', data=json_string)

+-------------------+----------+--------------------------------------------------------------------+
| Keyword Arguments | Required | Description                                                        |
+===================+==========+====================================================================+
| ``filename``      | ``N``    | Filename of a JSON config file.                                    |
+-------------------+----------+--------------------------------------------------------------------+
| ``data``          | ``N``    | Json String.                                                       |
+-------------------+----------+--------------------------------------------------------------------+
| ``kwargs``        | ``N``    | Keyword arguments to pass to ``json.loads``                        |
+-------------------+----------+--------------------------------------------------------------------+


kubernetes
----------

The ``kubernetes`` source type sp77ecifies that yapconf should load the configuration
from a `kubernetes ConfigMap`_.  In order to use the ``kubernetes`` capabilities in yapconf,
you need to install the package yapconf uses for kubernetes:

.. code-block:: console

    $ pip install yapconf[k8s]

**Example**

.. code-block:: python

    from kubernetes import client, config
    config.load_kube_config()

    client = client.CoreV1Api()

    my_spec.add_source(
        'label',
        'kubernetes',
        client=client,
        name='ConfigMapName'
    )


+-------------------+----------+--------------------------------------------------------------+
| Keyword Arguments | Required | Description                                                  |
+===================+==========+==============================================================+
| ``client``        | ``Y``    | Kubernetes client to use.                                    |
+-------------------+----------+--------------------------------------------------------------+
| ``name``          | ``Y``    | The name of the ``ConfigMap``.                               |
+-------------------+----------+--------------------------------------------------------------+
| ``namespace``     | ``N``    | The namespace for the ``ConfigMap``.                         |
+-------------------+----------+--------------------------------------------------------------+
| ``key``           | ``N``    | The key in the ``data`` portion of the ``ConfigMap``.        |
+-------------------+----------+--------------------------------------------------------------+
| ``config_type``   | ``N``    | The format of the data in the ``key`` (support json or yaml) |
+-------------------+----------+--------------------------------------------------------------+


yaml
----

The ``yaml`` source type lets you specify a YAML file to load.

**Example:**

.. code-block:: python

    # Load from YAML file
    filename = '/path/to/config.yaml'
    my_spec.add_source('label1', 'yaml', filename=filename)


+-------------------+----------+---------------------------------+
| Keyword Arguments | Required | Description                     |
+===================+==========+=================================+
| ``filename``      | ``Y``    | Filename of a YAML config file. |
+-------------------+----------+---------------------------------+
| ``encoding``      | ``N``    | Encoding of the YAML file       |
+-------------------+----------+---------------------------------+

.. _kubernetes ConfigMap: https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-configmap
