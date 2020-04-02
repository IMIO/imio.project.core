# -*- coding: utf-8 -*-

from OFS.Application import Application
from imio.helpers.cache import cleanRamCacheFor
from imio.project.core.browser.controlpanel import field_constraints
from imio.project.core.browser.controlpanel import get_budget_states
from imio.project.core.config import SUMMARIZED_FIELDS
from imio.project.core.content.project import IProject
from imio.project.core.utils import getProjectSpace
from plone import api
from plone.registry.interfaces import IRecordModifiedEvent
from Products.CMFPlone.utils import base_hasattr
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


def _updateSummarizedFields(obj, fields=None):
    """
      Update each summarized field on every parents, going up until the parent is the projectspace.
      Exception made if the parent is on initial state
    """

    # example for Budget Infos field:
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

    # retro-compatible with migration to 0.2
    if not fields:
        fields = SUMMARIZED_FIELDS

    pw = obj.portal_workflow
    obj_uid = obj.UID()
    # we take the field data saved on obj annotation
    obj_annotations = IAnnotations(obj)
    formatted_fields = {}
    for field_id, annotation_key in fields.items():
        formatted_field = {}
        if annotation_key in obj_annotations:
            formatted_field = dict(obj_annotations[annotation_key])
        # add self in field if not empty
        if getattr(obj, field_id, None):
            formatted_field[obj_uid] = getattr(obj, field_id, None)
        formatted_fields[field_id] = formatted_field

    parent = obj.aq_inner.aq_parent
    while not parent.portal_type == 'projectspace':
        workflows = pw.getWorkflowsFor(parent)
        # if parent state is initial_state, we don't set children field
        if workflows and workflows[0].initial_state == pw.getInfoFor(parent, 'review_state'):
            break
        parent_annotations = IAnnotations(parent)

        for field_id, annotation_key in fields.items():
            if annotation_key not in parent_annotations:
                parent_annotations[annotation_key] = {}
            # warning, we need to pass by an intermediate value then assign it using dict()
            # as new annotations, or annotations are lost upon Zope restart...
            new_annotations = parent_annotations[annotation_key]
            new_annotations.update(formatted_fields[field_id])
            parent_annotations[annotation_key] = dict(new_annotations)

        parent = parent.aq_inner.aq_parent


def _cleanParentsFields(obj, parent=None):
    """
      Update field data on every parents, cleaning sub objects info.
      When p_parent, it's a move. We don't modify obj but work on old parent
    """
    # uids_to_remove = [obj.UID()]
    obj_annotations = IAnnotations(obj)
    uids_to_remove = {}

    for field_id, annotation_key in SUMMARIZED_FIELDS.items():
        uids_to_remove_for_field = [obj.UID()]
        if annotation_key in obj_annotations:
            # remove obj's children too
            uids_to_remove_for_field.extend(obj_annotations[annotation_key].keys())
            if parent is None:
                obj_annotations[annotation_key] = {}
        uids_to_remove[field_id] = uids_to_remove_for_field

    if parent is None:
        parent = obj.aq_inner.aq_parent

    if isinstance(parent, Application):
        return  # This can happen when we try to remove a plone object

    while not parent.portal_type == 'projectspace':
        parent_annotations = IAnnotations(parent)

        for field_id, annotation_key in SUMMARIZED_FIELDS.items():
            if annotation_key in parent_annotations:
                # we remove all contained uids from annotation (needed when the state is backed to initial state)
                for uid in uids_to_remove[field_id]:
                    if uid in parent_annotations[annotation_key]:
                        del parent_annotations[annotation_key][uid]

                # We have to set new dict to be persisted in annotation
                parent_annotations[annotation_key] = dict(parent_annotations[annotation_key])

        parent = parent.aq_inner.aq_parent


def onAddProject(obj, event):
    """
      Handler when a project is added
    """
    # Update field data on every parents
    pw = obj.portal_workflow
    workflows = pw.getWorkflowsFor(obj)
    if not workflows or pw.getInfoFor(obj, 'review_state') in get_budget_states(obj.portal_type):
        _updateSummarizedFields(obj)
    # compute reference number
    if not base_hasattr(obj, 'symbolic_link'):
        projectspace = getProjectSpace(obj)
        projectspace.last_reference_number += 1
        obj.reference_number = projectspace.last_reference_number
        obj.reindexObject(['reference_number'])


