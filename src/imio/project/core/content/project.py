import datetime

from zope import schema
from zope.interface import implements
from zope.interface import Interface
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary
from z3c.form.widget import FieldWidget

from plone.app.textfield import RichText
from plone.autoform import directives
from plone.dexterity.content import Container
from plone.dexterity.schema import DexteritySchemaPolicy
from plone.formwidget.datetime.z3cform.widget import DateFieldWidget
from plone.supermodel import model

from collective.z3cform.datagridfield import DataGridField, DictRow
from collective.z3cform.rolefield.field import LocalRolesToPrincipals

from imio.project.core import _
from imio.project.core.utils import getVocabularyTermsForOrganization
from imio.project.core.utils import getProjectSpace


def DataGridFieldWithListingTableFactory(field, request):
    """IFieldWidget factory for DataGridField using the 'listing' class for the main table."""
    widget = DataGridField(request)
    # temporary fallback until display_table_css_class attribute is in collective.z3cform.datagridfield
    if hasattr(widget, 'display_table_css_class'):
        widget.display_table_css_class = 'listing'
    return FieldWidget(field, widget)


class IResultIndicatorSchema(Interface):
    """Schema used for the datagrid field 'result_indicator' of IProject."""
    label = schema.TextLine(
        title=_("Label"),
        required=True,)
    value = schema.Int(
        title=_("Expected value"),
        required=True,)
    reached_value = schema.Int(
        title=_("Reached value"),
        required=True,
        default=0,)


class IProject(model.Schema):
    """
        Project schema, field ordering
    """
    # use 'categories' field name  even if mono-valued for now, because 'category' is reserved
    categories = schema.Choice(
        title=_(u'Category'),
        description=_(u"Choose a category."),
        required=False,
        vocabulary=u'imio.project.core.content.project.categories_vocabulary',
    )

    priority = schema.Choice(
        title=_(u'Priority'),
        description=_(u"Choose a priority."),
        vocabulary=u'imio.project.core.content.project.priority_vocabulary',
    )

    budget = schema.Text(
        title=_(u"Budget"),
        description=_("Budget details"),
        required=False,
    )

    manager = LocalRolesToPrincipals(
        title=_(u"Manager"),
        description=_(u"Choose principals that will manage this project."),
        roles_to_assign=('Editor',),
        value_type=schema.Choice(
            vocabulary='imio.project.core.content.project.manager_vocabulary'
        ),
        required=True,
    )

    visible_for = LocalRolesToPrincipals(
        title=_(u"Visible for"),
        description=_(u"Choose principals that can see this project."),
        required=False,
        roles_to_assign=('Reader',),
        value_type=schema.Choice(
            vocabulary='imio.project.core.content.project.visible_for_vocabulary'
        ),
    )

    extra_concerned_people = schema.Text(
        title=_(u"Extra concerned people"),
        description=_(u"Specify here concerned people that do not have access "
                      "to the application, this will just be informational."),
        required=False,
    )

    result_indicator = schema.List(
        title=_(u'Result indicator'),
        description=_(u"Enter one indicator by row. Value is a number. "
                      "Label must precise the signification of this number."),
        required=False,
        value_type=DictRow(title=_("Result indicator"),
                           schema=IResultIndicatorSchema,
                           required=False),
    )
    directives.widget(result_indicator=DataGridFieldWithListingTableFactory)

    planned_begin_date = schema.Date(
        title=_(u'Planned begin date'),
        description=_(u"Enter the planned begin date."),
        required=False,
        defaultFactory=datetime.date.today,
    )
    directives.widget(planned_begin_date=DateFieldWidget)

    effective_begin_date = schema.Date(
        title=_(u'Effective begin date'),
        description=_(u"Enter the effective begin date."),
        required=False,
        defaultFactory=datetime.date.today,
    )
    directives.widget(effective_begin_date=DateFieldWidget)

    planned_end_date = schema.Date(
        title=_(u'Planned end date'),
        description=_(u"Enter the planned end date."),
        required=False,
        defaultFactory=datetime.date.today,
    )
    directives.widget(planned_end_date=DateFieldWidget)

    effective_end_date = schema.Date(
        title=_(u'Effective end date'),
        description=_(u"Enter the effective end date."),
        required=False,
        defaultFactory=datetime.date.today,
    )
    directives.widget(effective_end_date=DateFieldWidget)

    progress = schema.Int(
        title=_(u"Progress"),
        description=_(u"Progress estimation in %."),
        required=False,
        default=0,
    )

    comments = RichText(
        title=_(u"Comments"),
        description=_(u"Various comments"),
        required=False,
        default_mime_type='text/html',
        output_mime_type='text/html',
        allowed_mime_types=('text/html',),
    )


class Project(Container):
    """ """
    implements(IProject)
    __ac_local_roles_block__ = False


class CategoriesVocabulary(object):
    implements(IVocabularyFactory)

    def __call__(self, context):
        """"""
        projectspace = getProjectSpace(context)
        terms = []
        categories = projectspace.categories
        for category in categories:
            terms.append(SimpleTerm(category['key'], category['key'], category['label'], ))
        return SimpleVocabulary(terms)


class PriorityVocabulary(object):
    implements(IVocabularyFactory)

    def __call__(self, context):
        """"""
        projectspace = getProjectSpace(context)
        terms = []
        priorities = projectspace.priority
        for priority in priorities:
            terms.append(SimpleTerm(priority['key'], priority['key'], priority['label'], ))
        return SimpleVocabulary(terms)


class ManagerVocabulary(object):
    """
    """
    implements(IVocabularyFactory)

    def __call__(self, context):
        """"""
        return getVocabularyTermsForOrganization(context)


class VisibleForVocabulary(object):
    """
    """
    implements(IVocabularyFactory)

    def __call__(self, context):
        """"""
        return getVocabularyTermsForOrganization(context)


class ProjectSchemaPolicy(DexteritySchemaPolicy):
    """ """

    def bases(self, schemaName, tree):
        return (IProject, )
