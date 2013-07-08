# -*- coding: utf-8 -*-


def isNotCurrentProfile(context):
    return context.readDataFile("imioprojectcore_marker.txt") is None


def post_install(context):
    """Post install script"""
    if isNotCurrentProfile(context):
        return

    # add contacts
    _addContacts(context)


def _addContacts(context):
    """Add needed organizations"""
    if isNotCurrentProfile(context):
        return
    site = context.getSite()
    # add the 'contacts' directory if it does not already exists
    if not hasattr(site, 'contacts'):
        organization_types = [{'name': u'Commune', 'token': 'commune'}, ]

        organization_levels = [{'name': u'Echevinat', 'token': 'echevinat'},
                               {'name': u'Service', 'token': 'service'}, ]

        params = {'title': "Contacts",
                  'position_types': [],
                  'organization_types': organization_types,
                  'organization_levels': organization_levels,
                  }
        site.invokeFactory('directory', 'contacts', **params)
