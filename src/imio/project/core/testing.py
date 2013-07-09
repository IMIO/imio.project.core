# -*- coding: utf-8 -*-
"""Base module for unittesting."""

import unittest2
from plone.app.testing import PloneWithPackageLayer
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME

from plone.dexterity.utils import createContentInContainer

import imio.project.core


PROJECT_TESTING_PROFILE = PloneWithPackageLayer(
    zcml_filename="testing.zcml",
    zcml_package=imio.project.core,
    additional_z2_products=('imio.project.core', ),
    gs_profile_id='imio.project.core:testing',
    name="PROJECT_TESTS_PROFILE")

PROJECT_TESTING_PROFILE_INTEGRATION = IntegrationTesting(
    bases=(PROJECT_TESTING_PROFILE,), name="PROJECT_TESTING_PROFILE_INTEGRATION")

PROJECT_TEST_PROFILE_FUNCTIONAL = FunctionalTesting(
    bases=(PROJECT_TESTING_PROFILE,), name="PROJECT_TESTING_PROFILE_FUNCTIONAL")


class IntegrationTestCase(unittest2.TestCase):
    """Base class for integration tests."""

    layer = PROJECT_TESTING_PROFILE_INTEGRATION

    def setUp(self):
        super(IntegrationTestCase, self).setUp()
        self.portal = self.layer['portal']


class FunctionalTestCase(unittest2.TestCase):
    """Base class for functional tests."""

    layer = PROJECT_TEST_PROFILE_FUNCTIONAL

    def setUp(self):
        super(FunctionalTestCase, self).setUp()
        self.portal = self.layer['portal']
        # login as Manager and add a projectspace and 2 projects into it
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        login(self.portal, TEST_USER_NAME)
        params = {'id': u"projectspace",
                  'title': u"projectspace"}
        # datagridfield categories
        categories = [
            {'label': u"Category 1",
             'key': u"category-1"},
            {'label': u"Category 2",
             'key': u"category-2"},
            {'label': u"Category 3",
             'key': u"category-3"},
        ]
        params['categories'] = categories
        # datagridfield priority
        priority = [
            {'label': u"High",
             'key': u"high"},
            {'label': u"Normal",
             'key': u"normal"},
            {'label': u"Low",
             'key': u"low"},
        ]
        params['priority'] = priority
        projectspace = createContentInContainer(self.portal, 'projectspace', **params)
        projects = [
            {'id': u"project1",
             'title': u"Project 1",
             'categories': u"category-1",
             'priority': u"high", },
            {'id': u"project2",
             'title': u"Project 2",
             'categories': u"category-2",
             'priority': u"normal", },
        ]
        for project in projects:
            createContentInContainer(projectspace, 'project', **project)
