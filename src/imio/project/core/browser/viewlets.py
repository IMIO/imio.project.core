# -*- coding: utf-8 -*-
"""Custom viewlets."""

from plone.app.layout.viewlets import common as base

from plone import api


class AnnexesListViewlet(base.ViewletBase):
    """
    """

    def listAnnexes(self):
        portal_catalog = api.portal.get_tool('portal_catalog')
        folder_path = '/'.join(self.context.getPhysicalPath())
        annexes = portal_catalog(
                portal_type = "File",
                path={
                    'query': folder_path,
                    'depth': 1
                }
        )
        annexes_tuple = []
        for annexe in annexes:
            annexes_tuple.append((annexe.Title, annexe.getURL()))
        return annexes_tuple
