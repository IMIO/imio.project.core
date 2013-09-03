# -*- coding: utf-8 -*-

from zope.annotation import IAnnotations
from zope.browserpage.viewpagetemplatefile import ViewPageTemplateFile

from collective.z3cform.datagridfield.datagridfield import DataGridField

from imio.project.core.config import CHILDREN_BUDGET_INFOS_ANNOTATION_KEY


class BudgetInfosDataGridField(DataGridField):
    """Custom DataGridField widget used to display budget infos data..."""

    def render(self):
        """
          We override renderer so we can call original DataGridField renderer without customizing the template and add
          our own rendered template under.
        """
        # render original template
        original_template = DataGridField.render(self)
        # render our own template we will display just under original one
        budgetinfos_template = u''
        if self.mode == 'display':
            budgetinfos_template = ViewPageTemplateFile('budgetinfos_datagridfield_display.pt')(self)
        return original_template + budgetinfos_template

    def prepareBudgetInfosForDisplay(self,
                                     only_used_years=False,
                                     only_used_budget_types=True,
                                     fixed_years=[2013, 2014, 2015, 2016, 2017, 2018]):
        """
          Compute budget infos so it can be easily displayed by 'budgetinfos_datagridfield_display.pt'
          We need totals by budget_type and year to display something like :
          [budget_type/years][Global][2010][2011][2012][2013][2014][2015][2016]
          [budget_type_1    ][      ][   0][    ][    ][    ][    ][    ][    ]
          [budget_type_2    ][      ][   0][    ][    ][    ][    ][    ][    ]
          [budget_type_3    ][      ][   0][    ][    ][    ][    ][    ][    ]
          [budget_type_4    ][      ][   0][    ][    ][    ][    ][    ][    ]
          [budget_type_5    ][      ][   0][    ][    ][    ][    ][    ][    ]
          [budget_type_6    ][      ][   0][    ][    ][    ][    ][    ][    ]
          [budget_type_7    ][      ][   1][    ][    ][    ][    ][    ][    ]
          [TOTAL            ][      ][   1][    ][    ][    ][    ][    ][    ]

          We will return 5 values :
          - list of years sorted (years)
          - list of budget_types sorted (budget_types)
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
          If p_only_used_years is False, we will use p_fixed_years value.
        """
        annotations = IAnnotations(self.context)
        if not CHILDREN_BUDGET_INFOS_ANNOTATION_KEY in annotations:
            return {}
        res = {}
        years = only_used_years and [] or fixed_years
        budget_types = []
        total_by_year = {}
        total_by_budget_type = {}
        for datagridfieldrecord in annotations[CHILDREN_BUDGET_INFOS_ANNOTATION_KEY].itervalues():
            for line in datagridfieldrecord:
                year = line['year']
                budget_type = line['budget_type']
                amount = line['amount']
                # manage used years
                if only_used_years and not year in years:
                    years.append(year)
                # manage used budget_types
                if only_used_budget_types and not budget_type in budget_types:
                    budget_types.append(budget_type)
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
        return years, budget_types, res, total_by_year, total_by_budget_type
