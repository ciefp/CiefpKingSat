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

    def load_news(self):
        try:
            self["status"].setText("Fetching news from KingOfSat...")
            
            # DEBUG: Proveri šta vraća get_news()
            news_data = self.scraper.get_news()
            
            # DEBUG ispis
            debug_info = f"DEBUG: Type of news_data: {type(news_data)}\n"
            if isinstance(news_data, str):
                debug_info += f"DEBUG: String length: {len(news_data)}\n"
                debug_info += f"DEBUG: First 500 chars: {news_data[:500]}\n"
            elif isinstance(news_data, (list, dict)):
                debug_info += f"DEBUG: Length/size: {len(news_data)}\n"
            
            print(debug_info)  # Za logovanje
            
            # Proveri tip podataka
            if isinstance(news_data, str):
                # Ako je string, prikaži direktno
                if not news_data or news_data.strip() == "":
                    self["news"].setText("No news available or empty response from server.")
                    self["status"].setText("No news data")
                else:
                    # Formatiraj string za bolji prikaz
                    formatted_text = self.format_raw_text(news_data)
                    self["news"].setText(formatted_text)
                    self["status"].setText(f"Loaded news (raw text)")
                    
            elif isinstance(news_data, list):
                # Ako je lista, obradi kao strukturirane podatke
                if not news_data:
                    self["news"].setText("No news items found.")
                    self["status"].setText("No news available")
                    return
                
                # Konvertuj listu u grupisani format
                news_by_date = self.convert_list_to_grouped(news_data)
                
                # Formatiraj za prikaz
                formatted_text = self.format_news_text(news_by_date)
                
                # Broj vesti
                total_items = 0
                for date in news_by_date:
                    for satellite in news_by_date[date]:
                        total_items += len(news_by_date[date][satellite])
                
                self["news"].setText(formatted_text)
                self["status"].setText(f"Loaded {total_items} news items from {len(news_by_date)} dates")
                
            elif isinstance(news_data, dict):
                # Ako je dictionary, proveri strukturu
                if 'error' in news_data:
                    self["news"].setText(f"Error: {news_data.get('error', 'Unknown error')}")
                    self["status"].setText("Error loading news")
                else:
                    # Prikaži dictionary kao tekst
                    formatted_text = self.format_dict(news_data)
                    self["news"].setText(formatted_text)
                    self["status"].setText("News data (dictionary format)")
                    
            else:
                # Nepoznat format
                self["news"].setText(f"Unknown news format: {type(news_data)}\n\nData: {str(news_data)[:500]}...")
                self["status"].setText("Unknown data format")
            
        except Exception as e:
            error_details = traceback.format_exc()
            self["news"].setText(f"Error loading news:\n{str(e)}\n\nDetails:\n{error_details}")
            self["status"].setText("Error occurred")

    def format_raw_text(self, text):
        """Formatira raw tekst za prikaz"""
        if not text:
            return "No text available"
        
        # Formatiraj tekst
        formatted = ""
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Ako linija izgleda kao datum (sadrži godinu)
            if any(year in line for year in ['2024', '2025', '2026', '2027']):
                formatted += f"\n\n{'='*80}\n"
                formatted += f"{' ' * ((80 - len(line)) // 2)}{line}\n"
                formatted += f"{'='*80}\n\n"
            # Ako linija izgleda kao satelit
            elif '°E' in line or '°W' in line:
                formatted += f"\n{line}\n"
                formatted += f"{'-'*60}\n"
            else:
                # Obican tekst
                wrapped = textwrap.fill(line, width=75)
                formatted += f"{wrapped}\n\n"
        
        return formatted.strip()

    def format_dict(self, data_dict):
        """Formatira dictionary za prikaz"""
        if not data_dict:
            return "Empty dictionary"
        
        formatted = ""
        for key, value in data_dict.items():
            formatted += f"\n{key}:\n"
            formatted += f"{'-'*40}\n"
            
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        for k, v in item.items():
                            formatted += f"  {k}: {v}\n"
                        formatted += "\n"
                    else:
                        formatted += f"  {item}\n"
            elif isinstance(value, dict):
                for k, v in value.items():
                    formatted += f"  {k}: {v}\n"
            else:
                formatted += f"  {value}\n"
            
            formatted += "\n"
        
        return formatted.strip()

    def convert_list_to_grouped(self, news_list):
        """Konvertuje listu vesti u grupisani format"""
        news_by_date = {}
        
        for item in news_list:
            # Proveri da li je item dictionary
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
        
        # Sortiraj datume
        sorted_dates = sorted(news_by_date.keys(), key=self.parse_date, reverse=True)
        
        for date in sorted_dates:
            text += f"\n\n{'='*80}\n"
            text += f"{' ' * ((80 - len(date)) // 2)}{date}\n"
            text += f"{'='*80}\n\n"
            
            sat_news = news_by_date[date]
            sorted_satellites = sorted(sat_news.keys())
            
            for satellite in sorted_satellites:
                items = sat_news[satellite]
                if not items:
                    continue
                
                text += f"\n{satellite}\n"
                text += f"{'-'*60}\n"
                
                for item in items:
                    time_text = item.get('time', '')
                    channel = item.get('channel', '')
                    desc = item.get('text', '')
                    
                    if time_text and channel:
                        text += f"({time_text}) {channel}\n"
                    elif channel:
                        text += f"{channel}\n"
                    
                    if desc:
                        wrapped_desc = textwrap.fill(desc, width=75)
                        lines = wrapped_desc.split('\n')
                        
                        if len(lines) > 2:
                            desc_display = lines[0] + '\n' + lines[1][:72] + '...'
                        else:
                            desc_display = wrapped_desc
                        
                        text += f"  {desc_display}\n\n"
        
        return text.strip()

    def refresh(self):
        self["status"].setText("Refreshing news...")
        self["news"].setText("")
        self.timer.start(100, True)

    def exit(self):
        self.close()