# -*- coding: utf-8 -*-
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
from Components.Pixmap import Pixmap
from enigma import eTimer
import textwrap
import traceback
from ..lib.scraper import KingOfSatScraper

class CiefpNewsSingleScreen(Screen):
    skin = """    <screen name="CiefpNewsSingleScreen" position="center,center" size="1920,1080" title="KingOfSat News" flags="wfNoBorder">
        <!-- TITLE -->
        <widget name="title" render="Label" position="100,100" size="1720,60" font="Regular;34" halign="center" valign="center" foregroundColor="#ffffff" backgroundColor="#050505" zPosition="2" />

        <!-- PANEL -->
        <eLabel position="0,0" size="1920,1080" backgroundColor="#021f03" zPosition="-1" />

        <!-- GLAVNI PRIKAZ VESTI (page) -->
        <widget name="news" position="100,180" size="1720,780" foregroundColor="#ffffff" backgroundColor="#1a1a1a" font="Regular;28" />

        <!-- STATUS BAR -->
        <widget name="status" render="Label" position="100,980" size="1720,40" font="Regular;26" halign="left" valign="center" foregroundColor="#ffffff" backgroundColor="#050505" zPosition="1" />

        <!-- Red - Exit -->
        <widget name="key_red" position="100,1030" size="430,40" font="Bold;26" halign="center" valign="center" foregroundColor="#080808" backgroundColor="#a00000" zPosition="2" />
        <ePixmap pixmap="skin_default/buttons/red.png" position="100,1030" size="430,40" alphatest="blend" zPosition="1" />

        <!-- Green - Next -->
        <widget name="key_green" position="530,1030" size="430,40" font="Bold;26" halign="center" valign="center" foregroundColor="#080808" backgroundColor="#00a000" zPosition="2" />
        <ePixmap pixmap="skin_default/buttons/green.png" position="530,1030" size="430,40" alphatest="blend" zPosition="1" />

        <!-- Yellow - Prev -->
        <widget name="key_yellow" position="960,1030" size="430,40" font="Bold;26" halign="center" valign="center" foregroundColor="#080808" backgroundColor="#a0a000" zPosition="2" />
        <ePixmap pixmap="skin_default/buttons/yellow.png" position="960,1030" size="430,40" alphatest="blend" zPosition="1" />

        <!-- Blue - Refresh -->
        <widget name="key_blue" position="1390,1030" size="430,40" font="Bold;26" halign="center" valign="center" foregroundColor="#080808" backgroundColor="#0000a0" zPosition="2" />
        <ePixmap pixmap="skin_default/buttons/blue.png" position="1390,1030" size="430,40" alphatest="blend" zPosition="1" />
    </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session

        self["title"] = Label("KingOfSat News")
        self["news"] = ScrollLabel("")  # multi-line, bez skrolovanja
        self["status"] = Label("Loading news... Please wait")

        self["key_red"] = Label(_("Exit"))
        self["key_green"] = Label(_("Next"))
        self["key_yellow"] = Label(_("Prev"))
        self["key_blue"] = Label(_("Refresh"))

        # pagination state
        self.pages = []
        self.current_page = 0
        self.lines_per_page = 22  # za font 28 i visinu 780px

        self["actions"] = ActionMap(
            ["OkCancelActions", "ColorActions", "NavigationActions"],
            {
                "cancel": self.exit,
                "red": self.exit,

                "green": self.nextPage,
                "yellow": self.prevPage,
                "blue": self.refresh,

                "right": self.nextPage,
                "left": self.prevPage,
                "pageDown": self.nextPage,
                "pageUp": self.prevPage,
            },
            -1
        )

        self.scraper = KingOfSatScraper()
        self.timer = eTimer()
        self.timer.callback.append(self.load_news)
        self.timer.start(100, True)

    def parse_date(self, date_str):
        """Pretvara string datuma u tuple za sortiranje"""
        try:
            parts = date_str.split()
            if len(parts) >= 4:
                day = int(parts[1])
                month_str = parts[2]
                year = int(parts[3])

                month_map = {
                    'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
                    'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12
                }
                month = month_map.get(month_str, 1)
                return (year, month, day)
        except:
            pass
        return (0, 0, 0)

    def _make_pages(self, text):
        lines = text.split("\n")
        pages = []
        buf = []
        for line in lines:
            buf.append(line)
            if len(buf) >= self.lines_per_page:
                pages.append("\n".join(buf).rstrip())
                buf = []
        if buf:
            pages.append("\n".join(buf).rstrip())
        return pages if pages else [""]

    def _show_page(self):
        if not self.pages:
            self["news"].setText("")
            self["status"].setText("No news available")
            return

        if self.current_page < 0:
            self.current_page = 0
        if self.current_page > len(self.pages) - 1:
            self.current_page = len(self.pages) - 1

        self["news"].setText(self.pages[self.current_page])
        self["status"].setText("Page %d/%d" % (self.current_page + 1, len(self.pages)))

    def nextPage(self):
        if not self.pages:
            return
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self._show_page()

    def prevPage(self):
        if not self.pages:
            return
        if self.current_page > 0:
            self.current_page -= 1
            self._show_page()

    def load_news(self):
        try:
            self["status"].setText("Fetching news from KingOfSat...")
            news_data = self.scraper.get_news()

            if isinstance(news_data, str):
                if not news_data or news_data.strip() == "":
                    formatted_text = "No news available or empty response from server."
                else:
                    formatted_text = self.format_raw_text(news_data)

            elif isinstance(news_data, list):
                if not news_data:
                    formatted_text = "No news items found."
                else:
                    news_by_date = self.convert_list_to_grouped(news_data)
                    formatted_text = self.format_news_text(news_by_date)

            elif isinstance(news_data, dict):
                if 'error' in news_data:
                    formatted_text = "Error: %s" % (news_data.get('error', 'Unknown error'),)
                else:
                    formatted_text = self.format_dict(news_data)

            else:
                formatted_text = "Unknown news format: %s\n\nData: %s..." % (type(news_data), str(news_data)[:500])

            self.pages = self._make_pages(formatted_text)
            self.current_page = 0
            self._show_page()

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.pages = self._make_pages("Error loading news:\n%s\n\nDetails:\n%s" % (str(e), error_details))
            self.current_page = 0
            self._show_page()

    def format_raw_text(self, text):
        """Formatira raw tekst za prikaz"""
        if not text:
            return "No text available"

        formatted = ""
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if any(year in line for year in ['2024', '2025', '2026', '2027']):
                formatted += "\n\n" + ("=" * 80) + "\n"
                formatted += (" " * ((80 - len(line)) // 2)) + line + "\n"
                formatted += ("=" * 80) + "\n\n"
            elif '°E' in line or '°W' in line:
                formatted += "\n" + line + "\n"
                formatted += ("-" * 60) + "\n"
            else:
                wrapped = textwrap.fill(line, width=75)
                formatted += wrapped + "\n\n"

        return formatted.strip()

    def format_dict(self, data_dict):
        """Formatira dictionary za prikaz"""
        if not data_dict:
            return "Empty dictionary"

        formatted = ""
        for key, value in data_dict.items():
            formatted += "\n%s:\n" % key
            formatted += ("-" * 40) + "\n"

            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        for k, v in item.items():
                            formatted += "  %s: %s\n" % (k, v)
                        formatted += "\n"
                    else:
                        formatted += "  %s\n" % item
            elif isinstance(value, dict):
                for k, v in value.items():
                    formatted += "  %s: %s\n" % (k, v)
            else:
                formatted += "  %s\n" % value

            formatted += "\n"

        return formatted.strip()

    def convert_list_to_grouped(self, news_list):
        """Konvertuje listu vesti u grupisani format"""
        news_by_date = {}

        for item in news_list:
            if not isinstance(item, dict):
                continue

            date = item.get('date', 'Unknown Date')
            satellite = item.get('satellite', 'Unknown Satellite')

            if date not in news_by_date:
                news_by_date[date] = {}
            if satellite not in news_by_date[date]:
                news_by_date[date][satellite] = []

            news_by_date[date][satellite].append({
                'time': item.get('time', '00h00'),
                'channel': item.get('channel', 'Unknown'),
                'text': item.get('description', item.get('full_text', item.get('text', '')))
            })

        return news_by_date

    def format_news_text(self, news_by_date):
        """Formatira vesti za prikaz"""
        if not news_by_date:
            return "No news available."

        text = ""
        sorted_dates = sorted(news_by_date.keys(), key=self.parse_date, reverse=True)

        for date in sorted_dates:
            text += "\n\n" + ("=" * 80) + "\n"
            text += (" " * ((80 - len(date)) // 2)) + date + "\n"
            text += ("=" * 80) + "\n\n"

            sat_news = news_by_date[date]
            sorted_satellites = sorted(sat_news.keys())

            for satellite in sorted_satellites:
                items = sat_news[satellite]
                if not items:
                    continue

                text += "\n%s\n" % satellite
                text += ("-" * 60) + "\n"

                for item in items:
                    time_text = item.get('time', '')
                    channel = item.get('channel', '')
                    desc = item.get('text', '')

                    if time_text and channel:
                        text += "(%s) %s\n" % (time_text, channel)
                    elif channel:
                        text += "%s\n" % channel

                    if desc:
                        wrapped_desc = textwrap.fill(desc, width=75)
                        lines = wrapped_desc.split('\n')
                        if len(lines) > 3:
                            desc_display = "\n".join(lines[:3]) + "..."
                        else:
                            desc_display = wrapped_desc

                        text += "  %s\n\n" % desc_display

        return text.strip()

    def refresh(self):
        self["status"].setText("Refreshing news...")
        self["news"].setText("")
        self.pages = []
        self.current_page = 0
        self.timer.start(100, True)

    def exit(self):
        self.close()
