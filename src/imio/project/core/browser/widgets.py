# -*- coding: utf-8 -*-
from collections import namedtuple

from collective.z3cform.datagridfield.datagridfield import DataGridField
from imio.project.core.config import CHILDREN_ANALYTIC_BUDGETS_ANNOTATION_KEY
from imio.project.core.config import CHILDREN_BUDGET_INFOS_ANNOTATION_KEY
from imio.project.core.config import CHILDREN_PROJECTIONS_ANNOTATION_KEY
from imio.project.core.utils import getProjectSpace
from Products.CMFPlone.utils import base_hasattr
from zope.annotation import IAnnotations
from zope.browserpage.viewpagetemplatefile import ViewPageTemplateFile
from zope.component import queryUtility
from zope.schema.interfaces import IVocabularyFactory


class BudgetInfosDataGridField(DataGridField):
    """Custom DataGridField widget used to display budget infos data..."""

    def render(self):
        """
          We override renderer so we can call original DataGridField renderer without customizing the template and add
          our own rendered template under.
        """
        template = u''
        # render original template
        if self.mode != 'display' or (base_hasattr(self.context, 'budget') and self.context.budget):
            template = DataGridField.render(self)
        # render our own template we will display just under original one
        if self.mode == 'display':
            # we will display the originally rendered template in our template, so set it on self
            self.original_template = template
            template = ViewPageTemplateFile('budgetinfos_datagridfield_display.pt')(self)
        return template

    def prepareBudgetInfosForDisplay(self,
                                     only_used_years=False,
                                     only_used_budget_types=False):
        """
          Compute budget infos so it can be easily displayed by 'budgetinfos_datagridfield_display.pt'
          We need totals by budget_type and year to display something like :
          [budget_type/years][Global][2010][2011][2012][2013][2014][2015][2016]
          [budget_type_1    ][     5][   0][   0][   5][   -][   -][   -][   -]
          [budget_type_2    ][     5][   0][   0][   5][   -][   -][   -][   -]
          [budget_type_3    ][     5][   0][   0][   5][   -][   -][   -][   -]
          [budget_type_4    ][     5][   0][   0][   5][   -][   -][   -][   -]
          [budget_type_5    ][     5][   0][   0][   5][   -][   -][   -][   -]
          [budget_type_6    ][     7][   0][   2][   5][   -][   -][   -][   -]
          [budget_type_7    ][     8][   1][   2][   5][   -][   -][   -][   -]
          [TOTAL            ][    40][   1][   4][  35][   -][   -][   -][   -]

          We will return 5 values :
          - list of years sorted (years)
          - budget_types sorted (budget_types) : {'budget_type_id1': 'Budget type 1 title',
                                                  'budget_type_id2': 'Budget type 2 title',}
          - total_by_year : {2010: 125,
                             2011: 258,}
          -total_by_budget_type : {'budget_type1': 258,
                                   'budget_type1': 885,}
          - a dict that will appear like this :
          {2010: {'budget_type1': 125,
                  'budget_type2': 250,
                  'total': 375},
           2011: {'budget_type1': 50,
                  'budget_type2': 1222,
                  'total': 1272},
           'total_years': 1647
          }

          If p_only_used_years is True, we will return only years that were
          used not a fixed list of years, same if p_only_used_budget_types is True,
          we will only return used budget_types, not every existing one.
        """
        annotations = IAnnotations(self.context)
        if not CHILDREN_BUDGET_INFOS_ANNOTATION_KEY in annotations:
            return {}
        # get budget_types vocabulary so we can have a value to display as saved data is the key
        factory = queryUtility(IVocabularyFactory, u'imio.project.core.content.project.budget_type_vocabulary')
        budgetTypesVocab = factory(self.context)
        fixed_years = [str(y) for y in getProjectSpace(self.context).budget_years or []]
        res = {}
        years = only_used_years and [] or fixed_years
        budget_types = only_used_budget_types and {} or budgetTypesVocab.by_value
        total_by_year = {}
        total_by_budget_type = {}
        for datagridfieldrecord in annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY].itervalues():
            for line in datagridfieldrecord:
                year = str(line['year'])
                budget_type = line['budget_type']
                amount = line['amount']
                # manage used years
                if only_used_years and not year in years:
                    years.append(year)
                # manage used budget_types
                if only_used_budget_types and not budget_type in budget_types:
                    budget_types[budget_type] = budgetTypesVocab.getTerm(budget_type)
                # manage total by year/budget_type
                if not year in res:
                    res[year] = {}
                if not budget_type in res[year]:
                    res[year][budget_type] = 0
                res[year][budget_type] = res[year][budget_type] + amount
                # manage total by year
                if not year in total_by_year:
                    total_by_year[year] = 0
                total_by_year[year] = total_by_year[year] + amount
                # manage total by budget_type
                if not budget_type in total_by_budget_type:
                    total_by_budget_type[budget_type] = 0
                total_by_budget_type[budget_type] = total_by_budget_type[budget_type] + amount
        # make sure with have a result for every year if we use fixed_years
        for year in years:
            if not year in res:
                res[year] = {}
                for budget_type in budget_types:
                    res[year][budget_type] = '-'
        # make sure we have each budget_type for each year
        for line in res.itervalues():
            for budget_type in budget_types:
                if not budget_type in line:
                    line[budget_type] = '-'
        # make sure we have each total for each budget_type in total_by_budget_type
        for budget_type in budget_types:
            if not budget_type in total_by_budget_type:
                total_by_budget_type[budget_type] = '-'
        # compute super total, meaning total of total_by_years
        # (that is the same than total of total_by_budget_types)
        super_total = 0
        for total in total_by_year.values():
            super_total = super_total + total

        return years, budget_types, res, total_by_year, total_by_budget_type, super_total


