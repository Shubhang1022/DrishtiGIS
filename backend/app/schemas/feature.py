"""DrishtiGIS — AI Feature Pydantic schemas"""

from typing import Optional, Any
from pydantic import BaseModel


class AIFeatureResponse(BaseModel):
    id: str
    feature_type: str
    confidence: Optional[float]
    area_m2: Optional[float]
    model: Optional[str]
    model_version: Optional[str]
    source: str
    geometry: Optional[Any] = None
    _disclaimer: str = (
        "AI-derived observation — prototype demonstration only. "
        "Not a legal determination. Requires field verification."
    )

    model_config = {"from_attributes": True}


class AIFeatureListResponse(BaseModel):
    parcel_id: str
    total: int
    items: list[AIFeatureResponse]
