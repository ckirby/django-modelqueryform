#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

import modelqueryform

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

version = modelqueryform.__version__

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    print("You probably want to also tag the version now:")
    print("  git tag -a %s -m 'version %s'" % (version, version))
    print("  git push --tags")
    sys.exit()

readme = open('README.rst').read()

setup(
    name='django-modelqueryform',
    version=version,
    description="""App for generating forms allowing users to build model queries""",
    long_description=readme,
    author='Chaim Kirby',
    author_email='chaim.kirby@gmail.com',
    url='https://github.com/ckirby/django-modelqueryform',
    packages=[
        'modelqueryform',
    ],
    include_package_data=True,
    install_requires=[
    ],
    license="BSD",
    zip_safe=False,
    keywords='django-modelqueryform',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.4',
    ],
)
