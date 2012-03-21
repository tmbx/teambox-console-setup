#!/bin/bash

PATH=/sbin:/usr/sbin:/bin:/usr/bin

# Path to the certificate directory.
CERT_DIR="/etc/teambox/base/"
CERT_NAME="cert.pem"
KEY_NAME="cert_key.pem"
CSR_REQ_PATH="/etc/teambox/base-config/self_csr.req"

# Load the VERBOSE setting and other rcS variables
. /lib/init/vars.sh

# Define LSB log_* functions.
# Depend on lsb-base (>= 3.0-6) to ensure that this file is present.
. /lib/lsb/init-functions

# This function regenerates the certificate if required.
do_start()
{
        cd $CERT_DIR
        
        if [ ! -f $CERT_NAME ]; then
            # Generate self-signed certificate.
            openssl req -x509 -new -nodes \
                -days 9999 \
                -keyout $KEY_NAME \
                -config $CSR_REQ_PATH \
                -out $CERT_NAME
            chmod 666 $CERT_NAME
            chmod 666 $KEY_NAME
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
