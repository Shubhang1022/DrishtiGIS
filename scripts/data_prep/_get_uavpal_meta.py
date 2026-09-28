"""Download UAVPal README.md and Data_Conf.json from DANS DataStation."""
import urllib.request
import urllib.error
import ssl
import json
import hashlib
import os
from pathlib import Path

ctx = ssl.create_default_context()
BASE = 'https://phys-techsciences.datastations.nl'
OUT_DIR = Path('data/uavpal')
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Step 1: Get dataset metadata and file list
url = f'{BASE}/api/datasets/:persistentId/?persistentId=doi:10.17026/DANS-Z55-6GT4'
req = urllib.request.Request(url, headers={'User-Agent': 'DrishtiGIS/1.0', 'Accept': 'application/json'})
with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
    data = json.loads(r.read())

version = data['data']['latestVersion']
files = version.get('files', [])
print(f"Dataset: UAVPal v{version.get('versionNumber','?')} ({version.get('versionState','?')})")
print(f"Total files in dataset: {len(files)}")
print()

# Show all files
for f in files:
    df = f.get('dataFile', {})
    label = f.get('label', df.get('filename', '?'))
    size = df.get('filesize', df.get('originalFileSize', '?'))
    fid = df.get('id', '?')
    chk = df.get('checksum', {})
    restricted = f.get('restricted', False)
    print(f"  ID={fid}  size={size}  restricted={restricted}  {label}  {chk}")
