# -*- coding: utf-8 -*-
"""Init and utils."""

from imio.helpers.content import get_vocab as _voc
from plone import api
from zope.component import queryUtility
from zope.i18n.interfaces import ITranslationDomain
from zope.i18nmessageid import MessageFactory


_ = MessageFactory('imio.project.core')


def initialize(context):
    """Initializer called when used as a Zope 2 product."""


def _tr(msgid, domain='imio.project.core', mapping={}):
    translation_domain = queryUtility(ITranslationDomain, domain)
    sp = api.portal.get().portal_properties.site_properties
    return translation_domain.translate(msgid, target_language=sp.getProperty('default_language', 'fr'),
                                        mapping=mapping)
