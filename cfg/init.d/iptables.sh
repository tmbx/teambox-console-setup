#!/bin/sh

RULE_FILE="/etc/teambox/base/iptables.rules"

# Exit if the package is not installed or the firewall is not configured.
[ -x "/sbin/iptables" -a -f $RULE_FILE ] || exit 0

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
	# Return
	#   0 if daemon has been started
	#   1 if daemon was already running
	#   2 if daemon could not be started
        iptables-restore < $RULE_FILE
        return 0
}

case "$1" in
  start)
	[ "$VERBOSE" != no ] && log_daemon_msg "Loading iptables rules"
	
	do_start
	case "$?" in
		0|1) [ "$VERBOSE" != no ] && log_end_msg 0 ;;
		2) [ "$VERBOSE" != no ] && log_end_msg 1 ;;
	esac
	;;
  stop)
	;;
  restart)
	log_daemon_msg "Loading iptables rules"
	do_start
	;;
  *)
	echo "Usage: $SCRIPTNAME {start|stop|restart}" >&2
	exit 3
	;;
esac

:
