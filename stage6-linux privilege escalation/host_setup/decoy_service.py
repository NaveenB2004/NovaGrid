#!/usr/bin/env python3
"""
decoy_service.py - a red herring TCP service for the CTF box.

Listens on port 31337 and looks like an old, custom "admin backdoor"
protocol - the kind of thing that gets an attacker excited when nmap's
service/version detection can't fingerprint it. In reality it's a dead
end: banner-grabbing and even brute-forcing it teaches nothing and leads
nowhere. Its only purpose is to cost the attacker some time and reward
players who prioritize enumeration breadth over depth on any one lead.

Deploy as a systemd service on the HOST (not in the container) so it
shows up in nmap alongside the real ports.
"""
import socketserver

BANNER = b"legacyOpsAdmin build 0.9.3-internal (unsupported)\r\n> "

FAKE_RESPONSES = {
    b"help": b"commands: status, version, quit\r\n> ",
    b"status": b"service degraded - see ticket OPS-4471\r\n> ",
    b"version": b"legacyOpsAdmin 0.9.3-internal\r\n> ",
}


class DecoyHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.request.sendall(BANNER)
        while True:
            data = self.request.recv(1024).strip().lower()
            if not data or data == b"quit":
                break
            self.request.sendall(
                FAKE_RESPONSES.get(data, b"unrecognized command\r\n> ")
            )


if __name__ == "__main__":
    HOST, PORT = "0.0.0.0", 31337
    with socketserver.ThreadingTCPServer((HOST, PORT), DecoyHandler) as server:
        server.serve_forever()
