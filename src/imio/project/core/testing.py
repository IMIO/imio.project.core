# -*- coding: utf-8 -*-
"""Base module for unittesting."""

from collective.contact.plonegroup.config import PLONEGROUP_ORG
from plone import api
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import login
from plone.app.testing import PloneWithPackageLayer
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.dexterity.utils import createContentInContainer
from zope.event import notify
from zope.lifecycleevent import ObjectCreatedEvent

import imio.project.core
import unittest


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


class IntegrationTestCase(unittest.TestCase):
    """Base class for integration tests."""

    layer = PROJECT_TESTING_PROFILE_INTEGRATION

    def setUp(self):
        super(IntegrationTestCase, self).setUp()
        self.portal = self.layer['portal']


class FunctionalTestCase(unittest.TestCase):
    """Base class for functional tests."""

    layer = PROJECT_TEST_PROFILE_FUNCTIONAL

    def setUp(self):
        super(FunctionalTestCase, self).setUp()
        self.portal = self.layer['portal']
        self.pw = self.portal.portal_workflow
        # login as Manager and add a projectspace and 2 projects into it
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        login(self.portal, TEST_USER_NAME)
        # set registry config
        api.portal.set_registry_record('imio.project.settings.project_budget_states',
                                       ['to_be_scheduled', 'ongoing', 'terminated'])
        params = {'id': u"projectspace",
                  'title': u"projectspace"}
        # datagridfield categories
        categories_values = [
            {'label': u"Category 1",
             'key': 'category-1'},
            {'label': u"Category 2",
             'key': 'category-2'},
            {'label': u"Category 3",
             'key': 'category-3'},
        ]
        params['categories_values'] = categories_values
        # datagridfield priority
        priority_values = [
            {'label': u"Priority 1",
             'key': 'priority-1'},
            {'label': u"Priority 2",
             'key': 'priority-2'},
            {'label': u"Priority 3",
             'key': 'priority-3'},
        ]
        params['priority_values'] = priority_values
        # datagridfield budget_types
        budget_types = [
            {'label': u"Budget type 1",
             'key': 'budget-type-1'},
            {'label': u"Budget type 2",
             'key': 'budget-type-2'},
            {'label': u"Budget type 3",
             'key': 'budget-type-3'},
        ]
        params['budget_types'] = budget_types
        params['budget_years'] = [2013, 2014, 2015, 2016, 2017, 2018]
        # datagridfield plan
        plan_values = [
            {'label': u"Plan 1", 'key': 'plan-1'},
            {'label': u"Plan 2", 'key': 'plan-2'},
            {'label': u"Plan 3", 'key': 'plan-3'},
        ]
        params['plan_values'] = plan_values
        self.ps = createContentInContainer(self.portal, 'projectspace', **params)
        projects = [
            {'id': u"project-1",
             'title': u"Project 1",
             'categories': u"category-1",  # not list here to keep common test working
             'priority': u"priority-1",
             'budget': [{'budget_type': 'budget-type-1',
                         'year': 2018,
                         'amount': 500.0, }
                        ],
             'plan': plan_values[0]},            # not list here to keep common test working
            {'id': u"project-2",
             'title': u"Project 2",
             'categories': u"category-2",  # not list here to keep common test working
             'priority': u"priority-3",
             'budget': [{'budget_type': 'budget-type-2',
                         'year': 2017,
                         'amount': 125.0, }
                        ]},
        ]
        for project in projects:
            createContentInContainer(self.ps, 'project', **project)
        self.p1, self.p2 = self.ps['project-1'], self.ps['project-2']

        # creating directory
        self.org = createContentInContainer(self.portal['contacts'], 'organization',
                                            **{'id': PLONEGROUP_ORG, 'title': u"Mon organisation",
                                               'organization_type': u'commune'})
        notify(ObjectCreatedEvent(self.org))
        # Departments and services creation
        sublevels = [
            (u'Echevins',
             (u'1er échevin', u'2ème échevin', u'3ème échevin')),
            (u'Services',
             (u'ADL', (u'Direction gén', (u'Secrétariat Communal', u'Service Informatique')),
              (u'Direction financière', (u'Taxes', u'Recettes')), u'Service du Personnel')),
        ]

        for (department, services) in sublevels:
            dep = createContentInContainer(self.org, 'organization', title=department)
            for service in services:
                if isinstance(service, tuple):
                    (parent, children) = service
                    obj = createContentInContainer(dep, 'organization', title=parent)
                    for child in children:
                        createContentInContainer(obj, 'organization', title=child)
                else:
                    createContentInContainer(dep, 'organization', title=service)
