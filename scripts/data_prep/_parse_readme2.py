"""Dump the sections of README.md between known structural markers."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

content = open('data/uavpal/README.md', encoding='utf-8').read()

# Print the full README in chunks past the file tree section
# The file tree section starts around the first <details> block
# We want the parts AFTER the directory listing
parts = content.split('---')
print(f"Total '---' separators: {len(parts)-1}\n")
for i, part in enumerate(parts):
    stripped = part.strip()
    if stripped:
        print(f"=== SECTION {i} (len={len(stripped)}) ===")
        print(stripped[:800])
        print()
