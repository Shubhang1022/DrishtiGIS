"""DrishtiGIS — Dataset model"""

import uuid
from sqlalchemy import Column, String, Numeric, DateTime, text
from sqlalchemy.dialects.postgresql import UUID

try:
    from geoalchemy2 import Geometry  # type: ignore
    HAS_GEOALCHEMY = True
except ImportError:
    HAS_GEOALCHEMY = False

from app.core.database import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name         = Column(String, nullable=False)
    location     = Column(String, nullable=True)
    dataset_type = Column(String, nullable=False)   # 'orthomosaic'|'dsm'|'cadastral_gis'|'other'
    source       = Column(String, nullable=False)   # DataSource enum value
    file_path    = Column(String, nullable=True)
    crs          = Column(String, nullable=True)
    bounds       = Column(Geometry("POLYGON", srid=4326), nullable=True) if HAS_GEOALCHEMY else Column(String, nullable=True)
    resolution_m = Column(Numeric, nullable=True)
    status       = Column(String, nullable=False, default="uploaded")
    created_at   = Column(DateTime(timezone=True), server_default=text("now()"))
    updated_at   = Column(DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()"))
