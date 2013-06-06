import datetime

from zope import schema
from zope.interface import implements
from zope.interface import Interface
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary

from plone.app.z3cform.wysiwyg import WysiwygFieldWidget
from plone.autoform import directives
from plone.dexterity.content import Container
from plone.dexterity.schema import DexteritySchemaPolicy
from plone.formwidget.datetime.z3cform.widget import DateFieldWidget
from plone.supermodel import model

from collective.z3cform.datagridfield import DataGridFieldFactory, DictRow
from collective.z3cform.rolefield.field import LocalRolesToPrincipals

from imio.project import _


class IResultIndicatorSchema(Interface):
    """Schema used for the datagrid field 'result_indicator' of IProject."""
    label = schema.TextLine(
        title=_("Label"),
        required=True,)
    value = schema.Int(
        title=_("Value"),
        required=True,)


class IProject(model.Schema):
    """
        Project schema, field ordering
    """

    category = schema.List(
        title=_(u'Category'),
        description=_(u"Choose a category."),
        required=False,
        value_type=schema.Choice(
            vocabulary=u'imio.project.content.project.category_vocabulary',
        ),
    )

    priority = schema.Choice(
        title=_(u'Priority'),
        description=_(u"Choose a priority."),
        vocabulary=u'imio.project.content.project.priority_vocabulary',
    )

    budget = schema.Text(
        title=_(u"Budget"),
        description=_("Budget details"),
        required=False,
    )

    responsible = LocalRolesToPrincipals(
        title=_(u"Responsible"),
        roles_to_assign=('Editor',),
        value_type=schema.Choice(
            vocabulary="plone.principalsource.Principals"
        ),
        min_length=1,
        max_length=1,
        required=True,
    )

    visible_for = LocalRolesToPrincipals(
        title=_(u"Visible for"),
        description=_(u"Choose principals that can see this project."),
        required=False,
        roles_to_assign=('Reader',),
        value_type=schema.Choice(
            vocabulary=u'plone.principalsource.Principals'
        ),
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
    directives.widget(result_indicator=DataGridFieldFactory)

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
    )

    comments = schema.Text(
        title=_(u"Comments"),
        description=_(u"Various comments"),
        required=False,
    )
    directives.widget(comments=WysiwygFieldWidget)


class Project(Container):
    """ """
    implements(IProject)
    __ac_local_roles_block__ = False


class CategoryVocabulary(object):
    implements(IVocabularyFactory)

    def __call__(self, context):
        """"""
        terms = []
        terms.append(SimpleTerm(u'Category 1', u'cat1', u'Category 1'))
        return SimpleVocabulary(terms)
category_vocabulary_factory = CategoryVocabulary()


class PriorityVocabulary(object):
    implements(IVocabularyFactory)

    def __call__(self, context):
        """"""
        terms = []
        terms.append(SimpleTerm(u'Low', u'low', u'Low'))
        terms.append(SimpleTerm(u'Normal', u'normal', u'Normal'))
        terms.append(SimpleTerm(u'High', u'high', u'High'))
        return SimpleVocabulary(terms)
priority_vocabulary_factory = PriorityVocabulary()


class ProjectSchemaPolicy(DexteritySchemaPolicy):
    """ """

    def bases(self, schemaName, tree):
        return (IProject, )
