import datetime

from zope import schema
from zope.component.hooks import getSite
import zope.interface
from z3c.form import interfaces

from zope.interface import implements
from zope.interface import Interface
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary

from plone.app.textfield import RichText
from plone.autoform import directives
from plone.dexterity.content import Container
from plone.dexterity.schema import DexteritySchemaPolicy
from plone.formwidget.datetime.z3cform.widget import DateFieldWidget
from plone.supermodel import model
from z3c.form.widget import FieldWidget

from collective.z3cform.datagridfield import DictRow, DataGridFieldFactory
from collective.z3cform.rolefield.field import LocalRolesToPrincipals
from collective.contact.plonegroup.browser.settings import selectedOrganizationsPloneGroupsVocabulary

from imio.project.core import _
from imio.project.core.browser.widgets import BudgetInfosDataGridField
from imio.project.core.utils import getVocabularyTermsForOrganization
from imio.project.core.utils import getProjectSpace


@zope.interface.implementer(interfaces.IFieldWidget)
def BudgetInfosDataGridFieldFactory(field, request):
    """IFieldWidget factory for DataGridField using the 'BudgetInfosDataGridField' widget."""
    widget = BudgetInfosDataGridField(request)
    return FieldWidget(field, widget)


def default_year():
    """
      defaultFactory for the field IBudgetSchema.year
    """
    return datetime.date.today().year


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


class IBudgetSchema(Interface):
    """Schema used for the datagrid field 'budget' of IProject."""
    budget_type = schema.Choice(
        title=_(u'Budget_type'),
        description=_(u"Choose a budget type."),
        vocabulary=u'imio.project.core.content.project.budget_type_vocabulary',
    )
    year = schema.Choice(
        title=_(u'Year'),
        description=_(u"Choose a year."),
        vocabulary=u'imio.project.core.content.project.year_vocabulary',
        defaultFactory=default_year,
    )
    amount = schema.Float(
        title=_("Amount"),
        required=True,
        default=0.0,)


class IProject(model.Schema):
    """Project schema, field ordering."""
    reference_number = schema.Int(
        title=_(u"Reference number"),
        description=_(u"Unique identification"),
        required=False,
        default=0,
    )

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

    budget = schema.List(
        title=_(u'Budget'),
        description=_(u"Enter budget details.  If you have comments about budget, "
                      "use the field here above."),
        required=False,
        value_type=DictRow(title=_("Budget"),
                           schema=IBudgetSchema,
                           required=False),
    )
    directives.widget('budget', BudgetInfosDataGridFieldFactory, display_table_css_class='listing nosort')

    budget_comments = RichText(
        title=_(u"Budget comments"),
        description=_(u"Write here comments you have about budget."),
        required=False,
        default_mime_type='text/html',
        output_mime_type='text/html',
        allowed_mime_types=('text/html',),
    )

    manager = LocalRolesToPrincipals(
        title=_(u"Manager"),
        description=_(u"Choose principals that will manage this project."),
        roles_to_assign=('Editor', 'Reviewer', ),
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
    directives.widget('result_indicator', DataGridFieldFactory, display_table_css_class='listing nosort')

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

    observation = RichText(
        title=_(u"Observation"),
        description=_(u"Prior determination"),
        required=False,
        default_mime_type='text/html',
        output_mime_type='text/html',
        allowed_mime_types=('text/html',),
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
    def Title(self):
        return '%s (REF.%s)'% (self.title.encode('utf8'), self.reference_number)


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


class BudgetTypeVocabulary(object):
    implements(IVocabularyFactory)

    def __call__(self, context):
        """"""
        # here the context is not relevant as we are "out of nowhere"
        portal = getSite()
        current_obj = portal.REQUEST['PUBLISHED'].context
        projectspace = getProjectSpace(current_obj)
        terms = []
        budget_types = projectspace.budget_types
        for budget_type in budget_types:
            terms.append(SimpleTerm(budget_type['key'], budget_type['key'], budget_type['label'], ))
        return SimpleVocabulary(terms)


class YearVocabulary(object):
    implements(IVocabularyFactory)

    def __call__(self, context):
        """"""
        years = range(2009, 2030)
        terms = []
        for year in years:
            terms.append(SimpleTerm(year, year, year, ))
        return SimpleVocabulary(terms)


class ManagerVocabulary(object):
    """
        Create a vocabulary from the selected organization groups
    """
    implements(IVocabularyFactory)

    def __call__(self, context):
        return selectedOrganizationsPloneGroupsVocabulary(functions=['actioneditor'], group_title=False)


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
