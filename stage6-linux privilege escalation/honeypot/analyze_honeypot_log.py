#!/usr/bin/env python3
"""
analyze_honeypot_log.py - parses ssh_honeypot.log and produces a
detection/summary report: connection counts per IP, most-tried
credentials, a timeline, and basic burst/brute-force detection.

Usage:
    python3 analyze_honeypot_log.py /var/log/honeypot/ssh_honeypot.log
    python3 analyze_honeypot_log.py ssh_honeypot.log --json report.json
"""
import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime

CONNECT_RE = re.compile(
    r"^(?P<ts>[\d-]+ [\d:,]+) CONNECT ip=(?P<ip>[\d.]+) port=(?P<port>\d+)"
)
AUTH_RE = re.compile(
    r"^(?P<ts>[\d-]+ [\d:,]+) AUTH_ATTEMPT ip=(?P<ip>[\d.]+) "
    r"username=(?P<username>'[^']*'|\"[^\"]*\") "
    r"password=(?P<password>'[^']*'|\"[^\"]*\") -> (?P<result>\w+)"
)
AUTH_PUBKEY_RE = re.compile(
    r"^(?P<ts>[\d-]+ [\d:,]+) AUTH_ATTEMPT ip=(?P<ip>[\d.]+) "
    r"username=(?P<username>'[^']*'|\"[^\"]*\") auth_type=publickey "
    r"fingerprint=(?P<fingerprint>\S+) -> (?P<result>\w+)"
)

TS_FORMAT = "%Y-%m-%d %H:%M:%S,%f"


def strip_quotes(s: str) -> str:
    return s[1:-1] if s and s[0] in "'\"" and s[-1] in "'\"" else s


def parse_log(path):
    connects = []
    auth_attempts = []

    with open(path, "r", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")

            m = AUTH_RE.match(line)
            if m:
                auth_attempts.append({
                    "ts": m.group("ts"),
                    "ip": m.group("ip"),
                    "username": strip_quotes(m.group("username")),
                    "password": strip_quotes(m.group("password")),
                    "type": "password",
                    "result": m.group("result"),
                })
                continue

            m = AUTH_PUBKEY_RE.match(line)
            if m:
                auth_attempts.append({
                    "ts": m.group("ts"),
                    "ip": m.group("ip"),
                    "username": strip_quotes(m.group("username")),
                    "fingerprint": m.group("fingerprint"),
                    "type": "publickey",
                    "result": m.group("result"),
                })
                continue

            m = CONNECT_RE.match(line)
            if m:
                connects.append({
                    "ts": m.group("ts"),
                    "ip": m.group("ip"),
                    "port": m.group("port"),
                })
                continue

    return connects, auth_attempts


def build_report(connects, auth_attempts, burst_threshold=5, burst_window_sec=60):
    ips = Counter(c["ip"] for c in connects)
    creds = Counter(
        (a["username"], a.get("password", "<pubkey>")) for a in auth_attempts
    )
    usernames = Counter(a["username"] for a in auth_attempts)

    # naive brute-force burst detection: N+ attempts from the same IP
    # within burst_window_sec of each other
    by_ip_times = defaultdict(list)
    for a in auth_attempts:
        try:
            ts = datetime.strptime(a["ts"], TS_FORMAT)
        except ValueError:
            continue
        by_ip_times[a["ip"]].append(ts)

    bursts = {}
    for ip, times in by_ip_times.items():
        times.sort()
        max_in_window = 1
        start = 0
        for end in range(len(times)):
            while (times[end] - times[start]).total_seconds() > burst_window_sec:
                start += 1
            max_in_window = max(max_in_window, end - start + 1)
        if max_in_window >= burst_threshold:
            bursts[ip] = max_in_window

    timeline = sorted(connects + auth_attempts, key=lambda x: x["ts"])

    report = {
        "total_connections": len(connects),
        "total_auth_attempts": len(auth_attempts),
        "unique_source_ips": len(ips),
        "top_source_ips": ips.most_common(10),
        "top_usernames_tried": usernames.most_common(10),
        "top_credential_pairs": [
            {"username": u, "password": p, "count": c}
            for (u, p), c in creds.most_common(10)
        ],
        "suspected_bruteforce_ips": [
            {"ip": ip, "max_attempts_in_window": n,
             "window_seconds": burst_window_sec}
            for ip, n in sorted(bursts.items(), key=lambda x: -x[1])
        ],
        "first_event_ts": timeline[0]["ts"] if timeline else None,
        "last_event_ts": timeline[-1]["ts"] if timeline else None,
    }
    return report


def print_human_report(report):
    print("=" * 60)
    print("SSH HONEYPOT - DETECTION SUMMARY")
    print("=" * 60)
    print(f"Total connections     : {report['total_connections']}")
    print(f"Total auth attempts    : {report['total_auth_attempts']}")
    print(f"Unique source IPs      : {report['unique_source_ips']}")
    print(f"First event            : {report['first_event_ts']}")
    print(f"Last event             : {report['last_event_ts']}")

    print("\nTop source IPs:")
    for ip, count in report["top_source_ips"]:
        print(f"  {ip:<20} {count} connection(s)")

    print("\nTop usernames tried:")
    for username, count in report["top_usernames_tried"]:
        print(f"  {username:<20} {count} time(s)")

    print("\nTop credential pairs tried:")
    for entry in report["top_credential_pairs"]:
        print(f"  {entry['username']:<15} / {entry['password']:<15} "
              f"x{entry['count']}")

    print("\nSuspected brute-force sources "
          "(>= burst threshold attempts in the time window):")
    if not report["suspected_bruteforce_ips"]:
        print("  none detected")
    else:
        for entry in report["suspected_bruteforce_ips"]:
            print(f"  {entry['ip']:<20} {entry['max_attempts_in_window']} "
                  f"attempts within {entry['window_seconds']}s")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze the SSH honeypot log and produce a detection summary"
    )
    parser.add_argument("logfile", help="path to ssh_honeypot.log")
    parser.add_argument("--json", metavar="OUTFILE",
                         help="also write the report as JSON to OUTFILE")
    parser.add_argument("--burst-threshold", type=int, default=5,
                         help="min attempts within the window to flag as brute-force (default: 5)")
    parser.add_argument("--burst-window", type=int, default=60,
                         help="time window in seconds for burst detection (default: 60)")
    args = parser.parse_args()

    try:
        connects, auth_attempts = parse_log(args.logfile)
    except FileNotFoundError:
        print(f"[-] Log file not found: {args.logfile}", file=sys.stderr)
        sys.exit(1)

    report = build_report(
        connects, auth_attempts,
        burst_threshold=args.burst_threshold,
        burst_window_sec=args.burst_window,
    )
    print_human_report(report)

    if args.json:
        with open(args.json, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\n[+] JSON report written to {args.json}")


if __name__ == "__main__":
    main()
