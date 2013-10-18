# -*- coding: utf-8 -*-
"""Test the project.budgetInfos field behaviour."""

from zope.annotation import IAnnotations
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent
from plone.dexterity.utils import createContentInContainer

from imio.project.core.testing import FunctionalTestCase
from imio.project.core.config import CHILDREN_BUDGET_INFOS_ANNOTATION_KEY
from imio.project.core.content.project import default_year


class TestBudgetField(FunctionalTestCase):
    """Test the budget field behaviour that update parents annotations to store budget data."""

    def test_ParentsAreCorrectlyUpdatedOnAddModifySubProject(self):
        """Test that when adding or editing several levels of projects, parent projects are
           correctly updated regarding budget annotations."""
        # make this test is a sub test because it will create projects and sub projects and we will call it
        # in test_ParentsAreCorrectlyUpdatedOnRemoveSubProject to have a bunch of created projects
        self._createProjectsAndTestAnnotationsEvolution()

    def _createProjectsAndTestAnnotationsEvolution(self):
        """
          Helper method for the test_ParentsAreCorrectlyUpdatedOnAddSubProject test that
          will be called again in the test_ParentsAreCorrectlyUpdatedOnRemoveSubProject so
          a bunch of projects is created.
        """
        # project will contains informations about sub projects,
        # but the projectspace does not behave like that
        # so the project space does not have a CHILDREN_BUDGET_INFOS_ANNOTATION_KEY in his annotations
        projectspaceAnnotations = IAnnotations(self.portal.projectspace)
        self.failIf(CHILDREN_BUDGET_INFOS_ANNOTATION_KEY in projectspaceAnnotations)
        # as the project1 does not have any children, it does not have the annotations neither
        project1 = self.portal.projectspace['project-1']
        # we change initial state
        self.pw.doActionFor(project1, "set_to_be_scheduled")
        project1Annotations = IAnnotations(project1)
        self.failIf(CHILDREN_BUDGET_INFOS_ANNOTATION_KEY in project1Annotations)
        # now add a child to project1 with some valuable budget data
        params = {'title': 'Subproject 1',
                  'priority': 'priority-1',
                  'budget': [{'budget_type': 'budget-type-1',
                              'year': default_year() + 1,
                              'amount': 500.0, }
                             ],
                  }
        subproject1 = createContentInContainer(project1, 'project', **params)
        # subproject1 does not have the annotation but his parent should, except for initial state
        subproject1Annotations = IAnnotations(subproject1)
        self.failIf(CHILDREN_BUDGET_INFOS_ANNOTATION_KEY in subproject1Annotations)
        self.failIf(CHILDREN_BUDGET_INFOS_ANNOTATION_KEY in project1Annotations)
        # we change initial state
        self.pw.doActionFor(subproject1, "set_to_be_scheduled")
        self.failUnless(CHILDREN_BUDGET_INFOS_ANNOTATION_KEY in project1Annotations)
        self.assertEquals(project1Annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY],
                          {subproject1.UID(): subproject1.budget, })
        # while adding a sub-subproject1 every parents are updated with his budget data
        params = {'title': 'Sub-subproject 1',
                  'priority': 'priority-2',
                  'budget': [{'budget_type': 'budget-type-2',
                              'year': default_year(),
                              'amount': 255.0, }
                             ],
                  }
        subSubproject1 = createContentInContainer(subproject1, 'project', **params)
        # subSubproject1 does not have the annotation
        subSubproject1Annotations = IAnnotations(subSubproject1)
        self.failIf(CHILDREN_BUDGET_INFOS_ANNOTATION_KEY in subSubproject1Annotations)
        # but his direct parent subproject1 should have now relevant budget data and the
        # super parent project1 should have budget data of every sub projects, so budget data
        # of subSubproject1 and of subproject1
        self.failIf(CHILDREN_BUDGET_INFOS_ANNOTATION_KEY in subproject1Annotations)
        # we change initial state
        self.pw.doActionFor(subSubproject1, "set_to_be_scheduled")
        self.failUnless(CHILDREN_BUDGET_INFOS_ANNOTATION_KEY in subproject1Annotations)
        # subproject1 contains budget data of subSubproject1
        self.assertEquals(subproject1Annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY],
                          {subSubproject1.UID(): subSubproject1.budget, })
        # project1 contains budget data of subproject1 and subSubproject1
        self.assertEquals(project1Annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY],
                          {subproject1.UID(): subproject1.budget,
                           subSubproject1.UID(): subSubproject1.budget, })
        # if we add another sub project at the same level of the subSubproject1,
        # brother is not updated but parents are updated accordingly
        params = {'title': 'Sub-subproject 2',
                  'priority': 'priority-1',
                  'budget': [{'budget_type': 'budget-type-2',
                              'year': default_year(),
                              'amount': 155.0, }
                             ],
                  }
        subSubproject2 = createContentInContainer(subproject1, 'project', **params)
        # we change initial state
        self.pw.doActionFor(subSubproject2, "set_to_be_scheduled")
        # check that brother is not touched and subSubproject2 neither
        subSubproject2Annotations = IAnnotations(subSubproject2)
        self.failIf(CHILDREN_BUDGET_INFOS_ANNOTATION_KEY in subSubproject1Annotations)
        self.failIf(CHILDREN_BUDGET_INFOS_ANNOTATION_KEY in subSubproject2Annotations)
        # but now, subproject1 have infos of two sub projects
        self.assertEquals(subproject1Annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY],
                          {subSubproject1.UID(): subSubproject1.budget,
                           subSubproject2.UID(): subSubproject2.budget, })
        # and project1 has now budget data of his 3 children
        self.assertEquals(project1Annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY],
                          {subproject1.UID(): subproject1.budget,
                           subSubproject1.UID(): subSubproject1.budget,
                           subSubproject2.UID(): subSubproject2.budget, })
        # if we edit subSubproject2 budget, parents are correctly updated
        subSubproject2.budget = subSubproject2.budget[0]['amount'] + 50
        notify(ObjectModifiedEvent(subSubproject2))
        # and project1 has now budget data of his 3 children
        self.assertEquals(project1Annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY],
                          {subproject1.UID(): subproject1.budget,
                           subSubproject1.UID(): subSubproject1.budget,
                           subSubproject2.UID(): subSubproject2.budget, })

        return project1, subproject1, subSubproject1, subSubproject2, project1Annotations, \
            subproject1Annotations, subSubproject1Annotations, subSubproject2Annotations

    def test_ParentsAreCorrectlyUpdatedOnRemoveSubProject(self):
        """Test that when removing sub-projects, parent projects are
           correctly updated regarding budget annotations."""
        # first create some projects and sub-projects using the _createProjectsAndTestAnnotationsEvolution
        # this method returns several elements, so for PEP8 convenience, we store it in returns then dispatch...
        returns = self._createProjectsAndTestAnnotationsEvolution()
        project1 = returns[0]
        subproject1 = returns[1]
        subSubproject1 = returns[2]
        subSubproject2 = returns[3]
        project1Annotations = returns[4]
        subproject1Annotations = returns[5]
        subSubproject1Annotations = returns[6]
        subSubproject2Annotations = returns[7]
        project1 = self.portal.projectspace['project-1']
        project1Annotations = IAnnotations(project1)
        # now we have project1 that contains subproject and that contains 2
        # elements, subSubproject1 and subSubproject2, relevant annotations are correct
        # double check state, just to be sure...
        self.assertEquals(project1Annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY],
                          {subproject1.UID(): subproject1.budget,
                           subSubproject1.UID(): subSubproject1.budget,
                           subSubproject2.UID(): subSubproject2.budget, })
        self.assertEquals(subproject1Annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY],
                          {subSubproject1.UID(): subSubproject1.budget,
                           subSubproject2.UID(): subSubproject2.budget, })
        self.failIf(CHILDREN_BUDGET_INFOS_ANNOTATION_KEY in subSubproject1Annotations)
        self.failIf(CHILDREN_BUDGET_INFOS_ANNOTATION_KEY in subSubproject2Annotations)
        # now remove subSubproject1 and see what happens...
        subproject1.manage_delObjects(ids=['sub-subproject-1', ])
        # infos about subSubproject1 have disappeared from parents budget annotations
        self.assertEquals(project1Annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY],
                          {subproject1.UID(): subproject1.budget,
                           subSubproject2.UID(): subSubproject2.budget, })
        self.assertEquals(subproject1Annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY],
                          {subSubproject2.UID(): subSubproject2.budget, })
        # if we remove subproject1, as subSubproject2 is also removed, annotations on
        # project1 will be empty regarding budget data of children...
        project1.manage_delObjects(ids=['subproject-1', ])
        self.assertEquals(subproject1Annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY], {})
        # test that the fact that the annotation key is still present
        # is not a problem when adding a new subproject
        params = {'title': 'Subproject 2',
                  'priority': 'priority-2',
                  'budget': [{'budget_type': 'budget-type-2',
                              'year': default_year(),
                              'amount': 4555.0, }
                             ],
                  }
        subproject2 = createContentInContainer(project1, 'project', **params)
        # we change initial state
        self.pw.doActionFor(subproject2, "set_to_be_scheduled")
        subproject2Annotations = IAnnotations(subproject2)
        self.assertEquals(project1Annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY],
                          {subproject2.UID(): subproject2.budget, })
        self.failIf(CHILDREN_BUDGET_INFOS_ANNOTATION_KEY in subproject2Annotations)

        # Test on delete subproject without parent annotation
        project2 = self.portal.projectspace['project-2']
        project2Annotations = IAnnotations(project2)
        # we change initial state
        self.pw.doActionFor(project2, "set_to_be_scheduled")
        self.failIf(CHILDREN_BUDGET_INFOS_ANNOTATION_KEY in project2Annotations)
        # adding a subproject leaving it at initial state
        params = {'title': 'Subproject 2-1',
                  'priority': 'priority-2',
                  'budget': [{'budget_type': 'budget-type-2',
                              'year': default_year(),
                              'amount': 4555.0, }
                             ],
                  }
        subproject21 = createContentInContainer(project2, 'project', **params)
        self.failIf(CHILDREN_BUDGET_INFOS_ANNOTATION_KEY in project2Annotations)
        project2.manage_delObjects(ids=[subproject21.id, ])

    def test_ParentsAreCorrectlyUpdatedOnTransition(self):
        """Test that when changing state on sub-projects, parent projects are
           correctly updated regarding budget annotations."""
        # first create some projects and sub-projects using the _createProjectsAndTestAnnotationsEvolution
        # this method returns several elements, so for PEP8 convenience, we store it in returns then dispatch...
        returns = self._createProjectsAndTestAnnotationsEvolution()
        project1 = returns[0]
        subproject1 = returns[1]
        subSubproject1 = returns[2]
        subSubproject2 = returns[3]
        project1Annotations = returns[4]
        subproject1Annotations = returns[5]
        # verifying content
        self.assertEquals(len(project1Annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY].keys()), 3)
        self.assertEquals(len(subproject1Annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY].keys()), 2)
        # we transit to another state: => no change
        self.pw.doActionFor(subSubproject1, "begin")
        self.assertEquals(len(project1Annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY].keys()), 3)
        self.assertEquals(len(subproject1Annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY].keys()), 2)
        # we transit to previous state: => no change
        self.pw.doActionFor(subSubproject1, "back_to_be_scheduled")
        self.assertEquals(len(project1Annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY].keys()), 3)
        self.assertEquals(len(subproject1Annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY].keys()), 2)
        # we transit to initial state: => subprojet must be removed
        self.pw.doActionFor(subSubproject1, "back_to_created")
        self.assertEquals(len(project1Annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY].keys()), 2)
        self.assertEquals(len(subproject1Annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY].keys()), 1)
        self.assertNotIn(subSubproject1.UID(), project1Annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY].keys())
        self.assertNotIn(subSubproject1.UID(), subproject1Annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY].keys())
        # we transit to initial state: => subprojet must be removed
        self.pw.doActionFor(subSubproject1, "set_to_be_scheduled")
        self.assertEquals(len(project1Annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY].keys()), 3)
        self.assertEquals(len(subproject1Annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY].keys()), 2)
        self.assertIn(subSubproject1.UID(), project1Annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY].keys())
        self.assertIn(subSubproject1.UID(), subproject1Annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY].keys())
