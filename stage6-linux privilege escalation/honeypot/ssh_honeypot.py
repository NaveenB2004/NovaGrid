#!/usr/bin/env python3
"""
ssh_honeypot.py - a low-interaction SSH honeypot for the CTF box.

Presents a believable SSH login prompt on a chosen port, logs every
connecting IP, every username/password combination attempted, and (if
they get a fake shell) every command typed - then always fails auth
or drops the fake session. No real access is ever granted from here.

Purpose: gives the project a detection/blue-team angle - after the
attacker finishes the offensive chain, log analysis of
/var/log/honeypot/ssh_honeypot.log shows exactly what was tried, when,
and from where. Good material for an IDS/log-review section of a
report.

Requires: paramiko (pip install paramiko)
Needs a host key: generate once with
    ssh-keygen -t rsa -b 2048 -f honeypot_host_key -N ""
"""
import logging
import os
import socket
import threading

import paramiko

HOST = "0.0.0.0"
PORT = 2222
HOST_KEY_PATH = "/etc/honeypot/honeypot_host_key"
LOG_PATH = "/var/log/honeypot/ssh_honeypot.log"

os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s %(message)s",
)


class HoneypotServer(paramiko.ServerInterface):
    def __init__(self, client_ip):
        self.client_ip = client_ip
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        logging.info(
            "AUTH_ATTEMPT ip=%s username=%r password=%r -> DENIED",
            self.client_ip, username, password,
        )
        # Always deny - this is a low-interaction honeypot, not a trap
        # door. We want the log entry, not a compromised shell.
        return paramiko.AUTH_FAILED

    def check_auth_publickey(self, username, key):
        logging.info(
            "AUTH_ATTEMPT ip=%s username=%r auth_type=publickey fingerprint=%s -> DENIED",
            self.client_ip, username, key.get_fingerprint().hex(),
        )
        return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        return "password,publickey"

    def check_channel_shell_request(self, channel):
        return False

    def check_channel_pty_request(self, *args, **kwargs):
        return False


def handle_connection(client_sock, client_addr):
    client_ip = client_addr[0]
    logging.info("CONNECT ip=%s port=%s", client_ip, client_addr[1])
    try:
        transport = paramiko.Transport(client_sock)
        transport.local_version = "SSH-2.0-OpenSSH_8.9p1 Ubuntu-3"
        host_key = paramiko.RSAKey(filename=HOST_KEY_PATH)
        transport.add_server_key(host_key)
        server = HoneypotServer(client_ip)
        try:
            transport.start_server(server=server)
        except paramiko.SSHException:
            logging.info("HANDSHAKE_FAILED ip=%s", client_ip)
            return

        # Give it a moment in case of an auth attempt, then close.
        chan = transport.accept(5)
        if chan is not None:
            chan.close()
    except Exception as e:
        logging.info("ERROR ip=%s error=%s", client_ip, e)
    finally:
        try:
            transport.close()
        except Exception:
            pass


def main():
    if not os.path.exists(HOST_KEY_PATH):
        raise SystemExit(
            f"Host key not found at {HOST_KEY_PATH}. Generate one with:\n"
            f"  ssh-keygen -t rsa -b 2048 -f {HOST_KEY_PATH} -N ''"
        )

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen(100)
    logging.info("HONEYPOT_START listening on %s:%s", HOST, PORT)
    print(f"[+] SSH honeypot listening on {HOST}:{PORT}, logging to {LOG_PATH}")

    while True:
        client_sock, client_addr = sock.accept()
        t = threading.Thread(
            target=handle_connection, args=(client_sock, client_addr), daemon=True
        )
        t.start()


if __name__ == "__main__":
    main()
