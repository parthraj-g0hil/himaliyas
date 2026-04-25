#!/usr/bin/env python3
"""
Download itinerary place photos from Wikimedia Commons URLs (same targets as index.html).
Bulk scraping Google Images is against Google's Terms of Service; these are legal, reusable sources.

Writes into place-photos/day-NN/<place_id>/01-wikimedia.jpg
Then runs scan_place_photos.py so manifest.js picks them up.

Usage: python3 download_place_images.py
"""

from __future__ import annotations

import json
import os
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from io import BytesIO

try:
    from PIL import Image

    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False

from place_layout import PLACE_FOLDERS, place_dir

# (place_id, wikimedia_thumb_url)
PLACES: list[tuple[str, str]] = [
    ("d1", "https://upload.wikimedia.org/wikipedia/commons/thumb/9/98/Aerial_view_of_Ahmedabad%2C_India.jpg/960px-Aerial_view_of_Ahmedabad%2C_India.jpg"),
    ("d2a", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/49/Open_Hand_monument%2C_Chandigarh.jpg/960px-Open_Hand_monument%2C_Chandigarh.jpg"),
    ("d2b", "https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Mall_Road%2C_Shimla.jpg/960px-Mall_Road%2C_Shimla.jpg"),
    ("d3a", "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/Jakhu_Temple%2C_Shimla.jpg/960px-Jakhu_Temple%2C_Shimla.jpg"),
    ("d3b", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Kufri%2C_Himachal_Pradesh.jpg/960px-Kufri%2C_Himachal_Pradesh.jpg"),
    ("d3c", "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Narkanda_Himachal_Pradesh_view.jpg/960px-Narkanda_Himachal_Pradesh_view.jpg"),
    ("d4a", "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Sutlej_River_near_Rampur%2C_Himachal.JPG/960px-Sutlej_River_near_Rampur%2C_Himachal.JPG"),
    ("d4b", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Bhimakali_temple_Sarahan.jpg/960px-Bhimakali_temple_Sarahan.jpg"),
    ("d4c", "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Sangla_Valley%2C_Himachal_Pradesh.jpg/960px-Sangla_Valley%2C_Himachal_Pradesh.jpg"),
    ("d4d", "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Chitkul_Village.jpg/960px-Chitkul_Village.jpg"),
    ("d5a", "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e8/Kalpa%2C_Himachal_Pradesh.jpg/960px-Kalpa%2C_Himachal_Pradesh.jpg"),
    ("d5b", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Nako_Lake_and_village%2C_Himachal_Pradesh.jpg/960px-Nako_Lake_and_village%2C_Himachal_Pradesh.jpg"),
    ("d5c", "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Tabo_Monastery%2C_Spiti%2C_Himachal_Pradesh.jpg/960px-Tabo_Monastery%2C_Spiti%2C_Himachal_Pradesh.jpg"),
    ("d6a", "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7e/Dhankar_Gompa%2C_Spiti_Valley.jpg/960px-Dhankar_Gompa%2C_Spiti_Valley.jpg"),
    ("d6b", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/Kaza_town%2C_Spiti_Valley.jpg/960px-Kaza_town%2C_Spiti_Valley.jpg"),
    ("d7a", "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f5/Komic_village%2C_Spiti.jpg/960px-Komic_village%2C_Spiti.jpg"),
    ("d7b", "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Langza_Buddha_statue%2C_Spiti.jpg/960px-Langza_Buddha_statue%2C_Spiti.jpg"),
    ("d7c", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2d/Hikkim_post_office.jpg/960px-Hikkim_post_office.jpg"),
    ("d7d", "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Key_Monastery%2C_Spiti_Valley.jpg/960px-Key_Monastery%2C_Spiti_Valley.jpg"),
    ("d8", "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3b/Chandra_Taal_Lake.jpg/960px-Chandra_Taal_Lake.jpg"),
    ("d9a", "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Atal_Tunnel_southern_portal.jpg/960px-Atal_Tunnel_southern_portal.jpg"),
    ("d9b", "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Naggar_Castle%2C_Kullu_district.jpg/960px-Naggar_Castle%2C_Kullu_district.jpg"),
    ("d10a", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Paragliding_in_Manali.jpg/960px-Paragliding_in_Manali.jpg"),
    ("d10b", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Hidimba_Devi_Temple%2C_Manali.jpg/960px-Hidimba_Devi_Temple%2C_Manali.jpg"),
    ("d10c", "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Mall_Road_Manali_evening.jpg/960px-Mall_Road_Manali_evening.jpg"),
    ("d11a", "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Rock_Garden_Chandigarh.jpg/960px-Rock_Garden_Chandigarh.jpg"),
    ("d11b", "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Chandigarh_railway_station_entrance.jpg/960px-Chandigarh_railway_station_entrance.jpg"),
    ("d12", "https://upload.wikimedia.org/wikipedia/commons/thumb/9/98/Aerial_view_of_Ahmedabad%2C_India.jpg/960px-Aerial_view_of_Ahmedabad%2C_India.jpg"),
]

DAY_BY_ID: dict[str, int] = {}
for d, pid in PLACE_FOLDERS:
    DAY_BY_ID[pid] = d


def to_jpeg_bytes(data: bytes) -> bytes:
    """Normalize to JPEG."""
    if _HAS_PIL:
        im = Image.open(BytesIO(data)).convert("RGB")
        out = BytesIO()
        im.save(out, format="JPEG", quality=88, optimize=True)
        return out.getvalue()
    return data


DEFAULT_UA = (
    "SpitiTripMapOffline/1.0 (itinerary photo cache; Python urllib) "
    "+https://commons.wikimedia.org/"
)


def fetch_url(url: str, ctx: ssl.SSLContext, ua: str, attempts: int = 4) -> bytes:
    last: Exception | None = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": ua})
            with urllib.request.urlopen(req, context=ctx, timeout=60) as r:
                return r.read()
        except Exception as e:
            last = e
            time.sleep(1.5 * (i + 1))
    raise last  # type: ignore[misc]


def main() -> None:
    root = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(root, "place-photos")
    os.makedirs(out_dir, exist_ok=True)

    ctx = ssl.create_default_context()
    ua = os.environ.get("HTTP_USER_AGENT", DEFAULT_UA)

    manifest: dict[str, str] = {}
    failed: list[tuple[str, str, str]] = []
    for pid, url in PLACES:
        day = DAY_BY_ID.get(pid)
        if day is None:
            print("skip unknown id", pid, file=sys.stderr)
            continue
        dest_dir = place_dir(root, day, pid)
        os.makedirs(dest_dir, exist_ok=True)
        try:
            data = fetch_url(url, ctx, ua)
            if _HAS_PIL:
                data = to_jpeg_bytes(data)
            fname = "01-wikimedia.jpg"
            path = os.path.join(dest_dir, fname)
            with open(path, "wb") as f:
                f.write(data)
            rel = "/".join(["place-photos", f"day-{day:02d}", pid, fname])
            manifest[pid] = rel
            print("saved", path, len(data), "bytes")
        except Exception as e:
            err = str(e) or type(e).__name__
            failed.append((pid, url, err))
            print("FAILED", pid, err, file=sys.stderr)

    scan_path = os.path.join(root, "scan_place_photos.py")
    if os.path.isfile(scan_path):
        subprocess.run([sys.executable, scan_path], cwd=root, check=False)

    if failed:
        print(
            "\n---\n"
            "Some downloads failed. Common causes:\n"
            "  1. No internet or firewall blocking https://upload.wikimedia.org\n"
            "  2. VPN / corporate proxy: try another network, or fix HTTPS_PROXY\n"
            "  3. Missing Pillow: python3 -m pip install -r requirements.txt\n",
            file=sys.stderr,
        )
        for pid, url, err in failed:
            print(f"  {pid}: {err}\n    {url}", file=sys.stderr)
        sys.exit(2 if not manifest else 1)


if __name__ == "__main__":
    if not _HAS_PIL:
        print("Pillow is required to save JPEGs. Run: python3 -m pip install Pillow", file=sys.stderr)
        sys.exit(1)
    main()
