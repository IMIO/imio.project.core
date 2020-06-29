from collective.z3cform.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield import DictRow
from imio.helpers.content import get_schema_fields
from imio.project.core import _
from imio.project.core import _tr
from imio.project.core import _tr
from plone import api
from plone import api
from plone.autoform import directives
from plone.dexterity.content import Container
from plone.dexterity.schema import DexteritySchemaPolicy
from plone.supermodel import model
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import base_hasattr
from Products.CMFPlone.utils import safe_unicode
from z3c.form import validator
from z3c.form.browser.select import SelectFieldWidget
from zope import schema
from zope.component import provideAdapter
from zope.interface import implements
from zope.interface import implements
from zope.interface import Interface
from zope.interface import Invalid
from zope.interface import invariant
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.vocabulary import SimpleVocabulary

ERROR_VALUE_REMOVED_IS_IN_USE = "The key '${removed_key}' can not be removed because it is currently " \
                                "used (for example by '${used_by_url}')."


field_constraints = {
    'titles': {},
    'mandatory': {'project': ['IDublinCore.title']},
    'indexes': {'project': [('IDublinCore.title', 1)]},
    'empty': {'project': []},
}


def get_pt_fields_voc(pt, excluded, constraints={}):
    """
        Returns a vocabulary with the given portal type fields, not excluded.
        Mandatory ones are suffixed with asterisk.
    """
    terms = []
    mandatory = constraints.get('mandatory', {}).get(pt, [])
    positions = {fld: pos for fld, pos in constraints.get('indexes', {}).get(pt, [])}
    empty = constraints.get('empty', {}).get(pt, [])
    if pt not in constraints.setdefault('titles', {}):
        constraints['titles'][pt] = {}
    for name, field in get_schema_fields(type_name=pt, prefix=True):
        if name in excluded:
            continue
        title = _tr(field.title)
        constraints['titles'][pt][name] = title
        if name in mandatory:
            title = u'{} *'.format(title)
        if name in positions:
            title = u'{} {}'.format(title, positions[name])
        if name in empty:
            title = u'{} -'.format(title)
        terms.append(SimpleTerm(name, title=title))
    return SimpleVocabulary(terms)


def mandatory_check(data, constraints):
    """ Check the presence of mandatory fields """
    dic = data._Data_data___
    mandatory = constraints.get('mandatory', {})
    missing = {}
    for pt in mandatory:
        pt_fld = '{}_fields'.format(pt)
        if pt_fld in dic:
            for mand in mandatory[pt]:
                if mand not in dic[pt_fld]:
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
        if pt_fld in dic:
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


def _validateKeyNotUsed(context,
                        value,
                        stored_value,
                        attribute_using_keys,
                        sub_attribute_using_key=None,
                        portal_types=[]):
    """
      Check if a key was removed in the given p_value regarding p_stored_value on context.
      If a key was removed, check that no given p_portal_types is using it.
      It suppose that given p_value is a list of dicts with 'key' and 'label' as existing keys.
      Given p_attribute_using_keys is the name of the attribute of sub objects using this key.
      Given p_sub_attribute_using_key is in the case of a datagridfield using this vocabulary,
      it is the name of the column using the vocabulary..."""
    # we only go further if a key was actually removed
    # so compare stored values to new given values
    storedKeys = [stored['key'] for stored in stored_value]
    newKeys = [newValue['key'] for newValue in value]
    removedKeys = set(storedKeys).difference(set(newKeys))
    if not removedKeys:
        return
    # if we found removed keys, then check that it was not used
    params = {'path': {'query': '/'.join(context.getPhysicalPath())}, }
    if portal_types:
        params['portal_type'] = portal_types
    catalog = getToolByName(context, 'portal_catalog')
    brains = catalog(**params)
    for brain in brains:
        # do not validate context... (root element).  While doing a query on path, the context is also found...
        if brain.portal_type == context.portal_type:
            continue
        obj = brain.getObject()
        if not base_hasattr(obj, attribute_using_keys):
            continue
        used_value = getattr(obj, attribute_using_keys, ())
        # we need a tuple so 'set' here under works...
        # this is because we want this method to be a bit generic...
        if isinstance(used_value, unicode):
            used_value = (used_value, )
        # if we use a datagridfield, we have to get the relevant column
        if sub_attribute_using_key:
            # it means that we use a datagridfield and that data is stored
            # in a dict contained in the list...
            tmpres = []
            for line in used_value or ():
                tmpres.append(line[sub_attribute_using_key])
            used_value = tuple(tmpres)
        if not used_value:
            continue
        intersectionValues = set(used_value).intersection(removedKeys)
        if intersectionValues:
            wrong_removed_key = intersectionValues.pop()
            raise Invalid(_(ERROR_VALUE_REMOVED_IS_IN_USE,
                          mapping={'removed_key': wrong_removed_key,
                                   'used_by_url': obj.absolute_url(), }))


