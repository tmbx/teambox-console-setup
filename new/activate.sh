#!/bin/sh

if [ -e /etc/teambox/act/activation/main/act_data ]; then
    echo "This KPS has already been activated."
    exit 0
fi

set -x -e

mkdir -p /etc/teambox/act/identity/main
mkdir -p /etc/teambox/act/activation/main
mkdir -p /etc/teambox/act/keys/main

cat > /etc/teambox/act/activation/main/act_data <<EOF
---
:id_name: main
:parent_id_name:
:step: 7
:keys_name: main
:name: xy-enterprise
:parent_keys_name:
:org_id: 1
EOF
cat > /etc/teambox/act/identity/main/id_data <<EOF
:admin_name: "Dummy Admin"
:admin_email: dummy@admin
:org_id: 1
:kdn: xy-enterprise
EOF

KEYS_DIR=/etc/teambox/act/keys/main

cat > $KEYS_DIR/email.enc.pkey <<ENCPKEY
--- START ENCRYPTION PUBLIC KEY ---
--- END ENCRYPTION PUBLIC KEY ---
ENCPKEY
kctl importkey $KEYS_DIR/email.enc.pkey

cat > $KEYS_DIR/email.enc.skey <<ENCSKEY
--- START ENCRYPTION PRIVATE KEY ---
--- END ENCRYPTION PRIVATE KEY ---
ENCSKEY
kctl importkey $KEYS_DIR/email.enc.skey

cat > $KEYS_DIR/email.sig.pkey <<SIGPKEY
--- START SIGNATURE PUBLIC KEY ---
--- END SIGNATURE PUBLIC KEY ---
SIGPKEY
kctl importkey $KEYS_DIR/email.sig.pkey

cat > $KEYS_DIR/email.sig.skey <<SIGSKEY
--- START SIGNATURE PRIVATE KEY ---
--- END SIGNATURE PRIVATE KEY ---
SIGSKEY
kctl importkey $KEYS_DIR/email.sig.skey

kctl addorg xy-enterprise

# License for XY Enterprise: unlimited with all capabilities, good until 2020
tempfile=$(mktemp)
cat > $tempfile <<LICENSE
LICENSE
kctl importlicense $tempfile
rm $tempfile

chown -R www-data.www-data /etc/teambox/act*

kctl setorgstatus 1 2

