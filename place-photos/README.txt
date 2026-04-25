Day-wise + place-wise folders (auto gallery)
============================================

Folder pattern (NN = day number 01–12, <id> = place id from the map):

  place-photos/day-NN/<place_id>/

Examples:
  place-photos/day-02/d2a/          ← Chandigarh (Day 2)
  place-photos/day-02/d2b/          ← Shimla
  place-photos/day-08/d8/           ← Chandra Taal

Put any number of images (or one) in each folder. Names are sorted alphabetically
for the swipe order. Allowed: .jpg .jpeg .png .webp .gif

After adding or renaming files, regenerate the loader:

  cd /path/to/spiti-trip-map
  python3 scan_place_photos.py

This writes place-photos/manifest.js (and manifest.json). Reload the map page.
The HTML loads manifest.js so your photos appear without editing index.html.

First-time folder layout:

  python3 scan_place_photos.py --init

Place IDs (must match folder names)
------------------------------------
d1          Day 1  Ahmedabad
d2a, d2b    Day 2  Chandigarh, Shimla
d3a–d3c     Day 3  Jakhu, Kufri, Narkanda
d4a–d4d     Day 4  Rampur, Sarahan, Sangla, Chitkul
d5a–d5c     Day 5  Kalpa, Nako, Tabo
d6a, d6b    Day 6  Dhankar, Kaza
d7a–d7d     Day 7  Komic, Langza, Hikkim, Key
d8          Day 8  Chandra Taal
d9a, d9b    Day 9  Atal Tunnel, Naggar
d10a–d10c   Day 10 Paragliding, Hadimba, Manu/Vashisht/Mall
d11a, d11b  Day 11 Chandigarh, station
d12         Day 12 Ahmedabad arrival

Optional: Wikimedia starter images
----------------------------------
  python3 download_place_images.py

saves one JPEG per stop into the day folders and runs scan_place_photos.py
(requires Pillow: pip install -r requirements.txt).

If a folder has no files, the map uses the remoteImage URL from index.html for that pin.
