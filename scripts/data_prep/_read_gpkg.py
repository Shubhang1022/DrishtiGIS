"""Read Annotation.gpkg to get class schema."""
import sys
import sqlite3
import urllib.request
import ssl
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

gpkg_path = Path('data/uavpal/Annotation.gpkg')
if not gpkg_path.exists():
    ctx = ssl.create_default_context()
    print('Downloading Annotation.gpkg (2.8 MB)...')
    req = urllib.request.Request(
        'https://phys-techsciences.datastations.nl/api/access/datafile/121811',
        headers={'User-Agent': 'DrishtiGIS/1.0', 'Accept': '*/*'}
    )
    with urllib.request.urlopen(req, context=ctx, timeout=60) as r:
        data = r.read()
    gpkg_path.write_bytes(data)
    print(f'Downloaded: {len(data):,} bytes')

conn = sqlite3.connect(str(gpkg_path))
cur = conn.cursor()

# List all tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
print('Tables:', tables)
print()

# gpkg_contents
cur.execute('SELECT table_name, data_type, identifier, description FROM gpkg_contents')
print('gpkg_contents:')
for row in cur.fetchall():
    print(' ', row)
print()

# For each non-system table, show schema and sample rows
for t in tables:
    if t.startswith('gpkg') or t.startswith('rtree') or t.startswith('sqlite'):
        continue
    cur.execute(f'PRAGMA table_info("{t}")')
    cols = cur.fetchall()
    print(f'--- Table: {t!r} ---')
    print('  Columns:', [(c[1], c[2]) for c in cols])
    cur.execute(f'SELECT COUNT(*) FROM "{t}"')
    count = cur.fetchone()[0]
    print(f'  Row count: {count}')
    cur.execute(f'SELECT * FROM "{t}" LIMIT 10')
    for row in cur.fetchall():
        # Print everything except geometry blob
        cleaned = []
        for val in row:
            if isinstance(val, (bytes, memoryview)):
                cleaned.append(f'<GEOM {len(val) if isinstance(val,bytes) else "?"}B>')
            else:
                cleaned.append(val)
        print('  ', cleaned)
    print()

conn.close()
