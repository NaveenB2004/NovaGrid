#!/usr/bin/env python3
"""
build_stage2.py - builds the Stage 2 "Picture Imperfect" steganography
challenge. Generates a random flag, writes it to a temp text file, and
uses steghide to embed it inside a JPEG cover image with a weak,
hinted passphrase.

Usage:
    python3 build_stage2.py
Output:
    dist/memo_backup.jpg   (the challenge file to distribute to players)
    SOLUTION.txt            (private - flag + passphrase, for grading only)
"""
import os
import random
import string
import subprocess
import sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from flag_utils import build_mixed_flag

BASE = os.path.dirname(__file__)
DIST = os.path.join(BASE, "dist")
os.makedirs(DIST, exist_ok=True)

# Intentionally weak/guessable passphrase, consistent with the "hinted"
# design in the stage specification.
PASSPHRASE = "novagrid2024"


THEME_PHRASES = [
    ["hidden", "in", "plain", "sight"],
    ["pixels", "dont", "lie"],
    ["buried", "in", "the", "backup"],
    ["more", "than", "meets", "the", "eye"],
]


def build_flag():
    words = random.choice(THEME_PHRASES)
    flag, _ = build_mixed_flag("NOVA", words)
    return flag


def make_cover_image(path):
    img = Image.new("RGB", (800, 600), color=(235, 235, 240))
    d = ImageDraw.Draw(img)
    # A plausible "family photo backup" style cover image - simple shapes,
    # nothing suspicious, sized generously so LSB embedding has plenty of
    # room and doesn't visibly distort the image.
    d.rectangle((0, 400, 800, 600), fill=(120, 160, 110))
    d.ellipse((300, 150, 500, 350), fill=(250, 220, 170))
    d.rectangle((250, 350, 550, 600), fill=(80, 90, 140))
    d.ellipse((50, 50, 150, 150), fill=(255, 230, 120))
    img.save(path, "JPEG", quality=95)


def main():
    flag = build_flag()

    flag_file = os.path.join(BASE, "_flag.txt")
    with open(flag_file, "w") as f:
        f.write(flag + "\n")

    cover_path = os.path.join(BASE, "_cover.jpg")
    make_cover_image(cover_path)

    output_path = os.path.join(DIST, "memo_backup.jpg")
    if os.path.exists(output_path):
        os.remove(output_path)

    subprocess.run(
        [
            "steghide", "embed",
            "-cf", cover_path,
            "-ef", flag_file,
            "-sf", output_path,
            "-p", PASSPHRASE,
            "-z", "9",
        ],
        check=True, capture_output=True,
    )

    os.remove(flag_file)
    os.remove(cover_path)

    solution_path = os.path.join(BASE, "SOLUTION.txt")
    with open(solution_path, "w") as f:
        f.write(f"Stage 2 flag: {flag}\n")
        f.write(f"Passphrase: {PASSPHRASE}\n")
        f.write(f"Extraction: steghide extract -sf {output_path} -p {PASSPHRASE}\n")

    print(f"[+] Stage 2 built. Flag: {flag}")
    print(f"[+] Challenge file: {output_path}")
    print(f"[+] Solution notes written to {solution_path}")


if __name__ == "__main__":
    main()
