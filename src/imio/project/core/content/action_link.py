# -*- coding: utf-8 -*-

from imio.project.core import _
from plone.formwidget.contenttree import ObjPathSourceBinder
from z3c.relationfield.schema import RelationChoice
from zope.interface import implements
from collective.symlink.content.symlink import ISymlink, Symlink


class IActionLink(ISymlink):
    symbolic_link = RelationChoice(
        title=_(u"Symbolic link"),
        source=ObjPathSourceBinder(
            navigation_tree_query={"portal_type": ("pstaction",)},
            portal_type=("pstaction",),
        ),
        required=True,
    )


class ActionLink(Symlink):
    implements(IActionLink)
