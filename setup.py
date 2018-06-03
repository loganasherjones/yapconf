#!/usr/bin/env python
# -*- coding: utf-8 -*- 
"""The setup script."""

from setuptools import find_packages, setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'six<2',
    'python-box<4',
    'watchdog',
]

extras = {
    'deploy': ['wheel', 'twine', ],
    'etcd': ['python-etcd', ],
    'develop': ['isort', 'watchdog', ],
    'docs': ['sphinx', 'sphinx_rtd_theme', ],
    'k8s': ['kubernetes', ],
    'test': [
        'codecov',
        'coverage',
        'flake8',
        'funcsigs',
        'kubernetes',
        'mock',
        'pluggy<0.7,>=0.5',
        'pytest',
        'pytest-lazy-fixture',
        'pytest-cov',
        'pytest-runner',
        'python-etcd',
        'ruamel.yaml',
        'tox',
    ],
    'yaml': ['ruamel.yaml'],
}

setup(
    name='yapconf',
    version='0.3.0',
    description="Yet Another Python Configuration",
    long_description=readme + '\n\n' + history,
    author="Logan Asher Jones",
    author_email='loganasherjones@gmail.com',
    url='https://github.com/loganasherjones/yapconf',
    packages=find_packages(include=['yapconf']),
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='yapconf',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
    ],
    test_suite='tests',
    tests_require=extras['test'],
    extras_require=extras,
)
