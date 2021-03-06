# -*- coding: utf-8 -*-

from collective.z3cform.datagridfield import DictRow
from collective.z3cform.datagridfield.datagridfield import DataGridField
from imio.project.core import _
from imio.project.core.browser.widgets import AnalyticBudgetDataGridField
from imio.project.core.browser.widgets import ProjectionDataGridField
from imio.project.core.content.project import default_year
from plone.autoform import directives as form
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.interface import Interface
from zope.interface import implementer
from zope.interface import provider
from z3c.form import interfaces
from z3c.form.widget import FieldWidget


@implementer(interfaces.IFieldWidget)
def AnalyticBudgetDataGridFieldFactory(field, request):
    """IFieldWidget factory for DataGridField using the 'AnalyticBudgetDataGridField' widget."""
    widget = AnalyticBudgetDataGridField(request)
    return FieldWidget(field, widget)


@implementer(interfaces.IFieldWidget)
def ProjectionDataGridFieldFactory(field, request):
    """IFieldWidget factory for DataGridField using the 'ProjectionDataGridField' widget."""
    widget = ProjectionDataGridField(request)
    return FieldWidget(field, widget)


class IAnalyticBudgetSchema(Interface):
    """Schema used for the datagrid field 'analytic_budget' of IProject"""

    year = schema.Choice(
        title=_(u"Year"),
        # description=_(u"Choose a year."),
        vocabulary=u"imio.project.core.content.project.year_vocabulary",
        required=True,
        defaultFactory=default_year,
    )
    service = schema.TextLine(
        title=_(u"Budget Service"),
        required=True,
    )
    btype = schema.TextLine(
        title=_(u"Budget Type"),
        required=True,
    )
    article = schema.TextLine(
        title=_(u"Budget Article"),
        # description=_(u"Define the budget article."),
        required=True,
    )
    title = schema.TextLine(
        title=_(u"Budget Title"),
        # description=_(u"Define the budget article."),
        required=True,
    )
    amount = schema.Float(title=_("Amount"), required=True, default=0.0)
    # comment = schema.TextLine(
    #     title=_(u"Comment"),
    #     # description=_(u"Write a comment about this budget line."),
    #     required=False,
    # )


class IProjectionSchema(Interface):
    """Schema used for the datagrid field 'projection' of IProject"""

    service = schema.TextLine(
        title=_(u"Budget Service"),
        required=True,
    )
    btype = schema.TextLine(
        title=_(u"Budget Type"),
        required=True,
    )
    group = schema.TextLine(
        title=_(u"Budget Group"),
        # description=_(u"Define the budget article."),
        required=True,
    )
    title = schema.TextLine(
        title=_(u"Budget Title"),
        # description=_(u"Define the budget article."),
        required=True,
    )
    year = schema.Choice(
        title=_(u"Year"),
        # description=_(u"Choose a year."),
        vocabulary=u"imio.project.core.content.project.year_vocabulary",
        required=True,
        defaultFactory=default_year,
    )
    amount = schema.Float(title=_("Amount"), required=True, default=0.0)
    # article = schema.Choice(
    #     title=_(u"Budget Article"),
    #     # description=_(u"Define the budget article."),
    #     vocabulary=u"imio.project.core.PCCVocabulary",
    #     required=True,
    # )
    # comment = schema.TextLine(
    #     title=_(u"Comment"),
    #     # description=_(u"Write a comment about this budget line."),
    #     required=False,
    # )


@provider(IFormFieldProvider)
class IAnalyticBudget(model.Schema):
    """Budget field"""

    analytic_budget = schema.List(
        title=_(u"Analytic budget"),
        required=False,
        readonly=True,
        value_type=DictRow(
            title=_("Analytic budget"), schema=IAnalyticBudgetSchema, required=False
        ),
    )
    form.widget("analytic_budget", AnalyticBudgetDataGridFieldFactory, display_table_css_class="listing nosort")

    projection = schema.List(
        title=_(u"Projection"),
        required=False,
        readonly=True,
        value_type=DictRow(
            title=_("Projection"), schema=IProjectionSchema, required=False
        ),
    )
    form.widget("projection", ProjectionDataGridFieldFactory, display_table_css_class="listing nosort")

    form.order_before(projection='budget')
    form.order_before(analytic_budget='budget')


@implementer(IAnalyticBudget)
@adapter(IDexterityContent)
class AnalyticBudget(object):
    def __init__(self, context):
        self.context = context
