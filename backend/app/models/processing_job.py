"""DrishtiGIS — Processing Job model"""

import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"
    __table_args__ = (
        CheckConstraint("progress BETWEEN 0 AND 100", name="ck_processing_jobs_progress"),
    )

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id   = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=True)
    # queued | preparing | processing | analyzing | ready_for_review | published | failed
    status       = Column(String, nullable=False, default="queued")
    progress     = Column(Integer, nullable=True)
    started_at   = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error        = Column(String, nullable=True)
    result       = Column(JSONB, nullable=True)
    created_at   = Column(DateTime(timezone=True), server_default=text("now()"))
    updated_at   = Column(DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()"))
