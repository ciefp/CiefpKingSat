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

    def parse_channel_table(self, soup):
        """Nova metoda za parsiranje kanala na KingOfSat 2026+ strukturi"""
        channels = []
        current_freq = "N/A"

        rows = soup.find_all('tr')

        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 8:
                continue

            # Transponder red – frekvencija u index 2
            freq_text = cells[2].get_text(strip=True)
            if re.match(r'^\d{4,5}\.\d{2}$', freq_text):
                pol = cells[3].get_text(strip=True) if len(cells) > 3 else "-"
                beam = cells[5].get_text(strip=True) if len(cells) > 5 else "Europe"
                standard = cells[6].get_text(strip=True) if len(cells) > 6 else "DVB-S2"
                modulation = cells[7].get_text(strip=True) if len(cells) > 7 else "8PSK"
                sr_fec = cells[8].get_text(strip=True) if len(cells) > 8 else "30000 2/3"

                current_freq = f"{freq_text} {pol} - {beam} {standard} {modulation} {sr_fec}"
                continue

            # Kanal red – ime u index 2
            name = cells[2].get_text(strip=True)
            if name and len(name) > 1:
                channel = {}
                channel['name'] = name

                # Frekvencija (header)
                channel['frequency'] = current_freq

                channel['country'] = cells[3].get_text(strip=True) if len(cells) > 3 else "-"
                channel['category'] = cells[4].get_text(strip=True) if len(cells) > 4 else "-"

                # Paketi – razdvajanje po velikim slovima + poznati nazivi
                package_cell = cells[5].get_text(strip=True) if len(cells) > 5 else "-"
                if package_cell == "-":
                    channel['packages'] = []
                else:
                    # Split po velikim slovima (npr. AllenteDigiTVFocusSat → ['Allente', 'DigiTV', 'FocusSat'])
                    packages = re.findall(r'[A-Z][a-zA-Z0-9& ]*', package_cell)
                    # Dodaj poznate ako nisu uhvaćeni
                    known_packages = ["Allente", "Digi TV", "DigiTV", "Focus Sat", "FocusSat", "Direct One", "Telly",
                                      "Neosat", "Conax", "Cryptowork", "Nagravision"]
                    for k in known_packages:
                        if k in package_cell and k not in packages:
                            packages.append(k)
                    # Ukloni duplikate i očisti
                    packages = list(dict.fromkeys(p.strip() for p in packages if p.strip()))
                    channel['packages'] = packages

                # Kodiranje – preskačemo prikaz, ali čuvamo ako treba kasnije
                enc_cell = cells[6].get_text(strip=True) if len(cells) > 6 else "Unknown"
                if enc_cell.lower() in ["clear", "fta", "free", "unencrypted"]:
                    channel['encryptions'] = ["FTA"]
                else:
                    channel['encryptions'] = re.findall(r'[A-Z][^A-Z\s]*', enc_cell)

                channels.append(channel)

        return channels

    def parse_channel_table(self, soup, is_package=False):
        """Parsira kanale – radi i za satelite i za pakete"""
        channels = []
        current_freq = "N/A"

        rows = soup.find_all('tr')

        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 8:
                continue

            # Transponder red (samo za satelite)
            freq_text = cells[2].get_text(strip=True)
            if re.match(r'^\d{4,5}\.\d{2}$', freq_text) and not is_package:
                pol = cells[3].get_text(strip=True) if len(cells) > 3 else "-"
                beam = cells[5].get_text(strip=True) if len(cells) > 5 else "Europe"
                standard = cells[6].get_text(strip=True) if len(cells) > 6 else "DVB-S2"
                modulation = cells[7].get_text(strip=True) if len(cells) > 7 else "8PSK"
                sr_fec = cells[8].get_text(strip=True) if len(cells) > 8 else "30000 2/3"

                current_freq = f"{freq_text} {pol} - {beam} {standard} {modulation} {sr_fec}"
                continue

            # Kanal red
            name = cells[2].get_text(strip=True).strip()
            if name and len(name) > 1:
                channel = {}
                channel['name'] = name
                channel['frequency'] = current_freq  # čak i za pakete će biti "N/A" ili poslednji header

                channel['country'] = cells[3].get_text(strip=True).strip() if len(cells) > 3 else "-"
                channel['category'] = cells[4].get_text(strip=True).strip() if len(cells) > 4 else "-"
                channel['package'] = cells[5].get_text(strip=True).strip() if len(cells) > 5 else "-"
                channel['encryption'] = cells[6].get_text(strip=True).strip() if len(cells) > 6 else "Unknown"

                channels.append(channel)

        return channels

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

    # scraper.py - izmenite get_news metod:
    # U scraper.py, unutar get_news metode, nakon parsiranja dodaj:
    def get_news(self):
        """Dohvata vesti sa KingOfSat – grupisanje po datumu i satelitu"""
        cache_key = "news_grouped"
        cached_data = load_from_cache(cache_key)
        if cached_data:
            return cached_data

        try:
            url = f"{self.BASE_URL}news"
            response = self.session.get(url, timeout=self.timeout)

            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, 'html.parser')

            news_by_date = {}
            current_date = "Unknown Date"
            current_satellite = "Unknown Satellite"
            has_seen_date = False

            for element in soup.find_all(['h4', 'h5', 'p']):
                # DATE – h4
                if element.name == 'h4':
                    h4_text = element.get_text(" ", strip=True).strip()
                    if any(day in h4_text for day in
                           ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']):
                        current_date = h4_text
                        has_seen_date = True
                        current_satellite = "Unknown Satellite"
                        if current_date not in news_by_date:
                            news_by_date[current_date] = {}
                    continue

                # SATELLITE – h5
                if element.name == 'h5':
                    sat_text = element.get_text(" ", strip=True).strip()
                    if "Filtering" in sat_text or "display options" in sat_text.lower() or not has_seen_date:
                        continue

                    cleaned_sat = sat_text.replace('[', '').replace(']', '').strip()
                    if "°" in cleaned_sat or any(kw in cleaned_sat.lower() for kw in [
                        'hot bird', 'astra', 'eutelsat', 'turksat', 'nilesat', 'express', 'thor',
                        'amos', 'hellas', 'intelsat', 'ses', 'hispa', 'badr', 'yahsat'
                    ]):
                        current_satellite = cleaned_sat

                        if current_satellite not in news_by_date[current_date]:
                            news_by_date[current_date][current_satellite] = []
                    continue

                # NEWS – p
                if element.name != 'p':
                    continue

                channel_tag = element.find('a', class_='A3')
                if not channel_tag:
                    continue

                p_text = element.get_text(" ", strip=True).strip()

                # Pronađi sva vremena u tekstu (mogu biti više vesti u jednom <p>)
                time_matches = list(re.finditer(r'\((\d{1,2}h\d{2})\)', p_text))

                if not time_matches:
                    continue

                # Ako nema satelita, preskoči
                if current_satellite == "Unknown Satellite" or current_date == "Unknown Date":
                    continue

                # Za svako vreme kreiraj zasebnu vest
                for i, time_match in enumerate(time_matches):
                    time_text = time_match.group(1)

                    # Odredi deo teksta za ovu vest
                    start_idx = time_match.start()
                    if i < len(time_matches) - 1:
                        end_idx = time_matches[i + 1].start()
                        item_text = p_text[start_idx:end_idx]
                    else:
                        item_text = p_text[start_idx:]

                    # Ekstraktuj ime kanala
                    channel_name = channel_tag.get_text(strip=True).strip()

                    # Čišćenje teksta
                    clean_text = item_text.replace(f'({time_text})', '', 1).strip()
                    clean_text = re.sub(r'^\s*[-—]\s*', '', clean_text)  # Ukloni vodeći "-" ili "—"
                    clean_text = ' '.join(clean_text.split())  # Normalizuj beline

                    # Dodaj vest
                    news_item = {
                        'time': time_text,
                        'channel': channel_name,
                        'text': clean_text
                    }

                    news_by_date[current_date][current_satellite].append(news_item)

            # Sačuvaj u cache
            save_to_cache(cache_key, news_by_date)
            return news_by_date

        except Exception as e:
            log_error(f"Error getting news: {str(e)}")
            return {}



