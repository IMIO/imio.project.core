# -*- coding: utf-8 -*-

from Products.CMFPlone.utils import base_hasattr
from collective.contact.plonegroup.utils import get_own_organization
from imio.project.core.content.projectspace import IProjectSpace
from plone import api
from plone.app.dexterity.interfaces import ITypeSchemaContext
from plone.dexterity.interfaces import IDexterityContent
from Products.CMFPlone.utils import safe_unicode
from zope.component.hooks import getSite
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


def getVocabularyTermsForOrganization(context, organization_id='services', states=[], sort_on='path'):
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
    brains = catalog.unrestrictedSearchResults(**crit)
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
        return api.content.find(object_provides=IProjectSpace.__identifier__)[0].getObject()
    # sometimes, for inline validation for example on addView, context is not the object
    # but a Form of different kind, the real object is the form.context
    if not IDexterityContent.providedBy(context):
        context = context.context
    parent = context
    while not IProjectSpace.providedBy(parent) and parent.portal_type != 'Plone Site':
        parent = parent.aq_inner.aq_parent
    return parent


def reference_numbers_title(obj):
    """
    Describes the path of a Project, using reference numbers.
    Symlinks are marked with an (L).
    examples:
        - "OS.1 - OO.2 - A.4"
        - "OS.1 - OO.6 - A.4 (L)"
    """

    def short_title(obj):
        initials = {
            'strategicobjective': 'OS',
            'operationalobjective': 'OO',
            'pstaction': 'A',
            'pstsubaction': 'SA',
        }.get(obj.portal_type, '')
        reference_number = obj.reference_number or 0
        is_link = ' (L)' if base_hasattr(obj, '_link_portal_type') else ''
        return u'{}.{}{}'.format(initials, reference_number, is_link)

    refs = [short_title(obj)]
    parent = obj.aq_inner.aq_parent
    while not IProjectSpace.providedBy(parent):
        refs.append(short_title(parent))
        parent = parent.aq_inner.aq_parent
    refs.reverse()
    return u" - ".join(refs)


def get_budget_states(project):
    """
    Get the list of budget states of a given project type
    :param project:
    :type project: object
    :return: budget states field
    :rtype: list
    """
    import ipdb; ipdb.set_trace()
    project_space = getProjectSpace(project)
    return getattr(project_space, '{}_budget_states'.format(project.portal_type))
