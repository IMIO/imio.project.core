# encoding: utf-8

from imio.project.core.content.project import IProject
from plone.indexer import indexer
from Products.PluginIndexes.common.UnIndex import _marker as common_marker


@indexer(IProject)
def description_index(obj):
    # Index rendered description
    if obj.description_rich:
        transformed_value = obj.portal_transforms.convertTo('text/plain', obj.description_rich.output,
                                                            mimetype='text/html')
        return transformed_value.getData()
    return common_marker
