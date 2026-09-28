"""
DrishtiGIS — DataSource Enum
=============================
Mirrors the TypeScript DataSource enum in drishtigis/lib/demo-data/types.ts.
Every database record's `source` column must use one of these values.
"""

from enum import Enum


class DataSource(str, Enum):
    """Data classification for every record stored in or served by DrishtiGIS."""

    OFFICIAL_REFERENCE       = "OFFICIAL_REFERENCE"
    """Authoritative government cadastral / survey data."""

    AI_DERIVED               = "AI_DERIVED"
    """Output from a real AI model inference run."""

    OSM_OPENSTREETMAP        = "OSM_OPENSTREETMAP"
    """From OpenStreetMap — supplementary context, NOT official cadastral data."""

    DEMO_DATA_PROTOTYPE_ONLY = "DEMO_DATA_PROTOTYPE_ONLY"
    """Created for demonstration — never authoritative, clearly labeled."""

    RAW_RASTER_UAV           = "RAW_RASTER_UAV"
    """Original unprocessed UAV imagery."""

    PROCESSED_RASTER         = "PROCESSED_RASTER"
    """Derived from RAW_RASTER_UAV via documented pipeline."""

    AI_DERIVED_DEMO          = "AI_DERIVED_DEMO"
    """Demo placeholder AI output — NOT from a real model run."""

    AI_DERIVED_UAVPAL        = "AI_DERIVED_UAVPAL"
    """Real AI output from the UAVPal U-Net ResNet18 pipeline (Phase 3–5)."""

    SYNTHETIC_DEMO           = "SYNTHETIC_DEMO"
    """Synthetic prototype parcel/property data — explicitly NOT official cadastral data."""
