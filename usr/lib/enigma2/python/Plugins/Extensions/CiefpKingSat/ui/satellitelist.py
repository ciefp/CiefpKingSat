# -*- coding: utf-8 -*-
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from enigma import (
    eTimer,
    eListboxPythonMultiContent,
    gFont,
    RT_HALIGN_LEFT,
    RT_HALIGN_CENTER,
)
from ..lib.scraper import KingOfSatScraper
import re


class CiefpSatelliteList(Screen):
    skin = """
    <screen name="CiefpSatelliteList" position="center,center" size="1920,1080" flags="wfNoBorder">
        <widget name="title" position="100,80" size="1720,60" font="Regular;34" foregroundColor="#ffffff" backgroundColor="#050505" halign="center" />
        <!-- PANEL -->
        <eLabel position="0,0" size="1920,1080" backgroundColor="#021f03" zPosition="-1" />
        <widget name="list" position="100,150" size="1720,800" foregroundColor="#ffffff" backgroundColor="#1a1a1a" scrollbarMode="showNever" />
        <widget name="status" position="100,950" size="1720,40" font="Regular;26" foregroundColor="#ffffff" backgroundColor="#050505" halign="left" />
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
        <!-- Pozadina za Žuti taster  -->
        <ePixmap pixmap="skin_default/buttons/yellow.png" position="900,1000" size="300,60" alphatest="blend" zPosition="1" />
    </screen>
    """

    def __init__(self, session, sat_name, sat_url):
        Screen.__init__(self, session)
        self.session = session
        self.sat_name = sat_name
        self.sat_url = sat_url

        # LIST
        self["list"] = MenuList([], enableWrapAround=False, content=eListboxPythonMultiContent)
        self["list"].l.setItemHeight(40)
        self["list"].l.setFont(0, gFont("Regular", 26))
        self["list"].l.setFont(1, gFont("Bold", 26))
        self["list"].l.setFont(2, gFont("Regular", 26))
        self._disableSelectionBar()

        # LABELS
        self["title"] = Label(f"Channels on {self.sat_name}")
        self["status"] = Label("Loading...")
        self["key_red"] = Label(_("Exit"))
        self["key_green"] = Label(_("Next"))
        self["key_yellow"] = Label(_("Prev"))

        # ACTIONS
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

        # PAGINATION
        self.all_items = []
        self.page_size = 20
        self.current_page = 0

        self.scraper = KingOfSatScraper()
        self.timer = eTimer()
        self.timer.callback.append(self.loadChannels)
        self.timer.start(100, True)

    def _disableSelectionBar(self):
        """
        Na nekim image-ima MenuList uvek crta selection bar (plava traka)
        čak i kad ne koristimo UP/DOWN. Ovo ga gasi na više kompatibilnih načina.
        """
        try:
            # Neki MenuList imaju selectionEnabled(bool/int)
            self["list"].selectionEnabled(0)
        except Exception:
            pass
        try:
            # eListbox metoda (najčešće postoji)
            self["list"].l.setSelectionEnable(0)
        except Exception:
            pass
        try:
            # Pojedini buildovi imaju setSelectable
            self["list"].l.setSelectable(False)
        except Exception:
            pass

    # ======================================================
    # FORMAT & BUILD
    # ======================================================
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
                # ako postoji clear/fta -> tretiraj kao FTA i preskoči ostalo
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
            (eListboxPythonMultiContent.TYPE_TEXT, 860, 5, 380, 30, 1, RT_HALIGN_LEFT, "PACKAGE"),
            (eListboxPythonMultiContent.TYPE_TEXT, 1300, 5, 380, 30, 1, RT_HALIGN_LEFT, "ENC"),
        ]

    def buildChannelEntry(self, name, country, category, package, encryption):
        return [
            None,
            (eListboxPythonMultiContent.TYPE_TEXT, 10, 5, 480, 35, 0, RT_HALIGN_LEFT, name[:50]),
            (eListboxPythonMultiContent.TYPE_TEXT, 500, 5, 140, 35, 0, RT_HALIGN_LEFT, country[:18]),
            (eListboxPythonMultiContent.TYPE_TEXT, 650, 5, 200, 35, 0, RT_HALIGN_LEFT, category[:25]),
            (eListboxPythonMultiContent.TYPE_TEXT, 860, 5, 380, 35, 0, RT_HALIGN_LEFT, package[:35]),
            (eListboxPythonMultiContent.TYPE_TEXT, 1300, 5, 380, 35, 0, RT_HALIGN_LEFT, encryption[:30]),
        ]

    def buildTpHeader(self, text):
        return [
            None,
            (eListboxPythonMultiContent.TYPE_TEXT,
             0, 5, 1800, 35,
             2, RT_HALIGN_CENTER,
              f"────────────────── {text} ──────────────────")
        ]

    # ======================================================
    # LOAD DATA
    # ======================================================
    def loadChannels(self):
        try:
            channels = self.scraper.get_satellite_channels(self.sat_url)

            if not channels:
                self.all_items = []
                self.current_page = 0
                self.showPage()
                if "status" in self:
                    self["status"].setText("No channels found")
                return

            list_items = []
            list_items.append(self.buildHeaderEntry())

            current_tp = None
            tp_count = 0
            channel_count = 0

            for ch in channels:
                name = (ch.get("name", "") or "").strip()
                if not name:
                    continue

                tp_text = (ch.get("frequency", "N/A") or "N/A").strip()

                try:
                    tp_text = re.sub(r'(\d{4,6})(\d{1,2}/\d{1,2})\b', r'\1 \2', tp_text)
                except Exception:
                    pass

                # preskoči smeće
                bad = ("frequency", "name", "country", "category", "package", "encryption")
                if name.lower() in bad or tp_text.lower() in bad:
                    continue

                # ako nema TP, da ne pravi separator "N/A"
                if not tp_text or tp_text == "N/A":
                    tp_text = "TP: N/A"

                # novi TP separator
                if tp_text != current_tp:
                    current_tp = tp_text
                    tp_count += 1
                    list_items.append(self.buildTpHeader(tp_text))

                country = (ch.get("country", "-") or "-").strip()
                category = (ch.get("category", "-") or "-").strip()
                package = (ch.get("package", "-") or "-").strip()
                enc = ch.get("encryption", "")

                list_items.append(
                    self.buildChannelEntry(
                        name,
                        country,
                        category,
                        package,
                        self.formatEncryption(enc)  # ovde clear -> FTA
                    )
                )
                channel_count += 1

            # upiši u paging listu
            self.all_items = list_items
            self.current_page = 0
            self.showPage()

            # status i title info (bez crash-a ako widget ne postoji)
            if "status" in self:
                self["status"].setText(f"TP: {tp_count} | CH: {channel_count} | Total: {len(channels)}")
            if "title" in self:
                # ako već nameštaš title u __init__, ovo možeš i izbaciti
                self["title"].setText(f"Channels on {self.sat_name}")

            # transponder_info koristi samo ako postoji u skinu
            if "transponder_info" in self:
                self["transponder_info"].setText(self.sat_name)

        except Exception as e:
            import traceback
            print("[CiefpSatelliteList] Error:", str(e))
            print(traceback.format_exc())

            self.all_items = []
            self.current_page = 0
            self.showPage()

            if "status" in self:
                self["status"].setText(f"Loading failed: {str(e)[:80]}")

    # ======================================================
    # PAGINATION
    # ======================================================

    def showPage(self):
        start = self.current_page * self.page_size
        end = start + self.page_size

        self["list"].setList(self.all_items[start:end])
        self._disableSelectionBar()

        total_pages = max(1, (len(self.all_items) + self.page_size - 1) // self.page_size)
        self["status"].setText(
            f"Page {self.current_page + 1}/{total_pages} | Rows {start + 1}-{min(end, len(self.all_items))}"
        )

    def nextPage(self):
        max_page = (len(self.all_items) - 1) // self.page_size
        if self.current_page < max_page:
            self.current_page += 1
            self.showPage()

    def prevPage(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.showPage()

    # ======================================================

    def exit(self):
        self.close()
