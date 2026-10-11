# Stage 4 — "Endpoint Autopsy"
**Domain:** Digital Forensics   |   **Difficulty:** Moderate

## Scenario
A workstation believed to be the attacker's initial foothold was imaged
before it was wiped. Reconstruct what happened on it.

## Files provided
- `dist/endpoint.img` — a small forensic disk image
- `dist/access.log` — a log excerpt from the same time period

## Task
Recover deleted data from the image. You'll find more than one
candidate answer — use the log to work out which one is genuine.

## Flag format
`NOVA{...}`

## Hints
1. Not everything that looks like a flag is the flag.
2. Check timestamps, not just content.
