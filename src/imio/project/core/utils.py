# -*- coding: utf-8 -*-

from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary


def getVocabularyTermsForOrganization(context, organization_id='services'):
    """
      Submethod called by vocabularies to get their content from a query
      in the organizations of the 'contacts' directory.
      Given p_organisation_id is an organization of the 'plonegroup-organization'
      where to query the elements.
    """
    portal = context.portal_url.getPortalObject()
    terms = []
    catalog = portal.portal_catalog
    directory = portal.contacts
    brains = catalog(path={"query": '/'.join(directory.getPhysicalPath()), "depth": 1},
                     id="plonegroup-organization")
    if not brains:
        return SimpleVocabulary(terms)

    # query from the contacts.plonegroup-organization.organization_id
    base_orga = getattr(brains[0].getObject(), organization_id, None)
    if not base_orga:
        return SimpleVocabulary(terms)

    brains = catalog(path={"query": '/'.join(base_orga.getPhysicalPath()), "depth": 1},
                     portal_type="organization",
                     sort_on="getObjPositionInParent")
    for brain in brains:
        dep = brain.getObject()
        services_brains = catalog(path={"query": '/'.join(dep.getPhysicalPath()), "depth": 1},
                                  portal_type="organization",
                                  sort_on="getObjPositionInParent")
        if not services_brains:
            terms.append(SimpleTerm(dep.getId(), token=brain.id, title=dep.Title()))
        for service_brain in services_brains:
            comb = "%s - %s" % (dep.Title(), service_brain.Title)
            termId = "%s-%s" % (brain.id, service_brain.id)
            terms.append(SimpleTerm(termId, token=termId, title=comb))
    return SimpleVocabulary(terms)


def getProjectSpace(context):
    """
      Return the projectspace object, context is an element in a projectspace
    """
    # sometimes, for inline validation for example, context is not the object but a MyFormWrapper...
    if context.__module__ == 'Products.Five.metaclass':
        # the real context object is stored in 'context' of the MyFormWrapper...
        context = context.context
    parent = context
    while not parent.portal_type == 'projectspace':
        parent = parent.aq_inner.aq_parent
    return parent
