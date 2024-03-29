# -*- coding: utf-8 -*-
"""Installer for the imio.project package."""

from setuptools import find_packages
from setuptools import setup


long_description = (
    open('README.rst').read()
    + '\n' +
    'Contributors\n'
    '============\n'
    + '\n' +
    open('CONTRIBUTORS.rst').read()
    + '\n' +
    open('CHANGES.rst').read()
    + '\n')


setup(
    name='imio.project.core',
    version='1.3.2.dev0',
    description="Project management",
    long_description=long_description,
    # Get more from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 4.3",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
    ],
    keywords='',
    author='IMIO',
    author_email='dev@imio.be',
    url='http://pypi.python.org/pypi/imio.project.core',
    license='GPL',
    packages=find_packages('src', exclude=['ez_setup']),
    namespace_packages=['imio', 'imio.project'],
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Plone',
        'collective.contact.core',
        'collective.contact.plonegroup',
        'collective.dexteritytextindexer',
        'collective.z3cform.chosen',
        'collective.z3cform.datagridfield',
        'dexterity.localrolesfield',
        'plone.app.dexterity',
        'plone.app.lockingbehavior',
        'plone.app.versioningbehavior',
        'plone.principalsource',
        'plone.formwidget.datetime',
        'setuptools',
        'Products.PluggableAuthService>=1.11.3',
    ],
    extras_require={
        'test': [
            'plone.app.testing',
        ],
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
