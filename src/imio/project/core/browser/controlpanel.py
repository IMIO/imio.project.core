# -*- coding: utf-8 -*-

from imio.project.core import _
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.z3cform import layout
from z3c.form import form
from zope import schema
from zope.interface import Interface


class IImioProjectSettings(Interface):
    """"""



class SettingsEditForm(RegistryEditForm):
    """"""

    form.extends(RegistryEditForm)
    schema = IImioProjectSettings
    schema_prefix = 'imio.project.settings'
    label = _(u"Project settings")


SettingsView = layout.wrap_form(SettingsEditForm, ControlPanelFormWrapper)
