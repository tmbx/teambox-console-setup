#!/bin/bash

set -e

# Version of the product. This must be manually updated at every release.
PRODUCT_VERSION=2.1

# Special switches.
DEBUG=0
INSTALL_DEV=0
FAKE_ACT=0

for arg in $@; do
    if [ $arg = "dev" ]; then INSTALL_DEV=1; fi
    if [ $arg = "debug" ]; then DEBUG=1; fi
    if [ $arg = "fake_act" ]; then FAKE_ACT=1; fi
done

# Set the product version.
mkdir -p /etc/teambox/
echo "$PRODUCT_VERSION\n" > /etc/teambox/product_version

# Setup /etc/apt/sources.list.
echo -e "\n\n>>> Setting up /etc/apt/sources.list."
cat sources.list > /etc/apt/sources.list

if [ ! -z "$APTHTTPPROXY" ]; then
    echo 'http::proxy "$APTHTTPPROXY";' >> /etc/apt/apt.conf
fi

# Update the repository.
echo -e ">>> Updating repository."
apt-get update

# Remove all downloaded deb files. We want to reinstall packages even if they
# have the same version.
echo -e "\n\n>>> Removing downloaded deb files."
apt-get clean

# Remove rsyslog if it is installed.
echo -e ">>> Uninstalling rsyslog."
apt-get -y --force-yes remove rsyslog

# Upgrade the base packages.
echo -e "\n\n>>> Upgrading base packages."
apt-get --force-yes -y -o DPkg::Options::="--force-confdef" dist-upgrade

# Install the teambox-meta package.
echo -e "\n\n>>> Installing teambox-meta package."
apt-get --force-yes -y -o DPkg::Options::="--force-confdef" install teambox-meta

# Prevent Apache from crashing forever.
killall -9 apache2

# Install the development packages if desired.
if [ $INSTALL_DEV = 1 ]; then
    echo -e "\n\n>>> Installing development packages."
    apt-get --force-yes -y install gcc gdb valgrind mercurial scons debhelper fakeroot gnutls-dev libpq-dev libsqlite3-dev libjpeg-dev postgresql-server-dev-8.4 libmhash-dev
fi

# Fix the date.
echo -e "\n\n>>> Fixing the date."
/etc/init.d/ntp stop
ntpdate-debian
/etc/init.d/ntp start

# Explicitly reinstall the base packages.
echo -e "\n\n>>> Installing teambox-console-setup, kpython packages."
apt-get --force-yes -y install --reinstall teambox-console-setup kpython

# Normalize the system.
echo -e "\n\n>>> Normalizing the system."
/etc/teambox/base-config/normalize-system.sh

# Install the remaining Teambox packages.
PACKAGES="kweb kpylons kcd libkcdpg vncreflector kas-python kas-web-base kas-cfg kwmo freemium kctl kctllib kctlbin teambox-acttools tbxsosd-db tbxsos-utils tbxsos-xmlrpc tbxsos-stats tbxsos-config"

if [ $FAKE_ACT = 1 ]; then
    PACKAGES="$PACKAGES tbxsosd-tbxsos"
else
    echo ">>> Not installing tbxsosd-tbxsos, you will have to activate the TBXSOS."
fi

echo -e "\n\n>>> Installing remaining Teambox packages."
DEBIAN_FRONTEND=noninteractive DEBIAN_PRIORITY=critical apt-get --force-yes -y install --reinstall $PACKAGES

# Start Postgres.
echo -e "\n\n>>> Starting Postgres."
/etc/init.d/postgresql-8.4 start

# Create Postgres users.
echo -e "\n\n>>> Creating Postgres users."
su postgres -c '/usr/bin/kexecpg /etc/teambox/base-config/teambox_db.sqlpy'

# Create Postgres schemas.
echo -e "\n\n>>> Creating KCD Postgres schema."
/usr/bin/kexecpg -s create /etc/teambox/base-config/kcd_db.sqlpy

echo -e "\n\n>>> Creating kas-cfg Postgres schema."
/usr/bin/kexecpg -s create /etc/teambox/base-config/kas_cfg_db.sqlpy

echo -e "\n\n>>> Creating KWMO Postgres schema."
/usr/bin/kexecpg -s create /etc/teambox/base-config/kwmo_db.sqlpy

echo -e "\n\n>>> Creating Tbxsosd Postgres schema."
/usr/bin/kexecpg -s create /etc/teambox/base-config/tbxsosd_db.sqlpy

echo -e "\n\n>>> Creating Freemium Postgres schema."
/usr/bin/kexecpg -s create /etc/teambox/base-config/freemium_db.sqlpy

echo -e "\n\n>>> Creating TBXSOS-XMLRPC Postgres schema."
/usr/bin/kexecpg -s create /etc/teambox/base-config/tbxsos_xmlrpc_db.sqlpy

# Enable configuration services.
kplatshell enable tbxsos-configd
kplatshell enable tbxsos-config
kplatshell enable kas_cfg
kplatshell enable web_bridge

# Fake KPS activation.
if [ $FAKE_ACT = 1 ]; then
    echo -e "\n\n>>> Faking KPS activation."
    ./activate.sh
    echo "\n\n"
fi

# Clear the debian repository.
if [ $DEBUG = 0 ]; then
    echo -e "\n\n>>> Clearing /etc/apt/sources.lists."
    echo "" > /etc/apt/sources.list

    echo -e "\n\n>>> Updating repository."
    apt-get update
        
    echo -e "\n\n>>> Removing downloaded deb files."
    apt-get clean
fi

# Delete the SSH host keys.
if [ $DEBUG = 0 ]; then
    echo -e "\n\n>>> Deleting SSH keys."
    rm -f /etc/ssh/ssh_host*
fi

# Self-destruct the bootstrap data.
if [ $DEBUG = 0 ]; then
    echo ">>> Deleting bootstrap data."
    rm -rf /root/new
fi

# Remove root's mail file if it exists.
if [ $DEBUG = 0 ]; then
    echo ">>> Removing root's mail file."
    rm -rf /var/mail/root
fi

# Delete root's bash history.
if [ $DEBUG = 0 ]; then
    echo ">>> Deleting root's bash history."
    rm -f /root/.bash_history
fi

# Done!
echo
echo "Finished!"

