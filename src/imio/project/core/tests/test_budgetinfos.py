# -*- coding: utf-8 -*-
"""Test the project.budgetInfos field behaviour."""

from zope.annotation import IAnnotations
from plone.dexterity.utils import createContentInContainer

from imio.project.core.testing import FunctionalTestCase
from imio.project.core.config import CHILDREN_BUDGET_INFOS_ANNOTATION_KEY
from imio.project.core.content.project import default_year


class TestBudgetField(FunctionalTestCase):
    """Test the budget field behaviour that update parents annotations to store budget data."""

    def test_ParentsAreCorrectlyUpdated(self):
        """Test that when adding several levels of projects, parent projects are
           correctly updated regarding budgetInfos annotations."""
        # project will contains informations about sub projects,
        # but the projectspace does not behave like that
        # so the project space does not have a CHILDREN_BUDGET_INFOS_ANNOTATION_KEY in his annotations
        projectspaceAnnotations = IAnnotations(self.portal.projectspace)
        self.failIf(CHILDREN_BUDGET_INFOS_ANNOTATION_KEY in projectspaceAnnotations)
        # as the project1 does not have any children, it does not have the annotations neither
        project1 = self.portal.projectspace['project-1']
        project1Annotations = IAnnotations(project1)
        self.failIf(CHILDREN_BUDGET_INFOS_ANNOTATION_KEY in project1Annotations)
        # now add a child to project1 with some valuable budgetInfos
        params = {'title': 'Subproject 1',
                  'priority': 'priority-1',
                  'budget': [{'budget_type': 'budget-type-1',
                              'year': default_year() + 1,
                              'amount': 500.0, }
                             ],
                  }
        subproject1 = createContentInContainer(project1, 'project', **params)
        # subproject1 does not have the annotation but his parent should
        subproject1Annotations = IAnnotations(subproject1)
        self.failIf(CHILDREN_BUDGET_INFOS_ANNOTATION_KEY in subproject1Annotations)
        self.failUnless(CHILDREN_BUDGET_INFOS_ANNOTATION_KEY in project1Annotations)
        self.assertEquals(project1Annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY],
                          {subproject1.UID(): subproject1.budget, })
