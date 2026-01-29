# -*- coding: utf-8 -*-
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.ScrollLabel import ScrollLabel
from Components.Label import Label
from enigma import eTimer
from ..lib.scraper import KingOfSatScraper
import re

class CiefpSatelliteList(Screen):
    skin = """
    <screen name="CiefpSatelliteList" position="center,center" size="1920,1080" title="Satellite Channels" flags="wfNoBorder">
        <!-- TITLE -->
        <widget name="title" render="Label" position="100,100" size="1720,60" font="Regular;34" halign="center" valign="center" foregroundColor="#ffffff" backgroundColor="#1a1a1a" zPosition="2" />
        <widget name="channels" position="100,150" size="1720,780" font="Regular;28" />
        <widget name="status" position="100,950" size="1720,40" font="Regular;26" halign="left" valign="center" foregroundColor="#cccccc" />
        <ePixmap pixmap="skin_default/buttons/red.png" position="100,1000" size="300,40" alphatest="on" />
        <!-- Crveni taster - Back -->
        <widget name="key_red" position="100,1000" size="300,60" font="Bold;26" halign="center" valign="center" foregroundColor="#080808" backgroundColor="#a00000" zPosition="2" />
        <!-- Pozadina za crveni taster  -->
        <ePixmap pixmap="skin_default/buttons/red.png" position="100,1000" size="300,60" alphatest="blend" zPosition="1" />
    </screen>
    """
    
    def __init__(self, session, sat_name, sat_url):
        Screen.__init__(self, session)
        self.session = session
        self.sat_name = sat_name
        self.sat_url = sat_url
        
        self["channels"] = ScrollLabel("")
        self["title"] = Label(f"Channels on {sat_name}")
        self["status"] = Label("Loading... Please wait")
        self["key_red"] = Label(_("Exit"))
        
        self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "NavigationActions"], {
            "cancel": self.exit,
            "red": self.exit,
            "up": self["channels"].pageUp,
            "down": self["channels"].pageDown,
            "left": self["channels"].pageUp,
            "right": self["channels"].pageDown
        }, -1)
        
        self.scraper = KingOfSatScraper()
        self.timer = eTimer()
        self.timer.callback.append(self.loadChannels)
        self.timer.start(100, True)

    # U metodi loadChannels u satellitelist.py promeni formatiranje:
    def loadChannels(self):
        try:
            channels = self.scraper.get_satellite_channels(self.sat_url)
            if not channels:
                self["channels"].setText("No channels found or parsing error")
                self["status"].setText("Error loading data")
                return

            text = ""
            current_freq = None
            tp_counter = 0

            # Optimizovane širine kolona (smanjene za bolji prikaz)
            COLUMNS = {
                'name': {'start': 0, 'end': 40, 'title': 'CHANNEL NAME'},
                'country': {'start': 40, 'end': 55, 'title': 'COUNTRY'},
                'category': {'start': 55, 'end': 75, 'title': 'CATEGORY'},
                'package': {'start': 75, 'end': 140, 'title': 'PACKAGE'},
                'encryption': {'start': 140, 'end': 180, 'title': 'ENCRYPTION'}
            }

            def calculate_total_length():
                total = 0
                last_end = 0
                for col_name, col_info in COLUMNS.items():
                    if last_end < col_info['start']:
                        total += (col_info['start'] - last_end)
                    total += (col_info['end'] - col_info['start'])
                    last_end = col_info['end']
                return total

            TOTAL_LENGTH = calculate_total_length()
            # Funkcija za skraćivanje teksta sa "..." ako je predugačak
            def truncate(text, max_len, add_ellipsis=True):  # DODAJ : na kraju
                if not text:
                    return ""
                if len(text) <= max_len:
                    return text
                if add_ellipsis and max_len > 3:
                    return text[:max_len - 3] + "..."
                return text[:max_len]

            for channel in channels:
                freq_header = channel.get('frequency', 'N/A')

                if freq_header != current_freq:
                    current_freq = freq_header
                    tp_counter += 1

                    if tp_counter > 1:
                        text += "\n\n"

                    text += f"{current_freq}\n"

                    # Dodaj header liniju za svaki transponder
                    header_line = ""
                    last_end = 0

                    for col_name, col_info in COLUMNS.items():
                        width = col_info['end'] - col_info['start']

                        # Dodaj razmak između kolona ako postoji
                        if last_end < col_info['start']:
                            space_count = col_info['start'] - last_end
                            header_line += " " * space_count

                        # Header tekst
                        header_text = truncate(col_info['title'], width, False)
                        header_line += f"{header_text:<{width}}"

                        last_end = col_info['end']  # ISPRAVLJENO: end umesto end()

                    text += header_line + "\n"
                    # SEPARATOR - pokriva celu širinu header linije
                    text += "-" * TOTAL_LENGTH + "\n"  # Ili "--" * (TOTAL_LENGTH // 2)

                line = ""
                last_end = 0

                # Naziv kanala
                name = (channel.get('name', 'Unknown') or '').strip()
                width = COLUMNS['name']['end'] - COLUMNS['name']['start']
                name = truncate(name, width)
                line += f"{name:<{width}}"
                last_end = COLUMNS['name']['end']  # ISPRAVLJENO

                # Država
                country = (channel.get('country', '-') or '').strip()
                width = COLUMNS['country']['end'] - COLUMNS['country']['start']
                if last_end < COLUMNS['country']['start']:
                    line += " " * (COLUMNS['country']['start'] - last_end)
                country = truncate(country, width)
                line += f"{country:<{width}}"
                last_end = COLUMNS['country']['end']  # ISPRAVLJENO

                # Kategorija
                category = (channel.get('category', '-') or '').strip()
                width = COLUMNS['category']['end'] - COLUMNS['category']['start']
                if last_end < COLUMNS['category']['start']:
                    line += " " * (COLUMNS['category']['start'] - last_end)
                category = truncate(category, width)
                line += f"{category:<{width}}"
                last_end = COLUMNS['category']['end']  # ISPRAVLJENO

                # Paket
                package = channel.get('package', '-') or "-"
                width = COLUMNS['package']['end'] - COLUMNS['package']['start']
                if last_end < COLUMNS['package']['start']:
                    line += " " * (COLUMNS['package']['start'] - last_end)
                package = truncate(package, width)
                line += f"{package:<{width}}"
                last_end = COLUMNS['package']['end']  # ISPRAVLJENO

                # Enkripcija - POBOLJŠANJE
                encryption = ""
                enc = channel.get('encryption', '')
                if isinstance(enc, str):
                    enc_lower = enc.lower().strip()
                    if enc_lower in ['clear', 'fta', 'free', '0']:
                        encryption = "FTA"
                    elif enc_lower and enc_lower != 'undefined':
                        # Prikaži skraćenu verziju enkripcije
                        # Ukloni duplikate i skrati
                        if 'conax' in enc_lower and 'nagravision' in enc_lower:
                            encryption = "Conax/Nagra"
                        elif 'videoguard' in enc_lower:
                            encryption = "VideoGuard"
                        elif 'cryptoworks' in enc_lower:
                            encryption = "CryptoWorks"
                        else:
                            encryption = truncate(enc, 35)

                width = COLUMNS['encryption']['end'] - COLUMNS['encryption']['start']  # ISPRAVLJENO
                if last_end < COLUMNS['encryption']['start']:
                    line += " " * (COLUMNS['encryption']['start'] - last_end)
                encryption = truncate(encryption, width)
                line += f"{encryption:<{width}}"

                text += line + "\n"

            self["channels"].setText(text.strip() or "No valid channels parsed")
            self["status"].setText(f"Loaded {len(channels)} channels ({tp_counter} transponders)")

        except Exception as e:
            self["channels"].setText(f"Error: {str(e)}")
            self["status"].setText("Error occurred")

    def exit(self):
        self.close()