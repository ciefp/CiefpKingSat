#!/bin/bash
##setup command=wget -q "--no-check-certificate" https://raw.githubusercontent.com/ciefp/CiefpKingSat/main/installer.sh -O - | /bin/sh

######### Only These 2 lines to edit with new version ######
version='1.0'
changelog='\nInitial release\nSatellite & Package lists from KingOfSat\nNews viewer\nCache system'
##############################################################

TMPPATH=/tmp/CiefpKingSat

if [ ! -d /usr/lib64 ]; then
	PLUGINPATH=/usr/lib/enigma2/python/Plugins/Extensions/CiefpKingSat
else
	PLUGINPATH=/usr/lib64/enigma2/python/Plugins/Extensions/CiefpKingSat
fi

# Check internet connection
echo "Checking internet connection..."
if ! ping -c 1 8.8.8.8 >/dev/null 2>&1; then
    echo "No internet connection! Please check your network and try again."
    exit 1
fi

# Check opkg
if ! command -v opkg >/dev/null 2>&1; then
    echo "ERROR: opkg not found. This installer requires opkg package manager."
    exit 1
fi

# Check Python version and required packages
echo "Checking Python version and dependencies..."
if python --version 2>&1 | grep -q '^Python 3\.'; then
    echo "Python 3 detected"
    PYTHON=PY3
    PKG_REQUESTS="python3-requests"
    PKG_BS4="python3-beautifulsoup4"
    PKG_LXML="python3-lxml"
else
    echo "Python 2 detected - some features may not work properly"
    PYTHON=PY2
    PKG_REQUESTS="python-requests"
    PKG_BS4="python-beautifulsoup4"
    PKG_LXML="python-lxml"
fi

# Update opkg
opkg update >/dev/null 2>&1 || { echo "opkg update failed! Check internet."; exit 1; }

# Install missing dependencies
for pkg in $PKG_REQUESTS $PKG_BS4 $PKG_LXML; do
    if ! opkg list-installed | grep -q "^$pkg "; then
        echo "Installing $pkg..."
        opkg install $pkg || { echo "Failed to install $pkg"; exit 1; }
    fi
done

echo "All dependencies are installed."

# Download and extract plugin
echo "Downloading CiefpKingSat $version..."
cd /tmp
rm -rf $TMPPATH >/dev/null 2>&1
mkdir -p $TMPPATH
cd $TMPPATH

wget https://github.com/ciefp/CiefpKingSat/archive/refs/heads/main.tar.gz || { echo "Download failed!"; exit 1; }
tar -xzf main.tar.gz
cp -r CiefpKingSat-main/usr /

# Check if plugin installed correctly
if [ ! -d $PLUGINPATH ]; then
    echo "Something went wrong... Plugin not installed."
    exit 1
fi

rm -rf $TMPPATH >/dev/null 2>&1
sync

echo ""
echo "#########################################################"
echo "#           CiefpKingSat INSTALLED SUCCESSFULLY         #"
echo "#                ..:: CiefpSettings ::..                #"
echo "#                  developed by ciefp                   #"
echo "#########################################################"
echo "#           Your device will RESTART Now                #"
echo "#########################################################"
sleep 5
killall -9 enigma2
exit 0