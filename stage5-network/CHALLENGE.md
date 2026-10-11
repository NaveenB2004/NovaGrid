# Stage 5 — "Traffic Jam"
**Domain:** Networking   |   **Difficulty:** Moderate–Hard

## Scenario
A network tap captured traffic during the breach window. Whatever
technique the attacker used to get data out may still be sitting there on
the live network today.

## Files provided
- `dist/breach_capture.pcap`

## Task
Analyze the capture to recover a hidden passphrase, then find and access a
live service on the network segment that requires it.

## Flag format
`NOVA{...}`

## Hints
1. DNS queries aren't always about DNS.
2. Base32's alphabet has no lowercase letters and no 0 or 1.
