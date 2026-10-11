#!/usr/bin/env bash
# Run this ON THE VM (as root) after the base OS install and Docker setup.
# It creates the pivot user, plants the sudo/LD_PRELOAD misconfig for the
# privesc stage, and drops the two flags.
set -euo pipefail

USER2_PASS='R3plicate_This_2026!'   # must match webapp/.internal/host_access.txt

# --- 1. Create the pivot user (reached via creds leaked in the container) ---
if ! id -u user2 >/dev/null 2>&1; then
    useradd -m -s /bin/bash user2
fi
echo "user2:${USER2_PASS}" | chpasswd

# --- 2. A plausible "allowed" admin command user2 can run as root ---
mkdir -p /usr/local/sbin
cat > /usr/local/sbin/logcheck <<'EOF'
#!/usr/bin/env bash
# Rotates/tails the internal ops log. Approved for on-call use.
tail -n 50 /var/log/internalops/app.log 2>/dev/null || echo "no recent log entries"
EOF
chmod 755 /usr/local/sbin/logcheck
mkdir -p /var/log/internalops
touch /var/log/internalops/app.log
chown root:root /usr/local/sbin/logcheck /var/log/internalops/app.log

# --- 3. THE VULNERABILITY: sudoers rule preserves LD_PRELOAD ---
# This mirrors a real, commonly-seen misconfiguration (see GTFOBins'
# LD_PRELOAD sudo entry): an admin adds env_keep for a dev's tool but
# it isn't scoped, so it also applies to this rule.
cat > /etc/sudoers.d/90-internalops <<'EOF'
Defaults:user2 env_keep += "LD_PRELOAD"
user2 ALL=(root) NOPASSWD: /usr/local/sbin/logcheck
EOF
chmod 440 /etc/sudoers.d/90-internalops
visudo -c -f /etc/sudoers.d/90-internalops

# --- 4. Flags ---
USER_FLAG="flag{$(openssl rand -hex 16)}"
ROOT_FLAG="flag{$(openssl rand -hex 16)}"

echo "$USER_FLAG" > /home/user2/user.txt
chown user2:user2 /home/user2/user.txt
chmod 440 /home/user2/user.txt

echo "$ROOT_FLAG" > /root/root.txt
chmod 400 /root/root.txt

# --- 5. Install the red-herring decoy service (recon difficulty bump) ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "${SCRIPT_DIR}/decoy_service.py" /usr/local/sbin/decoy_service.py
chmod 755 /usr/local/sbin/decoy_service.py
cp "${SCRIPT_DIR}/decoy_service.service" /etc/systemd/system/decoy_service.service
systemctl daemon-reload
systemctl enable --now decoy_service

# --- 6. Install the SSH honeypot (detection/blue-team component) ---
HONEYPOT_DIR="$(cd "${SCRIPT_DIR}/../honeypot" && pwd)"
pip3 install -q -r "${HONEYPOT_DIR}/requirements.txt"
mkdir -p /etc/honeypot /var/log/honeypot
if [ ! -f /etc/honeypot/honeypot_host_key ]; then
    python3 -c "
import paramiko
key = paramiko.RSAKey.generate(2048)
key.write_private_key_file('/etc/honeypot/honeypot_host_key')
"
fi
cp "${HONEYPOT_DIR}/ssh_honeypot.py" /usr/local/sbin/ssh_honeypot.py
cp "${HONEYPOT_DIR}/ssh_honeypot.service" /etc/systemd/system/ssh_honeypot.service
systemctl daemon-reload
systemctl enable --now ssh_honeypot

echo "---------------------------------------------"
echo "Setup complete."
echo "user2 password : ${USER2_PASS}"
echo "user.txt       : ${USER_FLAG}"
echo "root.txt       : ${ROOT_FLAG}"
echo "(keep this output for your grading/solution notes only)"
echo "---------------------------------------------"
