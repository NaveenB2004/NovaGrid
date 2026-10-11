#!/usr/bin/env python3
"""
crypto_oracle.py - Stage 3 "The Cipher Memo" challenge service.

A deliberately weak "custom encryption" TCP service: it XORs whatever
plaintext a connecting client sends against a fixed, reused key, then
base64-encodes the result. This lets a player recover the key via a
chosen-plaintext attack (XOR is trivially broken under key reuse), then
apply that key to the separately-provided static memo ciphertext to
recover the flag.

Run as a long-lived service (see Dockerfile / systemd unit):
    python3 crypto_oracle.py
Listens on 0.0.0.0:4433.
"""
import base64
import os
import socketserver

KEY = os.environ.get("ORACLE_KEY", "N0v4Gr1dSecretKey2024!").encode()

BANNER = (
    b"NovaGrid Internal Memo Encryption Oracle v1.0\r\n"
    b"Send plaintext (one line, ends with newline) to receive base64 ciphertext.\r\n"
    b"> "
)


def xor_encrypt(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


class OracleHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.request.sendall(BANNER)
        while True:
            data = self.request.recv(4096)
            if not data:
                break
            plaintext = data.rstrip(b"\r\n")
            if plaintext.lower() in (b"quit", b"exit"):
                break
            ciphertext = xor_encrypt(plaintext, KEY)
            response = base64.b64encode(ciphertext) + b"\r\n> "
            self.request.sendall(response)


if __name__ == "__main__":
    HOST, PORT = "0.0.0.0", 4433
    with socketserver.ThreadingTCPServer((HOST, PORT), OracleHandler) as server:
        print(f"[+] Crypto oracle listening on {HOST}:{PORT}")
        server.serve_forever()
