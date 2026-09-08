"""DrishtiGIS — Parcel Pydantic schemas"""

from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel


class ParcelResponse(BaseModel):
    id: str
    property_id: Optional[str]
    plot_number: Optional[str]
    survey_number: Optional[str]
    area_m2: Optional[float]
    land_type: Optional[str]
    source: str
    city: Optional[str] = None
    state: Optional[str] = None
    # Geometry returned as GeoJSON dict (WGS84)
    geometry: Optional[Any] = None
    _source_label: str = "Prototype Dataset — Bhopal"

    model_config = {"from_attributes": True}


class ParcelListResponse(BaseModel):
    total: int
    items: list[ParcelResponse]
    _demo_disclaimer: str = (
        "Results contain prototype demonstration data only."
    )
