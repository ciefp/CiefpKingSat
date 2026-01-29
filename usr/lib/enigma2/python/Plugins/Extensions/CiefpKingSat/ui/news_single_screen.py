# -*- coding: utf-8 -*-
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
from Components.Pixmap import Pixmap
from enigma import eTimer
import textwrap
from ..lib.scraper import KingOfSatScraper

class CiefpNewsSingleScreen(Screen):
    skin = """
    <screen name="CiefpNewsSingleScreen" position="center,center" size="1920,1080" title="KingOfSat News" flags="wfNoBorder">
        <!-- TITLE -->
        <widget name="title" render="Label" position="100,100" size="1720,60" font="Regular;34" halign="center" valign="center" foregroundColor="#ffffff" backgroundColor="#1a1a1a" zPosition="2" />
        
        <!-- GLAVNI PRIKAZ VESTI -->
        <widget name="news" position="100,180" size="1720,780" font="Regular;28" />
        
        <!-- STATUS BAR -->
        <widget name="status" render="Label" position="100,980" size="1720,40" font="Regular;26" halign="left" valign="center" foregroundColor="#cccccc" backgroundColor="#000000" zPosition="1" />
        
        <!-- Crveni taster - Back -->
        <widget name="key_red" position="100,1030" size="300,40" font="Bold;26" halign="center" valign="center" foregroundColor="#080808" backgroundColor="#a00000" zPosition="2" />
        <ePixmap pixmap="skin_default/buttons/red.png" position="100,1030" size="300,40" alphatest="blend" zPosition="1" />
        
        <!-- Zeleni taster - Refresh -->
        <widget name="key_green" position="500,1030" size="300,40" font="Bold;26" halign="center" valign="center" foregroundColor="#080808" backgroundColor="#00a000" zPosition="2" />
        <ePixmap pixmap="skin_default/buttons/green.png" position="500,1030" size="300,40" alphatest="blend" zPosition="1" />
    </screen>
    """

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session

        self["title"] = Label("KingOfSat News")
        self["news"] = ScrollLabel("")
        self["status"] = Label("Loading news... Please wait")
        self["key_red"] = Label(_("Exit"))
        self["key_green"] = Label(_("Refresh"))

        self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "NavigationActions"], {
            "cancel": self.exit,
            "red": self.exit,
            "green": self.refresh,
            "up": self["news"].pageUp,
            "down": self["news"].pageDown,
            "left": self["news"].pageUp,
            "right": self["news"].pageDown,
            "pageUp": self["news"].pageUp,
            "pageDown": self["news"].pageDown
        }, -1)

        self.scraper = KingOfSatScraper()
        self.timer = eTimer()
        self.timer.callback.append(self.load_news)
        self.timer.start(100, True)

    def parse_date(self, date_str):
        """Pretvara string datuma u tuple (godina, mesec, dan) za sortiranje"""
        try:
            # Primer: "Thursday 29 January 2026"
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

    def format_news_text(self, news_by_date):
        """Formatira vesti za prikaz"""
        if not news_by_date:
            return "No news available or error loading data."
        
        text = ""
        
        # Sortiraj datume hronološki (najnovije prvo)
        sorted_dates = sorted(news_by_date.keys(), key=self.parse_date, reverse=True)
        
        for date in sorted_dates:
            # DODAJ DATUM kao header (centrirano)
            text += f"\n\n{'='*80}\n"
            text += f"{' ' * ((80 - len(date)) // 2)}{date}\n"
            text += f"{'='*80}\n\n"
            
            sat_news = news_by_date[date]
            
            # Sortiraj satelite abecedno
            sorted_satellites = sorted(sat_news.keys())
            
            for satellite in sorted_satellites:
                items = sat_news[satellite]
                if not items:
                    continue
                
                # DODAJ SATELIT kao sub-header (levo poravnato)
                text += f"\n{satellite}\n"
                text += f"{'-'*60}\n"
                
                # Dodaj sve vesti za ovaj satelit
                for item in items:
                    time_text = item['time']
                    channel = item['channel']
                    desc = item['text']
                    
                    # Formatiraj prvi red: (vreme) Channel Name
                    first_line = f"({time_text}) {channel}"
                    text += f"{first_line}\n"
                    
                    # Formatiraj opis u maksimalno 2 reda po 75 karaktera
                    wrapped_desc = textwrap.fill(desc, width=75)
                    lines = wrapped_desc.split('\n')
                    
                    # Ograniči na 2 reda, dodaj "..." ako je duže
                    if len(lines) > 2:
                        desc_display = lines[0] + '\n' + lines[1][:72] + '...'
                    else:
                        desc_display = wrapped_desc
                    
                    text += f"  {desc_display}\n\n"
        
        return text.strip()

    def convert_list_to_grouped(self, news_list):
        """Konvertuje listu vesti u grupisani format po datumu i satelitu"""
        news_by_date = {}
        
        for item in news_list:
            date = item.get('date', 'Unknown Date')
            satellite = item.get('satellite', 'Unknown Satellite')
            
            # Kreiraj strukturu ako ne postoji
            if date not in news_by_date:
                news_by_date[date] = {}
            if satellite not in news_by_date[date]:
                news_by_date[date][satellite] = []
            
            # Dodaj vest
            news_by_date[date][satellite].append({
                'time': item.get('time', '00h00'),
                'channel': item.get('channel', 'Unknown'),
                'text': item.get('description', item.get('full_text', ''))
            })
        
        return news_by_date

    def load_news(self):
        try:
            self["status"].setText("Fetching news from KingOfSat...")
            
            # Uzmi vesti - ovo vraća LISTU
            news_items = self.scraper.get_news()
            
            if not news_items:
                self["news"].setText("No news found or error loading data.")
                self["status"].setText("No news available")
                return
            
            # Konvertuj listu u grupisani format
            news_by_date = self.convert_list_to_grouped(news_items)
            
            # Formatiraj za prikaz
            formatted_text = self.format_news_text(news_by_date)
            
            # Broj vesti
            total_items = 0
            for date in news_by_date:
                for satellite in news_by_date[date]:
                    total_items += len(news_by_date[date][satellite])
            
            self["news"].setText(formatted_text)
            self["status"].setText(f"Loaded {total_items} news items from {len(news_by_date)} dates")
            
        except Exception as e:
            self["news"].setText(f"Error loading news:\n{str(e)}")
            self["status"].setText("Error occurred")

    def refresh(self):
        self["status"].setText("Refreshing news...")
        self["news"].setText("")
        self.timer.start(100, True)

    def exit(self):
        self.close()