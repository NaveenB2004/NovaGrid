#!/usr/bin/env python3
"""
build_stage1.py - builds the Stage 1 "Digital Footprint" OSINT challenge.

Generates a random flag, splits it into 3 fragments, and hides them across
three synthetic (fully fictional) mock web pages: a "SocialSphere" profile
page (HTML comment), a profile photo (EXIF metadata), and a public records
page (hidden DOM text). Run this once per deployment to get a fresh flag.

Usage:
    python3 build_stage1.py
Output:
    site/profile.html
    site/public-records.html
    site/assets/profile.jpg
    SOLUTION.txt   (private - the full flag + order, for grading only)
"""
import random
import string
import subprocess
import os
import sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from flag_utils import build_mixed_flag

OUT_DIR = os.path.join(os.path.dirname(__file__), "site")
ASSETS_DIR = os.path.join(OUT_DIR, "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)


# Thematic two-word phrase pool for Stage 1 - meaningful in context of the
# scenario. build_mixed_flag() leetifies each word and inserts a random
# alphanumeric token at a random position among the words, so mixing
# isn't confined to a trailing suffix.
THEME_PHRASES = [
    ("digital", "footprint"),
    ("leaked", "identity"),
    ("public", "trail"),
    ("open", "source"),
    ("social", "exposure"),
]


def build_flag():
    word1, word2 = random.choice(THEME_PHRASES)
    flag, words = build_mixed_flag("NOVA", [word1, word2])
    return flag, words


def make_avatar(path, seed_color):
    img = Image.new("RGB", (400, 400), color=seed_color)
    d = ImageDraw.Draw(img)
    d.ellipse((100, 80, 300, 280), fill=(220, 200, 180))
    d.ellipse((140, 140, 180, 180), fill=(60, 60, 60))
    d.ellipse((220, 140, 260, 180), fill=(60, 60, 60))
    d.arc((150, 190, 250, 240), start=200, end=340, fill=(90, 60, 50), width=6)
    d.rectangle((80, 280, 320, 400), fill=(70, 90, 140))
    img.save(path, "JPEG", quality=90)


def embed_exif_fragment(path, fragment):
    # Uses exiftool (apt: libimage-exiftool-perl) to hide fragment 2 in a
    # plausible-looking metadata field.
    subprocess.run(
        ["exiftool", "-overwrite_original", f"-Artist=nova_recruit_{fragment}", path],
        check=True, capture_output=True,
    )


def write_profile_html(fragment1, out_path):
    html = f"""<!doctype html>
<html>
<head><title>SocialSphere - alex.rivera</title></head>
<body style="font-family: sans-serif; max-width: 640px; margin: 40px auto;">
  <h1>alex.rivera</h1>
  <p>Systems Administrator @ NovaGrid Utilities | Joined March 2021</p>
  <img src="assets/profile.jpg" width="180" alt="profile photo">
  <p>Bio: Coffee, cycling, and keeping the lights on (literally). Ask me about
     home networking!</p>
  <p>Pinned post (Jan 2026): "Finally got my resume updated on the careers
     page after 3 years at the same job \u2014 link in the public records
     listing if anyone's hiring ;)"</p>
  <!-- internal-note: staging fragment {fragment1} do-not-index -->
</body>
</html>
"""
    with open(out_path, "w") as f:
        f.write(html)


def write_public_records_html(fragment3, out_path):
    html = f"""<!doctype html>
<html>
<head><title>Riverside County - Business & Professional Directory</title></head>
<body style="font-family: sans-serif; max-width: 640px; margin: 40px auto;">
  <h1>Business &amp; Professional Directory</h1>
  <p>Search results for "Rivera, Alex" \u2014 Systems Administrator, registered
     2021-03-15.</p>
  <table border="1" cellpadding="6" style="border-collapse: collapse;">
    <tr><th>Field</th><th>Value</th></tr>
    <tr><td>Registered Business</td><td>Rivera Home Networking Consulting</td></tr>
    <tr><td>Registration Date</td><td>2021-03-15</td></tr>
    <tr><td>Status</td><td>Active</td></tr>
  </table>
  <p style="color:#ffffff; font-size: 1px;">record_ref_{fragment3}</p>
</body>
</html>
"""
    with open(out_path, "w") as f:
        f.write(html)


def main():
    flag, words = build_flag()
    # word order in the flag = chronological order of the narrative clues:
    # oldest (public records, 2021) -> middle (photo, undated but implied
    # mid-tenure) -> newest (profile page pinned post, Jan 2026)
    fragment_oldest, fragment_middle, fragment_newest = words

    avatar_path = os.path.join(ASSETS_DIR, "profile.jpg")
    make_avatar(avatar_path, (200, 190, 170))
    embed_exif_fragment(avatar_path, fragment_middle)

    write_profile_html(fragment_newest, os.path.join(OUT_DIR, "profile.html"))
    write_public_records_html(fragment_oldest, os.path.join(OUT_DIR, "public-records.html"))

    solution_path = os.path.join(os.path.dirname(__file__), "SOLUTION.txt")
    with open(solution_path, "w") as f:
        f.write(f"Stage 1 flag: {flag}\n")
        f.write(f"Fragment locations: public-records.html hidden text "
                f"(record_ref_{fragment_oldest}, oldest/2021) -> "
                f"profile.jpg EXIF Artist field "
                f"(nova_recruit_{fragment_middle}, middle) -> "
                f"profile.html HTML comment ({fragment_newest}, newest/Jan 2026)\n")
        f.write("Ordering clue for players: assemble fragments oldest-to-newest "
                "using the dates visible on each page (business registration "
                "2021-03-15 is oldest; the pinned post Jan 2026 is newest) to "
                f"get {flag}\n")

    print(f"[+] Stage 1 built. Flag: {flag}")
    print(f"[+] Solution notes written to {solution_path}")


if __name__ == "__main__":
    main()
