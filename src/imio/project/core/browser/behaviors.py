# -*- coding: utf-8 -*-

from collective.z3cform.datagridfield import DictRow
from imio.project.core import _
from imio.project.core.browser.widgets import BudgetInfosDataGridField
from imio.project.core.utils import getProjectSpace
from plone.app.textfield import RichText
from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.supermodel import model
from z3c.form import interfaces
from z3c.form.widget import FieldWidget
from zope import schema
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import provider
from zope.schema.interfaces import IContextAwareDefaultFactory

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


class IBudgetSchema(Interface):
    """Schema used for the datagrid field 'budget' of IProject."""

    budget_type = schema.Choice(
        title=_(u"Budget_type"),
        description=_(u"Choose a budget type."),
        vocabulary=u"imio.project.core.content.project.budget_type_vocabulary",
    )
    year = schema.Choice(
        title=_(u"Year"),
        description=_(u"Choose a year."),
        vocabulary=u"imio.project.core.content.project.year_vocabulary",
        defaultFactory=default_year,
    )
    amount = schema.Float(title=_("Amount"), required=True, default=0.0)


@provider(IFormFieldProvider)
class IBudget(model.Schema):
    """Budget field"""

    budget = schema.List(
        title=_(u"Budget"),
        description=_(
            u"Enter budget details.  If you have comments about budget, "
            "use the field here above."
        ),
        required=False,
        value_type=DictRow(title=_("Budget"), schema=IBudgetSchema, required=False),
    )
    directives.widget(
        "budget",
        BudgetInfosDataGridFieldFactory,
        display_table_css_class="listing nosort",
    )

    budget_comments = RichText(
        title=_(u"Budget comments"),
        description=_(u"Write here comments you have about budget."),
        required=False,
        default_mime_type="text/html",
        output_mime_type="text/html",
        allowed_mime_types=("text/html",),
    )


@implementer(IBudget)
@adapter(IDexterityContent)
class Budget(object):
    def __init__(self, context):
        self.context = context

    @property
    def budget(self):
        return set(self.context.Subject())

    @budget.setter
    def tags(self, value):
        if value is None:
            value = ()
        self.context.setSubject(tuple(value))


class IBudgetMarker(Interface):
    """"""
