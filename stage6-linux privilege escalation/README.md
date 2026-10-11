# Hard-Tier CTF Box - "InternalOps"

A deliberately vulnerable VM for a penetration-testing module project.

**Difficulty:** Hard
**Chain:** JWT `alg:none` forgery -> insecure deserialization (RCE in container)
-> credential discovery -> host pivot -> `sudo`/`LD_PRELOAD` privesc to root

Everything here is intentionally insecure. Only run this inside an isolated
VM/host-only network built for this assignment - never on a shared or
internet-facing network.

## Repo layout
```
ctf-hard-box/
  webapp/            Vulnerable Flask app + Dockerfile/compose
    app.py
    templates/index.html
    .internal/host_access.txt   <- "leaked" pivot creds
  host_setup/
    setup_host.sh          Run once on the VM as root
    decoy_service.py        Red-herring TCP service (recon difficulty)
    decoy_service.service   systemd unit for the decoy
  attacker_scripts/
    jwt_forge.py         Forges the admin JWT
    pickle_rce.py        Builds/sends the pickle RCE payload
    evil.c               LD_PRELOAD privesc library (build on target)
  honeypot/
    ssh_honeypot.py         Low-interaction SSH honeypot (logs, denies auth)
    ssh_honeypot.service    systemd unit for the honeypot
    analyze_honeypot_log.py Parses the log into a detection summary report
  docs/
    SOLUTION.md         Private walkthrough - do NOT distribute to players
    DESIGN.md            Design rationale for your project write-up
```

## Build steps

### 1. Base VM
Follow the earlier VM setup (Debian/Ubuntu minimal install, Host-only or
NAT network, OpenSSH server enabled). Update the OS:
```
sudo apt update && sudo apt upgrade -y
```

### 2. Install Docker
```
sudo apt install -y docker.io docker-compose-plugin
sudo systemctl enable --now docker
```

### 3. Copy this project onto the VM
Copy the whole `ctf-hard-box/` folder onto the VM (scp, shared folder, or
git clone if you push it to a private repo).

### 4. Fix the pivot-creds file with the VM's real host-only IP
Before building, edit `webapp/.internal/host_access.txt` and replace
`10.10.10.X` with the VM's actual host-only network IP (`ip a` on the VM).
This is what the attacker will read after achieving RCE in the container.

### 5. Build and start the vulnerable web app container
```
cd ctf-hard-box/webapp
sudo docker compose up -d --build
```
Verify it's up: `curl http://127.0.0.1:58421/`

### 6. Run the host setup script (creates user2 + the sudo misconfig + flags)
```
cd ../host_setup
sudo ./setup_host.sh
```
**Save the printed output** (password + both flag values) somewhere private
for your own grading reference - it will not be shown again.

### 7. Lock down anything unintended
```
sudo ufw enable
sudo ufw allow 22/tcp
sudo ufw allow 58421/tcp
sudo ufw allow 31337/tcp   # decoy service - intentionally left open
sudo ufw allow 2222/tcp    # ssh honeypot - intentionally left open
sudo ss -tulpn      # confirm nothing ELSE unintended is listening
```

### 8. Snapshot, then test the full chain yourself
Take a VirtualBox/VMware snapshot. Then, from a separate attacker VM (e.g.
Kali) on the same host-only network, run through the full attack path in
`docs/SOLUTION.md` end-to-end before handing the box to anyone.

### 9. Export for distribution
```
File -> Export Appliance -> select the VM -> Format: OVA
```

## Notes for your project write-up
- Explain each vuln class (JWT alg confusion, insecure deserialization,
  credential reuse across container/host boundary, sudo env_keep misconfig)
  and why it's realistic (all four map to real CVEs/advisories, not
  contrived bugs).
- Include the `docs/SOLUTION.md` chain as your own reference appendix, not
  something given to whoever attacks the box.
