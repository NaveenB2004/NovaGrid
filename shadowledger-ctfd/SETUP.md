# Operation ShadowLedger — CTFd Platform Setup

This stands up the **platform host** described in §7.1 of the design report:
the CTFd container stack behind an nginx TLS front end, reachable only from
the isolated CTF-LAN. Stages 3, 5, and 6 are separate hosts/services you'll
wire in later — this doc only covers CTFd itself.

## 1. Prerequisites

- A hypervisor host with VirtualBox installed, ~8 vCPU / 16GB RAM / 100GB SSD
  free (per §5's resource estimate — that's the *box total*, this VM alone
  needs much less: 2 vCPU / 4GB RAM / 20GB disk is plenty for CTFd).
- An Ubuntu Server 24.04.4 LTS ISO.

## 2. Create the isolated CTF-LAN (VirtualBox host-only network)

This is what actually enforces the report's isolation requirement — not
anything in Docker.

Run this on your **hypervisor host** — the physical machine VirtualBox is
installed on (your laptop or the lab machine), in its own terminal,
*not* inside any VM. There's no VM to be inside yet at this point; this step
creates the virtual network adapter the platform VM will attach to in step 3.

**On Windows**, `VBoxManage.exe` isn't on PATH by default. Either add
`C:\Program Files\Oracle\VirtualBox` to PATH, or just call it by full path
as below. Also — Windows names host-only adapters differently from Linux/macOS
(no `vboxnet0`), so the commands themselves differ, not just the path:

```powershell
& "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" hostonlyif create
& "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" list hostonlyifs
# ^ find the "Name:" field of the adapter you just created, e.g.
#   "VirtualBox Host-Only Ethernet Adapter #2" — use that exact string below

& "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" hostonlyif ipconfig "VirtualBox Host-Only Ethernet Adapter #2" --ip 10.13.37.1 --netmask 255.255.255.0

& "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" list dhcpservers
# find the matching NetworkName (e.g. HostInterfaceNetworking-VirtualBox Host-Only Ethernet Adapter #2)
& "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" dhcpserver remove --netname "<paste that NetworkName>"
```

**On macOS/Linux**, VBoxManage is normally already on PATH, and the adapter
really is named `vboxnet0`:

```bash
VBoxManage hostonlyif create
VBoxManage hostonlyif ipconfig vboxnet0 --ip 10.13.37.1 --netmask 255.255.255.0
# Turn OFF the DHCP server VirtualBox adds by default, so IPs are deliberate
VBoxManage dhcpserver remove --netname HostInterfaceNetworking-vboxnet0 || true
```

Either way, the goal is the same by the end of this step: one host-only
adapter, statically addressed `10.13.37.1/24`, with no DHCP server running
on it. Note whatever the adapter's real name turned out to be — you'll pick
it from a dropdown in step 3 when attaching the VM's NIC, so the exact
string doesn't need to be typed again.

## 3. Create and provision the platform VM

1. New VM → Ubuntu Server 24.04.4 LTS, 2 vCPU / 4GB RAM / 20GB disk.
2. Network adapter: **Host-only Adapter**, attached to `vboxnet0`. Do **not**
   add a second bridged/NAT adapter — the report's §9.2 isolation guarantee
   depends on this VM having no other route out.
3. During install, give it a static IP on the host-only subnet, e.g.
   `10.13.37.10/24`, no gateway.
4. After first boot:
   ```bash
   sudo apt update && sudo apt install -y docker.io docker-compose-plugin openssl
   sudo usermod -aG docker $USER
   # log out/in for the group change to apply
   ```

## 4. Deploy CTFd

1. Copy this whole `shadowledger-ctfd/` directory onto the VM.
2. Generate secrets:
   ```bash
   cd shadowledger-ctfd
   cp .env.example .env
   # replace the three CHANGE_ME values in .env — e.g.:
   python3 -c "import secrets; print(secrets.token_hex(32))"   # -> CTFD_SECRET_KEY
   openssl rand -hex 16                                        # -> each MySQL password
   ```
3. Generate the self-signed cert for the lab TLS endpoint:
   ```bash
   chmod +x nginx/generate-cert.sh
   ./nginx/generate-cert.sh
   ```
4. Bring it up:
   ```bash
   docker compose up -d
   docker compose ps      # all four services should show "Up"
   docker compose logs -f ctfd   # watch until it reports "Booting worker"
   ```
5. From another VM on the same host-only network, browse to
   `https://10.13.37.10/` (accept the self-signed cert warning — expected,
   see the note in `generate-cert.sh`) and you should hit the CTFd setup
   wizard.

## 5. CTFd setup wizard

Run through the wizard once:

- **Event name**: Operation ShadowLedger
- **Event description**: short version of §3.1's scenario blurb
- Create the admin account (this is the account your group uses to author
  challenges — don't reuse it as a player account for testing).
- **Challenge visibility**: Private (participants must register/log in)
- **Registration**: your call — for a coursework demo, "Private" with
  accounts pre-created for the marker is usually cleanest.
- Skip the theme/logo step for now — cosmetic, do it later if you want.

Then, before loading any challenges:

- **Admin Panel → Config → Time**: set a start/end window if you want the
  box to auto-lock outside a play period.
- **Admin Panel → Config → Uploads**: leave as filesystem (the compose file
  already mounts `/var/uploads` to `./CTFd-data/uploads`, which is what gets
  used for Stages 1, 2, and 4's static bundles).

## 6. Create the six challenge categories

In **Admin Panel → Challenges → +**, create one challenge per stage, using
the domain as the category so the scoreboard groups them the way §4 of the
report describes:

| Stage | Category (CTFd field) | Type | Points (suggested) |
|---|---|---|---|
| 1 — The Digital Footprint | OSINT / Reconnaissance | standard | 50 |
| 2 — Picture Imperfect | Steganography | standard | 75 |
| 3 — The Cipher Memo | Cryptography | standard | 150 |
| 4 — Endpoint Autopsy | Digital Forensics | standard | 150 |
| 5 — Traffic Jam | Networking | standard | 250 |
| 6 — Breaching InternalOps | Web / Linux (capstone) | **two flags** — use CTFd's multi-flag or split into "S6 User" + "S6 Root" challenges with the root one requiring the user one as a prerequisite | 300 + 350 |

Leave the actual flag values, hints, and file uploads for when each stage's
content is actually built — this step just gets the scoreboard skeleton in
place so you can plug stages in independently as your group finishes them.

## 7. Verify isolation before going further

From the CTFd VM, confirm there is genuinely no path out:

```bash
ping -c2 8.8.8.8        # should fail / time out
curl -m5 https://example.com   # should fail
```

If either succeeds, stop and recheck step 3 — something is bridged/NAT'd
that shouldn't be, and that's a marked security-controls criterion (§9.3),
not just good practice.

## 8. Snapshot

Once the wizard is done and the empty categories are in place, shut the VM
down cleanly and take a VirtualBox snapshot (`base-ctfd-ready`) before
anyone starts authoring challenge content. That's your reset point per the
report's §6 "no corruptible state" reset plan for the static stages.

## Next

Ping me for whichever stage you want next — the crypto oracle (Stage 3) and
the network segment (Stage 5) are both small, self-contained Docker
services, so either is a natural next build. Stage 6 is the biggest lift
(Flask app + host-level privesc chain), worth its own session.
