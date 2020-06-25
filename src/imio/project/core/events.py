# -*- coding: utf-8 -*-

from OFS.Application import Application
from copy import deepcopy
from imio.helpers.cache import cleanRamCacheFor
from imio.project.core.content.projectspace import field_constraints
from imio.project.core.browser.controlpanel import get_budget_states
from imio.project.core.config import SUMMARIZED_FIELDS
from imio.project.core.content.project import IProject
from imio.project.core.content.projectspace import IProjectSpace
from imio.project.core.utils import getProjectSpace
from imio.project.core.utils import reference_numbers_title
from plone import api
from plone.registry.interfaces import IRecordModifiedEvent
from Products.CMFPlone.utils import base_hasattr
from zc.relation.interfaces import ICatalog
from zope.annotation import IAnnotations
from zope.component import getUtility
from zope.intid.interfaces import IIntIds
from zope.lifecycleevent.interfaces import IObjectAddedEvent

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
    # retrieve splitting coefficient to apply to amounts
    # useful for actions, subactions or their symlinks
    coefficient = amount_coefficient(obj)
    # we take the field data saved on obj annotation
    obj_annotations = IAnnotations(obj)
    formatted_fields = {}
    for field_id, annotation_key in fields.items():
        formatted_field = {}
        if annotation_key in obj_annotations:
            formatted_field = dict(obj_annotations[annotation_key])
        # add self in field if not empty
        field = deepcopy(getattr(obj, field_id, None))
        if field:
            for line in field:
                if 'amount' in line:
                    line['amount'] *= coefficient
            formatted_field[obj_uid] = field
        formatted_fields[field_id] = formatted_field

    parent = obj.aq_inner.aq_parent
    while not IProjectSpace.providedBy(parent):
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

    # if obj isn't a symlink, find all its potential symlinks and _updateSummarizedFields them.
    if not base_hasattr(obj, '_link_portal_type') and base_hasattr(obj, 'back_references'):
        for rel in obj.back_references():
            _updateSummarizedFields(rel)

def amount_coefficient(obj):
    """
    Calculates the coefficient to apply when splitting budget lines.
    If not applicable, defaults to 1.
    """

    obj_uid = obj.UID()
    coefficient = 1
    if base_hasattr(obj, '_link_portal_type'):
        obj = obj._link
    budget_split = getattr(obj, 'budget_split', None) or []
    for line in budget_split:
        if line.get('uid') == obj_uid:
            coefficient = line.get('percentage', 100.0) / 100.0
            break
    return coefficient


def update_budget_splits(obj, event=None):
    print "update_budget_splits", reference_numbers_title(obj)
    base_obj = obj._link if base_hasattr(obj, '_link_portal_type') else obj
    expected_objects = {base_obj}
    if IObjectAddedEvent.providedBy(event):
        expected_objects.add(obj)
    for rel in base_obj.back_references():
        expected_objects.add(rel)
    if getattr(base_obj, 'budget_split', None) is None:
        base_obj.budget_split = []
    expected_line_uids = [expected_obj.UID() for expected_obj in expected_objects]
    existing_line_uids = [line['uid'] for line in base_obj.budget_split]

    # remove old lines
    for uid_to_remove in set(existing_line_uids).difference(expected_line_uids):
        line_to_remove = [line for line in base_obj.budget_split if line['uid'] == uid_to_remove][0]
        base_obj.budget_split.remove(line_to_remove)

    # add new lines (100 % for base object, 0 % for links)
    for uid_to_add in set(expected_line_uids).difference(existing_line_uids):
        if obj.UID() == uid_to_add:
            object_to_add = obj
        else:
            object_to_add = api.content.get(UID=uid_to_add)
        percentage = 0.0 if base_hasattr(object_to_add, '_link_portal_type') else 100.0
        title = reference_numbers_title(object_to_add)
        base_obj.budget_split.append({
            'uid': uid_to_add,
            'percentage': percentage,
            'title': title,
        })

    # fix percentages if total isn't equal to 100.0
    current_percentages = sum([line['percentage'] for line in base_obj.budget_split])
    if current_percentages != 100.0:
        corrective_coefficient = 100.0 / current_percentages
        for line in base_obj.budget_split:
            line['percentage'] *= corrective_coefficient


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

    while not IProjectSpace.providedBy(parent):
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
    # compute reference number
    if not base_hasattr(obj, 'symbolic_link'):
        projectspace = getProjectSpace(obj)
        projectspace.last_reference_number += 1
        obj.reference_number = projectspace.last_reference_number
        obj.reindexObject(['reference_number'])
    # refresh budget split lines
    if base_hasattr(obj, 'budget_split'):
        update_budget_splits(obj, event)
    # Update field data on every parents
    pw = obj.portal_workflow
    workflows = pw.getWorkflowsFor(obj)
    if not workflows or pw.getInfoFor(obj, 'review_state') in get_budget_states(obj.portal_type):
        _updateSummarizedFields(obj)


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
        # clean link parents in both directions
        catalog = getUtility(ICatalog)
        intids = getUtility(IIntIds)
        for rel in catalog.findRelations({'to_id': intids.getId(obj), 'from_attribute': 'symbolic_link'}):
            _cleanParentsFields(rel.from_object)
        for rel in catalog.findRelations({'from_id': intids.getId(obj), 'from_attribute': 'symbolic_link'}):
            _cleanParentsFields(rel.to_object)


def onRemoveProject(obj, event):
    """
        When a project is removed
    """
    if base_hasattr(obj, 'budget_split'):
        update_budget_splits(obj)
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
    """
    Remove value to field which are hided in project space config
    :param event: pstprojectspace_modified
    :param dic: empty key in field_constraints
    :return: None
    """
    to_empty = []
    pt = ""
    for desc in event.descriptions:
        for attr in desc.attributes:
            if attr.endswith('fields'):
                pt = attr[:-7]
                for field in dic[pt]:
                    if field not in getattr(event.object, attr):
                        to_empty.append(field)
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
