"""
DrishtiGIS — Road & Access Corridor Models
============================================
Pan-India data models for road features, road classification,
centerlines, width estimates, and parcel access corridor analysis.

DISCLAIMER: All road access analysis represents spatial geometry proximity.
It does NOT constitute legal property access rights or official land record status.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RoadFeature(BaseModel):
    """Metadata and properties representing a single road segment or centerline feature."""
    road_id: str = Field(..., description="Unique road feature identifier, e.g. ROAD-BPL-0012")
    dataset_id: str = Field("DATASET-BHOPAL-UAV", description="Dataset identifier")
    region_id: str = Field("REGION-BPL-01", description="Region identifier")
    city: str = Field("Bhopal", description="City name")
    state: str = Field("Madhya Pradesh", description="State / UT name")
    country: str = Field("India", description="Country name")
    crs: str = Field("EPSG:4326", description="Coordinate Reference System identifier")
    source: str = Field(..., description="Data source name (e.g. OpenStreetMap, UAVPal AI)")
    source_type: str = Field(
        ...,
        description="Source classification: REFERENCE_GIS | AI_DERIVED | OFFICIAL_REFERENCE | SYNTHETIC_TEST | TEST_FIXTURE"
    )
    road_class: str = Field(
        "LOCAL",
        description="Road classification: PRIMARY | SECONDARY | LOCAL | ACCESS | PATHWAY | UNKNOWN"
    )
    name: Optional[str] = Field(None, description="Street / road name if available")
    surface_type: str = Field("PAVED", description="Surface type: PAVED | UNPAVED | GRAVEL | UNKNOWN")
    estimated_width_m: Optional[float] = Field(None, description="Estimated road width in meters")
    length_m: float = Field(0.0, description="Calculated segment length in meters")
    confidence: Optional[float] = Field(None, description="AI detection confidence score [0..1] if AI-derived")
    acquisition_datetime: Optional[str] = Field(None, description="ISO timestamp of source data capture")
    geometry_geojson: Optional[Dict[str, Any]] = Field(None, description="Road geometry (GeoJSON LineString/MultiLineString)")
    review_status: str = Field("UNREVIEWED", description="Surveyor review status")
    disclaimer: str = Field(
        "Road feature geometry — provided for geospatial reference.",
        description="Mandatory disclaimer label"
    )


class AccessCorridorSummary(BaseModel):
    """Parcel-level access corridor analysis summary."""
    parcel_id: str = Field(..., description="Parcel / Property identifier")
    dataset_id: str = Field("DATASET-BHOPAL-UAV", description="Dataset identifier")
    region_id: str = Field("REGION-BPL-01", description="Region identifier")
    access_status: str = Field(
        ...,
        description="Access status: ACCESS_DETECTED | NO_DETECTED_ACCESS_CORRIDOR | ACCESS_REVIEW_REQUIRED"
    )
    has_direct_access: bool = Field(False, description="Whether parcel intersects or directly adjoins a detected road")
    nearest_road_id: Optional[str] = Field(None, description="Identifier of the nearest detected road")
    nearest_road_name: Optional[str] = Field(None, description="Name of the nearest detected road")
    nearest_road_class: Optional[str] = Field(None, description="Road class of nearest road")
    distance_to_road_m: float = Field(0.0, description="Minimum spatial distance from parcel boundary to nearest road in meters")
    nearby_road_count: int = Field(0, description="Count of roads within 50 meters of parcel boundary")
    disclaimer: str = Field(
        "Spatial proximity analysis — does not constitute official legal access rights.",
        description="Mandatory non-legal disclaimer"
    )
