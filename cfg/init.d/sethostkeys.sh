#!/bin/sh

PATH=/sbin:/usr/sbin:/bin:/usr/bin

# Load the VERBOSE setting and other rcS variables
. /lib/init/vars.sh

# Define LSB log_* functions.
# Depend on lsb-base (>= 3.0-6) to ensure that this file is present.
. /lib/lsb/init-functions

#
# Function that starts the daemon/service
#
do_start()
{
	# Regenerate the SSH host keys if required.
	if [ ! -f /etc/ssh/ssh_host_dsa_key.pub ]; then
	    dpkg-reconfigure --terse openssh-server
	    /etc/init.d/ssh stop
	fi
}

#
# Function that stops the daemon/service
#
do_stop()
{
	#
	/bin/true
}

#
# Function that sends a SIGHUP to the daemon/service
#
do_reload() {
	#
	# If the daemon can reload its configuration without
	# restarting (for example, when it is sent a SIGHUP),
	# then implement that here.
	#
	#start-stop-daemon --stop --signal 1 --quiet --name $NAME
	return 0
}

case "$1" in
  start|force-start)
	[ "$VERBOSE" != no ] && log_daemon_msg "Starting $DESC" "$NAME"
	
	do_start
	case "$?" in
		0|1) [ "$VERBOSE" != no ] && log_end_msg 0 ;;
		2) [ "$VERBOSE" != no ] && log_end_msg 1 ;;
	esac
	;;
  stop|force-stop)
	[ "$VERBOSE" != no ] && log_daemon_msg "Stopping $DESC" "$NAME"
	do_stop
	case "$?" in
		0|1) [ "$VERBOSE" != no ] && log_end_msg 0 ;;
		2) [ "$VERBOSE" != no ] && log_end_msg 1 ;;
	esac
	;;
  *)
	echo "Usage: $SCRIPTNAME {start|stop}" >&2
	exit 3
	;;
esac

:
