# -*- coding: utf-8 -*-

from collective.z3cform.datagridfield import DictRow
from imio.project.core import _
from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import provider
from collective.z3cform.datagridfield.datagridfield import DataGridField
from imio.project.core.content.project import default_year


class IAnalyticBudgetSchema(Interface):
    """Schema used for the datagrid field 'analytic_budget' of IProject"""

    year = schema.Choice(
        title=_(u"Year"),
        description=_(u"Choose a year."),
        vocabulary=u"imio.project.core.content.project.year_vocabulary",
        required=True,
        defaultFactory=default_year,
    )
    economic_group = schema.TextLine(
        title=_(u"Economic Group"),
        description=_(u"Choose an economic group."),
        required=True,
    )
    amount = schema.Float(title=_("Amount"), required=True, default=0.0)
    comment = schema.TextLine(
        title=_(u"Comment"),
        description=_(u"Write a comment about this budget line."),
        required=False,
    )


@provider(IFormFieldProvider)
class IAnalyticBudget(model.Schema):
    """Budget field"""

    analytic_budget = schema.List(
        title=_(u"Analytic budget"),
        required=False,
        value_type=DictRow(
            title=_("Analytic budget"), schema=IAnalyticBudgetSchema, required=False
        ),
    )
    directives.widget(
        "analytic_budget",
        DataGridField,
        display_table_css_class="listing nosort",
    )


@implementer(IAnalyticBudget)
@adapter(IDexterityContent)
class AnalyticBudget(object):
    def __init__(self, context):
        self.context = context
