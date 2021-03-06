# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""

from zope.interface import Interface
from plone.theme.interfaces import IDefaultPloneLayer


class IImioProjectLayer(IDefaultPloneLayer):
    """Marker interface that defines a Zope 3 browser layer."""
