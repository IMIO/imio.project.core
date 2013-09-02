# -*- coding: utf-8 -*-


class ListContainedDexterityObjectsForDisplayAdapter(object):
    """ Return the dexterity objects contained, moreover the returned
        elements are renderable for display.
        element.context is the contained object
        element.widgets are the renderable widgets of the object
    """

    def __init__(self, context):
        self.context = context

    def listContainedObjects(self, portal_types=[]):
        """ Return a list of renderable objects. """

        res = []
        params = {}
        params['path'] = {'query': '/'.join(self.context.getPhysicalPath()),
                          'depth': 1}
        params['sort_on'] = 'getObjPositionInParent'
        # make sure we only list dexterity objects
        params['object_provides'] = 'plone.dexterity.interfaces.IDexterityContent'

        if portal_types:
            params['portal_type'] = portal_types

        for brain in self.context.portal_catalog(**params):
            obj = brain.getObject()
            renderedAction = obj.restrictedTraverse('@@view')
            renderedAction.update()
            res.append(renderedAction)
        return res
