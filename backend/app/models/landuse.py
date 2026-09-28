"""
DrishtiGIS — Land-Use Intelligence Models
============================================
Pan-India data models for observed land-use patterns and spatial zoning reference data.

DISCLAIMER: All observed land-use classifications represent AI-derived visual patterns
or reference GIS data. They do NOT constitute official legal land-use designations,
permitted zoning uses, or property ownership titles.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class LandUseFeature(BaseModel):
    """Metadata and properties representing a single land-use polygon feature."""
    landuse_id: str = Field(..., description="Unique land-use feature identifier, e.g. LU-BPL-0005")
    dataset_id: str = Field("DATASET-BHOPAL-UAV", description="Dataset identifier")
    region_id: str = Field("REGION-BPL-01", description="Region identifier")
    city: str = Field("Bhopal", description="City name")
    state: str = Field("Madhya Pradesh", description="State / UT name")
    country: str = Field("India", description="Country name")
    crs: str = Field("EPSG:4326", description="Coordinate Reference System identifier")
    source: str = Field(..., description="Data source name (e.g. OpenStreetMap, AI Pattern Engine)")
    source_type: str = Field(
        ...,
        description="Source classification: AI_DERIVED | REFERENCE_GIS | OFFICIAL_REFERENCE | SYNTHETIC_TEST | TEST_FIXTURE"
    )
    classification: str = Field(
        "RESIDENTIAL",
        description="Land-use pattern: RESIDENTIAL | COMMERCIAL | MIXED_USE | INSTITUTIONAL | OPEN_AREA | INDUSTRIAL | VEGETATION | WATER | UNKNOWN"
    )
    area_m2: float = Field(0.0, description="Polygon area in square meters")
    confidence: Optional[float] = Field(None, description="Pattern recognition confidence score [0..1]")
    evidence: str = Field(
        "Observed spatial pattern derived from imagery / reference data.",
        description="Description of evidence supporting observed classification"
    )
    acquisition_datetime: Optional[str] = Field(None, description="ISO timestamp of source data capture")
    geometry_geojson: Optional[Dict[str, Any]] = Field(None, description="Land-use polygon geometry (GeoJSON)")
    review_status: str = Field("UNREVIEWED", description="Surveyor review status")
    disclaimer: str = Field(
        "Observed land-use pattern — not an official legal zoning designation.",
        description="Mandatory non-legal disclaimer label"
    )


class ParcelLandUseSummary(BaseModel):
    """Parcel-level observed land-use pattern summary."""
    parcel_id: str = Field(..., description="Parcel / Property identifier")
    dataset_id: str = Field("DATASET-BHOPAL-UAV", description="Dataset identifier")
    region_id: str = Field("REGION-BPL-01", description="Region identifier")
    observed_land_use_pattern: str = Field(..., description="Primary observed land-use pattern")
    source_type: str = Field("REFERENCE_GIS", description="Source classification of land-use data")
    confidence: float = Field(0.90, description="Confidence score for observed pattern [0..1]")
    building_density_ratio: float = Field(0.0, description="Ratio of parcel area covered by detected building footprints")
    overlapping_landuse_id: Optional[str] = Field(None, description="ID of overlapping land-use feature if present")
    disclaimer: str = Field(
        "Observed physical land-use pattern — does not constitute legal zoning or permitted use.",
        description="Mandatory non-legal disclaimer"
    )
