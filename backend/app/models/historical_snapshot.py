"""DrishtiGIS — Historical Snapshot model"""

import uuid
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID

try:
    from geoalchemy2 import Geometry  # type: ignore
    HAS_GEOALCHEMY = True
except ImportError:
    HAS_GEOALCHEMY = False

from app.core.database import Base


class HistoricalSnapshot(Base):
    __tablename__ = "historical_snapshots"
    __table_args__ = (
        CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_historical_snapshots_confidence"),
    )

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id    = Column(UUID(as_uuid=True), ForeignKey("properties.id"), nullable=True)
    dataset_id     = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=True)
    captured_at    = Column(DateTime(timezone=True), nullable=False)
    imagery_source = Column(String, nullable=False)
    geometry       = Column(Geometry("MULTIPOLYGON", srid=4326), nullable=True) if HAS_GEOALCHEMY else Column(String, nullable=True)
    change_type    = Column(String, nullable=True)
    # change_type is EXPLICITLY nullable.
    # NULL means: no historical change classification is available because
    # real multi-temporal imagery is not available for the prototype dataset.
    # Valid non-null values when real data exists:
    #   'new_structure', 'boundary_change', 'demolition', 'land_use_change'
    confidence     = Column(Numeric, nullable=True)
    source         = Column(String, nullable=False)   # DataSource enum value
    created_at     = Column(DateTime(timezone=True), server_default=text("now()"))
