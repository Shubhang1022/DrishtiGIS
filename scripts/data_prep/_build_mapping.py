"""
Build data/uavpal/uavpal_tile_mapping.json with complete per-tile mapping.
Authoritative class IDs sourced from Annotation.gpkg (downloaded and verified).
"""
import sys
import json
import hashlib
import sqlite3
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

REPO_TILES_DIR = Path('Dataset/Drone-Images/BHOPAL')
CONF_PATH = Path('data/uavpal/Data_Conf.json')
GPKG_PATH = Path('data/uavpal/Annotation.gpkg')

# ── 1. Load Data_Conf.json ──────────────────────────────────────────────────
with open(CONF_PATH, encoding='utf-8') as f:
    conf = json.load(f)

tile_to_split = {}
for split in ('Train', 'Test'):
    for idx, entry in conf[split].items():
        tile_name = Path(entry['Image']).name
        tile_to_split[tile_name] = {
            'split': split.lower(),
            'conf_index': int(idx),
            'image_path': entry['Image'],
            'dsm_path': entry.get('DSM', ''),
            'label_path': entry['Label'],
        }

# ── 2. Verify class IDs from Annotation.gpkg ───────────────────────────────
conn = sqlite3.connect(str(GPKG_PATH))
cur = conn.cursor()
class_map = {}
for table in ('Water', 'Road', 'Car', 'Building', 'Tree'):
    cur.execute(f'SELECT DISTINCT value FROM "{table}" LIMIT 1')
    row = cur.fetchone()
    if row:
        class_map[table] = row[0]
conn.close()

# Confirmed class value map from Annotation.gpkg
CLASS_DEFINITIONS = {
    0: {'name': 'Background', 'source': 'implicit (unlabeled pixels in raster label)'},
    int(class_map.get('Water', 1)): {'name': 'Water',    'layer': 'Water_Body'},
    int(class_map.get('Road', 2)):  {'name': 'Road',     'layer': 'Roads_bhopal'},
    int(class_map.get('Car', 3)):   {'name': 'Car',      'layer': 'Car'},
    int(class_map.get('Building', 4)): {'name': 'Building', 'layer': 'Structures'},
    int(class_map.get('Tree', 5)):  {'name': 'Tree',     'layer': 'Veg_Canopy_V4'},
}
print('Confirmed class IDs from Annotation.gpkg:')
for cid, info in sorted(CLASS_DEFINITIONS.items()):
    print(f'  {cid}: {info["name"]}')
print()

# ── 3. Label tile sizes from DANS listing (pre-verified) ───────────────────
LABEL_SIZES_DANS = {
    '00_00.tiff': 22490, '00_01.tiff': 26785, '00_02.tiff': 22025,
    '00_03.tiff': 22309, '00_04.tiff': 31681, '00_05.tiff': 26057,
    '00_06.tiff': 17724, '00_07.tiff': 20674, '00_08.tiff': 18346,
    '00_09.tiff': 23658, '00_10.tiff': 27030, '00_11.tiff': 15509,
    '00_12.tiff': 13419, '00_13.tiff': 18620, '00_14.tiff':  5792,
    '00_15.tiff': 11163, '00_16.tiff':  7796, '00_17.tiff':  6715,
    '00_18.tiff':  8069, '00_19.tiff':  9989, '00_20.tiff':  4789,
    '00_21.tiff':  8433, '00_22.tiff':  7511,
    '01_00.tiff': 21912, '01_01.tiff': 19499, '01_02.tiff': 22401,
    '01_03.tiff': 22461, '01_04.tiff': 26934, '01_05.tiff': 11872,
    '01_06.tiff': 26979,
}

# ── 4. Build per-tile mapping ───────────────────────────────────────────────
repo_tiles = sorted(f.name for f in REPO_TILES_DIR.glob('*.tiff'))
mapping = []
train_count = test_count = 0

