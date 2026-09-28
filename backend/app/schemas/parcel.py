"""DrishtiGIS — Parcel and Property Pydantic Schemas"""

from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator


class PropertyType(str, Enum):
    HOUSE = "HOUSE"
    BUILDING = "BUILDING"
    VACANT_PLOT = "VACANT_PLOT"
    OTHER = "OTHER"


class PropertySchema(BaseModel):
    id: Optional[str] = None
    parcel_id: Optional[str] = None
    property_id: Optional[str] = None
    plot_number: Optional[str] = None
    survey_number: Optional[str] = None
    owner_name: Optional[str] = None
    current_owner_name: Optional[str] = None
    previous_owner_name: Optional[str] = None
    resident_count: Optional[int] = Field(default=None, ge=0)
    purchase_price_inr: Optional[float] = Field(default=None, ge=0)
    estimated_selling_price_inr: Optional[float] = Field(default=None, ge=0)
    valuation_year: Optional[int] = None
    property_type: PropertyType = PropertyType.HOUSE
    land_use: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = "Bhopal"
    state: Optional[str] = "Madhya Pradesh"
    country: Optional[str] = "India"
    record_status: str = "SYNTHETIC_DEMO"
    source_label: str = "Synthetic Demo Dataset — Bhopal"
    _source: str = "SYNTHETIC_DEMO"
    _disclaimer: str = "Synthetic prototype data — not an official land record."

    @field_validator("resident_count")
    @classmethod
    def validate_resident_count(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("resident_count must be non-negative or null.")
        return v

    @field_validator("purchase_price_inr")
    @classmethod
    def validate_purchase_price(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("purchase_price_inr must be non-negative or null.")
        return v

    @field_validator("estimated_selling_price_inr")
    @classmethod
    def validate_estimated_selling_price(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("estimated_selling_price_inr must be non-negative or null.")
        return v


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
    geometry: Optional[Any] = None
    _source_label: str = "Prototype Dataset — Bhopal"

    model_config = {"from_attributes": True}


class ParcelListResponse(BaseModel):
    total: int
    items: list[ParcelResponse]
    _demo_disclaimer: str = (
        "Results contain prototype demonstration data only."
    )
