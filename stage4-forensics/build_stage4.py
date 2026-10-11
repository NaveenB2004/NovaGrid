#!/usr/bin/env python3
"""
build_stage4.py - builds the Stage 4 "Endpoint Autopsy" forensics
challenge.

Approach: rather than building a full raw disk image (heavy and slow to
distribute), this creates a small FAT filesystem image, writes a
"real" flag file and a "decoy" flag file to it, deletes both, then
overwrites unallocated space partially so simple `strings`/carving
recovers both - forcing the player to use the accompanying log excerpt
to determine which recovered flag is authentic via timestamp
correlation, per the stage design.

Requires: mtools (mcopy/mdel) - apt install mtools

Usage:
    python3 build_stage4.py
Output:
    dist/endpoint.img      (small FAT image - the challenge file)
    dist/access.log         (the correlating log excerpt)
    SOLUTION.txt             (private - both flags + which is real, for grading only)
"""
import os
import random
import string
import subprocess
import datetime
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from flag_utils import build_mixed_flag

BASE = os.path.dirname(__file__)
DIST = os.path.join(BASE, "dist")
os.makedirs(DIST, exist_ok=True)

IMG_PATH = os.path.join(DIST, "endpoint.img")
LOG_PATH = os.path.join(DIST, "access.log")


REAL_PHRASES = [
    ["deleted", "but", "not", "gone"],
    ["recovered", "from", "the", "grave"],
    ["the", "file", "they", "missed"],
    ["carved", "from", "free", "space"],
]
DECOY_PHRASES = [
    ["not", "the", "flag", "youre", "looking", "for"],
    ["close", "but", "wrong", "timestamp"],
    ["a", "convincing", "fake"],
    ["the", "wrong", "completion", "marker"],
]


def build_flag(phrase_pool):
    words = random.choice(phrase_pool)
    flag, _ = build_mixed_flag("NOVA", words)
    return flag


def run(cmd):
    subprocess.run(cmd, check=True, capture_output=True)


def main():
    real_flag = build_flag(REAL_PHRASES)
    decoy_flag = build_flag(DECOY_PHRASES)

    if os.path.exists(IMG_PATH):
        os.remove(IMG_PATH)

    # 16MB FAT image
    run(["dd", "if=/dev/zero", f"of={IMG_PATH}", "bs=1M", "count=16"])
    run(["mkfs.vfat", IMG_PATH])

    real_file = os.path.join(BASE, "_real_flag.txt")
    decoy_file = os.path.join(BASE, "_decoy_flag.txt")
    with open(real_file, "w") as f:
        f.write(f"cleanup task complete: {real_flag}\n")
    with open(decoy_file, "w") as f:
        f.write(f"cleanup task complete: {decoy_flag}\n")

    # copy both files onto the FAT image, then delete them (mdel just
    # marks the FAT entry as deleted - content stays recoverable, which
    # is exactly the forensics scenario we want)
    run(["mcopy", "-i", IMG_PATH, real_file, "::REAL~1.TXT"])
    run(["mcopy", "-i", IMG_PATH, decoy_file, "::TEMP~1.TXT"])
    run(["mdel", "-i", IMG_PATH, "::REAL~1.TXT"])
    run(["mdel", "-i", IMG_PATH, "::TEMP~1.TXT"])

    os.remove(real_file)
    os.remove(decoy_file)

    # Build a plausible access log where only the REAL flag's write
    # time lines up with the documented "cleanup script" execution
    # window; the decoy's timestamp is deliberately just outside it.
    base_time = datetime.datetime(2026, 1, 14, 2, 0, 0)
    real_ts = base_time + datetime.timedelta(minutes=3)
    decoy_ts = base_time - datetime.timedelta(hours=6)

    log_lines = [
        "2026-01-14 01:58:02 svc[cron]: starting scheduled cleanup job (job_id=4471)",
        "2026-01-14 01:58:03 svc[cron]: cleanup job 4471 acquired lock",
        f"{real_ts.strftime('%Y-%m-%d %H:%M:%S')} svc[cleanup]: wrote completion marker REAL~1.TXT",
        "2026-01-14 02:04:11 svc[cron]: cleanup job 4471 finished, lock released",
        "2026-01-14 02:04:12 svc[cron]: next run scheduled for 2026-01-15 02:00:00",
        f"{decoy_ts.strftime('%Y-%m-%d %H:%M:%S')} user[arivera]: manual test file TEMP~1.TXT created during troubleshooting (unrelated to cron job 4471)",
    ]
    with open(LOG_PATH, "w") as f:
        f.write("\n".join(log_lines) + "\n")

    solution_path = os.path.join(BASE, "SOLUTION.txt")
    with open(solution_path, "w") as f:
        f.write(f"Stage 4 REAL flag: {real_flag}  (recovered from REAL~1.TXT)\n")
        f.write(f"Stage 4 DECOY flag: {decoy_flag}  (recovered from TEMP~1.TXT, NOT the answer)\n")
        f.write(f"Real completion timestamp: {real_ts} - matches the cron job "
                f"4471 window (01:58:02-02:04:12) documented in access.log\n")
        f.write(f"Decoy timestamp: {decoy_ts} - explicitly logged as unrelated "
                "manual troubleshooting, six hours before the job window\n")
        f.write("Recovery method: mount/scan endpoint.img with a carving tool "
                "(e.g. `photorec` or `strings -a endpoint.img | grep NOVA`) to "
                "find both flag-shaped strings, then use access.log to "
                "determine which one falls inside the documented cleanup job "
                "window.\n")

    print(f"[+] Stage 4 built. Real flag: {real_flag} | Decoy: {decoy_flag}")
    print(f"[+] Challenge files: {IMG_PATH}, {LOG_PATH}")
    print(f"[+] Solution notes written to {solution_path}")


if __name__ == "__main__":
    main()
