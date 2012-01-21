#!/usr/bin/env python
import os
import re
from setuptools import setup

__doc__="""
Useful stuff for django

"""

version = '0.0.2'

setup(name='django-fusionbox',
    version=version,
    description='Useful stuff for django',
    author='Fusionbox programmers',
    author_email='programmers@fusionbox.com',
    keywords='django boilerplate',
    long_description=__doc__,
    url='https://github.com/fusionbox/django-fusionbox',
    packages=['fusionbox', 'fusionbox.contact', 'fusionbox.db', 'fusionbox.forms', 'fusionbox.panels', 'fusionbox.panels.user_panel', 'fusionbox.templatetags', 'fusionbox.management', 'fusionbox.management.commands'],
    package_data={'fusionbox.panels.user_panel': ['templates/*',]},
    include_package_data=True,
    platforms = "any",
    license='BSD',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
    ],
    install_requires = ['BeautifulSoup', 'PyYAML', 'markdown'],
    requires = ['BeautifulSoup', 'PyYAML', 'markdown'],
    zip_safe=False,
)
