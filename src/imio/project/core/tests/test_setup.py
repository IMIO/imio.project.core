# -*- coding: utf-8 -*-
"""Setup/installation tests for this package."""

from imio.project.core.testing import IntegrationTestCase


class TestInstall(IntegrationTestCase):
    """Test installation of imio.project.core into Plone."""

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = self.portal.portal_quickinstaller

    def test_product_installed(self):
        """Test if imio.project.core is installed with portal_quickinstaller."""
        self.assertTrue(self.installer.isProductInstalled('imio.project.core'))

    def test_uninstall(self):
        """Test if imio.project.core is cleanly uninstalled."""
        self.installer.uninstallProducts(['imio.project.core'])
        self.assertFalse(self.installer.isProductInstalled('imio.project.core'))

    # browserlayer.xml
    def test_browserlayer(self):
        """Test that IImioProjectLayer is registered."""
        from imio.project.core.interfaces import IImioProjectLayer
        from plone.browserlayer import utils
        self.failUnless(IImioProjectLayer in utils.registered_layers())