def onModifyProject(obj, event):
    """
      Handler when a project is modified
    """
    # Update field data on every parents
    pw = obj.portal_workflow
    workflows = pw.getWorkflowsFor(obj)
    if not workflows or pw.getInfoFor(obj, 'review_state') in get_budget_states(obj.portal_type):
        _updateSummarizedFields(obj)


def onTransitionProject(obj, event):
    """
      Handler when a transition is done
    """
    # we pass creation, already managed by add event
    if event.transition is None:
        return
    old_in = event.old_state.id in get_budget_states(obj.portal_type)
    new_in = event.new_state.id in get_budget_states(obj.portal_type)
    # Update field data on parents
    if not old_in and new_in:
        _updateSummarizedFields(obj)
    elif old_in and not new_in:
        _cleanParentsFields(obj)


def onRemoveProject(obj, event):
    """
        When a project is removed
    """
    _cleanParentsFields(obj)


def onMoveProject(obj, event):
    """
      Handler when a project is moved.
    """
    # obj is the moved object
    # we pass creation, already managed by add event
    if event.oldParent is None or event.oldParent == event.newParent:
        return
    # we pass deletion, already managed by remove event
    if event.newParent is None and event.newName is None:
        return
    # bypass if we are removing the Plone Site => no more necessary ?
#    if event.object.portal_type == 'Plone Site':
#        return
    pw = obj.portal_workflow
    workflows = pw.getWorkflowsFor(obj)
    # Update field data on old and new parents
    if not workflows or pw.getInfoFor(obj, 'review_state') in get_budget_states(obj.portal_type):
        _cleanParentsFields(obj, parent=event.oldParent)
        _updateSummarizedFields(obj)


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


def empty_fields(event, dic):
    if event.oldValue is None:
        return  # site creation: nothing to do
    pt = event.record.fieldName[:-7]
    if pt not in dic:
        return  # nothing to do
    ovs, nvs = set(event.oldValue), set(event.newValue)
    removed = ovs - nvs
    es = set(dic[pt])  # set of configured fields to empty
    to_empty = es.intersection(removed)
    if not to_empty:
        return
    to_empty = [fld.split('.')[-1] for fld in to_empty]
    for brain in api.content.find(portal_type=pt):
        obj = brain.getObject()
        changed = False
        for fld in to_empty:
            if getattr(obj, fld, False):
                setattr(obj, fld, None)
                changed = True
        if changed:
            obj.reindexObject()


def registry_changed(event):
    """ Handler when the registry is changed """
    if IRecordModifiedEvent.providedBy(event):
        if event.record.interfaceName == 'imio.project.pst.browser.controlpanel.IImioPSTSettings':
            # empty some fields if necessary
            empty = field_constraints.get('empty', {})
            empty_fields(event, empty)
            # we redo budget globalization if states change
            catalog = api.portal.get_tool('portal_catalog')
            if event.record.fieldName.endswith('_budget_states'):
                # first remove all
                brains = catalog.searchResults(object_provides=IProject.__identifier__, sort_on='path',
                                               sort_order='reverse')
                for brain in brains:
                    obj = brain.getObject()
                    changed = False
                    obj_annotations = IAnnotations(obj)
                    for fld, AK in SUMMARIZED_FIELDS.items():
                        if AK in obj_annotations:
                            changed = True
                            del obj_annotations[AK]
                    if changed:
                        print "%s changed" % obj
                        obj.reindexObject()
                # globalize again
                brains = catalog.searchResults(object_provides=IProject.__identifier__, sort_on='path',
                                               sort_order='reverse')
                pw = api.portal.get_tool('portal_workflow')
                for brain in brains:
                    obj = brain.getObject()
                    if pw.getInfoFor(obj, 'review_state') in get_budget_states(obj.portal_type):
                        _updateSummarizedFields(obj)
