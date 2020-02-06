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
from zope.interface import Invalid
from zope.interface import invariant
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


field_constraints = {
    'titles': {},
    'mandatory': {'project': ['IDublinCore.title', 'IDublinCore.description']},
    'indexes': {'project': [('IDublinCore.title', 1), ('IDublinCore.description', 2)]},
}


def get_pt_fields_voc(pt, excluded, constraints={}):
    """
        Returns a vocabulary with the given portal type fields, not excluded.
        Mandatory ones are suffixed with asterisk.
    """
    terms = []
    mandatory = constraints.get('mandatory', {})
    if pt not in constraints.setdefault('titles', {}):
        constraints['titles'][pt] = {}
    print "=> "+pt
    for name, field in get_schema_fields(type_name=pt, prefix=True):
        if name in excluded:
            continue
        print name
        title = _tr(field.title)
        constraints['titles'][pt][name] = title
        if name in mandatory.get(pt, []):
            title = u'{} *'.format(title)
        terms.append(SimpleTerm(name, title=title))
    return SimpleVocabulary(terms)


def mandatory_check(data, constraints):
    """ Check the presence of mandatory fields """
    dic = data._Data_data___
    mandatory = constraints.get('mandatory', {})
    missing = {}
    for pt in mandatory:
        fld = '{}_fields'.format(pt)
        for mand in mandatory[pt]:
            if not mand in dic[fld]:
                if pt not in missing:
                    missing[pt] = []
                missing[pt].append(mand)
    msg = u''
    for pt in missing:
        fields = [u"'{}'".format(constraints['titles'][pt][fld]) for fld in missing[pt]]
        msg += _tr(u"for '${type}' type => ${fields}. ", mapping={'type': _tr(pt),
                                                                  'fields': ', '.join(fields)})
    if msg:
        raise Invalid(_(u'Missing mandatory fields: ${msg}', mapping={'msg': msg}))


def position_check(data, constraints):
    """ Check the position of fields """
    dic = data._Data_data___
    indexes = constraints.get('indexes', {})
    errors = {}
    for pt in indexes:
        pt_fld = '{}_fields'.format(pt)
        for (fld, i) in indexes[pt]:
            if dic[pt_fld].index(fld) + 1 != i:
                if pt not in errors:
                    errors[pt] = []
                errors[pt].append((fld, i))
    msg = u''
    for pt in errors:
        fields = [_tr(u"'${fld}' at position ${i}",
                      mapping={'fld': constraints['titles'][pt][fld], 'i': i}) for (fld, i) in errors[pt]]
        msg += _tr(u"for '${type}' type => ${fields}. ", mapping={'type': _tr(pt),
                                                                  'fields': ', '.join(fields)})
    if msg:
        raise Invalid(_(u'Some fields have to be at a specific position: ${msg}', mapping={'msg': msg}))


class ProjectFieldsVocabulary(object):
    implements(IVocabularyFactory)

    def __call__(self, context):
        return get_pt_fields_voc('project',
                                 ['IDublinCore.contributors', 'IDublinCore.creators', 'IDublinCore.effective',
                                  'IDublinCore.expires', 'IDublinCore.language', 'IDublinCore.rights',
                                  'IDublinCore.subjects', 'INameFromTitle.title', 'IVersionable.changeNote',
                                  'notes'],
                                 field_constraints)


class IImioProjectSettings(Interface):
    """"""

    project_fields = schema.List(
        title=_(u"${type} fields display", mapping={'type': _('Project')}),
        description=_(u'Put fields on the right to display it. Fields with asterisk are mandatory !'),
        value_type=schema.Choice(vocabulary=u'imio.project.core.ProjectFieldsVocabulary'),
#        value_type=schema.Choice(source=IMFields),  # a source is not managed by registry !!
    )

    @invariant
    def validateSettings(data):
        mandatory_check(data, field_constraints)
        position_check(data, field_constraints)


class SettingsEditForm(RegistryEditForm):
    """"""

    form.extends(RegistryEditForm)
    schema = IImioProjectSettings
    schema_prefix = 'imio.project.settings'
    label = _(u"Project settings")


SettingsView = layout.wrap_form(SettingsEditForm, ControlPanelFormWrapper)
