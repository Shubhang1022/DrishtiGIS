"""
Parse Data_Conf.json — map our 30 repo tiles to official IDs, splits, annotation paths.
Our 30 tiles: Dataset/Drone-Images/BHOPAL/  (00_00.tiff through 01_06.tiff)
"""
import sys
import json
import os
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

with open('data/uavpal/Data_Conf.json', encoding='utf-8') as f:
    conf = json.load(f)

print("=== Top-level keys ===")
print(list(conf.keys()))
print()

# Show structure of first entry per split
for split_key in conf.keys():
    split_data = conf[split_key]
    print(f"=== Split: {split_key!r} ===")
    print(f"  Count: {len(split_data)}")
    # Show first 3 entries
    for i, (idx, entry) in enumerate(split_data.items()):
        if i >= 3:
            print(f"  ... ({len(split_data)-3} more)")
            break
        print(f"  [{idx}]: {entry}")
    print()
