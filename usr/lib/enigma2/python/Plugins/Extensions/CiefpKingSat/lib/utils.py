# -*- coding: utf-8 -*-
import os
import json
import time
from datetime import datetime
from enigma import eEnv

PLUGIN_PATH = eEnv.resolve("${libdir}/enigma2/python/Plugins/Extensions/CiefpKingSat/")
CACHE_DIR = os.path.join(PLUGIN_PATH, "cache")
CACHE_DURATION = 3600  # 1 sat cache

def ensure_cache_dir():
    """Osigurava da cache direktorijum postoji"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    return CACHE_DIR

def get_cache_filename(url):
    """Generiše cache ime fajla od URL-a"""
    import hashlib
    filename = hashlib.md5(url.encode()).hexdigest() + ".json"
    return os.path.join(CACHE_DIR, filename)

def is_cache_valid(cache_file):
    """Proverava da li je cache još uvek validan"""
    if not os.path.exists(cache_file):
        return False
    
    file_mtime = os.path.getmtime(cache_file)
    current_time = time.time()
    
    return (current_time - file_mtime) < CACHE_DURATION

def save_to_cache(url, data):
    """Čuva podatke u cache"""
    ensure_cache_dir()
    cache_file = get_cache_filename(url)
    
    try:
        cache_data = {
            'timestamp': time.time(),
            'data': data,
            'url': url
        }
        
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error saving cache for {url}: {e}")
        return False

def load_from_cache(url):
    """Učitava podatke iz cache-a"""
    cache_file = get_cache_filename(url)
    
    if not os.path.exists(cache_file):
        return None
    
    if not is_cache_valid(cache_file):
        # Obriši stari cache
        try:
            os.remove(cache_file)
        except:
            pass
        return None
    
    try:
        with open(cache_file, 'r') as f:
            cache_data = json.load(f)
        
        return cache_data.get('data')
    except Exception as e:
        print(f"Error loading cache for {url}: {e}")
        return None

def clear_old_cache():
    """Briše stare cache fajlove"""
    ensure_cache_dir()
    
    current_time = time.time()
    deleted = 0
    
    for filename in os.listdir(CACHE_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(CACHE_DIR, filename)
            try:
                file_mtime = os.path.getmtime(filepath)
                if (current_time - file_mtime) > CACHE_DURATION * 24:  # 24 sata
                    os.remove(filepath)
                    deleted += 1
            except:
                pass
    
    return deleted

def format_channel_list(channels, max_lines=50):
    """Formatira listu kanala za prikaz"""
    if not channels:
        return "No channels found"
    
    text = ""
    for i, channel in enumerate(channels[:max_lines], 1):
        name = channel.get('name', 'Unknown')
        freq = channel.get('frequency', '')
        enc = channel.get('encryption', 'FTA')
        
        text += f"{i:3}. {name:<40} {freq:>10} {enc:>10}\n"
    
    if len(channels) > max_lines:
        text += f"\n... and {len(channels) - max_lines} more channels"
    
    return text

def log_error(error_message):
    """Loguje greške u fajl"""
    log_file = os.path.join(PLUGIN_PATH, "error.log")
    
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, 'a') as f:
            f.write(f"[{timestamp}] {error_message}\n")
    except:
        pass

def get_user_agent():
    """Vraća User-Agent za HTTP zahteve"""
    return "Mozilla/5.0 (X11; Linux armv7l) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"