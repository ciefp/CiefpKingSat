# -*- coding: utf-8 -*-
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
import os, gettext

PluginLanguageDomain = "CiefpKingSat"
PluginLanguagePath = "Extensions/CiefpKingSat/locale"

def localeInit():
    lang = language.getLanguage()[:2]
    os.environ["LANGUAGE"] = lang
    gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))

def _(txt):
    t = gettext.dgettext(PluginLanguageDomain, txt)
    if t == txt:
        t = gettext.gettext(txt)
    return t

localeInit()
language.addCallback(localeInit)

from Plugins.Plugin import PluginDescriptor
from .ui.main import CiefpKingSatMain

def main(session, **kwargs):
    session.open(CiefpKingSatMain)

def Plugins(**kwargs):
    return [PluginDescriptor(
        name="CiefpKingSat",
        description=_("KingOfSat Channel Information"),
        where=PluginDescriptor.WHERE_PLUGINMENU,
        icon="plugin.png",
        fnc=main
    )]