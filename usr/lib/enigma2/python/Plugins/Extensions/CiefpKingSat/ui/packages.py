# -*- coding: utf-8 -*-
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
from Components.Pixmap import Pixmap
from Screens.MessageBox import MessageBox
from . import satellitelist
from ..lib.scraper import KingOfSatScraper
from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_HALIGN_CENTER
import os
import re

# Putanja do glavnog plugin direktorijuma
PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Putanja do pozadinske slike
BACKGROUND = os.path.join(PLUGIN_DIR, "background.png")



class CiefpPackagesList(Screen):
    # OVO JE PRAVO MESTO ZA LISTU – na nivou klase, ne unutar __init__
    PACKAGES_BY_SAT = {
        "42.0°E - Turksat 3A;Turksat 4A;Turksat 5B;Turksat 6A": [
            ("Digiturk", "pack-digiturk"),
            ("D-Smart", "pack-dsmart")
        ],
        "39.0°E - Hellas Sat 3;Hellas Sat 4": [
            ("Tring", "pack-tring"),
            ("A1 BG", "pack-a1bg"),
            ("Bulsatcom", "pack-bulsatcom"),
            ("Orange Romania", "pack-orangeromania")
        ],
        "28.2°E - Astra 2E;Astra 2F;Astra 2G": [
            ("Sky Digital", "pack-skydigital"),
            ("Freesat", "pack-freesat"),
            ("BBC", "pack-bbc")
        ],
        "23.5°E - Astra 3B;Astra 3C": [
            ("Canal Digitaal", "pack-canaldigitaal"),
            ("TV Vlaanderen", "pack-tvvlaanderen"),
            ("Austriasat", "pack-austriasat"),
            ("Skylink", "pack-skylink"),
            ("Volna Telka", "pack-volnatelka")
        ],
        "19.2°E - Astra 1P;Astra 1M;Astra 1N": [
            ("Digital+ A", "pack-digitalplusa"),
            ("Sky Germany", "pack-skygermany"),
            ("HD Plus", "pack-hdplus"),
            ("Austriasat", "pack-austriasat"),
            ("ARD Digital", "pack-arddigital"),
            ("Boobles", "pack-boobles"),
            ("ORF Digital", "pack-orfdigital"),
            ("ZDF Vision", "pack-zdfvision"),
            ("SSR", "pack-ssr"),
            ("Canal", "pack-canal"),
            ("TNTSAT", "pack-tntsat"),
            ("BIS", "pack-bis"),
            ("Telesat", "pack-telesat"),
            ("MTV", "pack-mtv"),
            ("TV Vlaanderen", "pack-tvvlaanderen"),
            ("Canal Digitaal", "pack-canaldigitaal")
        ],
        "16.0°E - Eutelsat 16A": [
            ("Total TV", "pack-totaltv"),
            ("Pink", "pack-pink"),
            ("Digitalb", "pack-digitalb"),
            ("Orange SK", "pack-orangesk"),
            ("AntikSat", "pack-antiksat"),
            ("Team Media", "pack-teammedia"),
            ("MaxTV", "pack-maxtv"),
            ("Direct2Home", "pack-direct2home")
        ],
        "13.0°E - Hot Bird 13G;Hot Bird 13F": [
            ("Orange PL", "pack-orangepl"),
            ("Polsat", "pack-polsat"),
            ("NC+", "pack-ncplus"),
            ("NOVA", "pack-nova"),
            ("Total TV", "pack-totaltv"),
            ("Sky Digital", "pack-skydigital"),
            ("Austriasat", "pack-austriasat"),
            ("BIS", "pack-bis"),
            ("Telesat", "pack-telesat"),
            ("Tivusat", "pack-tivusat"),
            ("Sky Italia", "pack-skyitalia"),
            ("SSR", "pack-ssr"),
            ("RAI", "pack-rai"),
            ("TV Vlaanderen", "pack-tvvlaanderen"),
            ("Mediaset", "pack-mediaset"),
            ("Vivacom", "pack-vivacom")
        ],
        "9.0°E - Eutelsat 9B": [
            ("Kabelkiosk", "pack-kabelkiosk"),
            ("Cosmote", "pack-cosmote"),
            ("Mediaset", "pack-mediaset")
        ],
        "4.8°E - Astra 4A;Astra 4A": [
            ("Viasat", "pack-viasat"),
            ("Viasat UA", "pack-viasatua")
        ],
        "1.9°E - BulgariaSat": [
            ("Neosat", "pack-neosat")
        ],
        "0.8°W - Intelsat 10-02;Thor 5;Thor 6": [
            ("Allente", "pack-allente"),
            ("FocusSat", "pack-focussat"),
            ("Direct One", "pack-directone"),
            ("Telly", "pack-telly")
        ],
        "5.0°W - Eutelsat 5 West B": [
            ("BIS", "pack-bis"),
            ("Fransat", "pack-fransat"),
            ("RAI", "pack-rai")
        ],
        "30.0°W - Hispasat 30W-5;Hispasat 30W-6": [
            ("NOS", "pack-nos"),
            ("MEO", "pack-meo")
        ]
    }


    skin = """
    <screen name="CiefpPackagesList" position="center,center" size="1920,1080" title="Packages" flags="wfNoBorder">
        <!-- TITLE -->
        <widget name="title" render="Label" position="100,80" size="1720,60" font="Regular;34" halign="center" valign="center" foregroundColor="#ffffff" backgroundColor="#050505" zPosition="2" />
        <widget name="menu" position="100,150" size="1300,780" font="Regular;28" itemHeight="30" halign="left"  valign="center" foregroundColor="#ffffff" backgroundColor="#1a1a1a" scrollbarMode="showOnDemand" />
        <!-- PANEL -->
        <eLabel position="0,0" size="1920,1080" backgroundColor="#021f03" zPosition="-1" />
        <!-- BACKGROUND -->
        <widget name="background" position="1420,150" size="400,780" pixmap="%s" alphatest="on" zPosition="1" />
        <widget name="description" render="Label" position="100,950" size="1720,40" font="Regular;26" halign="left" valign="center" foregroundColor="#ffffff" backgroundColor="#050505" />
        <!-- Crveni taster - Back -->
        <widget name="key_red" position="100,1000" size="860,40" font="Bold;26" halign="center" valign="center" foregroundColor="#080808" backgroundColor="#a00000" zPosition="2" />
        <!-- Pozadina za crveni taster  -->
        <ePixmap pixmap="skin_default/buttons/red.png" position="100,1000" size="860,40" alphatest="blend" zPosition="1" />
        <!-- Zeleni taster - Back -->
        <widget name="key_green" position="960,1000" size="860,40" font="Bold;26" halign="center" valign="center" foregroundColor="#080808" backgroundColor="#00a000" zPosition="2" />
        <!-- Pozadina za Zeleni taster  -->
        <ePixmap pixmap="skin_default/buttons/green.png" position="960,1000" size="860,40" alphatest="blend" zPosition="1" />
    </screen>
    """ % BACKGROUND

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session

        self["background"] = Pixmap()
        
        # Flatten listu za prikaz (koristi klasnu varijablu)
        self.menu_items = []
        for sat, packages in self.PACKAGES_BY_SAT.items():  # ← self.PACKAGES_BY_SAT
            self.menu_items.append((f"──────── {sat} ────────", None))
            for package_name, package_url in packages:
                self.menu_items.append((f" {package_name}", package_url))

        self["menu"] = MenuList(self.menu_items)
        self["title"] = Label("CiefpKingSat - Packages")
        self["description"] = Label("Select a package to view its channels")
        self["key_red"] = Label(_("Exit"))
        self["key_green"] = Label(_("Select"))

        self["actions"] = ActionMap(["OkCancelActions", "ColorActions"], {
            "ok": self.ok,
            "cancel": self.exit,
            "red": self.exit,
            "green": self.ok,
        }, -1)

        self.scraper = KingOfSatScraper()

    def ok(self):
        selection = self["menu"].getCurrent()
        if not selection:
            return

        # Preskoči grupe
        if "Satelit" in selection[0] or "---" in selection[0]:
            return

        selected_name = selection[0].strip()  # " DigiTurk" → "DigiTurk"

        # Pronađi slug
        slug = None
        for sat_group, pkgs in self.PACKAGES_BY_SAT.items():
            for pkg_name, pkg_slug in pkgs:
                if pkg_name == selected_name:
                    slug = pkg_slug
                    break
            if slug:
                break

        if not slug:
            self.session.open(MessageBox, f"Paketa {selected_name} nije pronađen.", MessageBox.TYPE_ERROR)
            return

        channels = self.scraper.get_package_channels(slug)

        if not channels:
            self.session.open(MessageBox, f"Cannot load package: {selected_name}\nNo channels found.", MessageBox.TYPE_ERROR)
            return

        self.session.open(CiefpPackageChannels, selected_name, {'channels': channels})

    def exit(self):
        self.close()


