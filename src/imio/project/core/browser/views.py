# -*- coding: utf-8 -*-

from datetime import datetime
from os.path import dirname

from Products.Five.browser import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from imio.helpers.browser.views import ContainerView
from imio.project.core import _
from lxml import etree
from lxml.etree import XMLSyntaxError
from plone import api
from plone.dexterity.browser.add import DefaultAddForm
from plone.dexterity.browser.add import DefaultAddView
from plone.dexterity.browser.edit import DefaultEditForm
from plone.supermodel import model
from plone.z3cform.fieldsets.utils import add
from plone.z3cform.fieldsets.utils import remove
from Products.CMFPlone.utils import base_hasattr
from z3c.form import button
from z3c.form.field import Fields
from z3c.form.form import Form
from zope import schema
from zope.schema.interfaces import IVocabularyFactory


class PSContainerView(ContainerView):
    """ """

    collapse_all_fields = True
    collapse_all_fields_onload = True


def manage_fields(the_form, portal_type):
    """
        Remove and reorder fields
    """
    ordered = api.portal.get_registry_record('imio.project.settings.{}_fields'.format(portal_type), default=[]) or []
    # order kept fields
    for field_name in reversed(ordered):
        field = remove(the_form, field_name)
        if field is not None:
            add(the_form, field, index=0)
    # remove all other fields
    for group in [the_form] + the_form.groups:
        for field_name in group.fields:
            if field_name not in ordered:
                group.fields = group.fields.omit(field_name)


class ProjectContainerView(ContainerView):
    """ View form redefinition to customize fields. """

    def updateFieldsFromSchemata(self):
        super(ProjectContainerView, self).updateFieldsFromSchemata()
        manage_fields(self, self.context.portal_type)


class ProjectContainerEdit(DefaultEditForm):
    """
        Edit form redefinition to customize fields.
    """

    def updateFields(self):
        super(ProjectContainerEdit, self).updateFields()
        manage_fields(self, self.context.portal_type)


class ProjectAddForm(DefaultAddForm):

    portal_type = 'project'

    def updateFields(self):
        super(ProjectAddForm, self).updateFields()
        manage_fields(self, self.portal_type)


class ProjectContainerAdd(DefaultAddView):

    form = ProjectAddForm


class PSTExportAsXML(BrowserView):

    def __call__(self, *args, **kwargs):

        schema_file_path = dirname(__file__) + '/../model/schema_import_ecomptes_201805V1.xsd'
        schema_root = etree.parse(open(schema_file_path, 'rb'))
        schema = etree.XMLSchema(schema_root)
        parser = etree.XMLParser(schema=schema)

        raw_xml = self.index()
        parsed_xml = etree.fromstring(raw_xml.encode("utf8"), parser)  # if invalid, raises XMLSyntaxError

        # self.request.RESPONSE.setHeader("Content-type", "text/xml")  # open in browser
        now = datetime.now()
        self.request.RESPONSE.setHeader('Content-Disposition', 'attachment;filename="export_iApst_pour_ecomptes_{}'
                                        '.xml"'.format(now.strftime('%Y%m%d')))
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
            oo, depth=1,
            object_provides='imio.project.pst.content.action.IPSTAction',
            sort_on='getObjPositionInParent',
        )
        ret = []
        for brain in brains:
            obj = brain.getObject()
            if base_hasattr(obj, '_link_portal_type'):
                continue  # we escape action_link
            ret.append(obj)
            sub_brains = api.content.find(obj, depth=1, object_provides='imio.project.pst.content.action.IPSTSubAction',
                                          sort_on='getObjPositionInParent')
            for sub_brain in sub_brains:
                subobj = brain.getObject()
                if base_hasattr(subobj, '_link_portal_type'):
                    continue  # we escape subaction_link
                ret.append(subobj)
        return ret

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

    def progress(self, action):
        try:
            prog = int(action.progress or 0)
        except ValueError:
            return 0
        return prog


class IPSTImportFromEcomptesSchema(model.Schema):

    ecomptes_xml = schema.Bytes(
        title=_(u"XML document exported from eComptes"),
        description=u'',
        required=True,
    )


class PSTImportFromEcomptes(Form):
    label = _(u"Import data from eComptes")
    fields = Fields(IPSTImportFromEcomptesSchema)
    ignoreContext = True

    def parse_xml(self, data):
        schema_file_path = dirname(__file__) + '/../model/PST_eComptes_Export_201805V1.xsd'
        schema_root = etree.parse(open(schema_file_path, 'rb'))
        schema = etree.XMLSchema(schema_root)
        parser = etree.XMLParser(schema=schema)
        raw_xml = data.get('ecomptes_xml')
        parsed_xml = etree.fromstring(raw_xml, parser)  # if invalid, raises XMLSyntaxError
        return parsed_xml

    def update_pst(self, ecomptes_xml):
        all_articles_xml = ecomptes_xml.findall('.//Articles')
        for articles_xml in all_articles_xml:
            if not articles_xml.getchildren():
                continue
            element_xml = articles_xml.getparent()
            uid = element_xml.get('ElementId')
            element_dx = api.content.get(UID=uid)

            if element_dx:
                element_dx_articles = []
                for article_xml in articles_xml:
                    year = int(article_xml.xpath("Exercice/text()")[0])
                    service = article_xml.xpath("Service/text()")[0]
                    btype = article_xml.xpath("Type/text()")[0]
                    article = u'{0} - {1}'.format(
                        article_xml.xpath("CodeArticle/text()")[0],
                        article_xml.xpath("Libelle/text()")[0],
                    )
                    amount = float(article_xml.xpath("Montant/text()")[0])
                    element_dx_articles.append({
                        'year': year,
                        'service': service,
                        'btype': btype,
                        'article': article,
                        'amount': amount,
                        # 'comment': u'',  Removed from schema
                    })

                element_dx.analytic_budget = element_dx_articles

    @button.buttonAndHandler(_(u'Import'), name='import')
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
        else:
            try:
                parsed_xml = self.parse_xml(data)
            except XMLSyntaxError:
                IStatusMessage(self.request).addStatusMessage(
                    _(u'The imported document is not recognized as a valid eComptes export.'),
                    'error',
                )
            else:
                self.update_pst(parsed_xml)
                IStatusMessage(self.request).addStatusMessage(
                    _(u'The XML document has been successfully imported.'),
                    'info',
                )
