#!/bin/sh

# This script must be run when a system package is installed or upgraded to make
# the system behave as we want.

set -e

# Create the Teambox group.
groupadd -f teambox
adduser -q postgres teambox
adduser -q www-data teambox

# Give sudo access to www-data.
if ! grep "www-data ALL=(ALL) NOPASSWD: ALL" /etc/sudoers >/dev/null 2>&1; then
    echo "www-data ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
fi

# Fix the permissions of /etc/teambox.
mkdir -p /etc/teambox
chmod 0770 /etc/teambox/
chown root:teambox /etc/teambox/

# Fix permissions of /var/log/teambox.
mkdir -p /var/log/teambox
chmod 0775 /var/log/teambox/
chown root:teambox /var/log/teambox/

# Don't assign dumb IDs to network interfaces.
rm -f /etc/udev/rules.d/70-persistent-net.rules
rm -f /lib/udev/rules.d/75-persistent-net-generator.rules

# Remove unwanted cron jobs.
for file in apt aptitude bsdmainutils dpkg man-db samba standard; do
    rm -f /etc/cron.daily/$file
done
rm -f /etc/cron.weekly/man-db

# Remove motd stuff.
rm -f /etc/motd /etc/motd.tail /etc/issue.net /etc/update-motd.d/00-header

# Fix PAM stuff.
cp -f /etc/pam.d/login /tmp/login.tmp
cat /tmp/login.tmp | sed 's/^\(session\s*optional\s*pam_lastlog.so\)/#\1/g' > /etc/pam.d/login
rm -f /tmp/login.tmp

# Disable the samba daemons. Not using the init script because it's too slow.
update-rc.d samba disable >/dev/null 2>&1
killall nmbd smbd 2>/dev/null || true

# Reload the getty process.
killall getty

# Set the timezone.
ln -sf /usr/share/zoneinfo/America/Montreal /etc/localtime
echo "US/Eastern" > /etc/timezone

# Reconfigure the system locales.
mkdir -p /var/lib/locales/supported.d
cp -f /etc/teambox/base-config/teambox-locale /var/lib/locales/supported.d/
rm -f /var/lib/locales/supported.d/en
locale-gen
echo 'LANG="en_US.UTF-8"' > /etc/default/locale

# Reconfigure /etc/sysctl.conf.
cp -f /etc/teambox/base-config/sysctl.conf /etc/
sysctl -p > /dev/null && true

# Reconfigure and restart syslog-ng.
cp -f /etc/teambox/base-config/syslog-ng.conf /etc/syslog-ng/
/etc/init.d/syslog-ng restart

# Make a symlink for open-vm-tools and restart open-vm-tools so that it loads
# its kernel modules properly.
ln -sf /etc/init.d/open-vm-tools /etc/rc2.d/S30open-vm-tools
/etc/init.d/open-vm-tools restart || true

# Install the Teambox cluster with the correct encoding if required.
if [ ! -d "/var/lib/postgresql/8.4/teambox" ]; then

    # Stop Postgres if it is running.
    echo ">>> Stopping Postgres to create the teambox cluster."
    /etc/init.d/postgresql-8.4 stop

    echo ">>> Creating the Postgres teambox cluster."
    rm -rf /etc/postgresql/8.4/teambox
    pg_createcluster \
        --encoding "LATIN1" \
        --locale "en_US.ISO-8859-1" \
        --socketdir /var/run/postgresql \
        8.4 teambox
fi

# Reconfigure Postgres without restarting it.
cp -f /etc/teambox/base-config/pg_hba.conf /etc/postgresql/8.4/teambox/
cp -f /etc/teambox/base-config/postgresql.conf /etc/postgresql/8.4/teambox/
rm -f /var/log/postgresql/*

# Reconfigure Apache without restarting it.
cp -f /etc/teambox/base-config/apache2.conf /etc/apache2/
for file in httpd.conf ports.conf sites-available/default sites-available/default-ssl sites-enabled/000-default; do
    rm -f /etc/apache2/$file
done
a2enmod alias > /dev/null
a2enmod deflate > /dev/null
a2enmod headers > /dev/null
a2enmod ssl > /dev/null
a2enmod proxy > /dev/null
a2enmod proxy_http > /dev/null
rm -f /var/log/apache2/*

