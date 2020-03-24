# -*- coding: utf-8 -*-

from imio.migrator.migrator import Migrator
from imio.project.core.content.project import IProject
from imio.project.core.content.projectspace import IProjectSpace
from plone import api
from Products.CMFPlone.utils import base_hasattr

import logging

logger = logging.getLogger('imio.project.core')


class Migrate_To_1_3(Migrator):

    def __init__(self, context):
        Migrator.__init__(self, context)

    def run(self):

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

        # reindex projects too
        brains = catalog.searchResults(object_provides=IProject.__identifier__)
        for brain in brains:
            brain.getObject().reindexObject()

        # Display duration
        self.finish()


def migrate(context):
    Migrate_To_1_3(context).run()
