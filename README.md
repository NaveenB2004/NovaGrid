# NovaGrid 

These are the five supporting stages for the "Operation ShadowLedger" CTF
Play Box, designed to run alongside the Stage 6 "InternalOps" capstone
(the `ctf-hard-box` project you already have). Together they form the full
six-stage box described in the design report.

| Stage | Title | Domain | Difficulty | Delivery |
|---|---|---|---|---|
| 1 | The Digital Footprint | OSINT / Reconnaissance | Easy | Static files |
| 2 | Picture Imperfect | Steganography | Easy | Static file |
| 3 | The Cipher Memo | Cryptography | Moderate | Docker service + static file |
| 4 | Endpoint Autopsy | Digital Forensics | Moderate | Static files |
| 5 | Traffic Jam | Networking | Moderate–Hard | Static file + Docker service |
| 6 | Breaching InternalOps | Web + Linux | Hard | Dedicated VM *(see ctf-hard-box)* |

## One-time setup (on your build machine or the lab VM)

```bash
sudo apt update
sudo apt install -y python3-pip steghide libimage-exiftool-perl \
  mtools dosfstools zip vsftpd docker.io docker-compose-plugin
pip3 install --break-system-packages pillow scapy
```

## Build everything at once

```bash
cd shadowledger
./build_all.sh
```

This regenerates a **fresh, randomized flag** for every stage and writes
each one's `SOLUTION.txt` (private — for your grading/answer key only, do
not distribute to players). Re-run it any time you want a clean set of
flags for a new cohort or a re-run.

## Deploying each stage

### Stage 1 — OSINT (static, no server needed)
Just distribute the `stage1-osint/site/` folder to players (e.g. upload it
as a zip to CTFd, or serve it with any static file server / `python3 -m
http.server` from inside `site/`).

### Stage 2 — Steganography (static, no server needed)
Distribute `stage2-stego/dist/memo_backup.jpg` as a downloadable challenge
file in CTFd.

### Stage 3 — Cryptography (Docker service + static file)
```bash
cd stage3-crypto
docker compose up -d --build
```
This starts the oracle on port 4433. Separately distribute
`stage3-crypto/dist/memo.txt.enc` as a downloadable file.

### Stage 4 — Forensics (static, no server needed)
Distribute both `stage4-forensics/dist/endpoint.img` and
`stage4-forensics/dist/access.log` as downloadable challenge files.

### Stage 5 — Networking (static file + Docker service)
Before building, edit `stage5-network/vsftpd.conf` and set
`pasv_address` to the VM's real host-only IP (required for passive-mode
FTP to work for players connecting from a separate attacker VM). Then:
```bash
cd stage5-network
docker compose up -d --build
```
Separately distribute `stage5-network/dist/breach_capture.pcap` as a
downloadable file.

### Stage 6 — Capstone
Follow the existing `ctf-hard-box/README.md` you already have.

## Player-facing material
Each stage folder has a `CHALLENGE.md` — this is the text you give to
players (via CTFd's challenge description field, or as a README alongside
the downloadable files). It does **not** contain the flag or the solution.

## Verifying everything before you hand it out
Every stage in this bundle was built and solved end-to-end during
development to confirm the intended path actually works:
- Stage 1: all three fragments extract correctly and reassemble to the flag
- Stage 2: `steghide extract` recovers the flag with the hinted passphrase
- Stage 3: the chosen-plaintext attack against the oracle recovers the key,
  which correctly decrypts the static memo
- Stage 4: `strings`/carving recovers both flags; the log timestamp
  correlation correctly identifies the real one
- Stage 5: the pcap's DNS labels decode to the correct passphrase, which
  correctly unlocks the FTP archive

Re-verify this yourself after any edits, and again after deploying to the
actual lab VM (network/IP-dependent stages — 3, 5, 6 — are the most likely
to need adjustment for your specific environment).
