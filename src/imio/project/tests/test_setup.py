# -*- coding: utf-8 -*-
"""Setup/installation tests for this package."""

from imio.project.testing import IntegrationTestCase


class TestInstall(IntegrationTestCase):
    """Test installation of imio.project into Plone."""

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = self.portal.portal_quickinstaller

    def test_product_installed(self):
        """Test if imio.project is installed with portal_quickinstaller."""
        self.assertTrue(self.installer.isProductInstalled('imio.project'))

    def test_uninstall(self):
        """Test if imio.project is cleanly uninstalled."""
        self.installer.uninstallProducts(['imio.project'])
        self.assertFalse(self.installer.isProductInstalled('imio.project'))

    # browserlayer.xml
    def test_browserlayer(self):
        """Test that IImioProjectLayer is registered."""
        from imio.project.interfaces import IImioProjectLayer
        from plone.browserlayer import utils
        self.failUnless(IImioProjectLayer in utils.registered_layers())
