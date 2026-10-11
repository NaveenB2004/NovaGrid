# Stage 1 — "The Digital Footprint"
**Domain:** OSINT / Reconnaissance   |   **Difficulty:** Easy

## Scenario
A NovaGrid Utilities employee's public online presence was used to build a
pretext for the later breach. You've been given a starting point — explore
what's publicly visible and reconstruct what the attacker learned.

## Files provided
- `site/profile.html` — a mock "SocialSphere" profile page
- `site/public-records.html` — a mock public business directory page
- `site/assets/profile.jpg` — a profile photo linked from the profile page

Open `site/profile.html` in a browser (or just read the files directly) to
begin.

## Task
Find three hidden flag fragments across the provided pages and combine them
**in chronological order** (oldest to newest, based on the dates shown on
each page) to form the flag.

## Flag format
`NOVA{...}`

## Hints
1. Not everything on a page is meant to be read in the browser.
2. Images carry more than pixels.
