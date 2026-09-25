# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import re
import time
import html as html_module
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

    def get_dab_transmissions(self):
        """Dohvata DAB over DVB podatke sa KingOfSat-a.

        Parser je namerno zasnovan na sadržaju redova (<tr>), a ne na
        konkretnim CSS klasama, jer se HTML KingOfSat-a povremeno menja.
        Rezultat je lista mux objekata kompatibilna sa DAB ekranom.
        """
        cache_key = "dab_transmissions_v7"
        cached_data = load_from_cache(cache_key)
        if cached_data:
            return cached_data

        url = f"{self.BASE_URL}dab"
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            results = self._parse_dab_html_bs(soup)

            if results:
                save_to_cache(cache_key, results)
            return results

        except requests.exceptions.Timeout:
            log_error(f"Timeout scraping {url}")
        except requests.exceptions.RequestException as e:
            log_error(f"HTTP error scraping DAB: {e}")
        except Exception as e:
            import traceback
            log_error(f"Error getting DAB: {e}")
            print(traceback.format_exc())
        return []

    @staticmethod
    def _text(node):
        return " ".join(node.stripped_strings) if node else ""

    def _parse_dab_html_bs(self, soup):
        """Parse the current KingOfSat /dab layout.

        A satellite/frequency row is followed by one or more DAB mux rows;
        every mux is followed by its DAB+ station rows.  We intentionally
        use cell text and semantic markers rather than CSS class names.
        """
        results = []
        current_satellite = "Unknown"
        current_position = ""
        current_frequency = "N/A"
        current_mux = None

        for row in soup.find_all("tr"):
            text = self._text(row)
            if not text:
                continue

            cells = [self._text(c) for c in row.find_all(["td", "th"])]
            lower = text.lower()

            # Satellite/frequency row, e.g.:
            # 7.0°E | Eutelsat 7C | ... | 11513.80 V | DWW4 | Western | DVB-S2 | QPSK | 17017 | 2/3 | ...
            freq_match = re.search(r'\b(\d{4,5}\.\d{2})\s+([HV])\b', text)
            if freq_match:
                current_frequency = "%s %s" % (freq_match.group(1), freq_match.group(2))
                current_mux = None

                # Izvuci SR, standard, modulaciju i FEC iz reda
                # Format: "7.0°E Eutelsat 7C DWW4 Western DVB-S2 QPSK 17017 2/3 2026-07-27"
                sr_match = re.search(r'\b(\d{4,5})\s+(\d+/\d+)\b', text)
                standard_match = re.search(r'\b(DVB-S2X|DVB-S2|DVB-S)\b', text, re.I)
                modulation_match = re.search(r'\b(QPSK|8PSK|16APSK|32APSK)\b', text, re.I)

                current_sr = sr_match.group(1) if sr_match else ""
                current_fec = sr_match.group(2) if sr_match else ""
                current_standard = standard_match.group(1) if standard_match else ""
                current_modulation = modulation_match.group(1) if modulation_match else ""

                # Sačuvaj u zasebne promenljive koje će se koristiti pri kreiranju mux-a
                self._current_sr = current_sr
                self._current_fec = current_fec
                self._current_standard = current_standard
                self._current_modulation = current_modulation

                # Prefer the explicit position/satellite cells at the start.
                if len(cells) >= 2:
                    pos = cells[0]
                    sat = cells[1]
                    if re.search(r'\d+(?:\.\d+)?°[EW]', pos):
                        current_position = pos
                    if sat and sat.lower() not in ("name", "satellite"):
                        current_satellite = sat

                # Also support the h5 heading used by some KingOfSat versions.
                parent = row.find_previous("h5")
                if parent:
                    links = parent.find_all("a")
                    if links:
                        current_satellite = self._text(links[0]) or current_satellite
                    if len(links) > 1:
                        current_position = self._text(links[1]) or current_position
                continue

            # DAB mux row. Current page example:
            # PID 101 (MPE) ... | IP: 239... port 50020 | DAB | Mux | EID: 0x....
            if re.search(r'\bPID\s+\d+\s*\(MPE\)', text, re.I) and re.search(r'\bDAB\b', text, re.I):
                pid_match = re.search(r'\bPID\s+(\d+)\s*\(MPE\)', text, re.I)
                ip_match = re.search(r'\bIP(?:\s+address)?\s*[:|]?\s*([0-9.]+)\s+(?:port|\|\s*port)\s+(\d+)', text, re.I)
                if not ip_match:
                    ip_match = re.search(r'\b([0-9]{1,3}(?:\.[0-9]{1,3}){3})\s+port\s+(\d+)', text, re.I)
                eid_match = re.search(r'\bEID\s*:\s*(0x[0-9a-fA-F]+)', text, re.I)

                mux_name = ""
                # Cell-based extraction is safest: the cell after DAB is mux name.
                for i, cell in enumerate(cells):
                    if cell.strip().upper() == "DAB" and i + 1 < len(cells):
                        mux_name = cells[i + 1].strip()
                        break
                if not mux_name:
                    m = re.search(r'\bDAB\b\s*\|?\s*(.*?)\s*(?:\|\s*EID\s*:|$)', text, re.I)
                    if m:
                        mux_name = m.group(1).strip(" |-")

                current_mux = {
                    "satellite": ("%s (%s)" % (current_satellite, current_position)) if current_position else current_satellite,
                    "position": current_position,
                    "frequency": current_frequency,
                    "mux_name": mux_name or "DAB",
                    "ip_address": ip_match.group(1) if ip_match else "",
                    "port": ip_match.group(2) if ip_match else "",
                    "pid": pid_match.group(1) if pid_match else "",
                    "eid": eid_match.group(1) if eid_match else "",
                    "sr": getattr(self, "_current_sr", ""),
                    "fec": getattr(self, "_current_fec", ""),
                    "standard": getattr(self, "_current_standard", ""),
                    "modulation": getattr(self, "_current_modulation", ""),
                    "stations": [],
                }
                results.append(current_mux)
                continue

            # DAB+ station row.
            if current_mux is not None:
                dab_indexes = [i for i, value in enumerate(cells) if value.strip().upper() == "DAB+"]
                if not dab_indexes:
                    continue

                # Uzmi POSLEDNJI DAB+ (prvi je često ikona/alt tekst)
                audio_index = dab_indexes[-1]

                # Ako je DAB+ na poziciji 0, to je verovatno header red
                if audio_index <= 0:
                    continue

                name = cells[audio_index - 1].strip()
                if not name or name.lower() in ("identification", "audio mode"):
                    continue

                rest = cells[audio_index + 1:]
                current_mux["stations"].append({
                    "name": name,
                    "audio_mode": cells[audio_index],
                    "ch_id": rest[0] if len(rest) > 0 else "",
                    "sid": rest[1] if len(rest) > 1 else "",
                    "bitrate": rest[2] if len(rest) > 2 else "",
                    "update": rest[3] if len(rest) > 3 else "",
                })
        # De-duplicate only exact mux records.
        cleaned = []
        seen = set()
        for mux in results:
            key = (
                mux.get("satellite", ""), mux.get("frequency", ""),
                mux.get("ip_address", ""), mux.get("port", ""),
                mux.get("mux_name", ""), mux.get("eid", "")
            )
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(mux)
        return cleaned

    # Zadržavamo stari naziv metode radi kompatibilnosti sa eventualnim
    # drugim delovima plugina koji je pozivaju.
    def _parse_dab_html(self, html):
        soup = BeautifulSoup(html, "html.parser")
        return self._parse_dab_html_bs(soup)

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