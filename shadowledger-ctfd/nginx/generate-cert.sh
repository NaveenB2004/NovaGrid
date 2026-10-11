#!/usr/bin/env bash
# Generates a self-signed cert for the isolated CTF-LAN.
# Fine here because participants never leave the lab network — there's no
# public CA to satisfy and nothing to phish, it's just TLS-in-transit on
# the isolated segment.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p certs
openssl req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout certs/ctfd.key \
  -out certs/ctfd.crt \
  -subj "/C=LK/ST=Western/L=Colombo/O=IE3132/CN=shadowledger.ctf-lan"
echo "Cert written to nginx/certs/ctfd.crt and nginx/certs/ctfd.key"
