from zope.component import provideAdapter
from zope import schema
from zope.interface import implements
from zope.interface import Interface
from zope.interface import Invalid

from z3c.form import validator
from z3c.form.widget import FieldWidget

from plone.autoform import directives
from plone.dexterity.content import Container
from plone.dexterity.schema import DexteritySchemaPolicy
from plone.supermodel import model

from collective.z3cform.datagridfield import DataGridField, DictRow

from Products.CMFCore.utils import getToolByName

from imio.project.core import _


def DataGridFieldWithListingTableFactory(field, request):
    """
        IFieldWidget factory for DataGridField using the 'listing' class for the main table.
    """
    widget = DataGridField(request)
    # temporary fallback until display_table_css_class attribute is in collective.z3cform.datagridfield
    if hasattr(widget, 'display_table_css_class'):
        widget.display_table_css_class = 'listing'
    return FieldWidget(field, widget)


def _validateKeyNotUsed(context, value, stored_value, attribute_using_keys, portal_types=[]):
    """
      Check if a key was removed in the given p_value regarding p_stored_value on context.
      If a key was removed, check that no given p_portal_types is using it.
      It suppose that given p_value is a list of dicts with 'key' and 'label' as existing keys."""
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
        used_value = getattr(obj, attribute_using_keys, ())
        # we need a tuple so 'set' here under works...
        # this is because we want this method to be a bit generic...
        if isinstance(used_value, unicode):
            used_value = (used_value, )
        if not used_value:
            used_value = ()
        intersectionValues = set(used_value).intersection(removedKeys)
        if intersectionValues:
            wrong_removed_key = intersectionValues.pop()
            defaultMsg = u"The key '%s' that was removed is used by some elements " \
                         u"(like for example '%s') and can not be removed!" % \
                         (wrong_removed_key, obj.absolute_url())
            raise Invalid(_(u"The key '${removed_key}' can not be removed because it is "
                            u"currently used (for example by '${used_by_url}').",
                          mapping={'removed_key': wrong_removed_key,
                                   'used_by_url': obj.absolute_url(), },
                          default=defaultMsg))


class RemovedValueIsNotUsedByCategoriesFieldValidator(validator.SimpleFieldValidator):
    def validate(self, value):
        # while removing a value from a defined vocabulary, check that
        # it is not used anywhere...
        super(validator.SimpleFieldValidator, self).validate(value)
        stored_value = getattr(self.context, self.field.getName())
        _validateKeyNotUsed(self.context,
                            value,
                            stored_value,
                            'categories',
                            [])


class RemovedValueIsNotUsedByPriorityFieldValidator(validator.SimpleFieldValidator):
    def validate(self, value):
        # while removing a value from a defined vocabulary, check that
        # it is not used anywhere...
        super(validator.SimpleFieldValidator, self).validate(value)
        stored_value = getattr(self.context, self.field.getName())
        _validateKeyNotUsed(self.context,
                            value,
                            stored_value,
                            'priority',
                            [])


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


class IProjectSpace(model.Schema):
    """
        Project schema, field ordering
    """
    categories = schema.List(
        title=_(u'Categories values'),
        description=_(u"Enter one different value by row. Label is the displayed value. Key is the stored value:"
                      " in lowercase, without space."),
        required=True,
        value_type=DictRow(title=u"",
                           schema=IVocabularySchema,
                           required=False),
    )
    directives.widget(categories=DataGridFieldWithListingTableFactory)

    priority = schema.List(
        title=_(u'Priority values'),
        description=_(u"Enter one different value by row. Label is the displayed value. Key is the stored value:"
                      " in lowercase, without space."),
        required=True,
        value_type=DictRow(title=u"",
                           schema=IVocabularySchema,
                           required=False),
    )
    directives.widget(priority=DataGridFieldWithListingTableFactory)

validator.WidgetValidatorDiscriminators(RemovedValueIsNotUsedByCategoriesFieldValidator,
                                        field=IProjectSpace['categories'])
provideAdapter(RemovedValueIsNotUsedByCategoriesFieldValidator)

validator.WidgetValidatorDiscriminators(RemovedValueIsNotUsedByPriorityFieldValidator,
                                        field=IProjectSpace['priority'])
provideAdapter(RemovedValueIsNotUsedByPriorityFieldValidator)


class ProjectSpace(Container):
    """ """
    implements(IProjectSpace)


class ProjectSpaceSchemaPolicy(DexteritySchemaPolicy):
    """ """

    def bases(self, schemaName, tree):
        return (IProjectSpace, )
