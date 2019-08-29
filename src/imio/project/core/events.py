# -*- coding: utf-8 -*-

from OFS.Application import Application
from imio.helpers.cache import cleanRamCacheFor
from imio.project.core.config import CHILDREN_BUDGET_INFOS_ANNOTATION_KEY as CBIAK
from imio.project.core.content.project import IProject
from imio.project.core.utils import getProjectSpace
from plone import api
from zope.annotation import IAnnotations

"""
Removing act: onRemoveProject on act, onModifyProject on oo
Adding act: onAddProject on act, onModifyProject on oo
Transition act: onTransitionProject on act
Move act: onMovedProject on act, onModifyProject on oo1, onModifyProject on oo2
Move oo: onMovedProject on act, onMovedProject on oo, onModifyProject on os1, onModifyProject on os2
Copy act: onAddProject on act2, onModifyProject on oo
Copy oo: onAddProject on act2, onAddProject on 002, onModifyProject on os
"""


def _updateParentsBudgetInfos(obj):
    """
      Update budget infos on every parents, going up until the parent is the projectspace.
      Exception made if the parent is on initial state
    """
    # formatBudgetInfos : take current obj budget infos and budget infos defined on children
    # that have been saved in current object annotations with key CHILDREN_BUDGET_INFOS_ANNOTATION_KEY
    # stored data will be something like :
    # {'eb6e7ee6bdd441dfb47de3871a1d0d4c': [{'amount': 500.0, 'budget_type': 'ville', 'year': 2013}],
    #  '84979391585241b3a7944bde39bc3ffd': [{'amount': 50.0, 'budget_type': 'europe', 'year': 2013},
    #                                       {'amount': 5165.0,
    #                                        'budget_type': 'federation-wallonie-bruxelles',
    #                                        'year': 2013}],
    #  'b887fed0b90f4aadba523ecaaa9391e6': [{'amount': 50.0, 'budget_type': 'europe', 'year': 2013},
    #                                       {'amount': 125.0, 'budget_type': 'ville', 'year': 2013}]
    # }

    formattedBudgetInfos = {}
    pw = obj.portal_workflow
    objUID = obj.UID()
    # we take the budget infos saved on obj annotation
    obj_annotations = IAnnotations(obj)
    if CBIAK in obj_annotations:
        formattedBudgetInfos = dict(obj_annotations[CBIAK])
    # add self in budgetInfos if not empty
    if obj.budget:
        formattedBudgetInfos[objUID] = obj.budget

    parent = obj.aq_inner.aq_parent
    while not parent.portal_type == 'projectspace':
        workflows = pw.getWorkflowsFor(parent)
        # if parent state is initial_state, we don't set children budget
        if workflows and workflows[0].initial_state == pw.getInfoFor(parent, 'review_state'):
            break
        parent_annotations = IAnnotations(parent)
        if not CBIAK in parent_annotations:
            parent_annotations[CBIAK] = {}
        # warning, we need to pass by an intermediate value then assign it using dict()
        # as new annotations, or annotations are lost upon Zope restart...
        new_annotations = parent_annotations[CBIAK]
        new_annotations.update(formattedBudgetInfos)
        parent_annotations[CBIAK] = dict(new_annotations)
        parent = parent.aq_inner.aq_parent


def _cleanParentsBudgetInfos(obj, parent=None):
    """
      Update budget infos on every parents, cleaning sub objects info.
      When p_parent, it's a move. We don't modify obj but work on old parent
    """
    uids = [obj.UID()]
    obj_annotations = IAnnotations(obj)
    if CBIAK in obj_annotations:
        uids.extend(obj_annotations[CBIAK].keys())
        if parent is None:
            obj_annotations[CBIAK] = {}
    if parent is None:
        parent = obj.aq_inner.aq_parent
    if isinstance(parent, Application):
        return  # This can happen when we try to remove a plone object
    while not parent.portal_type == 'projectspace':
        parent_annotations = IAnnotations(parent)
        if CBIAK in parent_annotations:
            # we remove all contained uids from annotation (needed when the state is backed to initial state)
            for uid in uids:
                if uid in parent_annotations[CBIAK]:
                    del parent_annotations[CBIAK][uid]
            # We have to set new dict to be persisted in annotation
            parent_annotations[CBIAK] = dict(parent_annotations[CBIAK])
        parent = parent.aq_inner.aq_parent


def onAddProject(obj, event):
    """
      Handler when a project is added
    """
    # Update budget infos on every parents
    pw = obj.portal_workflow
    workflows = pw.getWorkflowsFor(obj)
    if not workflows or workflows[0].initial_state != pw.getInfoFor(obj, 'review_state'):
        _updateParentsBudgetInfos(obj)
    # compute reference number
    projectspace = getProjectSpace(obj)
    projectspace.last_reference_number += 1
    obj.reference_number = projectspace.last_reference_number
    obj.reindexObject(['reference_number'])


def onModifyProject(obj, event):
    """
      Handler when a project is modified
    """
    # Update budget infos on every parents
    pw = obj.portal_workflow
    workflows = pw.getWorkflowsFor(obj)
    if not workflows or workflows[0].initial_state != pw.getInfoFor(obj, 'review_state'):
        _updateParentsBudgetInfos(obj)


def onTransitionProject(obj, event):
    """
      Handler when a transition is done
    """
    # we pass creation, already managed by add event
    if event.transition is None:
        return
    pw = obj.portal_workflow
    workflows = pw.getWorkflowsFor(obj)
    # Update budget infos on parents
    if event.old_state.title == workflows[0].initial_state and event.new_state.title != workflows[0].initial_state:
        _updateParentsBudgetInfos(obj)
    elif event.new_state.title == workflows[0].initial_state and event.old_state.title != workflows[0].initial_state:
        _cleanParentsBudgetInfos(obj)


def onRemoveProject(obj, event):
    """
        When a project is removed
    """
    _cleanParentsBudgetInfos(obj)


def onMoveProject(obj, event):
    """
      Handler when a project is moved.
    """
    # obj is the moved object
    # we pass creation, already managed by add event
    if event.oldParent is None or event.oldParent == event.newParent:
        return
    pw = obj.portal_workflow
    workflows = pw.getWorkflowsFor(obj)
    # Update budget infos on old and new parents
    if not workflows or workflows[0].initial_state != pw.getInfoFor(obj, 'review_state'):
        _cleanParentsBudgetInfos(obj, parent=event.oldParent)
        _updateParentsBudgetInfos(obj)


def onModifyProjectSpace(obj, event):
    """
      Handler when a projectspace is modified
    """
    if not event.descriptions:
        return
    for desc in event.descriptions:
        if 'use_ref_number' in desc.attributes:
            pc = api.portal.get_tool('portal_catalog')
            for brain in pc(object_provides=IProject.__identifier__):
                brain.getObject().reindexObject(['Title', 'sortable_title'])
            cleanRamCacheFor('imio.prettylink.adapters.getLink')
