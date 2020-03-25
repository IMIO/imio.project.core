# -*- coding: utf-8 -*-
"""Test the ProjectSpace content."""

from zope.interface import Invalid
from zope.i18n import translate

from Products.CMFCore.utils import getToolByName

from imio.project.core.testing import FunctionalTestCase
from imio.project.core.content.projectspace import IProjectSpace
from imio.project.core.content.projectspace import RemovedValueIsNotUsedByCategoriesFieldValidator
from imio.project.core.content.projectspace import RemovedValueIsNotUsedByPriorityFieldValidator
from imio.project.core.content.projectspace import RemovedValueIsNotUsedByBudgetTypesFieldValidator
from imio.project.core.content.projectspace import ERROR_VALUE_REMOVED_IS_IN_USE


class TestProjectSpace(FunctionalTestCase):
    """Test the PorjectSpace content."""

    def test_RemovedValueIsNotUsedByCategoriesFieldValidator(self):
        """Test the RemovedValueIsNotUsedByCategoriesFieldValidator validator that
           validates that removed keys in the ProjectSpace.categories attribute actually managing
           a vocabulary are not used by already created elements and can be removed safely."""
        stored_value = list(self.portal.projectspace.categories_values)
        categories_validator = RemovedValueIsNotUsedByCategoriesFieldValidator(self.portal.projectspace,
                                                                               None,
                                                                               None,
                                                                               IProjectSpace['categories_values'],
                                                                               None)
        self._checkValidateKeyNotUsed(stored_value, categories_validator, 'categories', 'Category', None)

    def test_RemovedValueIsNotUsedByPriorityFieldValidator(self):
        """Test the RemovedValueIsNotUsedByPriorityFieldValidator validator that
           validates that removed keys in the ProjectSpace.priority attribute actually managing
           a vocabulary are not used by already created elements and can be removed safely."""
        # check the priority validator
        stored_value = list(self.portal.projectspace.priority_values)
        priority_validator = RemovedValueIsNotUsedByPriorityFieldValidator(self.portal.projectspace,
                                                                           None,
                                                                           None,
                                                                           IProjectSpace['priority_values'],
                                                                           None)
        self._checkValidateKeyNotUsed(stored_value, priority_validator, 'priority', 'Priority', None)

    def test_RemovedValueIsNotUsedByBudgetTypesFieldValidator(self):
        """Test the RemovedValueIsNotUsedByBudgetTypesFieldValidator validator that
           validates that removed keys in the ProjectSpace.budget_types attribute actually managing
           a vocabulary are not used by already created elements and can be removed safely."""
        # check the budget_types validator
        stored_value = list(self.portal.projectspace.budget_types)
        budget_types_validator = RemovedValueIsNotUsedByBudgetTypesFieldValidator(self.portal.projectspace,
                                                                                  None,
                                                                                  None,
                                                                                  IProjectSpace['budget_types'],
                                                                                  None)
        self._checkValidateKeyNotUsed(stored_value, budget_types_validator, 'budget', 'Budget type', 'budget_type')

    def _checkValidateKeyNotUsed(self, stored_value, validator, fieldName, fieldValue, sub_attribute_using_key):
        """
          Helper method for testing the RemovedValueIsNotUsedByXXXFieldValidator
        """
        plone_utils = getToolByName(self.portal, 'plone_utils')
        # just calling it with no changes
        validator.validate(stored_value)

        # now add a value
        new_value = list(stored_value)
        new_value.append({'label': u"New value", 'key': 'new-value'})
        # still behaving right
        validator.validate(new_value)

        # now remove a used value
        # remove value used by 'project-1'
        project1 = self.portal.projectspace['project-1']
        field_key = "%s-1" % plone_utils.normalizeString(fieldValue)
        project1_field_value = getattr(project1, fieldName)
        # now take into account the fact that we check a datagridfield or a simple value
        # either we take the saved value, either we get the value in the relevant column of a datagridfield...
        value_to_compare = sub_attribute_using_key and \
            project1_field_value[0][sub_attribute_using_key] or \
            project1_field_value
        self.assertEquals(value_to_compare, field_key)
        # remove the first element of new-value that is actually used
        new_value_without_first = list(new_value)
        # the first element that we will pop is the one we expect
        self.assertEquals(new_value_without_first[0], {'label': u"%s 1" % fieldValue, 'key': field_key})
        new_value_without_first.pop(0)
        with self.assertRaises(Invalid) as raised:
            validator.validate(new_value_without_first)
        self.assertEquals(translate(raised.exception.message),
                          translate(ERROR_VALUE_REMOVED_IS_IN_USE,
                                    mapping={'removed_key': field_key,
                                             'used_by_url': 'http://nohost/plone/projectspace/project-1', }))

        # now remove project1 using the value, the new_value_without_first will validate correctly then
        self.portal.projectspace.manage_delObjects(ids=['project-1', ])
        validator.validate(new_value_without_first)

        # a value that is not used at all can be removed, like last added one 'new-value'
        new_value_without_newvalue = list(new_value)
        self.assertEquals(new_value_without_newvalue[-1], {'label': u"New value", 'key': 'new-value'})
        new_value_without_newvalue.pop(-1)
        validator.validate(new_value_without_newvalue)
