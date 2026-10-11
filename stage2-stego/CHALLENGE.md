# Stage 2 — "Picture Imperfect"
**Domain:** Steganography   |   **Difficulty:** Easy

## Scenario
The attacker exfiltrated an internal memo hidden inside an innocuous image
on a compromised employee's personal cloud photo backup.

## Files provided
- `dist/memo_backup.jpg`

## Task
This image is more than it appears. Find the hidden data and recover the
flag.

## Flag format
`NOVA{...}`

## Hints
1. This image is heavier than it looks.
2. Check for steganography tool signatures before trying to brute-force
   anything — a weak, guessable passphrase is intentional here.
