# -*- coding: utf-8 -*-

from collective.contact.plonegroup.utils import get_own_organization
from plone import api
from plone.app.dexterity.interfaces import ITypeSchemaContext
from plone.dexterity.interfaces import IDexterityContent
from Products.CMFPlone.utils import safe_unicode
from zope.component.hooks import getSite
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


def getVocabularyTermsForOrganization(context, organization_id='services', states=[], sort_on='getObjPositionInParent'):
    """
      Submethod called by vocabularies to get their content from a query
      in the organizations of the 'contacts' directory.
      Given p_organisation_id is an organization of the 'plonegroup-organization'
      where to query the elements.
    """
    portal = context.portal_url.getPortalObject()
    terms = []
    own_org = get_own_organization()
    if not own_org or organization_id not in own_org:
        return SimpleVocabulary(terms)
    sub = own_org[organization_id]
    sub_path = '/'.join(sub.getPhysicalPath())
    sub_path_len = len(sub_path) + 1
    catalog = portal.portal_catalog
    crit = {'path': {"query": sub_path, 'depth': 10},
            'portal_type': "organization",
            'sort_on': sort_on}
    if states:
        crit['review_state'] = states
    brains = catalog(**crit)
    levels = {}
    for brain in brains:
        path = brain.getPath()[sub_path_len:]
        if not path:
            continue  # organization_id itself
        value = safe_unicode(brain.UID)
        title = safe_unicode(brain.Title)
        level = len(path.split('/'))
        levels[level] = {'id': value, 'title': title}
        if level > 1:
            #value = u'{}-{}'.format(levels[level-1]['id'], value)
            title = u'{} - {}'.format(levels[level-1]['title'], title)
        terms.append(SimpleTerm(value, token=value, title=title))
    return SimpleVocabulary(terms)


def getProjectSpace(context):
    """
      Return the projectspace object, context is an element in a projectspace
    """
    # MUST BE ANALYZED BECAUSE it's called many time at view or edit
    # if context is None, we have to find it in request
    if context is None:
        portal = getSite()
        if 'PUBLISHED' not in portal.REQUEST:
            # This happen in rare situation (e.g. contentree widget search)
            context = portal.REQUEST['PARENTS'][-1]
        elif hasattr(portal.REQUEST['PUBLISHED'], 'context'):
            context = portal.REQUEST['PUBLISHED'].context
        else:
            context = portal.REQUEST['PARENTS'][0]
    # when editing dexterity fields in configuration, like on operationalobjective
    if ITypeSchemaContext.providedBy(context):
        return api.content.find(portal_type='projectspace')[0].getObject()
    # sometimes, for inline validation for example on addView, context is not the object
    # but a Form of different kind, the real object is the form.context
    if not IDexterityContent.providedBy(context):
        context = context.context
    parent = context
    while not parent.portal_type == 'projectspace':
        parent = parent.aq_inner.aq_parent
    return parent
