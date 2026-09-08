"""DrishtiGIS — Discrepancy model"""

import uuid
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Discrepancy(Base):
    __tablename__ = "discrepancies"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parcel_id      = Column(UUID(as_uuid=True), ForeignKey("parcels.id"), nullable=True)
    feature_id     = Column(UUID(as_uuid=True), ForeignKey("ai_features.id"), nullable=True)
    type           = Column(String, nullable=False)  # 'area_mismatch'|'boundary_mismatch'|'new_structure'|'other'
    official_value = Column(Numeric, nullable=True)
    ai_value       = Column(Numeric, nullable=True)
    difference     = Column(Numeric, nullable=True)
    difference_pct = Column(Numeric, nullable=True)
    severity       = Column(String, nullable=True)   # 'low'|'medium'|'high'
    status         = Column(String, nullable=True, default="pending_review")
    created_at     = Column(DateTime(timezone=True), server_default=text("now()"))
