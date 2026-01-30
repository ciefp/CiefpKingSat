### CiefpKingSat - Enigma2 Plugin

**KingOfSat Viewer for Enigma2 receivers**  

Plugin for quick access to satellite TV channel lists, TV packages and latest news from [KingOfSat.net](https://en.kingofsat.net).

![Plugin screenshot](https://github.com/ciefp/CiefpKingSat/blob/main/ciefpkingsat1.jpg)  
![Plugin screenshot](https://github.com/ciefp/CiefpKingSat/blob/main/ciefpkingsat2.jpg)  
![Plugin screenshot](https://github.com/ciefp/CiefpKingSat/blob/main/ciefpkingsat3.jpg)  
![Plugin screenshot](https://github.com/ciefp/CiefpKingSat/blob/main/ciefpkingsat4.jpg)  

## Features
## 🔹 CiefpKingSat v2.0 – Major UI & Usability Upgrade 🔹
- This release represents a major step forward in both usability and visual presentation of the plugin.
- Starting from a simple text-based channel listing, CiefpKingSat has evolved into a fully structured, 
- table-based browsing experience with consistent layout across all sections.

## ✅ What’s New in v2.0

• Completely redesigned Satellite Channels screen with tabular layout
• Added column headers (Channel, Country, Category, Package, Encryption)
• Implemented transponder grouping headers for easier frequency overview
• Introduced pagination system (Next / Prev) instead of continuous scrolling
• Unified layout and colors across Satellite, Packages, Channels and News screens
• Packages screen now uses the same table-based channel view
• News screen converted to paged reading mode with Next / Prev & Left / Right support
• Improved fonts, spacing and alignment for better readability
• Clearer encryption display (FTA shown instead of “clear”)
• Better performance and smoother navigation

## 🎯 Result
- CiefpKingSat v2.0 offers a cleaner, faster and more professional user experience, 
- bringing the plugin to a much higher visual and functional level compared to previous versions.

## Supported images

- OpenPLi
- OpenATV
- BlackHole
- Dream-Elite
- ...and most other recent Enigma2 images (Python 3)

## Installation

### Online installer (recommended)

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
