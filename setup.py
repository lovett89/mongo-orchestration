#!/usr/bin/python

import sys

extra_deps = []
extra_test_deps = []
if sys.version_info[:2] == (2, 6):
    extra_deps.append('argparse')
    extra_test_deps.append('unittest2')

try:
    from setuptools import setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup  # NOQA

setup(
    name='pymongo-orchestration',
    version='0.1',
    author='Mikhail Mamrouski',
    author_email='mmamrouski@gmail.com',
    install_requires=['pymongo>=2.7.2',
                      'bottle>=0.12.7',
                      'requests>=1.1'] + extra_deps,
    tests_require=['nose>=1.2', 'coverage>=3.5'] + extra_test_deps,
    test_suite='nose.collector'
)