class CiefpPackageChannels(Screen):
    skin = """
    <screen name="CiefpPackageChannels" position="center,center" size="1920,1080" title="Package Channels" flags="wfNoBorder">
        <!-- PANEL -->
        <eLabel position="0,0" size="1920,1080" backgroundColor="#021f03" zPosition="-1" />

        <!-- TITLE -->
        <widget name="title" render="Label" position="100,80" size="1720,60" font="Regular;34" halign="center" valign="center"
                foregroundColor="#ffffff" backgroundColor="#050505" zPosition="2" />

        <!-- LISTA (TABULAR) -->
        <widget name="channels" position="100,150" size="1720,800" foregroundColor="#ffffff" backgroundColor="#1a1a1a" scrollbarMode="showNever" />

        <!-- STATUS BAR --> 
        <widget name="status" render="Label" position="100,950" size="1720,40" font="Regular;26" halign="left" valign="center"
                foregroundColor="#cccccc" backgroundColor="#050505" zPosition="1" />

        <!-- Crveni taster - Back -->
        <widget name="key_red" position="100,1000" size="573,40" font="Bold;26" halign="center" valign="center"
                foregroundColor="#080808" backgroundColor="#a00000" zPosition="2" />
        <ePixmap pixmap="skin_default/buttons/red.png" position="100,1000" size="573,40" alphatest="blend" zPosition="1" />

        <!-- Zeleni / Žuti - paging -->
        <widget name="key_green" position="673,1000" size="573,40" font="Bold;26" halign="center" valign="center"
                foregroundColor="#080808" backgroundColor="#00a000" zPosition="2" />
        <ePixmap pixmap="skin_default/buttons/green.png" position="673,1000" size="300,60" alphatest="blend" zPosition="1" />

        <widget name="key_yellow" position="1246,1000" size="573,40" font="Bold;26" halign="center" valign="center"
                foregroundColor="#080808" backgroundColor="#a09d00" zPosition="2" />
        <ePixmap pixmap="skin_default/buttons/yellow.png" position="1246,1000" size="300,60" alphatest="blend" zPosition="1" />
    </screen>
    """
    def __init__(self, session, package_name, package_data):
        Screen.__init__(self, session)
        self.session = session
        self.package_name = package_name
        self.package_data = package_data or {}

        self["title"] = Label(f"{package_name} - Channels")
        self["status"] = Label("")
        self["key_red"] = Label(_("Back"))
        self["key_green"] = Label(_("Next"))
        self["key_yellow"] = Label(_("Prev"))

        # Tabular list (isto kao satellite)
        self["channels"] = MenuList([], enableWrapAround=False, content=eListboxPythonMultiContent)
        self["channels"].l.setItemHeight(40)
        self["channels"].l.setFont(0, gFont("Regular", 26))
        self["channels"].l.setFont(1, gFont("Bold", 26))
        self["channels"].l.setFont(2, gFont("Regular", 26))
        self._disableSelectionBar()

        self["actions"] = ActionMap(
            ["OkCancelActions", "ColorActions", "NavigationActions"],
            {
                "cancel": self.exit,
                "red": self.exit,

                "green": self.nextPage,
                "yellow": self.prevPage,

                "right": self.nextPage,
                "left": self.prevPage,
            },
            -1
        )

        # Pagination
        self.all_items = []
        self.page_size = 20
        self.current_page = 0

        self._buildItems()
        self.showPage()

    def _disableSelectionBar(self):
        """
        Gasi plavu selection traku (ne koristimo selekciju jer je paging preko boja).
        Različiti image-i imaju različite metode, pa probamo više opcija.
        """
        try:
            self["channels"].selectionEnabled(0)
        except Exception:
            pass
        try:
            self["channels"].l.setSelectionEnable(0)
        except Exception:
            pass
        try:
            self["channels"].l.setSelectable(False)
        except Exception:
            pass

    def formatEncryption(self, enc):
        # 1) Normalizuj u listu tokena
        if enc is None:
            tokens = []
        elif isinstance(enc, (list, tuple, set)):
            tokens = [str(x) for x in enc if x]
        else:
            s = str(enc).strip()
            # razdvajanje ako je "Conax/Nagra", "Conax, Nagra", "Conax + Nagra" itd.
            for sep in ["/", ",", ";", "+", "|"]:
                s = s.replace(sep, " ")
            tokens = [t for t in s.split() if t]

        if not tokens:
            return "FTA"

        out = []
        for t in tokens:
            tl = t.lower()

            # FTA varijante
            if tl in ("fta", "free", "clear", "unencrypted", "0"):
                return "FTA"

            if "videoguard" in tl or "nds" in tl:
                out.append("VideoGuard")
            elif "conax" in tl:
                out.append("Conax")
            elif "nagra" in tl or "nagravision" in tl:
                out.append("Nagravision")
            elif "irdeto" in tl:
                out.append("Irdeto")
            elif "viaccess" in tl:
                out.append("Viaccess")
            elif "cryptoworks" in tl:
                out.append("CryptoWorks")
            elif "biss" in tl:
                out.append("BISS")
            else:
                out.append(t[:12])

        # ukloni duplikate, zadrži redosled
        seen = set()
        out2 = []
        for x in out:
            if x not in seen:
                seen.add(x)
                out2.append(x)

        return "/".join(out2) if out2 else "FTA"

    def buildHeaderEntry(self):
        return [
            None,
            (eListboxPythonMultiContent.TYPE_TEXT, 10, 5, 480, 30, 1, RT_HALIGN_LEFT, "CHANNEL"),
            (eListboxPythonMultiContent.TYPE_TEXT, 500, 5, 140, 30, 1, RT_HALIGN_LEFT, "COUNTRY"),
            (eListboxPythonMultiContent.TYPE_TEXT, 650, 5, 200, 30, 1, RT_HALIGN_LEFT, "CATEGORY"),
            (eListboxPythonMultiContent.TYPE_TEXT, 860, 5, 320, 30, 1, RT_HALIGN_LEFT, "PACKAGE"),
            (eListboxPythonMultiContent.TYPE_TEXT, 1300, 5, 320, 30, 1, RT_HALIGN_LEFT, "ENC"),
        ]

    def buildTpHeader(self, text):
        return [
            None,
            (eListboxPythonMultiContent.TYPE_TEXT,
             0, 5, 1800, 35,
             2, RT_HALIGN_CENTER,
              f"────────────────── {text} ──────────────────")
        ]

    def buildChannelEntry(self, name, country, category, package, enc):
        return [
            None,
            (eListboxPythonMultiContent.TYPE_TEXT, 10, 5, 480, 35, 0, RT_HALIGN_LEFT, str(name)[:50]),
            (eListboxPythonMultiContent.TYPE_TEXT, 500, 5, 140, 35, 0, RT_HALIGN_LEFT, str(country)[:18]),
            (eListboxPythonMultiContent.TYPE_TEXT, 650, 5, 200, 35, 0, RT_HALIGN_LEFT, str(category)[:25]),
            (eListboxPythonMultiContent.TYPE_TEXT, 860, 5, 320, 35, 0, RT_HALIGN_LEFT, str(package)[:35]),
            (eListboxPythonMultiContent.TYPE_TEXT, 1300, 5, 320, 35, 0, RT_HALIGN_LEFT, str(enc)[:30]),
        ]

    def _buildItems(self):
        channels = self.package_data.get("channels", []) or []
        if not channels:
            self.all_items = [self.buildTpHeader("No channels available for this package.")]
            self["status"].setText(f"Package: {self.package_name} | Loaded 0 channels")
            return

        items = [self.buildHeaderEntry()]
        current_tp = None
        shown_channels = 0

        for ch in channels:
            name = (ch.get("name", "") or "").strip()
            if not name:
                continue

            tp_text = (ch.get("frequency", "N/A") or "N/A").strip()

            # popravi SR/FEC kad je zalepljeno (npr. 220002/3)
            try:
                tp_text = re.sub(r'(\d{4,6})(\d{1,2}/\d{1,2})\b', r'\1 \2', tp_text)
            except Exception:
                pass

            bad = ("frequency", "name", "country", "category", "package", "encryption")
            if name.lower() in bad or tp_text.lower() in bad:
                continue

            if not tp_text or tp_text == "N/A":
                tp_text = "TP: N/A"

            if tp_text != current_tp:
                current_tp = tp_text
                items.append(self.buildTpHeader(tp_text))

            items.append(
                self.buildChannelEntry(
                    name,
                    (ch.get("country", "-") or "-").strip(),
                    (ch.get("category", "-") or "-").strip(),
                    (ch.get("package", self.package_name) or self.package_name).strip(),
                    self.formatEncryption(ch.get("encryption", "")),
                )
            )
            shown_channels += 1

        self.all_items = items
        self["status"].setText(f"Package: {self.package_name} | Loaded {shown_channels} channels")

    def showPage(self):
        if not self.all_items:
            self["channels"].setList([])
            self["status"].setText(f"Package: {self.package_name} | Loaded 0 channels")
            return

        start = self.current_page * self.page_size
        end = start + self.page_size

        self["channels"].setList(self.all_items[start:end])
        self._disableSelectionBar()

        total_pages = max(1, (len(self.all_items) + self.page_size - 1) // self.page_size)
        self["status"].setText(
            f"Package: {self.package_name} | Page {self.current_page + 1}/{total_pages} | Rows {start + 1}-{min(end, len(self.all_items))}"
        )

    def nextPage(self):
        if not self.all_items:
            return
        max_page = (len(self.all_items) - 1) // self.page_size
        if self.current_page < max_page:
            self.current_page += 1
            self.showPage()

    def prevPage(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.showPage()

    def exit(self):
        self.close()

