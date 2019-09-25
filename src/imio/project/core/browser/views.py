# -*- coding: utf-8 -*-

from Products.Five.browser import BrowserView
from datetime import datetime
from imio.helpers.browser.views import ContainerView
from lxml import etree
from os.path import dirname
from plone import api
from z3c.form.interfaces import HIDDEN_MODE
from zope.schema.interfaces import IVocabularyFactory


class PSTContainerView(ContainerView):
    """ """

    collapse_all_fields = True
    collapse_all_fields_onload = True


class PSTProjectContainerView(ContainerView):
    """ """

    def updateWidgets(self, prefix=None):
        super(ContainerView, self).updateWidgets(prefix)

        # hide empty budget fields
        for field_id, widget_id in (
            ('projection', 'IAnalyticBudget.projection'),
            ('analytic_budget', 'IAnalyticBudget.analytic_budget'),
            ('budget', 'budget'),
            ('budget_comments', 'budget_comments'),
        ):
            if not getattr(self.context, field_id, None):
                self.widgets[widget_id].mode = HIDDEN_MODE


class PSTExportAsXML(BrowserView):

    def __call__(self, *args, **kwargs):

        schema_file_path = dirname(__file__) + '/../model/schema_import_ecomptes_201805V1.xsd'
        schema_root = etree.parse(open(schema_file_path, 'rb'))
        schema = etree.XMLSchema(schema_root)
        parser = etree.XMLParser(schema=schema)

        raw_xml = self.index()
        parsed_xml = etree.fromstring(raw_xml.encode("utf8"), parser)  # if invalid, raises XMLSyntaxError

        self.request.RESPONSE.setHeader("Content-type", "text/xml")
        return raw_xml

    @property
    def identifiants(self):
        now = datetime.now()
        return {
            'identifiant_id': now.strftime('%Y%m%d'),
            'exercice': getattr(self.context, 'current_fiscal_year') or now.year,
            'INS': getattr(self.context, 'INS_code') or '99999',
        }

    @property
    def strategic_objectives(self):
        brains = api.content.find(
            self.context,
            depth=1,
            object_provides="imio.project.pst.content.strategic.IStrategicObjective",
            sort_on='getObjPositionInParent',
        )
        return [brain.getObject() for brain in brains]

    def operational_objectives(self, os):
        brains = api.content.find(
            os,
            depth=1,
            object_provides="imio.project.pst.content.operational.IOperationalObjective",
            sort_on='getObjPositionInParent',
        )
        return [brain.getObject() for brain in brains]

    def actions_and_subactions(self, oo):
        brains = api.content.find(
            oo,
            object_provides=[
                "imio.project.pst.content.action.IPSTAction",
                "imio.project.pst.content.action.IPSTSubAction",
            ],
            sort_on='getObjPositionInParent',
        )
        return [brain.getObject() for brain in brains]

    def status(self, element):
        element_state = api.content.get_state(element)
        ecompte_status = {
            'created': 'NON_COMMENCE',
            'ongoing': 'EN_COURS',
            'achieved': 'TERMINE',
            'stopped': 'PROBLEME',
            'terminated': 'TERMINE',
            'to_be_scheduled': 'EN_ATTENTE',
        }
        return ecompte_status.get(element_state)

    def responsable(self, element):
        factory = api.portal.getUtility(
            IVocabularyFactory,
            name='imio.project.core.content.project.manager_vocabulary',
        )

        if element.administrative_responsible:
            term_id = element.administrative_responsible[0]
            return factory(element).getTerm(term_id).title
        else:
            return None

    def mandataire(self, element, oo=None):
        factory = api.portal.getUtility(
            IVocabularyFactory,
            name='imio.project.pst.content.operational.representative_responsible_vocabulary',
        )

        if element.representative_responsible:
            term_id = element.representative_responsible[0]
            return factory(element).getTerm(term_id).title
        elif oo and oo.representative_responsible:
            term_id = oo.representative_responsible[0]
            return factory(oo).getTerm(term_id).title
        else:
            return None

    def departement(self, element):
        factory = api.portal.getUtility(
            IVocabularyFactory,
            name='imio.project.core.content.project.manager_vocabulary',
        )

        if element.manager:
            term_id = element.manager[0]
            return factory(element).getTerm(term_id).title
        else:
            return None

    def action_begin_date(self, action):
        if action.effective_begin_date:
            return action.effective_begin_date
        else:
            return action.planned_begin_date

    def action_end_date(self, action):
        if action.effective_end_date:
            return action.effective_end_date
        else:
            return action.planned_end_date

    def exercice(self, element):
        return element.created().year()

    def libelle(self, element):
        if element.portal_type == 'strategicobjective':
            return 'OS.{0} - {1}'.format(
                element.reference_number,
                element.title.encode('utf8'),
            )
        elif element.portal_type == 'operationalobjective':
            return 'OO.{0} - {1}'.format(
                element.reference_number,
                element.title.encode('utf8'),
            )
        elif element.portal_type == 'pstaction':
            return 'A.{0} - {1}'.format(
                element.reference_number,
                element.title.encode('utf8'),
            )
        elif element.portal_type == 'pstsubaction':
            action = element.__parent__
            return 'A.{0} - SA.{1} - {2}'.format(
                action.reference_number,
                element.reference_number,
                element.title.encode('utf8'),
            )
