# Stage 3 — "The Cipher Memo"
**Domain:** Cryptography   |   **Difficulty:** Moderate

## Scenario
An intercepted internal memo is protected by an in-house "custom"
encryption scheme. The team that built it is confident it's secure because
nobody outside the company knows the algorithm. You know better.

## Connect to the oracle
```
nc <target-ip> 4433
```
Send it any text and it will "encrypt" it for you.

## Files provided
- `dist/memo.txt.enc` — the real, intercepted memo, already encrypted

## Task
Use the oracle to work out how the "encryption" really works, recover
whatever secret makes it work, and use that to decrypt the provided memo.

## Flag format
`NOVA{...}`

## Hints
1. The service will encrypt anything you send it — that's not nothing.
2. XOR is its own inverse.
