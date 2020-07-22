# -*- coding: utf-8 -*-

from imio.migrator.migrator import Migrator
from imio.project.core.config import SUMMARIZED_FIELDS
from imio.project.core.content.project import IProject
from imio.project.core.content.projectspace import IProjectSpace
from imio.project.core.events import _updateSummarizedFields
from imio.project.core.utils import get_budget_states
from plone import api
from Products.CMFPlone.utils import base_hasattr
from zope.annotation import IAnnotations

import logging

logger = logging.getLogger('imio.project.core')


class Migrate_To_1_3(Migrator):

    def __init__(self, context):
        Migrator.__init__(self, context)

    def run(self):
        self.runProfileSteps('imio.project.core', steps=['plone.app.registry'],
                             run_dependencies=False)
        # moved categories ps attribute to renamed attribute
        catalog = api.portal.get_tool('portal_catalog')
        brains = catalog.searchResults(object_provides=IProjectSpace.__identifier__)
        for brain in brains:
            obj = brain.getObject()
            for old, new in (('categories', 'categories_values'), ('priority', 'priority_values')):
                if not base_hasattr(obj, old):
                    continue
                setattr(obj, new, list(getattr(obj, old) or []))
                delattr(obj, old)
                obj.reindexObject()

        # clean annotations and reindex to correct link
        brains = catalog.searchResults(object_provides=IProject.__identifier__, sort_on='path', sort_order='reverse')
        for brain in brains:
            obj = brain.getObject()
            obj_annotations = IAnnotations(obj)
            changed = False
            for fld, AK in SUMMARIZED_FIELDS.items():
                if AK in obj_annotations:
                    changed = True
                    del obj_annotations[AK]
            if changed:
                obj.reindexObject()

        brains = catalog.searchResults(object_provides=IProject.__identifier__, sort_on='path', sort_order='reverse')
        pw = api.portal.get_tool('portal_workflow')
        for brain in brains:
            obj = brain.getObject()
            if pw.getInfoFor(obj, 'review_state') in get_budget_states(obj):
                _updateSummarizedFields(obj)

        # Display duration
        self.finish()


def migrate(context):
    Migrate_To_1_3(context).run()
