from zope import schema
from zope.interface import Interface, implements
from z3c.form.widget import FieldWidget
from plone.autoform import directives
from plone.dexterity.content import Container
from plone.dexterity.schema import DexteritySchemaPolicy
from plone.supermodel import model
from collective.z3cform.datagridfield import DataGridField, DictRow
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


class IVocabularySchema(Interface):
    """
        Schema used for the vocabulary datagrid field.
    """
    label = schema.TextLine(
        title=_("Label"),
        required=True,)
    key = schema.TextLine(
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


class ProjectSpace(Container):
    """ """
    implements(IProjectSpace)


class ProjectSpaceSchemaPolicy(DexteritySchemaPolicy):
    """ """

    def bases(self, schemaName, tree):
        return (IProjectSpace, )