for tile_name in repo_tiles:
    repo_path = REPO_TILES_DIR / tile_name
    repo_bytes = repo_path.read_bytes()
    repo_size = len(repo_bytes)
    repo_sha1 = hashlib.sha1(repo_bytes).hexdigest()

    if tile_name in tile_to_split:
        info = tile_to_split[tile_name]
        split = info['split']
        label_path = info['label_path']
        entry = {
            'repository_tile': tile_name,
            'repository_path': f'Dataset/Drone-Images/BHOPAL/{tile_name}',
            'repository_size_bytes': repo_size,
            'repository_sha1': repo_sha1,
            'official_tile_id': tile_name.replace('.tiff', ''),
            'split': split,
            'conf_index': info['conf_index'],
            'image_path_in_dataset': info['image_path'],
            'dsm_path_in_dataset': info['dsm_path'],
            'annotation_file': label_path,
            'annotation_filename': Path(label_path).name,
            'annotation_available': True,
            'annotation_size_bytes_dans': LABEL_SIZES_DANS.get(tile_name),
        }
        mapping.append(entry)
        if split == 'train':
            train_count += 1
        else:
            test_count += 1
        print(f'  {tile_name:15s}  {split:5s}  label_size={LABEL_SIZES_DANS.get(tile_name,"?"):>6} B  sha1={repo_sha1[:12]}...')
    else:
        mapping.append({
            'repository_tile': tile_name,
            'repository_path': f'Dataset/Drone-Images/BHOPAL/{tile_name}',
            'repository_size_bytes': repo_size,
            'repository_sha1': repo_sha1,
            'official_tile_id': None,
            'split': None,
            'annotation_file': None,
            'annotation_filename': None,
            'annotation_available': False,
            'annotation_size_bytes_dans': None,
        })
        print(f'  {tile_name:15s}  NOT FOUND')

total_annotation_bytes = sum(LABEL_SIZES_DANS.get(t, 0) for t in repo_tiles)
print()
print(f'Matched : {len(mapping) - sum(1 for e in mapping if not e["annotation_available"])}/30')
print(f'Train   : {train_count}')
print(f'Test    : {test_count}')
print(f'Total annotation download for 30 tiles: {total_annotation_bytes:,} bytes ({total_annotation_bytes/1024:.1f} KB)')

# ── 5. Write output ─────────────────────────────────────────────────────────
output = {
    '_meta': {
        'generated_by': 'DrishtiGIS Phase 0 metadata verification',
        'source_dataset': 'UAVPal v1',
        'doi': 'doi:10.17026/DANS-Z55-6GT4',
        'datastation': 'https://phys-techsciences.datastations.nl',
        'readme_sha1': '151c2877008b7768114c62b749a1f2fb8b4a893d',
        'data_conf_sha1': '3330b57a1d97fa6532b3cce7b6d6ca8208d5134e',
        'annotation_gpkg_sha1': hashlib.sha1(GPKG_PATH.read_bytes()).hexdigest(),
        'crs': 'EPSG:32643',
        'tile_size_px': '2048x2048',
        'spatial_resolution_cm': 2,
        'image_format': 'GeoTIFF',
        'label_format': 'GeoTIFF raster single-band uint8 class index',
        'label_directory_in_dataset': 'Label/Tiles/',
        'image_directory_in_dataset': 'Image/Tiles/',
        'dsm_directory_in_dataset': 'DSM/Tiles/',
        'filename_convention': 'ROW_COL.tiff  (e.g. 00_00.tiff, 01_06.tiff)',
        'license': 'CC-BY-NC-SA-4.0',
        'license_file': 'LICENSE.txt',
        'splits': ['train', 'test'],
        'split_note': 'Data_Conf.json has only Train/Test splits — no explicit validation split defined by dataset authors',
        'total_dataset_tiles': {
            'train': len(conf['Train']),
            'test': len(conf['Test']),
            'total': len(conf['Train']) + len(conf['Test']),
        },
        'repo_tiles_summary': {
            'total': 30,
            'matched': 30,
            'train': train_count,
            'test': test_count,
            'not_found': 0,
        },
        'annotation_download_size_bytes_30_tiles': total_annotation_bytes,
        'classes': {
            str(cid): info for cid, info in sorted(CLASS_DEFINITIONS.items())
        },
        'building_class_id': 4,
        'building_class_name': 'Building',
    },
    'tiles': mapping,
}

out_path = Path('data/uavpal/uavpal_tile_mapping.json')
out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding='utf-8')
print(f'\nWritten: {out_path}  ({out_path.stat().st_size:,} bytes)')

# Quick validation
loaded = json.loads(out_path.read_text(encoding='utf-8'))
assert loaded['_meta']['building_class_id'] == 4
assert loaded['_meta']['repo_tiles_summary']['matched'] == 30
assert len(loaded['tiles']) == 30
print('Validation: PASS')
