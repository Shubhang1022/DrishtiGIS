"""
Map all 30 repository tiles to UAVPal Data_Conf.json entries.
Produces data/uavpal/uavpal_tile_mapping.json
"""
import sys
import json
import hashlib
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

# Our 30 tiles
REPO_TILES_DIR = Path('Dataset/Drone-Images/BHOPAL')
repo_tiles = sorted(f.name for f in REPO_TILES_DIR.glob('*.tiff'))
print(f"Repository tiles ({len(repo_tiles)}): {repo_tiles}")
print()

# Load Data_Conf.json
with open('data/uavpal/Data_Conf.json', encoding='utf-8') as f:
    conf = json.load(f)

# Build lookup: filename -> (split, conf_index, entry)
tile_to_split = {}
for split in ('Train', 'Test'):
    for idx, entry in conf[split].items():
        img_path = entry['Image']              # e.g. "Image/Tiles/00_00.tiff"
        tile_name = Path(img_path).name       # e.g. "00_00.tiff"
        tile_to_split[tile_name] = {
            'split': split.lower(),
            'conf_index': int(idx),
            'image_path': entry['Image'],
            'dsm_path': entry.get('DSM', ''),
            'label_path': entry['Label'],
        }

# Full dataset summary
print(f"Data_Conf.json: Train={len(conf['Train'])} tiles, Test={len(conf['Test'])} tiles")
print(f"Total tiles in conf: {len(conf['Train']) + len(conf['Test'])}")
print()

# Map our 30 tiles
mapping = []
train_count = 0
test_count = 0
not_found = []

for tile_name in repo_tiles:
    repo_path = REPO_TILES_DIR / tile_name
    repo_size = repo_path.stat().st_size

    if tile_name in tile_to_split:
        info = tile_to_split[tile_name]
        split = info['split']
        # Annotation label path (relative to UAVPal root)
        label_path = info['label_path']
        label_filename = Path(label_path).name

        # SHA1 of our local tile
        sha1 = hashlib.sha1(repo_path.read_bytes()).hexdigest()

        entry = {
            'repository_tile': tile_name,
            'repository_size_bytes': repo_size,
            'repository_sha1': sha1,
            'official_tile_id': tile_name.replace('.tiff', ''),
            'split': split,
            'conf_index': info['conf_index'],
            'image_path_in_dataset': info['image_path'],
            'dsm_path_in_dataset': info['dsm_path'],
            'annotation_file': label_path,
            'annotation_filename': label_filename,
            'annotation_available': True,
        }
        mapping.append(entry)
        if split == 'train':
            train_count += 1
        else:
            test_count += 1
        print(f"  {tile_name:15s} -> {split:5s}  label={label_path}")
    else:
        not_found.append(tile_name)
        mapping.append({
            'repository_tile': tile_name,
            'repository_size_bytes': repo_size,
            'official_tile_id': None,
            'split': None,
            'annotation_file': None,
            'annotation_filename': None,
            'annotation_available': False,
        })
        print(f"  {tile_name:15s} -> NOT FOUND in Data_Conf.json")

print()
print(f"=== SUMMARY ===")
print(f"  Total repo tiles matched : {len(mapping) - len(not_found)}/30")
print(f"  Train  : {train_count}")
print(f"  Test   : {test_count}")
print(f"  Not found: {not_found}")

# Build annotation size lookup from the DANS file listing
# (sizes from the API output we already ran)
# Label tiles in DANS listing — small files (~11KB-32KB) are label masks
# Medium files (~640KB-700KB) are DSM tiles
# Large files (~5MB-8MB) are RGB image tiles
# We'll note this in the output

# Compute total annotation download size
# From the DANS listing, label tiles have size in range ~2K-32K bytes
# We matched label sizes from the listing for our 30 tiles
dans_label_sizes = {
    '00_00.tiff': 22490, '00_01.tiff': 26785, '00_02.tiff': 22025,
    '00_03.tiff': 22309, '00_04.tiff': 31681, '00_05.tiff': 26057,
    '00_06.tiff': 17724, '00_07.tiff': 20674, '00_08.tiff': 18346,
    '00_09.tiff': 23658, '00_10.tiff': 27030, '00_11.tiff': 15509,
    '00_12.tiff': 13419, '00_13.tiff': 18620, '00_14.tiff': 5792,
    '00_15.tiff': 11163, '00_16.tiff': 7796,  '00_17.tiff': 6715,
    '00_18.tiff': 8069,  '00_19.tiff': 9989,  '00_20.tiff': 4789,
    '00_21.tiff': 8433,  '00_22.tiff': 7511,
    '01_00.tiff': 21912, '01_01.tiff': 19499, '01_02.tiff': 22401,
    '01_03.tiff': 22461, '01_04.tiff': 26934, '01_05.tiff': 11872,
    '01_06.tiff': 26979,
}

total_annotation_bytes = sum(dans_label_sizes.get(t, 0) for t in repo_tiles)
print(f"  Total annotation download size (30 tiles): {total_annotation_bytes:,} bytes ({total_annotation_bytes/1024:.1f} KB)")

# Enrich mapping with annotation sizes
for entry in mapping:
    tile = entry['repository_tile']
    if entry['annotation_available']:
        entry['annotation_size_bytes_dans'] = dans_label_sizes.get(tile, None)

# Write output
output = {
    '_meta': {
        'source': 'UAVPal v1, doi:10.17026/DANS-Z55-6GT4',
        'datastation': 'https://phys-techsciences.datastations.nl',
        'readme_sha1': '151c2877008b7768114c62b749a1f2fb8b4a893d',
        'data_conf_sha1': '3330b57a1d97fa6532b3cce7b6d6ca8208d5134e',
        'crs': 'EPSG:32643',
        'tile_size_px': '2048x2048',
        'image_format': 'GeoTIFF',
        'label_format': 'GeoTIFF raster (single-band, uint8 class index)',
        'total_dataset_tiles': {'train': len(conf['Train']), 'test': len(conf['Test'])},
        'repo_tiles_matched': len(mapping) - len(not_found),
        'repo_tiles_train': train_count,
        'repo_tiles_test': test_count,
        'annotation_total_bytes_30_tiles': total_annotation_bytes,
        'note': 'Data_Conf.json has only Train/Test splits — no explicit validation split',
    },
    'tiles': mapping,
}

out_path = Path('data/uavpal/uavpal_tile_mapping.json')
out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding='utf-8')
print(f"\nWritten: {out_path} ({out_path.stat().st_size:,} bytes)")