class RemovedValueIsNotUsedByCategoriesFieldValidator(validator.SimpleFieldValidator):
    def validate(self, value):
        # while removing a value from a defined vocabulary, check that
        # it is not used anywhere...
        super(validator.SimpleFieldValidator, self).validate(value)
        # in the creation process, the validator is called but it is not necessary
        if not self.context.portal_type == 'projectspace':
            return
        stored_value = getattr(self.context, self.field.getName())
        _validateKeyNotUsed(self.context,
                            value,
                            stored_value,
                            'categories',
                            None,
                            [])


class RemovedValueIsNotUsedByPriorityFieldValidator(validator.SimpleFieldValidator):
    def validate(self, value):
        # while removing a value from a defined vocabulary, check that
        # it is not used anywhere...
        super(validator.SimpleFieldValidator, self).validate(value)
        # in the creation process, the validator is called but it is not necessary
        if not self.context.portal_type == 'projectspace':
            return
        stored_value = getattr(self.context, self.field.getName())
        _validateKeyNotUsed(self.context,
                            value,
                            stored_value,
                            'priority',
                            None,
                            [])


class RemovedValueIsNotUsedByBudgetTypesFieldValidator(validator.SimpleFieldValidator):
    def validate(self, value):
        # while removing a value from a defined vocabulary, check that
        # it is not used anywhere...
        super(validator.SimpleFieldValidator, self).validate(value)
        # in the creation process, the validator is called but it is not necessary
        if not self.context.portal_type == 'projectspace':
            return
        stored_value = getattr(self.context, self.field.getName())
        _validateKeyNotUsed(self.context,
                            value,
                            stored_value,
                            # we use a datagridfield, we need to provide field using
                            # value and column name of the datagridfield...
                            'budget',
                            'budget_type',
                            [])


class ProjectFieldsVocabulary(object):
    implements(IVocabularyFactory)

    def __call__(self, context):
        return get_pt_fields_voc('project',
                                 ['IDublinCore.description', 'IDublinCore.contributors', 'IDublinCore.creators',
                                  'IDublinCore.effective', 'IDublinCore.expires', 'IDublinCore.language',
                                  'IDublinCore.rights', 'IDublinCore.subjects', 'INameFromTitle.title',
                                  'IVersionable.changeNote', 'notes'],
                                 field_constraints)


class IVocabularySchema(Interface):
    """
        Schema used for the vocabulary datagrid field.
    """
    label = schema.TextLine(
        title=_("Label"),
        required=True,)
    key = schema.ASCIILine(
        title=_("Key"),
        required=True,)


possible_years = SimpleVocabulary([SimpleTerm(y) for y in range(2012, 2030)])


