# -*- coding: utf-8 -*-

from imio.helpers.content import get_schema_fields
from imio.project.core import _
from imio.project.core import _tr
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.z3cform import layout
from z3c.form import form
from zope import schema
from zope.interface import implements
from zope.interface import Interface
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


def get_pt_fields_voc(pt, excluded):
    terms = []
    for name, field in get_schema_fields(type_name=pt, prefix=True):
        if name in excluded:
            continue
        terms.append(SimpleTerm(name, title=_tr(field.title)))
    return SimpleVocabulary(terms)


class ProjectFieldsVocabulary(object):
    implements(IVocabularyFactory)

    def __call__(self, context):
        return get_pt_fields_voc('project',
                                 ['IDublinCore.contributors', 'IDublinCore.creators', 'IDublinCore.effective',
                                  'IDublinCore.expires', 'IDublinCore.language', 'IDublinCore.rights',
                                  'IDublinCore.subjects', 'INameFromTitle.title', 'IVersionable.changeNote',
                                  'notes'])


class IImioProjectSettings(Interface):
    """"""

    project_fields = schema.List(
        title=_(u"${type} fields display", mapping={'type': _('Project')}),
        value_type=schema.Choice(vocabulary=u'imio.project.core.ProjectFieldsVocabulary'),
#        value_type=schema.Choice(source=IMFields),  # a source is not managed by registry !!
    )


class SettingsEditForm(RegistryEditForm):
    """"""

    form.extends(RegistryEditForm)
    schema = IImioProjectSettings
    schema_prefix = 'imio.project.settings'
    label = _(u"Project settings")


SettingsView = layout.wrap_form(SettingsEditForm, ControlPanelFormWrapper)
