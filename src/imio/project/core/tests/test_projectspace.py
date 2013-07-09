# -*- coding: utf-8 -*-
"""Test the ProjectSpace content."""

from zope.interface import Invalid
from zope.i18n import translate

from imio.project.core.testing import FunctionalTestCase
from imio.project.core.content.projectspace import IProjectSpace
from imio.project.core.content.projectspace import RemovedValueIsNotUsedByCategoriesFieldValidator
from imio.project.core.content.projectspace import RemovedValueIsNotUsedByPriorityFieldValidator


class TestProjectSpace(FunctionalTestCase):
    """Test the PorjectSpace content."""

    def test_RemovedValueIsNotUsedByCategoriesFieldValidator(self):
        """Test the RemovedValueIsNotUsedByCategoriesFieldValidator validator that
           validates that removed keys in the ProjectSpace.categories attribute actually managing
           a vocabulary are not used by already created elements and can be removed safely."""
        stored_value = list(self.portal.projectspace.categories)
        categories_validator = RemovedValueIsNotUsedByCategoriesFieldValidator(self.portal.projectspace,
                                                                               None,
                                                                               None,
                                                                               IProjectSpace['categories'],
                                                                               None)
        self._checkValidateKeyNotUsed(stored_value, categories_validator, 'categories', 'Category')

    def test_RemovedValueIsNotUsedByPriorityFieldValidator(self):
        """Test the RemovedValueIsNotUsedByPriorityFieldValidator validator that
           validates that removed keys in the ProjectSpace.priority attribute actually managing
           a vocabulary are not used by already created elements and can be removed safely."""
        # check the priority validator
        stored_value = list(self.portal.projectspace.priority)
        priority_validator = RemovedValueIsNotUsedByPriorityFieldValidator(self.portal.projectspace,
                                                                           None,
                                                                           None,
                                                                           IProjectSpace['priority'],
                                                                           None)
        self._checkValidateKeyNotUsed(stored_value, priority_validator, 'priority', 'Priority')

    def _checkValidateKeyNotUsed(self, stored_value, validator, fieldName, fieldValue):
        """
          Helper method for testing the RemovedValueIsNotUsedByXXXFieldValidator
        """
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
        self.assertEquals(getattr(project1, fieldName), '%s-1' % fieldValue.lower())
        # remove the first element of new-value that is actually used
        new_value_without_first = list(new_value)
        # the first element that we will pop is the one we expect
        self.assertEquals(new_value_without_first[0], {'label': u"%s 1" % fieldValue, 'key': '%s-1' % fieldValue.lower()})
        new_value_without_first.pop(0)
        with self.assertRaises(Invalid) as raised:
            validator.validate(new_value_without_first)
        self.assertEquals(translate(raised.exception.message),
                          u"The key '%s-1' that was removed is used by some elements "
                          u"(like for example 'http://nohost/plone/projectspace/project-1') "
                          u"and can not be removed!" % fieldValue.lower())

        # now remove project1 using the value, the new_value_without_first will validate correctly then
        self.portal.projectspace.manage_delObjects(ids=['project-1', ])
        validator.validate(new_value_without_first)

        # a value that is not used at all can be removed, like last added one 'new-value'
        new_value_without_newvalue = list(new_value)
        self.assertEquals(new_value_without_newvalue[-1], {'label': u"New value", 'key': 'new-value'})
        new_value_without_newvalue.pop(-1)
        validator.validate(new_value_without_newvalue)
