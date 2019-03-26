# -*- coding: utf-8 -*-

from imio.project.core.testing import FunctionalTestCase
from imio.project.core.utils import getVocabularyTermsForOrganization
from plone import api


class TestUtils(FunctionalTestCase):
    """ test utils module of imio.project.core. """

    def test_getVocabularyTermsForOrganization(self):
        voc = getVocabularyTermsForOrganization(self.portal)
        self.assertListEqual([term.value for term in voc._terms],
                             [u'adl', u'direction-gen', u'direction-gen-secretariat-communal',
                              u'direction-gen-service-informatique', u'direction-financiere',
                              u'direction-financiere-taxes', u'direction-financiere-recettes', u'service-du-personnel'])
        self.assertListEqual([term.title for term in voc._terms],
                             [u'ADL', u'Direction gén', u'Direction gén - Secrétariat Communal',
                              u'Direction gén - Service Informatique', u'Direction financière',
                              u'Direction financière - Taxes', u'Direction financière - Recettes',
                              u'Service du Personnel'])
        # using a sub organization
        voc = getVocabularyTermsForOrganization(self.portal, organization_id='echevins')
        self.assertListEqual([term.value for term in voc._terms],
                             [u'1er-echevin', u'2eme-echevin', u'3eme-echevin'])
        self.assertListEqual([term.title for term in voc._terms],
                             [u'1er échevin', u'2ème échevin', u'3ème échevin'])
        # adding state
        api.content.transition(self.org['echevins']['1er-echevin'], 'deactivate')
        voc = getVocabularyTermsForOrganization(self.portal, organization_id='echevins', states='active')
        self.assertListEqual([term.value for term in voc._terms],
                             [u'2eme-echevin', u'3eme-echevin'])
        self.assertListEqual([term.title for term in voc._terms],
                             [u'2ème échevin', u'3ème échevin'])
