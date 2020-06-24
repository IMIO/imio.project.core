# -*- coding: utf-8 -*-

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
        Remove and reorder fields
    """
    ordered = getattr(getProjectSpace(the_form.context), '{}_fields'.format(portal_type))
    # order kept fields
    for field_name in reversed(ordered):
        field = remove(the_form, field_name)
        if field is not None:
            add(the_form, field, index=0)
    # remove all other fields
    for group in [the_form] + the_form.groups:
        for field_name in group.fields:
            if field_name not in ordered:
                # we remove reference_number in view mode. It is needed in edit or add to manage it automatically.
                if field_name == 'reference_number' and mode != 'view':
                    continue
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
