"""DrishtiGIS — Parcel model"""

import uuid
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID

try:
    from geoalchemy2 import Geometry  # type: ignore
    HAS_GEOALCHEMY = True
except ImportError:
    HAS_GEOALCHEMY = False

from app.core.database import Base


class Parcel(Base):
    __tablename__ = "parcels"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id   = Column(String, unique=True, nullable=True)
    plot_number   = Column(String, nullable=True)
    survey_number = Column(String, nullable=True)
    area_m2       = Column(Numeric, nullable=True)
    land_type     = Column(String, nullable=True)
    geometry      = Column(Geometry("MULTIPOLYGON", srid=4326), nullable=True) if HAS_GEOALCHEMY else Column(String, nullable=True)
    source        = Column(String, nullable=False)   # DataSource enum value
    dataset_id    = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=True)
    created_at    = Column(DateTime(timezone=True), server_default=text("now()"))
    updated_at    = Column(DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()"))
