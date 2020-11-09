# -*- coding: utf-8 -*-

from collective.behavior.talcondition.utils import _evaluateExpression
from imio.helpers.browser.views import ContainerView
from imio.project.core.utils import getProjectSpace
from plone import api
from plone.dexterity.browser.add import DefaultAddForm
from plone.dexterity.browser.add import DefaultAddView
from plone.dexterity.browser.edit import DefaultEditForm
from plone.z3cform.fieldsets.utils import add
from plone.z3cform.fieldsets.utils import remove


class PSContainerView(ContainerView):
    """ """

    collapse_all_fields = True
    collapse_all_fields_onload = True


def manage_fields(the_form, portal_type, mode):
    """
        Remove, reorder and restrict fields
    """

    fields_schemas = getattr(getProjectSpace(the_form.context), '{}_fields'.format(portal_type), [])
    if not fields_schemas:
        return
    to_input = []
    to_display = []

    for fields_schema in reversed(fields_schemas):
        field_name = fields_schema['field_name']
        read_condition = fields_schema.get('read_tal_condition') or ""
        write_condition = fields_schema.get('write_tal_condition') or ""
        if _evaluateExpression(the_form.context, expression=read_condition):
            to_display.append(field_name)
        if _evaluateExpression(the_form.context, expression=write_condition):
            to_input.append(field_name)

        field = remove(the_form, field_name)
        if field is not None and field_name in to_display:
            add(the_form, field, index=0)
            if mode != 'view' and field_name not in to_input:
                field.mode = "display"

    for group in [the_form] + the_form.groups:
        for field_name in group.fields:
            if field_name == 'reference_number' and mode != 'view':
                continue
            if field_name not in to_display:
                group.fields = group.fields.omit(field_name)


class ProjectContainerView(ContainerView):
    """ View form redefinition to customize fields. """

    def updateFieldsFromSchemata(self):
        super(ProjectContainerView, self).updateFieldsFromSchemata()
        manage_fields(self, self.context.portal_type, 'view')


class ProjectContainerEdit(DefaultEditForm):
    """
        Edit form redefinition to customize fields.
    """

    def updateFields(self):
        super(ProjectContainerEdit, self).updateFields()
        manage_fields(self, self.context.portal_type, 'edit')


class ProjectAddForm(DefaultAddForm):

    portal_type = 'project'

    def updateFields(self):
        super(ProjectAddForm, self).updateFields()
        manage_fields(self, self.portal_type, 'add')


class ProjectContainerAdd(DefaultAddView):

    form = ProjectAddForm
