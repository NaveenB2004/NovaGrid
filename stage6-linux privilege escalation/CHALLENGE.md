# Stage 6 — "Breaching InternalOps"
**Domain:** Web Exploitation + Linux Privilege Escalation   |   **Difficulty:** Hard

## Scenario
NovaBreach's internal operations team runs a small web portal for on-call
staff. Earlier stages of this investigation showed the attackers were
interested in it. You have been authorised to assess the portal and the
server it runs on, and to find out how far an attacker could have gone.

Start from the outside and work your way in. There are two objectives:
gain a foothold on the server as a normal user, then take full control of
it.

## Target
- **Host:** `192.168.56.108` (host-only lab network)
- No credentials are provided. No source code is provided.

## Rules of engagement
- Only attack the target IP above. Do not attack the CTFd platform, other
  players, or any other machine on the network.
- Do not run denial-of-service attacks or anything that would destroy the
  target for other players.
- Everything on the target is deliberately vulnerable and fully in scope
  *unless* it is listed above as out of scope.
- Use your own attacker machine (for example Kali) on the same host-only
  network.

## Objectives
| # | Objective | Where to look |
|---|---|---|
| 1 | **User flag** — gain access as a regular user on the host | `user.txt` in that user's home directory |
| 2 | **Root flag** — escalate to full control of the host | `root.txt` in root's home directory |

Submit each flag as its own challenge in CTFd.

## Flag format
`flag{...}` — the flag is 32 hexadecimal characters inside the braces.

## Hints
Hints cost points in CTFd. Try without them first.

1. Not everything listening on the host is part of the target. Some
   services are decoys, and some watch you back.
2. Web applications often trust data that arrives from the client. Ask
   yourself what the app is trusting and whether you can change it.
3. What a compromised process can read is often more useful than what it
   can do. Look around the environment you land in before trying to break
   out of it.
4. When you have a shell as a normal user, check what you are allowed to run
   as root, and pay attention to *how* it is allowed to run.

## Notes
- The box is monitored. Noisy scanning and repeated failed logins against
  the wrong services will be logged.
- If the target stops responding, tell the organiser instead of trying to
  crash it again.


