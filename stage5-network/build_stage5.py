#!/usr/bin/env python3
"""
build_stage5.py - builds the Stage 5 "Traffic Jam" networking challenge.

Produces:
  1. dist/breach_capture.pcap - a packet capture containing a sequence of
     DNS queries whose subdomain labels are Base32-encoded fragments of a
     passphrase (simulating DNS-tunnelled exfiltration).
  2. ftp_share/backup.zip - a password-protected archive (password =
     the same passphrase) containing the flag, to be placed on the live
     FTP server's anonymous-accessible share (see docker-compose.yml).

Requires: scapy (pip), zip (apt)

Usage:
    python3 build_stage5.py
Output:
    dist/breach_capture.pcap
    ftp_share/backup.zip
    SOLUTION.txt   (private - flag + passphrase, for grading only)
"""
import base64
import os
import random
import string
import subprocess
import sys
from scapy.all import Ether, IP, UDP, DNS, DNSQR, wrpcap

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from flag_utils import build_mixed_flag

BASE = os.path.dirname(__file__)
DIST = os.path.join(BASE, "dist")
FTP_SHARE = os.path.join(BASE, "ftp_share")
os.makedirs(DIST, exist_ok=True)
os.makedirs(FTP_SHARE, exist_ok=True)

EXFIL_DOMAIN = "sync.novagrid-internal.net"
ATTACKER_IP = "203.0.113.77"
VICTIM_IP = "10.10.10.45"
DNS_SERVER_IP = "10.10.10.1"


THEME_PHRASES = [
    ["tunneled", "through", "dns"],
    ["exfil", "hidden", "in", "queries"],
    ["the", "traffic", "never", "lies"],
    ["base32", "gave", "it", "away"],
]


def build_flag():
    words = random.choice(THEME_PHRASES)
    flag, _ = build_mixed_flag("NOVA", words)
    return flag


def build_passphrase():
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=12))


def chunk(s, n):
    return [s[i:i + n] for i in range(0, len(s), n)]


def build_pcap(passphrase, out_path):
    b32 = base64.b32encode(passphrase.encode()).decode().rstrip("=")
    chunks = chunk(b32, 8)  # small chunks per label, like a real tunnel

    packets = []
    ts = 1768435200.0  # arbitrary fixed capture start time
    sport = 51820
    for i, c in enumerate(chunks):
        qname = f"{c}.{EXFIL_DOMAIN}"
        pkt = (
            Ether() /
            IP(src=VICTIM_IP, dst=DNS_SERVER_IP) /
            UDP(sport=sport + i, dport=53) /
            DNS(rd=1, qd=DNSQR(qname=qname, qtype="TXT"))
        )
        pkt.time = ts + i * 0.35
        packets.append(pkt)

    # sprinkle in a handful of unrelated, ordinary-looking DNS queries as
    # noise so the player has to filter, not just read every packet
    noise_domains = ["updates.ubuntu.com", "pool.ntp.org", "api.github.com",
                      "clients3.google.com", "outlook.office365.com"]
    for i, d in enumerate(noise_domains):
        pkt = (
            Ether() /
            IP(src=VICTIM_IP, dst=DNS_SERVER_IP) /
            UDP(sport=52000 + i, dport=53) /
            DNS(rd=1, qd=DNSQR(qname=d, qtype="A"))
        )
        pkt.time = ts - 5 + i * 1.1
        packets.append(pkt)

    packets.sort(key=lambda p: p.time)
    wrpcap(out_path, packets)


def build_protected_ftp_archive(flag, passphrase, out_path):
    flag_file = os.path.join(BASE, "_flag.txt")
    with open(flag_file, "w") as f:
        f.write(flag + "\n")
    if os.path.exists(out_path):
        os.remove(out_path)
    subprocess.run(
        ["zip", "-j", "-P", passphrase, out_path, flag_file],
        check=True, capture_output=True,
    )
    os.remove(flag_file)


def main():
    flag = build_flag()
    passphrase = build_passphrase()

    pcap_path = os.path.join(DIST, "breach_capture.pcap")
    build_pcap(passphrase, pcap_path)

    archive_path = os.path.join(FTP_SHARE, "backup.zip")
    build_protected_ftp_archive(flag, passphrase, archive_path)

    solution_path = os.path.join(BASE, "SOLUTION.txt")
    b32 = base64.b32encode(passphrase.encode()).decode().rstrip("=")
    with open(solution_path, "w") as f:
        f.write(f"Stage 5 flag: {flag}\n")
        f.write(f"Passphrase (also the zip password): {passphrase}\n")
        f.write(f"Base32 of passphrase (as seen split across DNS labels): {b32}\n")
        f.write(f"pcap: {pcap_path}\n")
        f.write(f"Protected archive: {archive_path} (served via anonymous FTP)\n")
        f.write("Solve: filter the pcap for DNS queries to *.novagrid-internal.net, "
                "concatenate the subdomain labels in capture-time order, "
                "Base32-decode the result to recover the passphrase, nmap the "
                "live segment to find the anonymous FTP server, download "
                "backup.zip, and unzip it with the recovered passphrase.\n")

    print(f"[+] Stage 5 built. Flag: {flag} | Passphrase: {passphrase}")
    print(f"[+] pcap: {pcap_path}")
    print(f"[+] FTP share archive: {archive_path}")
    print(f"[+] Solution notes written to {solution_path}")


if __name__ == "__main__":
    main()