class IProjectSpace(model.Schema):
    """
        Project schema, field ordering
    """
    last_reference_number = schema.Int(
        title=_(u"Last reference number"),
        # description=_(u""),
        required=False,
        default=0,
    )

    categories_values = schema.List(
        title=_(u'Categories values'),
        description=_(u"Enter one different value by row. Label is the displayed value. Key is the stored value:"
                      " in lowercase, without space."),
        required=True,
        value_type=DictRow(title=u"",
                           schema=IVocabularySchema,
                           required=False),
    )
    directives.widget('categories_values', DataGridFieldFactory, display_table_css_class='listing', allow_reorder=True)

    priority_values = schema.List(
        title=_(u'Priority values'),
        description=_(u"Enter one different value by row. Label is the displayed value. Key is the stored value:"
                      " in lowercase, without space."),
        required=True,
        value_type=DictRow(title=u"",
                           schema=IVocabularySchema,
                           required=False),
    )
    directives.widget('priority_values', DataGridFieldFactory, display_table_css_class='listing', allow_reorder=True)

    budget_types = schema.List(
        title=_(u'Budget types values'),
        description=_(u"Enter one different value by row. Label is the displayed value. Key is the stored value:"
                      " in lowercase, without space."),
        required=True,
        value_type=DictRow(title=u"",
                           schema=IVocabularySchema,
                           required=False),
    )
    directives.widget('budget_types', DataGridFieldFactory, display_table_css_class='listing', allow_reorder=True)

    budget_years = schema.List(
        title=_(u'Budget concerned years'),
        # description=_(u"Select all years concerned by budget."),
        required=True,
        value_type=schema.Choice(vocabulary=possible_years)
    )
    directives.widget('budget_years', SelectFieldWidget, multiple='multiple', size=6)

    project_budget_states = schema.List(
        title=_(u"${type} budget globalization states", mapping={'type': _('Project')}),
        description=_(u'Put states on the right for which you want to globalize budget fields.'),
        required=False,
        value_type=schema.Choice(vocabulary=u'imio.project.core.ProjectStatesVocabulary'),
    )

    use_ref_number = schema.Bool(
        title=_(u'Use reference number'),
        description=_(u'Used in Title, documents, etc.'),
        default=True,
    )

    INS_code = schema.TextLine(
        title=_(u'INS Code'),
        # description=_(u'5-character code statistically representing the town'),
        required=False,
    )

    current_fiscal_year = schema.Int(
        title=_(u'Current fiscal year'),
        # description=_(u''),
        required=False,
    )

    plan_values = schema.List(
        title=_(u'Plan values'),
        description=_(u"Enter one different value by row. Label is the displayed value. Key is the stored value:"
                      " in lowercase, without space."),
        required=True,
        value_type=DictRow(title=u"",
                           schema=IVocabularySchema,
                           required=False),
    )
    directives.widget('plan_values', DataGridFieldFactory, display_table_css_class='listing', allow_reorder=True)

    project_fields = schema.List(
        title=_(u"${type} fields display", mapping={'type': _('Project')}),
        description=_(u'Put fields on the right to display it. Flags are : ...'),
        value_type=schema.Choice(vocabulary=u'imio.project.core.ProjectFieldsVocabulary'),
        # value_type=schema.Choice(source=IMFields),  # a source is not managed by registry !!
    )

    @invariant
    def validateSettings(data):
        mandatory_check(data, field_constraints)
        position_check(data, field_constraints)


validator.WidgetValidatorDiscriminators(RemovedValueIsNotUsedByCategoriesFieldValidator,
                                        field=IProjectSpace['categories_values'])
provideAdapter(RemovedValueIsNotUsedByCategoriesFieldValidator)

validator.WidgetValidatorDiscriminators(RemovedValueIsNotUsedByPriorityFieldValidator,
                                        field=IProjectSpace['priority_values'])
provideAdapter(RemovedValueIsNotUsedByPriorityFieldValidator)

validator.WidgetValidatorDiscriminators(RemovedValueIsNotUsedByBudgetTypesFieldValidator,
                                        field=IProjectSpace['budget_types'])
provideAdapter(RemovedValueIsNotUsedByBudgetTypesFieldValidator)


class ProjectSpace(Container):
    """ """
    implements(IProjectSpace)


class ProjectSpaceSchemaPolicy(DexteritySchemaPolicy):
    """ """

    def bases(self, schemaName, tree):
        return (IProjectSpace, )


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