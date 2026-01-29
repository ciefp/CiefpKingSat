### CiefpKingSat - Enigma2 Plugin

**KingOfSat Viewer for Enigma2 receivers**  
Plugin for quick access to satellite TV channel lists, TV packages and latest news from [KingOfSat.net](https://en.kingofsat.net).

![Plugin screenshot](https://github.com/ciefp/CiefpKingSat/blob/main/ciefpkingsat1.jpg)  
![Plugin screenshot](https://github.com/ciefp/CiefpKingSat/blob/main/ciefpkingsat2.jpg)  
![Plugin screenshot](https://github.com/ciefp/CiefpKingSat/blob/main/ciefpkingsat3.jpg)  
![Plugin screenshot](https://github.com/ciefp/CiefpKingSat/blob/main/ciefpkingsat4.jpg)  

## Features

- Browse **satellite channel lists** grouped by transponder/frequency  
  (Name, Country, Category, Package, Encryption/FTA status)
- View popular **TV packages** grouped by satellite  
  (Digi TV, Sky, Total TV, MaxTV, Bulsatcom, NOS, Allente, etc.)
- Read latest **KingOfSat news** (grouped by date and satellite)
- Local **cache system** (1 hour) – fast loading, less server load
- Clean and simple interface with ScrollLabel for long lists

## Supported images

- OpenPLi
- OpenATV
- BlackHole
- Dream-Elite
- ...and most other recent Enigma2 images (Python 3)

## Installation

### Method 1 – Online installer (recommended)

```bash
wget -q "--no-check-certificate" https://raw.githubusercontent.com/ciefp/CiefpKingSat/main/installer.sh -O - | /bin/sh

```
## The installer will:
- Check internet connection
- Install required dependencies (python3-requests, python3-beautifulsoup4, python3-lxml)
- Download and install the plugin
- Restart GUI automatically

## Dependencies (automatically installed)
- python3-requests
- python3-beautifulsoup4
- python3-lxml

## Usage
- Go to Plugins → CiefpKingSat
Choose:
- Satellites – browse channels by satellite
- Packages – browse TV packages (grouped by satellite)
- News – latest KingOfSat updates

Use green button to select / red to exit

## Changelog
v1.0 – 2026
• Initial release
• Satellite & package channel lists
• KingOfSat news viewer
• Local cache system
• Clean UI with grouping

## Author
• ciefp
• GitHub: https://github.com/ciefp
• X/Twitter: @ciefp

## License
This project is licensed under the GPL-3.0 License – see the LICENSE file for details.
Data is scraped from KingOfSat.net – all rights belong to their owners.
## Enjoy & happy watching! 📡
