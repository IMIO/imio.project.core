from zope.annotation import IAnnotations
from imio.project.core.events import _updateParentsBudgetInfos, _cleanParentsBudgetInfos
from imio.project.core.config import CHILDREN_BUDGET_INFOS_ANNOTATION_KEY


def trace_obj(out, obj):
    obj_annotations = IAnnotations(obj)
    formattedBudgetInfos = {}
    if CHILDREN_BUDGET_INFOS_ANNOTATION_KEY in obj_annotations:
        formattedBudgetInfos = dict(obj_annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY])
    out.append("obj: %s, budget: %s, annot: %s" % ('/'.join(obj.getPhysicalPath()[4:]), obj.budget, formattedBudgetInfos))


def update_budget_infos(self):
    """
        update budget infos of current element and sub objects
    """
    out=[]
    #trace_obj(out, self)
    pw = self.portal_workflow
    context_path = '/'.join(self.getPhysicalPath())
    # First we clean the annotation
    brains = self.portal_catalog(portal_type=['operationalobjective', 'strategicobjective', ], path=context_path, sort_on='path')
    for brain in brains:
        obj = brain.getObject()
        obj_annotations = IAnnotations(obj)
        out.append("working on obj: %s" % ('/'.join(obj.getPhysicalPath()[4:])))
        if CHILDREN_BUDGET_INFOS_ANNOTATION_KEY in obj_annotations:
            obj_annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY] = {}
            out.append("Made empty")
    # Secondly we reconstruct the annotation dic
    brains = self.portal_catalog(portal_type=['operationalobjective', 'pstaction', ], path={'query': context_path}, sort_on='path')
    for brain in brains:
        obj = brain.getObject()
        #trace_obj(out, obj)
        out.append("working on obj: %s" % ('/'.join(obj.getPhysicalPath()[4:])))
        workflows = pw.getWorkflowsFor(obj)
        if not workflows or workflows[0].initial_state != pw.getInfoFor(obj, 'review_state'):
            _updateParentsBudgetInfos(obj)
            out.append("Added info to parents")
        else:
            # useless
            _cleanParentsBudgetInfos(obj)
            out.append("Removed info from parents")
    return "\n".join(out)


def print_budget_infos(self):
    """
        print budget infos
    """
    out=[]
    context_path = '/'.join(self.getPhysicalPath())
    # First we clean the annotation
    brains = self.portal_catalog(portal_type=['operationalobjective', 'strategicobjective', ], path=context_path, sort_on='path')
    for brain in brains:
        trace_obj(out, brain.getObject())
    return "\n".join(out)
