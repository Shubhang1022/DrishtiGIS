"""
DrishtiGIS — Multi-Epoch Historical Models & Schemas
======================================================
Pan-India data models for temporal datasets, dataset registration,
building footprint change detection, and parcel change aggregation.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class EpochMetadata(BaseModel):
    """Metadata representing a single temporal capture epoch for a dataset/region."""
    epoch_id: str = Field(..., description="Unique epoch identifier, e.g. EPOCH-BPL-2024-01")
    dataset_id: str = Field(..., description="Dataset identifier, e.g. DATASET-BHOPAL-UAV")
    region_id: str = Field(..., description="Region identifier, e.g. REGION-BPL-01")
    city: str = Field(..., description="City name")
    state: str = Field(..., description="State / UT name")
    crs: str = Field("EPSG:4326", description="Coordinate Reference System identifier")
    acquisition_datetime: str = Field(..., description="ISO 8601 acquisition timestamp")
    resolution_m: float = Field(..., description="Spatial resolution in meters per pixel")
    source_type: str = Field(..., description="Source type: UAV_ORTHOMOSAIC | SATELLITE_HIGH_RES | TEST_FIXTURE")
    description: Optional[str] = Field(None, description="Human readable dataset description")
    building_count: int = Field(0, description="Total AI building extractions in this epoch")
    is_baseline: bool = Field(False, description="Whether this epoch serves as the primary baseline")


class BuildingChangeItem(BaseModel):
    """Individual building footprint change detection result."""
    change_id: str = Field(..., description="Unique change item identifier")
    change_type: str = Field(..., description="Change classification: ADDED | REMOVED | MODIFIED | UNCHANGED")
    baseline_building_id: Optional[str] = Field(None, description="ID of building in baseline epoch")
    target_building_id: Optional[str] = Field(None, description="ID of building in target epoch")
    parcel_id: Optional[str] = Field(None, description="Associated parcel/property ID")
    area_baseline_m2: Optional[float] = Field(None, description="Baseline footprint area in sq. meters")
    area_target_m2: Optional[float] = Field(None, description="Target footprint area in sq. meters")
    area_delta_m2: float = Field(0.0, description="Footprint area difference (target - baseline)")
    iou_score: float = Field(0.0, description="Intersection over Union spatial overlap score [0..1]")
    centroid_shift_m: float = Field(0.0, description="Distance shift between building centroids in meters")
    confidence_score: float = Field(1.0, description="Analytical change detection confidence score [0..1]")
    geometry_geojson: Optional[Dict[str, Any]] = Field(None, description="Change highlight geometry (GeoJSON)")
    review_status: str = Field("UNREVIEWED", description="Surveyor review status: UNREVIEWED | VERIFIED_CHANGE | DISCREPANCY_FLAGGED | REJECTED")
    disclaimer: str = Field(
        "Observed AI building footprint difference — not an official cadastral change or legal violation.",
        description="Mandatory disclaimer for change observations"
    )


class ParcelChangeSummary(BaseModel):
    """Aggregated change summary for a specific parcel/property."""
    parcel_id: str = Field(..., description="Property / parcel identifier")
    baseline_epoch_id: str = Field(..., description="Baseline epoch ID")
    target_epoch_id: str = Field(..., description="Target epoch ID")
    baseline_building_count: int = Field(0, description="Building count in baseline epoch")
    target_building_count: int = Field(0, description="Building count in target epoch")
    added_count: int = Field(0, description="Number of newly detected buildings")
    removed_count: int = Field(0, description="Number of absent/removed buildings")
    modified_count: int = Field(0, description="Number of significantly modified building footprints")
    unchanged_count: int = Field(0, description="Number of unchanged buildings")
    total_area_change_m2: float = Field(0.0, description="Net built footprint area change in m²")
    changes: List[BuildingChangeItem] = Field(default_factory=list, description="List of individual building change items")
    last_evaluated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