class AnalyticBudgetDataGridField(DataGridField):
    """Custom DataGridField widget used to display analytic budget infos"""

    def render(self):
        """
          We override renderer so we can call original DataGridField renderer without customizing the template and add
          our own rendered template under.
        """
        template = u''
        # render original template
        if self.mode != 'display' or (base_hasattr(self.context, 'analytic_budget') and self.context.analytic_budget):
            template = DataGridField.render(self)
        # render our own template we will display just under original one
        if self.mode == 'display':
            # we will display the originally rendered template in our template, so set it on self
            self.original_template = template
            template = ViewPageTemplateFile('analytic_budget_datagridfield_display.pt')(self)
        return template

    def prepareAnalyticBudgetForDisplay(self):
        annotations = IAnnotations(self.context)
        if CHILDREN_ANALYTIC_BUDGETS_ANNOTATION_KEY not in annotations:
            return {}

        res = {}
# no need to have all years. Articles are defined only for the current year.
#        fixed_years = [str(y) for y in getProjectSpace(self.context).budget_years or []]
#        for year in fixed_years:
#            res.setdefault(year, {'revenues': 0.0, 'expenses': 0.0})

        for datagridfieldrecord in annotations[CHILDREN_ANALYTIC_BUDGETS_ANNOTATION_KEY].itervalues():
            for line in datagridfieldrecord:
                year = str(line['year'])
                budget_type = line['btype'].lower()
                amount = line['amount']
                res_year = res.setdefault(year, {'revenues': 0.0, 'expenses': 0.0})
                if 'r' in budget_type:
                    res_year['revenues'] += amount
                elif 'd' in budget_type:
                    res_year['expenses'] += amount

        for amounts in res.values():
            margin = amounts['revenues'] - amounts['expenses']
            amounts['total'] = '{:+.1f}'.format(margin) if margin else '-'
            for key in ('revenues', 'expenses'):
                if not amounts[key]:
                    amounts[key] = '-'

        return res


class ProjectionDataGridField(DataGridField):
    """Custom DataGridField widget used to display projections"""

    def render(self):
        """
          We override renderer so we can call original DataGridField renderer without customizing the template and add
          our own rendered template under.
        """

        # render our own template
        if self.mode == 'display':
            template = ViewPageTemplateFile('projection_datagridfield_display.pt')(self)
        else:
            # render original template
            template = DataGridField.render(self)
        return template

    @property
    def budget_years(self):
        return [str(y) for y in getProjectSpace(self.context).budget_years or []]

    def prepareProjectionForSingleDisplay(self):
        if not base_hasattr(self.context, 'projection') or not self.context.projection:
            return {}

        ProjectionLine = namedtuple('ProjectionLine', ['service', 'btype', 'group', 'title'])
        fixed_years = self.budget_years
        res = {}
        for line in self.context.projection:
            service = line['service']
            btype = line['btype']
            group = line['group']
            title = line['title']
            year = str(line['year'])
            amount = line['amount']

            projection_line = ProjectionLine(service, btype, group, title)
            amounts = res.setdefault(projection_line, {y: 0.0 for y in fixed_years})
            amounts[year] = amount

        return res

    def prepareProjectionForMultipleDisplay(self):
        annotations = IAnnotations(self.context)
        if CHILDREN_PROJECTIONS_ANNOTATION_KEY not in annotations:
            return {}

        # fixed_years = self.budget_years
        res = {}
        # for year in fixed_years:
        #     res.setdefault(year, {'revenues': 0.0, 'expenses': 0.0})

        for datagridfieldrecord in annotations[CHILDREN_PROJECTIONS_ANNOTATION_KEY].itervalues():
            for line in datagridfieldrecord:
                year = str(line['year'])
                budget_type = line['btype'].lower()
                amount = line['amount']
                res_year = res.setdefault(year, {'revenues': 0.0, 'expenses': 0.0})
                if 'r' in budget_type:
                    res_year['revenues'] += amount
                elif 'd' in budget_type:
                    res_year['expenses'] += amount

        for amounts in res.values():
            margin = amounts['revenues'] - amounts['expenses']
            amounts['total'] = '{:+.1f}'.format(margin) if margin else '0.0'

        return res
