"""DrishtiGIS — AI Feature model"""

import uuid
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID

try:
    from geoalchemy2 import Geometry  # type: ignore
    HAS_GEOALCHEMY = True
except ImportError:
    HAS_GEOALCHEMY = False

from app.core.database import Base


class AIFeature(Base):
    __tablename__ = "ai_features"
    __table_args__ = (
        CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_ai_features_confidence"),
    )

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id    = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=True)
    feature_type  = Column(String, nullable=False)  # 'building'|'road'|'tree'|'water'
    confidence    = Column(Numeric, nullable=True)
    area_m2       = Column(Numeric, nullable=True)
    geometry      = Column(Geometry("MULTIPOLYGON", srid=4326), nullable=True) if HAS_GEOALCHEMY else Column(String, nullable=True)
    model         = Column(String, nullable=True)
    model_version = Column(String, nullable=True)
    source        = Column(String, nullable=False)   # Always 'AI_DERIVED' or 'AI_DERIVED_DEMO'
    created_at    = Column(DateTime(timezone=True), server_default=text("now()"))
