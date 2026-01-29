# -*- coding: utf-8 -*-
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Components.Label import Label
from Components.Pixmap import Pixmap
from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_VALIGN_CENTER
from . import satellitelist, packages, news_single_screen
import json
import os
import glob


# Putanja do glavnog plugin direktorijuma
PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Putanja do pozadinske slike
BACKGROUND = os.path.join(PLUGIN_DIR, "background.png")

class CiefpKingSatMain(Screen):
    skin = """
    <screen name="CiefpKingSatMain" position="center,center" size="1920,1080" title="CiefpKingSat - KingOfSat Viewer" flags="wfNoBorder">
        <widget name="menu" position="100,150" size="1300,780" font="Regular;36" itemHeight="39" halign="left"  valign="center" scrollbarMode="showOnDemand" />
        <!-- TITLE -->
        <widget name="title" render="Label" position="100,100" size="1720,60" font="Regular;34" halign="center" valign="center" foregroundColor="#ffffff" backgroundColor="#1a1a1a" zPosition="2" />
        <widget name="description" position="100,950" size="1720,40" font="Regular;26" itemHeight="30" halign="left"  valign="center" foregroundColor="#cccccc" />
        <!-- BACKGROUND -->
        <widget name="background" position="1420,150" size="400,780" pixmap="%s" alphatest="on" zPosition="1" />
        <!-- Crveni taster - Back -->
        <widget name="key_red" position="100,1000" size="300,60" font="Bold;28" halign="center" valign="center" foregroundColor="#080808" backgroundColor="#a00000" zPosition="2" />
        <!-- Pozadina za crveni taster  -->
        <ePixmap pixmap="skin_default/buttons/red.png" position="100,1000" size="300,60" alphatest="blend" zPosition="1" />
        <!-- Zeleni taster - Back -->
        <widget name="key_green" position="500,1000" size="300,60" font="Bold;28" halign="center" valign="center" foregroundColor="#080808" backgroundColor="#00a000" zPosition="2" />
        <!-- Pozadina za Zeleni taster  -->
        <ePixmap pixmap="skin_default/buttons/green.png" position="500,1000" size="300,60" alphatest="blend" zPosition="1" />
        <!-- Žuti taster - Back -->
        <widget name="key_yellow" position="900,1000" size="300,60" font="Bold;28" halign="center" valign="center" foregroundColor="#080808" backgroundColor="#a09d00" zPosition="2" />
        <!-- Pozadina za žuti taster  -->
        <ePixmap pixmap="skin_default/buttons/yellow.png" position="900,1000" size="300,60" alphatest="blend" zPosition="1" />
        <!-- Plavi taster - Back -->
        <widget name="key_blue" position="1300,1000" size="300,60" font="Bold;28" halign="center" valign="center" foregroundColor="#080808" backgroundColor="#0003a0" zPosition="2" />
        <!-- Pozadina za plavi taster  -->
        <ePixmap pixmap="skin_default/buttons/blue.png" position="1300,1000" size="300,60" alphatest="blend" zPosition="1" />
    </screen>
    """ % BACKGROUND
    
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.title = "CiefpKingSat"
        
        self["background"] = Pixmap()
        
        # Sateliti iz specifikacije
        self.satellites = [
            ("75.0°E - ABS-2", "pos-75E"),
            ("70.5°E - Eutelsat 70B", "pos-70.5E"),
            ("68.5°E - Intelsat 20 (IS-20)", "pos-68.5E"),
            ("62.0°E - Intelsat 39", "pos-62E"),
            ("56.0°E - Express AT1", "pos-56E"),
            ("55.0°E - Yamal 402", "pos-55E"),
            ("53.0°E - Express AM6", "pos-53E"),
            ("52.5°E - Yahsat 1A", "pos-52.5E"),
            ("52.0°E - TurkmenÄlem / MonacoSat", "pos-52E"),
            ("51.5°E - Belintersat 1", "pos-51.5E"),
            ("50.0°E - Turksat 4B", "pos-50E"),
            ("46.0°E - Azerspace-1", "pos-46E"),
            ("42.0°E - Turksat 3A;Turksat 4A;Turksat 5B;Turksat 6A", "pos-42E"),
            ("39.0°E - Hellas Sat 3;Hellas Sat 4", "pos-39E"),
            ("36.0°E - Express AMU1", "pos-36E"),
            ("31.0°E - Turksat 5A", "pos-31E"),
            ("30.5°E - Arabsat 5A;Arabsat 6A", "pos-30.5E"),
            ("28.2°E - Astra 2E;Astra 2F;Astra 2G", "pos-28.2E"),
            ("26.0°E - Badr 4;Badr 5;Badr 7;Badr 8", "pos-26E"),
            ("25.5°E - Es'hail 1;Es'hail 2", "pos-25.5E"),
            ("23.5°E - Astra 3B;Astra 3C", "pos-23.5E"),
            ("21.6°E - Astra 1N", "pos-21.6E"),
            ("19.2°E - Astra 1P;Astra 1M;Astra 1N", "pos-19.2E"),
            ("16.0°E - Eutelsat 16A", "pos-16E"),
            ("13.0°E - Hot Bird 13G;Hot Bird 13F", "pos-13E"),
            ("10.0°E - Eutelsat 10B ", "pos-10E"),
            ("9.0°E - Eutelsat 9B", "pos-9E"),
            ("7.0°E - Eutelsat 7B;Eutelsat 7C", "pos-7E"),
            ("4.8°E - Astra 4A;Astra 4A", "pos-4.8E"),
            ("3.0°E - Rascom QAF 1R", "pos-3E"),
            ("1.9°E - BulgariaSat", "pos-1.9E"),
            ("0.8°W - Intelsat 10-02;Thor 5;Thor 6", "pos-0.8W"),
            ("4.0°W - Amos 3", "pos-4W"),
            ("5.0°W - Eutelsat 5 West B", "pos-5W"),
            ("7.0°W - Nilesat 102;Nilesat 301;Nilesat 201", "pos-7W"),
            ("8.0°W - Eutelsat 8 West D;Express AM 8", "pos-8W"),
            ("14.0°W - Express AM 8 ", "pos-14W"),
            ("15.0°W - Telstar 12 Vantage", "pos-15W"),
            ("22.0°W - SES 4", "pos-22W"),
            ("24.5°W - AlComSat 1", "pos-24.5W"),
            ("30.0°W - Hispasat 30W-5;Hispasat 30W-6", "pos-30W"),
            ("34.5°W - Intelsat 35", "pos-34.5W")
        ]
        
        self["menu"] = MenuList(self.satellites)
        self["title"] = Label("CiefpKingSat - Select Satellite")
        self["description"] = Label("Select a satellite to view its channels")
        
        self["key_red"] = Label(_("Exit"))
        self["key_green"] = Label(_("Packages"))
        self["key_yellow"] = Label(_("News"))
        self["key_blue"] = Label(_("Tools"))
        
        self["actions"] = ActionMap(["OkCancelActions", "ColorActions"], {
            "ok": self.ok,
            "cancel": self.exit,
            "red": self.exit,
            "green": self.packages,
            "yellow": self.news,
            "blue": self.tools_menu
        }, -1)
        
    def ok(self):
        selection = self["menu"].getCurrent()
        if selection:
            sat_name, sat_url = selection
            self.session.open(satellitelist.CiefpSatelliteList, sat_name, sat_url)
    
    def packages(self):
        self.session.open(packages.CiefpPackagesList)
    
    def news(self):
        self.session.open(news_single_screen.CiefpNewsSingleScreen)
    
    def tools_menu(self):
        """Otvara ChoiceBox sa opcijama za alate"""
        menu = [
            (_("Clear Cache"), "clear_cache"),
            (_("Plugin Info"), "plugin_info"),
            (_("About"), "about"),
        ]
        
        self.session.openWithCallback(
            self.tools_menu_callback,
            ChoiceBox,
            title="CiefpKingSat - Tools",
            list=menu
        )
    
    def tools_menu_callback(self, choice):
        """Obrada izbora iz tools menija"""
        if choice is None:
            return
        
        choice_id = choice[1]
        
        if choice_id == "clear_cache":
            self.clear_cache()
        elif choice_id == "plugin_info":
            self.show_plugin_info()
        elif choice_id == "about":
            self.show_about()
    
    def clear_cache(self):
        """Briše sve cache fajlove"""
        try:
            # Pronađi plugin direktorijum
            import sys
            plugin_path = "/usr/lib/enigma2/python/Plugins/Extensions/CiefpKingSat"
            
            # Proveri da li postoji cache direktorijum
            cache_dir = os.path.join(plugin_path, "cache")
            
            if not os.path.exists(cache_dir):
                self.session.open(MessageBox, "Cache directory not found!", MessageBox.TYPE_ERROR)
                return
            
            # Pronađi sve .json fajlove u cache direktorijumu
            cache_files = glob.glob(os.path.join(cache_dir, "*.json"))
            
            if not cache_files:
                self.session.open(MessageBox, "No cache files to clear!", MessageBox.TYPE_INFO)
                return
            
            # Obriši fajlove
            deleted_count = 0
            for cache_file in cache_files:
                try:
                    os.remove(cache_file)
                    deleted_count += 1
                except:
                    pass
            
            # Prikaži rezultat
            message = f"Successfully cleared cache!\nDeleted {deleted_count} cache files."
            self.session.open(MessageBox, message, MessageBox.TYPE_INFO)
            
        except Exception as e:
            error_msg = f"Error clearing cache:\n{str(e)}"
            self.session.open(MessageBox, error_msg, MessageBox.TYPE_ERROR)
    
    def show_plugin_info(self):
        """Prikazuje informacije o pluginu"""
        info_text = (
            "CiefpKingSat - KingOfSat Viewer\n\n"
            "Version: 1.0\n"
            "Author: Ciefp\n"
            "Description: Plugin for viewing KingOfSat satellite and package data\n\n"
            "Features:\n"
            "- Satellite channel lists\n"
            "- Package channel lists\n"
            "- KingOfSat news updates\n"
            "- Cache system for faster loading"
        )
        self.session.open(MessageBox, info_text, MessageBox.TYPE_INFO)
    
    def show_about(self):
        """Prikazuje about informacije"""
        about_text = (
            "CiefpKingSat Plugin\n\n"
            "This plugin provides access to KingOfSat.net data including:\n"
            "- Satellite channel listings\n"
            "- TV package information\n"
            "- Latest satellite news\n\n"
            "Data is cached locally for faster access.\n"
            "Use 'Clear Cache' option to refresh data."
        )
        self.session.open(MessageBox, about_text, MessageBox.TYPE_INFO)
    
    def exit(self):
        self.close()