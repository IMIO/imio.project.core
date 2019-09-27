# -*- coding: utf-8 -*-

from zope import schema
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.z3cform import layout
from z3c.form import form
from zope.interface import Interface

from imio.project.core import _


class ISettings(Interface):
    """"""

    allow_the_encoding_of_the_analytical_budget = schema.Bool(
        title=_(u"Allow the encoding of the analytical budget ?"), required=True, default=True
    )


class SettingsEditForm(RegistryEditForm):
    """"""

    form.extends(RegistryEditForm)
    schema = ISettings
    label = _(u"PST settings")


SettingsView = layout.wrap_form(SettingsEditForm, ControlPanelFormWrapper)
