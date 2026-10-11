# Design Rationale - "InternalOps" Hard-Tier CTF Box

## Learning objectives
This box was designed to require chaining four distinct, realistic
vulnerability classes rather than any single "one-shot" exploit:

| Stage | Vulnerability class | Real-world analogue |
|---|---|---|
| 1 | Full-range port scanning discipline | Services often run on non-default ports in real environments; default top-1000 scans miss them |
| 2 | JWT algorithm-confusion (`alg:none`) | CVE-class bug seen in multiple JWT library misconfigurations (e.g. early `node-jsonwebtoken`, various custom implementations) |
| 3 | Insecure deserialization (Python `pickle`) | Matches real advisories (e.g. Django/Flask apps unpickling user input); OWASP A08:2021 |
| 4 | Container/host credential leakage & reuse | Common in real breaches - secrets committed to app configs, reused across environments |
| 5 | `sudo` `env_keep` misconfiguration + `LD_PRELOAD` injection | Documented technique in GTFOBins; realistic sysadmin mistake when scoping `Defaults env_keep` too broadly |

## Why this qualifies as "hard"
- No stage is solvable by running a single public exploit/script found via
  `searchsploit` - each requires understanding the underlying mechanism
  (JWT structure, pickle's `__reduce__` protocol, dynamic linker behavior).
- The chain requires **pivoting between two separate privilege contexts**
  (container -> host), which is a step many "medium" boxes skip.
- The final privesc is not a checklist GTFOBins lookup on an obvious
  `sudo -l` entry - the attacker must realize `env_keep` extends the
  intended low-risk command into a full privilege-preservation channel.
- A decoy service (`decoy_service.py`) is included to penalize attackers
  who fixate on the first unusual thing they find instead of completing
  broad enumeration - a realistic and commonly tested discipline in
  professional pentesting engagements.

## Threat modeling summary (for a report/write-up)
- **Entry point:** web application exposed on a non-standard port.
- **Trust boundary broken at each stage:**
  1. Authentication trust broken via JWT forgery (no valid credentials
     needed for stage 2 onward).
  2. Process/data trust broken via deserialization of untrusted input.
  3. Environment trust broken via secrets left in application config
     inside the container image.
  4. Privilege trust broken via an overly broad `sudoers` environment
     preservation rule.

## Suggested rubric for grading if peers attack the box
| Milestone | Points |
|---|---|
| Full port scan finds the hidden web service | 10 |
| Forges valid admin JWT | 20 |
| Achieves RCE via pickle deserialization | 25 |
| Finds pivot credentials and reaches the host as `user2` | 20 |
| Identifies the `env_keep`/`LD_PRELOAD` misconfiguration | 10 |
| Achieves root and submits both flags | 15 |

## Limitations / things to disclose in your write-up
- The container runs its process as root inside the container namespace
  (simplifies the exercise); in a hardened real deployment this would
  itself be flagged as a misconfiguration worth remediating.
- The decoy service is unauthenticated by design and intentionally does
  nothing exploitable - documented here so a grader doesn't mistake it
  for an unintended vulnerability.
