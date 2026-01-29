# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import re
import time
from .utils import save_to_cache, load_from_cache, log_error, get_user_agent

class KingOfSatScraper:
    BASE_URL = "https://en.kingofsat.net/"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': get_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.timeout = 25
    
    def get_satellite_channels(self, sat_url):
        """Dohvata listu kanala za dati satelit sa cache podrškom"""
        # Proveri cache prvo
        cache_key = f"satellite_{sat_url}"
        cached_data = load_from_cache(cache_key)
        if cached_data:
            return cached_data
        
        try:
            url = f"{self.BASE_URL}{sat_url}"
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code != 200:
                log_error(f"HTTP {response.status_code} for {url}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # POKUŠAJ NOVU METODU ZA PARSIRANJE
            channels = self.parse_channel_table(soup)
            
            # AKO NOVA METODA NIJE PRONAŠLA KANALE, POKUŠAJ STARU METODU
            if not channels:
                channels = self._fallback_parse_channels(soup, sat_url)
            
            # Sačuvaj u cache
            if channels:
                save_to_cache(cache_key, channels)
            
            return channels
            
        except requests.exceptions.Timeout:
            log_error(f"Timeout scraping {sat_url}")
            return []
        except Exception as e:
            log_error(f"Error scraping {sat_url}: {str(e)}")
            return []

    # U metodi get_package_channels (scraper.py) zameni:
    def get_package_channels(self, package_slug):
        cache_key = f"package_{package_slug}"
        cached_data = load_from_cache(cache_key)
        if cached_data:
            return cached_data

        try:
            url = f"{self.BASE_URL}{package_slug}"
            response = self.session.get(url, timeout=self.timeout)

            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, 'html.parser')

            # Koristimo parse_channel_table sa is_package=False da bismo dobili frekvencije
            channels = self.parse_channel_table(soup, is_package=False)

            # Ako nema kanala, pokušaj staru metodu
            if not channels:
                channels = self._fallback_parse_package_channels(soup)

            # Dodaj package name svakom kanalu
            package_name = package_slug.replace('pack-', '').replace('-', ' ').title()
            for channel in channels:
                channel['package'] = package_name
                # Ako nemamo frequency, postavimo default
                if 'frequency' not in channel or channel['frequency'] == 'N/A':
                    channel['frequency'] = f"Package: {package_name}"

            if channels:
                save_to_cache(cache_key, channels)

            return channels

        except Exception as e:
            print(f"[ERROR] Greška pri parsiranju paketa {package_slug}: {str(e)}")
            return []

    # U metodi parse_channel_table promeni da uvek vraća frequency (čak i za pakete):
    def parse_channel_table(self, soup, is_package=False):
        """Parsira kanale – radi i za satelite i za pakete"""
        channels = []
        current_freq = "N/A"
        current_satellite = "Unknown"

        rows = soup.find_all('tr')

        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 6:
                continue

            # Za satelite: transponder red (ima frekvenciju)
            freq_text = cells[2].get_text(strip=True) if len(cells) > 2 else ""

            # Proveri da li je ovo frekvencija (broj sa decimalnom tačkom)
            if re.match(r'^\d{4,5}\.\d{2}$', freq_text) and not is_package:
                pol = cells[3].get_text(strip=True) if len(cells) > 3 else "-"
                beam = cells[5].get_text(strip=True) if len(cells) > 5 else "Europe"
                standard = cells[6].get_text(strip=True) if len(cells) > 6 else "DVB-S2"
                modulation = cells[7].get_text(strip=True) if len(cells) > 7 else "8PSK"
                sr_fec = cells[8].get_text(strip=True) if len(cells) > 8 else "30000 2/3"

                current_freq = f"{freq_text} {pol} - {beam} {standard} {modulation} {sr_fec}"
                continue

            # Za pakete: možda imamo satelit + frekvenciju u istoj ćeliji
            cell_text = cells[2].get_text(strip=True) if len(cells) > 2 else ""
            if is_package and ('Hellas Sat' in cell_text or 'Astra' in cell_text or 'Eutelsat' in cell_text):
                current_freq = cell_text
                continue

            # Kanal red
            name = cells[2].get_text(strip=True).strip() if not is_package else cells[0].get_text(strip=True).strip()
            if name and len(name) > 1:
                channel = {}
                channel['name'] = name
                channel['frequency'] = current_freq

                if is_package:
                    channel['country'] = cells[1].get_text(strip=True).strip() if len(cells) > 1 else "-"
                    channel['category'] = cells[2].get_text(strip=True).strip() if len(cells) > 2 else "-"
                    channel['package'] = cells[3].get_text(strip=True).strip() if len(cells) > 3 else "-"
                    channel['encryption'] = cells[4].get_text(strip=True).strip() if len(cells) > 4 else "Unknown"
                else:
                    channel['country'] = cells[3].get_text(strip=True).strip() if len(cells) > 3 else "-"
                    channel['category'] = cells[4].get_text(strip=True).strip() if len(cells) > 4 else "-"
                    channel['package'] = cells[5].get_text(strip=True).strip() if len(cells) > 5 else "-"
                    channel['encryption'] = cells[6].get_text(strip=True).strip() if len(cells) > 6 else "Unknown"

                channels.append(channel)

        return channels

    def parse_satellite(self, soup):
        """Parser za satelite – sa frekvencijom i grupisanjem po transponderu"""
        channels = []
        current_freq = "N/A"

        rows = soup.find_all('tr')

        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 8:
                continue

            freq_text = cells[2].get_text(strip=True)
            if re.match(r'^\d{4,5}\.\d{2}$', freq_text):
                pol = cells[3].get_text(strip=True) if len(cells) > 3 else "-"
                beam = cells[5].get_text(strip=True) if len(cells) > 5 else "Europe"
                standard = cells[6].get_text(strip=True) if len(cells) > 6 else "DVB-S2"
                modulation = cells[7].get_text(strip=True) if len(cells) > 7 else "8PSK"
                sr_fec = cells[8].get_text(strip=True) if len(cells) > 8 else "30000 2/3"

                current_freq = f"{freq_text} {pol} - {beam} {standard} {modulation} {sr_fec}"
                continue

            name = cells[2].get_text(strip=True).strip()
            if name and len(name) > 1:
                channel = {
                    'name': name,
                    'frequency': current_freq,
                    'country': cells[3].get_text(strip=True).strip() if len(cells) > 3 else "-",
                    'category': cells[4].get_text(strip=True).strip() if len(cells) > 4 else "-",
                    'package': cells[5].get_text(strip=True).strip() if len(cells) > 5 else "-",
                    'encryption': cells[6].get_text(strip=True).strip() if len(cells) > 6 else "Unknown",
                }
                channels.append(channel)

        return channels

    def parse_package(self, soup):
        """Parser za pakete – bez frekvencije, fokus na ime, zemlja, kategorija, enkripcija"""
        channels = []
        rows = soup.find_all('tr')

        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 5:
                continue

            # Preskoči header
            first = cells[0].get_text(strip=True)
            if "Name" in first or "Country" in first or not first.strip():
                continue

            name = cells[0].get_text(strip=True).strip()
            if not name or len(name) < 3:
                continue

            channel = {
                'name': name,
                'satellite': cells[1].get_text(strip=True).strip() if len(cells) > 1 else "Unknown",
                'country': cells[2].get_text(strip=True).strip() if len(cells) > 2 else "-",
                'category': cells[3].get_text(strip=True).strip() if len(cells) > 3 else "-",
                'package': self.package_name if hasattr(self, 'package_name') else "Unknown",
                'encryption': cells[4].get_text(strip=True).strip() if len(cells) > 4 else "Unknown",
                'frequency': "N/A"
            }
            channels.append(channel)

        return channels

    def clean_news_text(self, text):
        import re

        # ukloni SID / PID / Audio info
        text = re.sub(r'SID:\d+.*', '', text)
        text = re.sub(r'PID:\d+.*', '', text)

        # ukloni jezike (Bulgarian, English, itd.)
        text = re.sub(r'\b[A-Z][a-z]+ian\b', '', text)

        # ukloni zagrade koje nisu MHz
        text = re.sub(r'\([^)]*\)', lambda m: m.group(0) if 'MHz' in m.group(0) else '', text)

        # normalizuj razmake
        text = ' '.join(text.split())

        return text.strip()

    def get_news(self):
        """Dohvata vesti sa KingOfSat – vraća LISTU (kompatibilno sa starim UI)"""

        cache_key = "news_list_v2"
        cached_data = load_from_cache(cache_key)
        if cached_data:
            return cached_data

        news_list = []

        try:
            url = f"{self.BASE_URL}news"
            response = self.session.get(url, timeout=self.timeout)

            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, 'html.parser')

            current_date = None
            current_satellite = None

            for el in soup.find_all(['h4', 'h5', 'p']):

                # =====================
                # DATUM
                # =====================
                if el.name == 'h4':
                    date_text = el.get_text(" ", strip=True)
                    if date_text:
                        current_date = date_text
                    continue

                # =====================
                # SATELIT
                # =====================
                if el.name == 'h5':
                    sat_link = el.find('a')
                    if not sat_link:
                        continue

                    sat_text = sat_link.get_text(strip=True)
                    if not sat_text:
                        continue

                    current_satellite = sat_text
                    continue

                # =====================
                # POJEDINAČNA VEST
                # =====================
                if el.name != 'p':
                    continue

                time_tag = el.find('a', class_='upd')
                channel_tag = el.find('a', class_='A3')

                if not time_tag or not channel_tag:
                    continue

                if not current_date or not current_satellite:
                    continue

                time_text = time_tag.get_text(strip=True).strip("()")
                channel_name = channel_tag.get_text(strip=True)

                # kompletan tekst paragrafa
                raw_text = el.get_text(" ", strip=True)

                # ukloni vreme i ime kanala iz opisa
                clean_text = raw_text
                clean_text = clean_text.replace(time_tag.get_text(strip=True), '', 1)
                clean_text = clean_text.replace(channel_name, '', 1)

                # dodatno čišćenje
                clean_text = self.clean_news_text(clean_text)

                news_list.append({
                    "date": current_date,
                    "satellite": current_satellite,
                    "time": time_text,
                    "channel": channel_name,
                    "description": clean_text
                })

            save_to_cache(cache_key, news_list)
            return news_list

        except Exception as e:
            log_error(f"Error getting news: {str(e)}")
            return []