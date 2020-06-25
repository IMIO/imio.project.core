# -*- coding: utf-8 -*-

from imio.project.core import _
from imio.project.core import _tr
from plone import api
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.z3cform import layout
from Products.CMFPlone.utils import safe_unicode
from z3c.form import form
from zope import schema
from zope.interface import implements
from zope.interface import Interface
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


def get_budget_states(portal_type):
    return api.portal.get_registry_record('imio.project.settings.{}_budget_states'.format(portal_type),
                                          default=[]) or []


class ProjectStatesVocabulary(object):
    """ Project workflow states """
    implements(IVocabularyFactory)

    def __call__(self, context):

        pw = api.portal.get_tool('portal_workflow')

        for workflow in pw.getWorkflowsFor('project'):
            states = [value for value in workflow.states.values()]
        terms = []
        for state in states:
            terms.append(SimpleTerm(state.id, title=_tr(safe_unicode(state.title), domain='plone')))
        return SimpleVocabulary(terms)


class IImioProjectSettings(Interface):
    """"""

    project_budget_states = schema.List(
        title=_(u"${type} budget globalization states", mapping={'type': _('Project')}),
        description=_(u'Put states on the right for which you want to globalize budget fields.'),
        required=False,
        value_type=schema.Choice(vocabulary=u'imio.project.core.ProjectStatesVocabulary'),
    )


class SettingsEditForm(RegistryEditForm):
    """"""

    form.extends(RegistryEditForm)
    schema = IImioProjectSettings
    schema_prefix = 'imio.project.settings'
    label = _(u"Project settings")


SettingsView = layout.wrap_form(SettingsEditForm, ControlPanelFormWrapper)
