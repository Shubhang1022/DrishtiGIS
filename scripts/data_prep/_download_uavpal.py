"""
Download UAVPal README.md and Data_Conf.json from DANS DataStation.
Verified file IDs from dataset v1 listing:
  README.md    -> ID=121832  SHA-1=151c2877008b7768114c62b749a1f2fb8b4a893d
  Data_Conf.json -> ID=121813  SHA-1=3330b57a1d97fa6532b3cce7b6d6ca8208d5134e
"""
import urllib.request
import ssl
import hashlib
import sys
from pathlib import Path

BASE = "https://phys-techsciences.datastations.nl"
OUT_DIR = Path("data/uavpal")
OUT_DIR.mkdir(parents=True, exist_ok=True)

TARGETS = [
    {
        "file_id": 121832,
        "filename": "README.md",
        "expected_sha1": "151c2877008b7768114c62b749a1f2fb8b4a893d",
        "expected_size": 56013,
    },
    {
        "file_id": 121813,
        "filename": "Data_Conf.json",
        "expected_sha1": "3330b57a1d97fa6532b3cce7b6d6ca8208d5134e",
        "expected_size": 86580,
    },
]

ctx = ssl.create_default_context()
all_ok = True

for t in TARGETS:
    out_path = OUT_DIR / t["filename"]
    url = f"{BASE}/api/access/datafile/{t['file_id']}"
    print(f"\nDownloading {t['filename']} from ID={t['file_id']} ...")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "DrishtiGIS/1.0", "Accept": "*/*"},
    )
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=60) as r:
            content = r.read()
    except Exception as e:
        print(f"  ERROR downloading: {e}")
        all_ok = False
        continue

    # Write file
    out_path.write_bytes(content)
    actual_size = len(content)

    # Verify SHA-1
    actual_sha1 = hashlib.sha1(content).hexdigest()
    sha1_ok = actual_sha1 == t["expected_sha1"]
    size_ok = actual_size == t["expected_size"]

    print(f"  Saved  : {out_path}")
    print(f"  Size   : {actual_size:,} bytes  (expected {t['expected_size']:,})  [{'OK' if size_ok else 'MISMATCH'}]")
    print(f"  SHA-1  : {actual_sha1}")
    print(f"  Expect : {t['expected_sha1']}")
    print(f"  Verify : {'PASS' if sha1_ok else 'FAIL — CHECKSUM MISMATCH'}")

    if not sha1_ok or not size_ok:
        all_ok = False

print()
print("=" * 60)
print(f"Download result: {'ALL PASS' if all_ok else 'FAILED — see above'}")
sys.exit(0 if all_ok else 1)
