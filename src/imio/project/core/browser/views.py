# -*- coding: utf-8 -*-
from zope.component import getMultiAdapter
from Products.Five import BrowserView

from imio.project.pst.interfaces import IListContainedDexterityObjectsForDisplay


class ContainerFolderListingView(BrowserView):
    """
      This manage the elements listed on the view of a dexterity container
    """
    def __init__(self, context, request):
        self.context = context
        self.request = request
        portal_state = getMultiAdapter((self.context, self.request), name=u'plone_portal_state')
        self.portal = portal_state.portal()

    def listRenderedContainedElements(self, portal_types=[]):
        """
          Get the contained elements, rendered for display
          If p_portal_types is specified, only return elements having the required portal_type
        """
        return IListContainedDexterityObjectsForDisplay(self.context).listContainedObjects(portal_types)

