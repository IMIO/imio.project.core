from collective import dexteritytextindexer
from collective.contact.plonegroup.browser.settings import selectedOrganizationsVocabulary
from collective.z3cform.chosen.widget import AjaxChosenMultiFieldWidget
from collective.z3cform.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield import DictRow
from dexterity.localrolesfield.field import LocalRolesField
from imio.project.core import _
from imio.project.core.browser.widgets import BudgetInfosDataGridField
from imio.project.core.content.projectspace import IProjectSpace
from imio.project.core.utils import getProjectSpace
from imio.project.core.utils import getVocabularyTermsForOrganization
from plone.app.dexterity import PloneMessageFactory as _PMF
from plone.app.textfield import RichText
from plone.autoform import directives
from plone.dexterity.content import Container
from plone.dexterity.schema import DexteritySchemaPolicy
from plone.formwidget.datetime.z3cform.widget import DateFieldWidget
from plone.supermodel import model
from Products.CMFPlone.utils import base_hasattr
from z3c.form import interfaces
from z3c.form.browser.select import SelectFieldWidget
from z3c.form.widget import FieldWidget
from zope import schema
from zope.interface import implements
from zope.interface import Interface
from zope.interface import provider
from zope.schema.interfaces import IContextAwareDefaultFactory
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

import datetime
import zope.interface


@zope.interface.implementer(interfaces.IFieldWidget)
def BudgetInfosDataGridFieldFactory(field, request):
    """IFieldWidget factory for DataGridField using the 'BudgetInfosDataGridField' widget."""
    widget = BudgetInfosDataGridField(request)
    return FieldWidget(field, widget)


@provider(IContextAwareDefaultFactory)
def default_year(context):
    """
      defaultFactory for the field IBudgetSchema.year
    """
    years = getProjectSpace(None).budget_years or []
    year = datetime.date.today().year
    if year in years:
        return year
    elif year + 1 in years:
        return year + 1
    elif years:
        return years[-1]
    else:
        return None


@provider(IContextAwareDefaultFactory)
def default_categories(context):
    """
      defaultFactory for the field categories.
      It's called when categories is None or missing ?, in view or edit mode.
    """
    if IProjectSpace.providedBy(context):
        return []
    elif IProject.providedBy(context) and base_hasattr(context, 'categories') and context.categories:
        return context.categories
    return []


@provider(IContextAwareDefaultFactory)
def default_plan(context):
    """
      defaultFactory for the field plan.
    """
    if IProjectSpace.providedBy(context):
        return []
    elif IProject.providedBy(context) and base_hasattr(context, 'plan') and context.plan:
        return context.plan
    return []


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
    year = schema.Choice(
        title=_(u'Year'),
        # description=_(u"Choose a year."),
        vocabulary=u'imio.project.core.content.project.year_vocabulary',
        defaultFactory=default_year,
    )


class IBudgetSchema(Interface):
    """Schema used for the datagrid field 'budget' of IProject."""
    budget_type = schema.Choice(
        title=_(u'Budget_type'),
        # description=_(u"Choose a budget type."),
        vocabulary=u'imio.project.core.content.project.budget_type_vocabulary',
    )
    year = schema.Choice(
        title=_(u'Year'),
        # description=_(u"Choose a year."),
        vocabulary=u'imio.project.core.content.project.year_vocabulary',
        defaultFactory=default_year,
    )
    amount = schema.Float(
        title=_("Amount"),
        required=True,
        default=0.0,)


