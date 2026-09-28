"""
Provenance and evidence formatting for DrishtiGIS AI Assistant.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel

SYNTHETIC_DISCLAIMER = "Synthetic prototype data — not an official land record."

class ProvenanceInfo(BaseModel):
    source_type: str
    dataset_id: Optional[str] = None
    region_id: Optional[str] = None
    feature_id: Optional[str] = None
    model: Optional[str] = None
    acquisition_datetime: Optional[str] = None
    confidence: Optional[float] = None
    disclaimer: Optional[str] = None

def create_provenance(
    source_type: str,
    dataset_id: Optional[str] = "uavpal_bhopal",
    region_id: Optional[str] = "bhopal_mp",
    feature_id: Optional[str] = None,
    model: Optional[str] = None,
    acquisition_datetime: Optional[str] = None,
    confidence: Optional[float] = None,
    is_synthetic: bool = False
) -> ProvenanceInfo:
    """Build a structured provenance object for GIS AI responses."""
    
    disclaimer = SYNTHETIC_DISCLAIMER if is_synthetic or source_type == "SYNTHETIC_DEMO" else None
    
    if source_type == "AI_DERIVED_UAVPAL" and not model:
        model = "U-Net + ResNet18"
        
    return ProvenanceInfo(
        source_type=source_type,
        dataset_id=dataset_id,
        region_id=region_id,
        feature_id=feature_id,
        model=model,
        acquisition_datetime=acquisition_datetime,
        confidence=confidence,
        disclaimer=disclaimer
    )
