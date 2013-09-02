# -*- coding: utf-8 -*-

from zope.annotation import IAnnotations
from imio.project.core.config import CHILDREN_BUDGET_INFOS_ANNOTATION_KEY


def _updateParentsBudgetInfos(obj):
    """
      Update budget infos on every parents, going up until the parent is the projectspace
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
    objUID = obj.UID()
    # we take the budget infos saved on obj annotation
    obj_annotations = IAnnotations(obj)
    if CHILDREN_BUDGET_INFOS_ANNOTATION_KEY in obj_annotations:
        formattedBudgetInfos = obj_annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY]
    # add self in budgetInfos
    formattedBudgetInfos[objUID] = obj.budget

    parent = obj.aq_inner.aq_parent
    while not parent.portal_type == 'projectspace':
        parent_annotations = IAnnotations(parent)
        if not CHILDREN_BUDGET_INFOS_ANNOTATION_KEY in parent_annotations:
            parent_annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY] = {}
        parent_annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY].update(formattedBudgetInfos)
        parent = parent.aq_inner.aq_parent


def onAddProject(obj, event):
    """
      Handler when a project is added
    """
    # Update budget infos on every parents
    _updateParentsBudgetInfos(obj)


def onModifyProject(obj, event):
    """
      Handler when a project is modified
    """
    # Update budget infos on every parents
    _updateParentsBudgetInfos(obj)


def onRemoveProject(obj, event):
    """
    """
    objUID = obj.UID()
    parent = obj.aq_inner.aq_parent
    while not parent.portal_type == 'projectspace':
        parent_annotations = IAnnotations(parent)
        # here we are sure that parent has an annotation with key CHILDREN_BUDGET_INFOS_ANNOTATION_KEY
        # and that it has a key with given p_obj UID, but as remove event is called several times, we need to check...
        if objUID in parent_annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY]:
            del parent_annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY][objUID]
        parent = parent.aq_inner.aq_parent