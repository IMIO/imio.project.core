# -*- coding: utf-8 -*-

from plone import api
from plone.app.dexterity.interfaces import ITypeSchemaContext
from plone.dexterity.interfaces import IDexterityContent
from Products.ATContentTypes.interfaces.interfaces import IATContentType
from zope.component.hooks import getSite
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


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
            terms.append(SimpleTerm(dep.getId().decode('utf8'),
                                    token=brain.id.decode('utf8'),
                                    title=dep.Title().decode('utf8')))
        for service_brain in services_brains:
            comb = "%s - %s" % (dep.Title().decode('utf8'),
                                service_brain.Title.decode('utf8'))
            termId = "%s-%s" % (brain.id.decode('utf8'),
                                service_brain.id.decode('utf8'))
            terms.append(SimpleTerm(termId, token=termId, title=comb))
    return SimpleVocabulary(terms)


def getProjectSpace(context):
    """
      Return the projectspace object, context is an element in a projectspace
    """
    # MUST BE ANALYZED BECAUSE it's called many time at view or edit
    # if context is None, we have to find it in request
    if context is None:
        portal = getSite()
        if hasattr(portal.REQUEST['PUBLISHED'], 'context'):
            context = portal.REQUEST['PUBLISHED'].context
        else:
            context = portal.REQUEST['PARENTS'][0]
    # sometimes, for inline validation for example on addView, context is not the object
    # but a Form of different kind, the real object is the form.context
    elif not IDexterityContent.providedBy(context):
        context = context.context
    # when editing dexterity fields in configuration, like on operationalobjective
    elif ITypeSchemaContext.providedBy(context):
        return api.content.find(portal_type='projectspace')[0].getObject()
    parent = context
    while not parent.portal_type == 'projectspace':
        parent = parent.aq_inner.aq_parent
    return parent