class IProject(model.Schema):
    """Project schema, field ordering."""

    dexteritytextindexer.searchable('description_rich')
    description_rich = RichText(
        title=_PMF(u'label_description', default=u'Summary'),
        required=False,
        default_mime_type='text/html',
        output_mime_type='text/x-html-safe',
    )

    dexteritytextindexer.searchable('reference_number')
    reference_number = schema.Int(
        title=_(u"Reference number"),
        # description=_(u"Unique identification"),
        required=False,
        default=0,
    )

    categories = schema.List(
        title=_(u'Categories'),
        # description=_(u"Choose categories."),
        required=False,
        value_type=schema.Choice(source='imio.project.core.content.project.categories_vocabulary'),
        defaultFactory=default_categories,
    )
    directives.widget('categories', AjaxChosenMultiFieldWidget, populate_select=True)

    priority = schema.Choice(
        title=_(u'Priority'),
        # description=_(u"Choose a priority."),
        vocabulary=u'imio.project.core.content.project.priority_vocabulary',
    )

    budget = schema.List(
        title=_(u'Budget'),
        # description=_(u"Enter budget details.  If you have comments about budget, "
        #               "use the field here above."),
        required=False,
        value_type=DictRow(title=_("Budget"),
                           schema=IBudgetSchema,
                           required=False),
    )
    directives.widget('budget', BudgetInfosDataGridFieldFactory, display_table_css_class='listing nosort')

    budget_comments = RichText(
        title=_(u"Budget comments"),
        # description=_(u"Write here comments you have about budget."),
        required=False,
        default_mime_type='text/html',
        output_mime_type='text/html',
        allowed_mime_types=('text/html',),
    )

    manager = LocalRolesField(
        title=_(u"Manager"),
        # description=_(u"Choose principals that will manage this project."),
        value_type=schema.Choice(
            vocabulary='imio.project.core.content.project.manager_vocabulary'
        ),
        required=True,
        min_length=1,
    )
    directives.widget('manager', AjaxChosenMultiFieldWidget, populate_select=True)

    visible_for = LocalRolesField(
        title=_(u"Visible for"),
        # description=_(u"Choose principals that can see this project."),
        required=False,
        value_type=schema.Choice(
            vocabulary='imio.project.core.content.project.visible_for_vocabulary'
        ),
    )

    extra_concerned_people = schema.Text(
        title=_(u"Extra concerned people"),
        # description=_(u"Specify here concerned people that do not have access "
        #               "to the application, this will just be informational."),
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
        # description=_(u"Enter the planned begin date."),
        required=False,
#        defaultFactory=datetime.date.today,
    )
    directives.widget(planned_begin_date=DateFieldWidget)

    effective_begin_date = schema.Date(
        title=_(u'Effective begin date'),
        # description=_(u"Enter the effective begin date."),
        required=False,
#        defaultFactory=datetime.date.today,
    )
    directives.widget(effective_begin_date=DateFieldWidget)

    planned_end_date = schema.Date(
        title=_(u'Planned end date'),
        # description=_(u"Enter the planned end date."),
        required=False,
#        defaultFactory=datetime.date.today,
    )
    directives.widget(planned_end_date=DateFieldWidget)

    effective_end_date = schema.Date(
        title=_(u'Effective end date'),
        # description=_(u"Enter the effective end date."),
        required=False,
#        defaultFactory=datetime.date.today,
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
        # description=_(u"Prior determination"),
        required=False,
        default_mime_type='text/html',
        output_mime_type='text/html',
        allowed_mime_types=('text/html',),
    )

    comments = RichText(
        title=_(u"Comments"),
        # description=_(u"Various comments"),
        required=False,
        default_mime_type='text/html',
        output_mime_type='text/html',
        allowed_mime_types=('text/html',),
    )

    plan = schema.List(
        title=_(u'Plan'),
        # description=_(u"Choose plan."),
        required=False,
        value_type=schema.Choice(source='imio.project.core.content.project.plan_vocabulary'),
        defaultFactory=default_plan,
    )
    directives.widget('plan', AjaxChosenMultiFieldWidget, populate_select=True)


class Project(Container):
    """ """
    implements(IProject)
    __ac_local_roles_block__ = False

    def Title(self):
        if getattr(getProjectSpace(self), 'use_ref_number', True):
            return '%s (REF.%s)' % (self.title.encode('utf8'), self.reference_number)
        else:
            return self.title.encode('utf8')


class CategoriesVocabulary(object):
    implements(IVocabularyFactory)

    def __call__(self, context):
        """"""
        projectspace = getProjectSpace(context)
        terms = []
        for category in projectspace.categories_values:
            terms.append(SimpleTerm(category['key'], category['key'], category['label'], ))
        return SimpleVocabulary(terms)


class PriorityVocabulary(object):
    implements(IVocabularyFactory)

    def __call__(self, context):
        """"""
        projectspace = getProjectSpace(context)
        terms = []
        for priority in projectspace.priority_values:
            terms.append(SimpleTerm(priority['key'], priority['key'], priority['label'], ))
        return SimpleVocabulary(terms)


class BudgetTypeVocabulary(object):
    implements(IVocabularyFactory)

    def __call__(self, context):
        """"""
        projectspace = getProjectSpace(None)
        terms = []
        budget_types = projectspace.budget_types
        for budget_type in budget_types:
            terms.append(SimpleTerm(budget_type['key'], budget_type['key'], budget_type['label'], ))
        return SimpleVocabulary(terms)


class YearVocabulary(object):
    implements(IVocabularyFactory)

    def __call__(self, context):
        """"""
        years = getProjectSpace(None).budget_years or []
        return SimpleVocabulary([SimpleTerm(y) for y in years])


class ManagerVocabulary(object):
    """
        Create a vocabulary from the selected organization groups
    """
    implements(IVocabularyFactory)

    def __call__(self, context):
        return selectedOrganizationsVocabulary()


class VisibleForVocabulary(object):
    """
    """
    implements(IVocabularyFactory)

    def __call__(self, context):
        """"""
        return getVocabularyTermsForOrganization(context, states='active')


class PlanVocabulary(object):
    implements(IVocabularyFactory)

    def __call__(self, context):
        """"""
        projectspace = getProjectSpace(context)
        terms = []
        for plan in projectspace.plan_values:
            terms.append(SimpleTerm(plan['key'], plan['key'], plan['label'], ))
        return SimpleVocabulary(terms)


class ProjectSchemaPolicy(DexteritySchemaPolicy):
    """ """

    def bases(self, schemaName, tree):
        return (IProject, )
