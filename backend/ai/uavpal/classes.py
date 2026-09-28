"""
UAVPal class definitions — authoritative source.

Class IDs sourced directly from Annotation.gpkg (DANS doi:10.17026/DANS-Z55-6GT4).
DO NOT change these values — they are the pixel values in the label GeoTIFFs.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class UAVPalClass:
    id: int
    name: str
    colour_rgb: Tuple[int, int, int]   # QGIS display colour from Annotation.gpkg styles
    description: str


# Canonical class definitions — verified against Annotation.gpkg layer 'value' field
CLASSES: Tuple[UAVPalClass, ...] = (
    UAVPalClass(0, "Background",  (0,   0,   0),   "Unlabeled / background pixels"),
    UAVPalClass(1, "Water",       (0,   0,   255),  "Water bodies (layer: Water_Body)"),
    UAVPalClass(2, "Road",        (128, 128, 128),  "Roads and paved surfaces (layer: Roads_bhopal)"),
    UAVPalClass(3, "Car",         (255, 255, 0),    "Vehicles (layer: Car)"),
    UAVPalClass(4, "Building",    (166, 123, 91),   "Building rooftops (layer: Structures)"),
    UAVPalClass(5, "Tree",        (0,   128, 0),    "Tree canopy (layer: Veg_Canopy_V4)"),
)

# Fast lookup dictionaries
CLASS_BY_ID:   Dict[int, UAVPalClass] = {c.id:   c for c in CLASSES}
CLASS_BY_NAME: Dict[str, UAVPalClass] = {c.name: c for c in CLASSES}

NUM_CLASSES:       int = len(CLASSES)       # 6
VALID_CLASS_IDS:   Tuple[int, ...] = tuple(c.id for c in CLASSES)   # (0,1,2,3,4,5)
BUILDING_CLASS_ID: int = 4                  # Building — primary segmentation target

# Colour palette as a flat list (class_id → [R, G, B]) for visualization
COLOUR_PALETTE: Dict[int, Tuple[int, int, int]] = {c.id: c.colour_rgb for c in CLASSES}


def validate_class_id(class_id: int) -> bool:
    """Return True if class_id is a valid UAVPal label value."""
    return class_id in CLASS_BY_ID


def class_name(class_id: int) -> str:
    """Return the class name for a given ID, or 'Unknown' if not found."""
    return CLASS_BY_ID[class_id].name if class_id in CLASS_BY_ID else "Unknown"


def is_building(class_id: int) -> bool:
    """Return True if class_id is the Building class (4)."""
    return class_id == BUILDING_CLASS_ID
