#!/usr/bin/env python3
"""
build_stage3.py - generates the Stage 3 flag and the static encrypted
memo file that players must decrypt using the key they recover from the
crypto_oracle.py service (same fixed key, ORACLE_KEY env var / default
below - keep these in sync at deploy time).

Usage:
    python3 build_stage3.py
Output:
    dist/memo.txt.enc     (base64 ciphertext - the challenge file)
    SOLUTION.txt           (private - flag + key, for grading only)
"""
import base64
import os
import random
import string
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from flag_utils import build_mixed_flag

BASE = os.path.dirname(__file__)
DIST = os.path.join(BASE, "dist")
os.makedirs(DIST, exist_ok=True)

# Must match ORACLE_KEY used by crypto_oracle.py at deploy time.
KEY = "N0v4Gr1dSecretKey2024!".encode()


def xor_encrypt(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


THEME_PHRASES = [
    ["weak", "cipher", "broken"],
    ["key", "reuse", "exposed"],
    ["custom", "crypto", "fails"],
    ["xor", "is", "not", "encryption"],
]


def build_flag():
    words = random.choice(THEME_PHRASES)
    flag, _ = build_mixed_flag("NOVA", words)
    return flag


def main():
    flag = build_flag()
    memo_plaintext = (
        "INTERNAL MEMO - NovaGrid Ops\n"
        "From: j.alderman@internal\nTo: ops-team@internal\n"
        "Subject: Re: scheduled maintenance window\n\n"
        "Confirming the maintenance window for this weekend. Access code "
        f"for the ops portal rollback if needed: {flag}\n"
        "Please do not forward this outside the team.\n"
    ).encode()

    ciphertext = xor_encrypt(memo_plaintext, KEY)
    out_path = os.path.join(DIST, "memo.txt.enc")
    with open(out_path, "wb") as f:
        f.write(base64.b64encode(ciphertext))

    solution_path = os.path.join(BASE, "SOLUTION.txt")
    with open(solution_path, "w") as f:
        f.write(f"Stage 3 flag: {flag}\n")
        f.write(f"Oracle key: {KEY.decode()}\n")
        f.write(f"Challenge file: {out_path} (base64 of XOR(plaintext, key))\n")
        f.write("Solve: query the oracle with a long, mostly-repeating "
                "plaintext (e.g. 40 'A' characters) to recover the "
                "keystream via XOR differential analysis against known "
                "plaintext, reconstruct the key, then XOR-decrypt the "
                "base64-decoded memo file with that key.\n")

    print(f"[+] Stage 3 built. Flag: {flag}")
    print(f"[+] Challenge file: {out_path}")
    print(f"[+] Solution notes written to {solution_path}")


if __name__ == "__main__":
    main()
