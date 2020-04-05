# -*- coding: utf-8 -*-
"""Test the project.budgetInfos field behaviour."""

from imio.project.core.config import CHILDREN_BUDGET_INFOS_ANNOTATION_KEY as CBIAK
from imio.project.core.testing import FunctionalTestCase
from plone import api
from plone.dexterity.utils import createContentInContainer
from zope.annotation import IAnnotations
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent


class TestProjectFields(FunctionalTestCase):
    """"""

    def test_Plan(self):
        """"""
        self.assertEquals(self.p1.plan, {'label': u"Plan 1", 'key': 'plan-1'})

