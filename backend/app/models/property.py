"""DrishtiGIS — Property model"""

import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Property(Base):
    __tablename__ = "properties"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parcel_id   = Column(UUID(as_uuid=True), ForeignKey("parcels.id"), nullable=True)
    property_id = Column(String, unique=True, nullable=True)
    address     = Column(String, nullable=True)
    city        = Column(String, nullable=False)
    state       = Column(String, nullable=False)
    land_type   = Column(String, nullable=True)
    status      = Column(String, nullable=True)
    source      = Column(String, nullable=False)   # DataSource enum value
    created_at  = Column(DateTime(timezone=True), server_default=text("now()"))
    updated_at  = Column(DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()"))
