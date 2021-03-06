# -*- coding: utf-8 -*-

# the annotation key where we store budget infos coming from children on a project
CHILDREN_ANALYTIC_BUDGETS_ANNOTATION_KEY = 'imio.project.core-analyticbudgets'
CHILDREN_BUDGET_INFOS_ANNOTATION_KEY = 'imio.project.core-budgetinfos'
CHILDREN_PROJECTIONS_ANNOTATION_KEY = 'imio.project.core-projections'

SUMMARIZED_FIELDS = {
    'budget': CHILDREN_BUDGET_INFOS_ANNOTATION_KEY,
    'analytic_budget': CHILDREN_ANALYTIC_BUDGETS_ANNOTATION_KEY,
    'projection': CHILDREN_PROJECTIONS_ANNOTATION_KEY,
}
