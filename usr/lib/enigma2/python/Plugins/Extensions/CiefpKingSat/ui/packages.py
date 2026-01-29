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
import os

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
        <widget name="title" render="Label" position="100,100" size="1720,60" font="Regular;34" halign="center" valign="center" foregroundColor="#ffffff" backgroundColor="#1a1a1a" zPosition="2" />
        <widget name="menu" position="100,150" size="1300,780" font="Regular;36" itemHeight="39" halign="left"  valign="center" scrollbarMode="showOnDemand" />
        <!-- BACKGROUND -->
        <widget name="background" position="1420,150" size="400,780" pixmap="%s" alphatest="on" zPosition="1" />
        <widget name="description" render="Label" position="100,950" size="1720,40" font="Regular;26" halign="left" valign="center" foregroundColor="#cccccc" />
        <!-- Crveni taster - Back -->
        <widget name="key_red" position="100,1000" size="300,60" font="Bold;26" halign="center" valign="center" foregroundColor="#080808" backgroundColor="#a00000" zPosition="2" />
        <!-- Pozadina za crveni taster  -->
        <ePixmap pixmap="skin_default/buttons/red.png" position="100,1000" size="300,60" alphatest="blend" zPosition="1" />
        <!-- Zeleni taster - Back -->
        <widget name="key_green" position="500,1000" size="300,60" font="Bold;26" halign="center" valign="center" foregroundColor="#080808" backgroundColor="#00a000" zPosition="2" />
        <!-- Pozadina za Zeleni taster  -->
        <ePixmap pixmap="skin_default/buttons/green.png" position="500,1000" size="300,60" alphatest="blend" zPosition="1" />
    </screen>
    """ % BACKGROUND

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session

        self["background"] = Pixmap()
        
        # Flatten listu za prikaz (koristi klasnu varijablu)
        self.menu_items = []
        for sat, packages in self.PACKAGES_BY_SAT.items():  # ← self.PACKAGES_BY_SAT
            self.menu_items.append((f"--- {sat} ---", None))
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
        <!-- TITLE -->
        <widget name="title" render="Label" position="100,100" size="1720,60" font="Regular;34" halign="center" valign="center" foregroundColor="#ffffff" backgroundColor="#1a1a1a" zPosition="2" />

        <!-- GLAVNA LISTA KANALA -->
        <widget name="channels" position="100,180" size="1720,740" font="Regular;28" scrollbarMode="showOnDemand" />

        <!-- STATUS BAR -->
        <widget name="status" render="Label" position="100,940" size="1720,50" font="Regular;26" halign="left" valign="center" foregroundColor="#cccccc" backgroundColor="#000000" zPosition="1" />

        <!-- Crveni taster - Back -->
        <widget name="key_red" position="100,1000" size="300,60" font="Bold;26" halign="center" valign="center" foregroundColor="#080808" backgroundColor="#a00000" zPosition="2" />

        <!-- Pozadina za crveni taster (opcionalno) -->
        <ePixmap pixmap="skin_default/buttons/red.png" position="100,1000" size="300,60" alphatest="blend" zPosition="1" />
    </screen>
    """

    def __init__(self, session, package_name, package_data):
        Screen.__init__(self, session)
        self.session = session
        self.package_name = package_name
        self.package_data = package_data

        self["title"] = Label(f"{package_name} - Channels")
        self["status"] = Label(f"Package: {package_name} | Loaded {len(package_data.get('channels', []))} channels")
        self["key_red"] = Label(_("Back"))

        self["channels"] = ScrollLabel("")

        self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "NavigationActions"], {
            "cancel": self.exit,
            "red": self.exit,
            "up": self["channels"].pageUp,
            "down": self["channels"].pageDown,
            "left": self["channels"].pageUp,
            "right": self["channels"].pageDown
        }, -1)

        self.displayChannels()

    # U klasi CiefpPackageChannels, metodi displayChannels zameni sa:
    def displayChannels(self):
        if not self.package_data or 'channels' not in self.package_data or not self.package_data['channels']:
            self["channels"].setText("No channels available for this package.")
            return

        text = ""
        current_freq = None
        tp_counter = 0

        channels = self.package_data['channels']

        # Definicija kolona za pakete
        COLUMNS = {
            'name': {'start': 0, 'end': 40, 'title': 'CHANNEL NAME'},
            'country': {'start': 40, 'end': 55, 'title': 'COUNTRY'},
            'category': {'start': 55, 'end': 75, 'title': 'CATEGORY'},
            'package': {'start': 75, 'end': 140, 'title': 'PACKAGE'},
            'encryption': {'start': 140, 'end': 180, 'title': 'ENCRYPTION'}
        }

        # Izračunaj ukupnu dužinu linije
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

        # Funkcija za skraćivanje teksta
        def truncate(text, max_len, add_ellipsis=True):
            if not text:
                return ""
            if len(text) <= max_len:
                return text
            if add_ellipsis and max_len > 3:
                return text[:max_len - 3] + "..."
            return text[:max_len]

        for channel in channels:
            freq_header = channel.get('frequency', 'N/A')

            # Ako frekvencija nije postavljena, koristi package name
            if freq_header == 'N/A' or not freq_header:
                freq_header = f"Package: {self.package_name}"

            if freq_header != current_freq:
                current_freq = freq_header
                tp_counter += 1

                if tp_counter > 1:
                    text += "\n\n"

                text += f"{current_freq}\n"

                # Dodaj header liniju
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

                    last_end = col_info['end']

                text += header_line + "\n"
                # SEPARATOR
                text += "-" * TOTAL_LENGTH + "\n"

            # Formiraj liniju za kanal
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
            package = (channel.get('package', '-') or '').strip()
            width = COLUMNS['package']['end'] - COLUMNS['package']['start']
            if last_end < COLUMNS['package']['start']:
                line += " " * (COLUMNS['package']['start'] - last_end)
            package = truncate(package, width)
            line += f"{package:<{width}}"
            last_end = COLUMNS['package']['end']  # ISPRAVLJENO

            # Enkripcija
            encryption = ""
            enc = channel.get('encryption', '')
            if isinstance(enc, str):
                enc_lower = enc.lower().strip()
                if enc_lower in ['clear', 'fta', 'free', '0', 'unencrypted']:
                    encryption = "FTA"
                elif enc_lower and enc_lower != 'undefined':
                    if 'conax' in enc_lower and 'nagravision' in enc_lower:
                        encryption = "Conax/Nagra"
                    elif 'videoguard' in enc_lower:
                        encryption = "VideoGuard"
                    elif 'cryptoworks' in enc_lower:
                        encryption = "CryptoWorks"
                    else:
                        encryption = truncate(enc, 35)

            width = COLUMNS['encryption']['end'] - COLUMNS['encryption']['start']
            if last_end < COLUMNS['encryption']['start']:
                line += " " * (COLUMNS['encryption']['start'] - last_end)
            encryption = truncate(encryption, width)
            line += f"{encryption:<{width}}"

            text += line + "\n"

        self["channels"].setText(text.strip())
        self["status"].setText(f"Package: {self.package_name} | Loaded {len(channels)} channels")

    def exit(self):
        self.close()