# SSH Honeypot

A low-interaction SSH honeypot for the box's blue-team/detection angle.
It listens on port 2222, presents a believable OpenSSH banner, and logs:

- every connecting IP and port
- every username/password combination attempted
- every public-key auth attempt (with fingerprint)

...then **always denies authentication**. No real shell or filesystem
access is ever granted through this service - it exists purely to
generate a realistic log trail for detection/analysis exercises.

## Why include this
If your module wants both an offensive (exploit the box) and a
defensive (detect/analyze the attack) component, this gives you real
log data to work with: after someone attacks the box, `ssh_honeypot.log`
shows exactly what was probed, when, and from where - good material for
a log-review or basic-IDS section of your report.

## Install (run as root on the VM host)
```bash
cd honeypot
pip3 install -r requirements.txt

mkdir -p /etc/honeypot /var/log/honeypot
python3 -c "
import paramiko
key = paramiko.RSAKey.generate(2048)
key.write_private_key_file('/etc/honeypot/honeypot_host_key')
"

cp ssh_honeypot.py /usr/local/sbin/ssh_honeypot.py
cp ssh_honeypot.service /etc/systemd/system/ssh_honeypot.service
systemctl daemon-reload
systemctl enable --now ssh_honeypot

sudo ufw allow 2222/tcp
```

## Verifying it works
From another machine:
```bash
ssh -p 2222 root@<vm-ip>
# type any password - it will always be rejected
```
Then check the log:
```bash
tail -f /var/log/honeypot/ssh_honeypot.log
```
You should see a `CONNECT` line and an `AUTH_ATTEMPT ... -> DENIED` line
with the exact credentials that were tried.

## Analyzing the log (detection report)
After someone attacks the box, generate a summary report:
```bash
python3 analyze_honeypot_log.py /var/log/honeypot/ssh_honeypot.log
```
This prints:
- total connections / auth attempts / unique source IPs
- top source IPs by connection count
- top usernames and credential pairs tried
- naive brute-force detection (flags any IP with 5+ auth attempts
  within a 60-second window - both thresholds are adjustable via
  `--burst-threshold` and `--burst-window`)

Add `--json report.json` to also get a machine-readable version you can
drop straight into a report appendix or feed into a chart.

Example:
```bash
python3 analyze_honeypot_log.py /var/log/honeypot/ssh_honeypot.log \
  --json /home/user/honeypot_report.json \
  --burst-threshold 3 --burst-window 30
```

## Notes for your write-up
- This is intentionally **low-interaction** (no fake shell, no command
  logging) to keep the attack surface of the honeypot itself minimal -
  a compromised honeypot is a real risk in high-interaction designs
  (e.g. Cowrie-style honeypots that emulate a full shell).
- Real SSH stays on port 22 as the actual pivot path (see the main
  chain in `docs/SOLUTION.md`); this honeypot on 2222 is a separate,
  parallel decoy specifically for credential-harvesting visibility.
- Combined with `host_setup/decoy_service.py` (the fake admin service
  on 31337), this gives you two different flavors of decoy: one that
  wastes an attacker's time (decoy_service), and one that actively
  fingerprints their behavior (the honeypot).
