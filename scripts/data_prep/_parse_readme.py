"""Parse UAVPal README.md for class definitions, annotation info, license, etc."""
import sys
import re
sys.stdout.reconfigure(encoding='utf-8')

content = open('data/uavpal/README.md', encoding='utf-8').read()
print(f"README length: {len(content)} chars\n")

# Find sections containing class/annotation info
keywords = [
    'class', 'Class', 'background', 'Background',
    'Building', 'building', 'Vegetation', 'vegetation',
    'Impervious', 'impervious', 'Low Vegetation', 'Tree',
    'pixel', 'Pixel', 'annotation', 'Annotation',
    'license', 'License', 'LICENSE',
    'cite', 'Cite', 'citation',
    'EPSG', 'epsg', 'CRS', 'coordinate',
    'split', 'Split', 'train', 'Train', 'test', 'Test', 'val', 'Val',
    'color', 'Color', 'RGB value', 'palette',
    '| ID', '| id', '| Class', '| class',
]

found_sections = {}
for kw in keywords:
    idx = content.find(kw)
    if idx != -1 and kw not in found_sections:
        found_sections[kw] = idx

# Sort by position
for kw, idx in sorted(found_sections.items(), key=lambda x: x[1]):
    snippet = content[max(0, idx-20):idx+300]
    print(f"=== '{kw}' at pos {idx} ===")
    print(snippet)
    print()
