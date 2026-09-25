# -*- coding: utf-8 -*-
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Screens.MessageBox import MessageBox
from enigma import (
    eTimer,
    eListboxPythonMultiContent,
    gFont,
    RT_HALIGN_LEFT,
    RT_HALIGN_CENTER,
)
from ..lib.scraper import KingOfSatScraper
import threading

PAGE_ROWS = 12


class _PagedScreen(Screen):
    """Common page-based DAB view: LEFT/RIGHT changes page, no selection bar."""
    row_y = 195
    row_h = 55

    def _init_rows(self):
        self._rows = []
        for i in range(PAGE_ROWS):
            name = "row%d" % i
            y = self.row_y + i * self.row_h
            self[name] = Label("")
            # Position is defined in skin; this keeps runtime logic simple.
            self._rows.append(self[name])

    def _clear_rows(self):
        for row in self._rows:
            row.setText("")

    def _set_page_rows(self, lines):
        self._clear_rows()
        for i, line in enumerate(lines[:PAGE_ROWS]):
            self._rows[i].setText(line)

    def _page_info(self, total):
        pages = max(1, (total + self.page_size - 1) // self.page_size)
        self.page_count = pages
        if self.page_index >= pages:
            self.page_index = pages - 1
        return pages

    def page_left(self):
        if self.page_index > 0:
            self.page_index -= 1
            self._render_page()

    def page_right(self):
        pages = self._page_info(len(self._page_items))
        if self.page_index + 1 < pages:
            self.page_index += 1
            self._render_page()


class CiefpDabList(_PagedScreen):
    """DAB over DVB: satellites. LEFT/RIGHT pages; OK opens current satellite."""

    skin = """
    <screen name="CiefpDabList" position="center,center" size="1920,1080" flags="wfNoBorder">
        <eLabel position="0,0" size="1920,1080" backgroundColor="#021f03" zPosition="-1" />
        <widget name="title" position="100,80" size="1720,60" font="Regular;34" halign="center" valign="center" foregroundColor="#ffffff" backgroundColor="#050505" zPosition="2" />
        <widget name="header" position="100,150" size="1720,45" font="Bold;26" halign="left" valign="center" foregroundColor="#ffffff" backgroundColor="#303030" />
        %s
        <widget name="status" position="100,860" size="1720,40" font="Regular;26" halign="center" valign="center" foregroundColor="#ffffff" backgroundColor="#050505" />
        <widget name="key_red" position="100,920" size="430,40" font="Bold;26" halign="center" valign="center" foregroundColor="#080808" backgroundColor="#a00000" />
        <widget name="key_green" position="530,920" size="430,40" font="Bold;26" halign="center" valign="center" foregroundColor="#080808" backgroundColor="#00a000" />
        <widget name="key_yellow" position="960,920" size="430,40" font="Bold;26" halign="center" valign="center" foregroundColor="#080808" backgroundColor="#a09d00" />
        <widget name="key_blue" position="1390,920" size="430,40" font="Bold;26" halign="center" valign="center" foregroundColor="#080808" backgroundColor="#0003a0" />
    </screen>
    """ % "\n".join(
        '<widget name="row%d" position="100,%d" size="1720,55" font="Regular;26" halign="left" valign="center" foregroundColor="#ffffff" backgroundColor="#1a1a1a" />' % (i, 195 + i * 55)
        for i in range(PAGE_ROWS)
    )
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.scraper = KingOfSatScraper()
        self.dab_data = []
        self.satellites = []
        self._page_items = []
        self.page_size = 1          # <-- MORA BITI TU
        self.page_index = 0
        self.page_count = 1
        self._loading = False
        self._dab_result = None
        self._dab_error = None

        self["title"] = Label("DAB over DVB Transmissions - All Satellites")
        self["header"] = Label("SATELLITE                         MUXES                         RADIO STATIONS")
        self["status"] = Label("Loading DAB data...")
        self["key_red"] = Label(_("Exit"))
        self["key_green"] = Label(_("Select"))
        self["key_yellow"] = Label(_("All Info"))
        self["key_blue"] = Label(_("Refresh"))
        self._init_rows()

        self["actions"] = ActionMap(
            ["OkCancelActions", "ColorActions", "NavigationActions"],
            {
                "cancel": self.exit,
                "red": self.exit,
                "green": self.select,
                "yellow": self.show_all_info,
                "blue": self.refresh,
                "ok": self.select,
                "left": self.page_left,
                "right": self.page_right,
            }, -1
        )

        self.timer = eTimer()
        self.timer.callback.append(self._start_load)
        self.timer.start(500, True)

    def _start_load(self):
        if self._loading:
            return
        self._loading = True
        self["status"].setText("Fetching DAB data from KingOfSat...")
        t = threading.Thread(target=self._load_in_thread, daemon=True)
        t.start()

    def _load_in_thread(self):
        try:
            self._dab_result = self.scraper.get_dab_transmissions()
            self._dab_error = None
        except Exception as e:
            self._dab_result = None
            self._dab_error = str(e)
        self._result_timer = eTimer()
        self._result_timer.callback.append(self._process_result)
        self._result_timer.start(100, True)

    def _process_result(self):
        self._loading = False
        if self._dab_error:
            self._clear_rows()
            self["status"].setText("Error: " + self._dab_error[:100])
            return
        if not self._dab_result:
            self._clear_rows()
            self["status"].setText("No DAB data found")
            return

        self.dab_data = self._dab_result
        groups = {}
        for mux in self.dab_data:
            groups.setdefault(mux.get("satellite", "Unknown"), []).append(mux)
        self.satellites = [(sat, groups[sat]) for sat in sorted(groups)]
        self._page_items = self.satellites
        self.page_index = 0
        self._render_page()

    def _render_page(self):
        total = len(self._page_items)
        pages = self._page_info(total)
        start = self.page_index * self.page_size
        page = self._page_items[start:start + self.page_size]
        lines = []
        for sat, muxes in page:
            stations = sum(len(m.get("stations", [])) for m in muxes)
            lines.append("%-42s   %4d muxes   %5d radio stations" % (sat[:42], len(muxes), stations))
        self._set_page_rows(lines)
        self["status"].setText("Page %d/%d   |   %d satellites   |   %d muxes   |   %d radio stations" % (
            self.page_index + 1, pages, len(self.satellites), len(self.dab_data),
            sum(len(m.get("stations", [])) for m in self.dab_data)))

    def select(self):
        if not self.satellites:
            return
        idx = self.page_index * self.page_size
        if idx >= len(self.satellites):
            return
        sat, items = self.satellites[idx]
        self.session.open(CiefpDabSatellite, sat, items)

    def refresh(self):
        try:
            from ..lib.utils import save_to_cache
            save_to_cache("dab_transmissions_v7", None)
        except Exception:
            pass
        self._clear_rows()
        self["status"].setText("Refreshing DAB data...")
        self.timer.start(100, True)

    def show_all_info(self):
        """Prikazuje informativni ekran sa listom svih satelita (bez selekcije)."""
        if not self.satellites:
            self.session.open(MessageBox, "No DAB data loaded yet.", MessageBox.TYPE_INFO)
            return
        self.session.open(CiefpDabAllInfo, self.satellites, len(self.dab_data))

    def exit(self):
        self.close()

class CiefpDabSatellite(Screen):
    """Prikaz svih DAB stanica za satelit, grupisano po mux-u/frekvenciji."""

    skin = """
    <screen name="CiefpDabSatellite" position="center,center" size="1920,1080" flags="wfNoBorder">
        <eLabel position="0,0" size="1920,1080" backgroundColor="#021f03" zPosition="-1" />
        <widget name="title" render="Label" position="100,50" size="1720,60" font="Regular;34"
                halign="center" valign="center" foregroundColor="#ffffff" backgroundColor="#050505" zPosition="2" />
        <widget name="list" position="100,120" size="1720,840" foregroundColor="#ffffff"
                backgroundColor="#1a1a1a" scrollbarMode="showNever" />
        <widget name="status" render="Label" position="100,970" size="1720,40" font="Regular;26"
                halign="left" valign="center" foregroundColor="#ffffff" backgroundColor="#050505" zPosition="1" />
        <widget name="key_red" position="100,1020" size="573,40" font="Bold;26" halign="center" valign="center"
                foregroundColor="#080808" backgroundColor="#a00000" zPosition="2" />
        <ePixmap pixmap="skin_default/buttons/red.png" position="100,1020" size="573,40" alphatest="blend" zPosition="1" />
        <widget name="key_green" position="673,1020" size="573,40" font="Bold;26" halign="center" valign="center"
                foregroundColor="#080808" backgroundColor="#00a000" zPosition="2" />
        <ePixmap pixmap="skin_default/buttons/green.png" position="673,1020" size="573,40" alphatest="blend" zPosition="1" />
        <widget name="key_yellow" position="1246,1020" size="573,40" font="Bold;26" halign="center" valign="center"
                foregroundColor="#080808" backgroundColor="#a09d00" zPosition="2" />
        <ePixmap pixmap="skin_default/buttons/yellow.png" position="1246,1020" size="573,40" alphatest="blend" zPosition="1" />
    </screen>
    """

    def __init__(self, session, sat_name, dab_items):
        Screen.__init__(self, session)
        self.session = session
        self.sat_name = sat_name
        self.dab_items = dab_items or []

        self["title"] = Label("DAB - " + sat_name)
        self["status"] = Label("")
        self["key_red"] = Label(_("Back"))
        self["key_green"] = Label(_("Next"))
        self["key_yellow"] = Label(_("Prev"))

        self["list"] = MenuList([], enableWrapAround=False, content=eListboxPythonMultiContent)
        self["list"].l.setItemHeight(35)
        self["list"].l.setFont(0, gFont("Regular", 26))
        self["list"].l.setFont(1, gFont("Bold", 26))
        self["list"].l.setFont(2, gFont("Regular", 26))

        # onemogući selection bar (kao u satellitelist)
        try:
            self["list"].selectionEnabled(0)
        except Exception:
            pass
        try:
            self["list"].l.setSelectionEnable(0)
        except Exception:
            pass
        try:
            self["list"].l.setSelectable(False)
        except Exception:
            pass

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

        self.all_items = []
        self.page_size = 24
        self.current_page = 0

        self._buildItems()
        self.showPage()

    # ------------------------------------------------------------------
    # BUILD LIST
    # ------------------------------------------------------------------
    def buildHeaderEntry(self):
        return [
            None,
            (eListboxPythonMultiContent.TYPE_TEXT, 10, 5, 700, 30, 1, RT_HALIGN_LEFT, "STATION NAME"),
            (eListboxPythonMultiContent.TYPE_TEXT, 720, 5, 160, 30, 1, RT_HALIGN_LEFT, "MODE"),
            (eListboxPythonMultiContent.TYPE_TEXT, 890, 5, 160, 30, 1, RT_HALIGN_LEFT, "CH ID"),
            (eListboxPythonMultiContent.TYPE_TEXT, 1060, 5, 220, 30, 1, RT_HALIGN_LEFT, "SID"),
            (eListboxPythonMultiContent.TYPE_TEXT, 1290, 5, 220, 30, 1, RT_HALIGN_LEFT, "BITRATE"),
            (eListboxPythonMultiContent.TYPE_TEXT, 1520, 5, 300, 30, 1, RT_HALIGN_LEFT, "UPDATE"),
        ]

    def buildStationEntry(self, station):
        return [
            None,
            (eListboxPythonMultiContent.TYPE_TEXT, 10, 5, 700, 35, 0, RT_HALIGN_LEFT,
             str(station.get("name", ""))[:60]),
            (eListboxPythonMultiContent.TYPE_TEXT, 720, 5, 160, 35, 0, RT_HALIGN_LEFT,
             str(station.get("audio_mode", ""))[:10]),
            (eListboxPythonMultiContent.TYPE_TEXT, 890, 5, 160, 35, 0, RT_HALIGN_LEFT,
             str(station.get("ch_id", ""))[:10]),
            (eListboxPythonMultiContent.TYPE_TEXT, 1060, 5, 220, 35, 0, RT_HALIGN_LEFT,
             str(station.get("sid", ""))[:15]),
            (eListboxPythonMultiContent.TYPE_TEXT, 1290, 5, 220, 35, 0, RT_HALIGN_LEFT,
             str(station.get("bitrate", ""))[:15]),
            (eListboxPythonMultiContent.TYPE_TEXT, 1520, 5, 300, 35, 0, RT_HALIGN_LEFT,
             str(station.get("update", ""))[:15]),
        ]

    def buildMuxHeaderEntry(self, freq, mux_name, ip, port, pid):
        """Separator između mux-eva - prikazuje frekvenciju, mux, IP:port, PID."""
        sep = "─────────── %s - %s - %s:%s (PID %s) ───────────" % (
            freq, mux_name, ip, port, pid)
        return [
            None,
            (eListboxPythonMultiContent.TYPE_TEXT,
             0, 5, 1800, 35, 2, RT_HALIGN_CENTER, sep)
        ]

    def _buildItems(self):
        if not self.dab_items:
            self.all_items = []
            self["status"].setText("%s | No DAB multiplexes" % self.sat_name)
            return

        items = [self.buildHeaderEntry()]

        total_stations = 0
        for mux in self.dab_items:
            stations = mux.get("stations", [])
            # separator za mux
            items.append(self.buildMuxHeaderEntry(
                mux.get("frequency", "N/A"),
                mux.get("mux_name", "DAB"),
                mux.get("ip_address", ""),
                mux.get("port", ""),
                mux.get("pid", ""),
            ))
            # stanice
            for st in stations:
                items.append(self.buildStationEntry(st))
                total_stations += 1

        self.all_items = items
        self["status"].setText("%s | %d muxes | %d stations" % (
            self.sat_name, len(self.dab_items), total_stations))

    # ------------------------------------------------------------------
    # PAGINATION
    # ------------------------------------------------------------------
    def showPage(self):
        if not self.all_items:
            self["list"].setList([])
            return

        start = self.current_page * self.page_size
        end = start + self.page_size

        self["list"].setList(self.all_items[start:end])

        try:
            self["list"].selectionEnabled(0)
        except Exception:
            pass
        try:
            self["list"].l.setSelectionEnable(0)
        except Exception:
            pass
        try:
            self["list"].l.setSelectable(False)
        except Exception:
            pass

        total_pages = max(1, (len(self.all_items) + self.page_size - 1) // self.page_size)
        self["status"].setText(
            "%s | Page %d/%d | Rows %d-%d" % (
                self.sat_name, self.current_page + 1, total_pages,
                start + 1, min(end, len(self.all_items)))
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

class CiefpDabAllInfo(Screen):
    """Informativni ekran - svi sateliti sa frekvencijama i brojem stanica."""

    skin = """
    <screen name="CiefpDabAllInfo" position="center,center" size="1920,1080" flags="wfNoBorder">
        <eLabel position="0,0" size="1920,1080" backgroundColor="#021f03" zPosition="-1" />
        <widget name="title" render="Label" position="100,50" size="1720,60" font="Regular;34"
                halign="center" valign="center" foregroundColor="#ffffff" backgroundColor="#050505" zPosition="2" />
        <widget name="list" position="100,120" size="1720,840" foregroundColor="#ffffff"
                backgroundColor="#1a1a1a" scrollbarMode="showNever" />
        <widget name="status" render="Label" position="100,970" size="1720,40" font="Regular;26"
                halign="left" valign="center" foregroundColor="#ffffff" backgroundColor="#050505" zPosition="1" />
        <widget name="key_red" position="100,1020" size="573,40" font="Bold;26" halign="center" valign="center"
                foregroundColor="#080808" backgroundColor="#a00000" zPosition="2" />
        <ePixmap pixmap="skin_default/buttons/red.png" position="100,1020" size="573,40" alphatest="blend" zPosition="1" />
        <widget name="key_green" position="673,1020" size="573,40" font="Bold;26" halign="center" valign="center"
                foregroundColor="#080808" backgroundColor="#00a000" zPosition="2" />
        <ePixmap pixmap="skin_default/buttons/green.png" position="673,1020" size="573,40" alphatest="blend" zPosition="1" />
        <widget name="key_yellow" position="1246,1020" size="573,40" font="Bold;26" halign="center" valign="center"
                foregroundColor="#080808" backgroundColor="#a09d00" zPosition="2" />
        <ePixmap pixmap="skin_default/buttons/yellow.png" position="1246,1020" size="573,40" alphatest="blend" zPosition="1" />
    </screen>
    """

    def __init__(self, session, satellites, total_muxes):
        Screen.__init__(self, session)
        self.session = session
        self.satellites = satellites or []
        self.total_muxes = total_muxes

        self["title"] = Label("DAB - All Satellites Info")
        self["status"] = Label("")
        self["key_red"] = Label(_("Close"))
        self["key_green"] = Label(_("Next"))
        self["key_yellow"] = Label(_("Prev"))

        self["list"] = MenuList([], enableWrapAround=False, content=eListboxPythonMultiContent)
        self["list"].l.setItemHeight(36)
        self["list"].l.setFont(0, gFont("Regular", 26))
        self["list"].l.setFont(1, gFont("Bold", 26))
        self["list"].l.setFont(2, gFont("Regular", 26))

        # onemogući selection bar
        try:
            self["list"].selectionEnabled(0)
        except Exception:
            pass
        try:
            self["list"].l.setSelectionEnable(0)
        except Exception:
            pass
        try:
            self["list"].l.setSelectable(False)
        except Exception:
            pass

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

        self.all_items = []
        self.page_size = 24
        self.current_page = 0

        self._buildItems()
        self.showPage()

    # ------------------------------------------------------------------
    # BUILD LIST
    # ------------------------------------------------------------------
    def buildHeaderEntry(self):
        return [
            None,
            (eListboxPythonMultiContent.TYPE_TEXT, 10, 5, 900, 30, 1, RT_HALIGN_LEFT, "SATELLITE / FREQUENCY"),
            (eListboxPythonMultiContent.TYPE_TEXT, 920, 5, 250, 30, 1, RT_HALIGN_LEFT, "MUXES"),
            (eListboxPythonMultiContent.TYPE_TEXT, 1180, 5, 300, 30, 1, RT_HALIGN_LEFT, "RADIO STATIONS"),
        ]

    def buildSatelliteEntry(self, sat_name, mux_count, station_count):
        """Naslov satelita - bold, sa ukupnim brojem mux-eva i stanica."""
        return [
            None,
            (eListboxPythonMultiContent.TYPE_TEXT, 10, 5, 900, 35, 1, RT_HALIGN_LEFT,
             str(sat_name)[:80]),
            (eListboxPythonMultiContent.TYPE_TEXT, 920, 5, 250, 35, 1, RT_HALIGN_LEFT,
             "%d muxes" % mux_count),
            (eListboxPythonMultiContent.TYPE_TEXT, 1180, 5, 300, 35, 1, RT_HALIGN_LEFT,
             "%d radio stations" % station_count),
        ]

    def buildFrequencyEntry(self, freq, sr, fec, standard, modulation, station_count):
        """Frekvencija - regular, uvucena, sa SR/FEC/standard/modulacijom."""
        freq_line = "- %s  %s %s %s %s" % (freq, sr, fec, standard, modulation)
        return [
            None,
            (eListboxPythonMultiContent.TYPE_TEXT, 30, 5, 880, 35, 0, RT_HALIGN_LEFT,
             freq_line[:75]),
            (eListboxPythonMultiContent.TYPE_TEXT, 920, 5, 250, 35, 0, RT_HALIGN_LEFT, ""),
            (eListboxPythonMultiContent.TYPE_TEXT, 1180, 5, 300, 35, 0, RT_HALIGN_LEFT,
             "%d" % station_count),
        ]

    def _buildItems(self):
        items = [self.buildHeaderEntry()]

        for sat_name, muxes in self.satellites:
            # Ukupno za satelit
            total_st = sum(len(m.get("stations", [])) for m in muxes)
            items.append(self.buildSatelliteEntry(sat_name, len(muxes), total_st))

            # Grupisanje mux-eva po frekvenciji (jer na istoj freq može biti više mux-eva)
            freq_groups = {}
            for mux in muxes:
                freq = mux.get("frequency", "N/A")
                if freq not in freq_groups:
                    freq_groups[freq] = {
                        "muxes": [],
                        "stations": 0,
                        "sr": "",
                        "fec": "",
                        "standard": "",
                        "modulation": "",
                    }
                freq_groups[freq]["muxes"].append(mux)
                freq_groups[freq]["stations"] += len(mux.get("stations", []))
                # Uzmi SR/FEC/standard/modulaciju iz prvog mux-a
                if not freq_groups[freq]["sr"]:
                    freq_groups[freq]["sr"] = mux.get("sr", "")
                    freq_groups[freq]["fec"] = mux.get("fec", "")
                    freq_groups[freq]["standard"] = mux.get("standard", "")
                    freq_groups[freq]["modulation"] = mux.get("modulation", "")

            # Prikaži svaku frekvenciju
            for freq in sorted(freq_groups.keys()):
                fg = freq_groups[freq]
                items.append(self.buildFrequencyEntry(
                    freq,
                    fg["sr"],
                    fg["fec"],
                    fg["standard"],
                    fg["modulation"],
                    fg["stations"],
                ))

        self.all_items = items
        self["status"].setText("%d satellites | %d muxes | %d radio stations" % (
            len(self.satellites), self.total_muxes,
            sum(len(m.get("stations", [])) for _, muxes in self.satellites for m in muxes)))

    # ------------------------------------------------------------------
    # PAGINATION
    # ------------------------------------------------------------------
    def showPage(self):
        if not self.all_items:
            self["list"].setList([])
            return

        start = self.current_page * self.page_size
        end = start + self.page_size

        self["list"].setList(self.all_items[start:end])

        try:
            self["list"].selectionEnabled(0)
        except Exception:
            pass
        try:
            self["list"].l.setSelectionEnable(0)
        except Exception:
            pass
        try:
            self["list"].l.setSelectable(False)
        except Exception:
            pass

        total_pages = max(1, (len(self.all_items) + self.page_size - 1) // self.page_size)
        self["status"].setText(
            "Page %d/%d   |   %d satellites   |   %d muxes   |   %d radio stations" % (
                self.current_page + 1, total_pages,
                len(self.satellites), self.total_muxes,
                sum(len(m.get("stations", [])) for _, muxes in self.satellites for m in muxes))
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