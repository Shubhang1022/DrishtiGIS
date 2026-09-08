# DrishtiGIS backend package — models
from app.models.user import User
from app.models.dataset import Dataset
from app.models.parcel import Parcel
from app.models.property import Property
from app.models.ai_feature import AIFeature
from app.models.discrepancy import Discrepancy
from app.models.processing_job import ProcessingJob
from app.models.historical_snapshot import HistoricalSnapshot

__all__ = [
    "User",
    "Dataset",
    "Parcel",
    "Property",
    "AIFeature",
    "Discrepancy",
    "ProcessingJob",
    "HistoricalSnapshot",
]
