"""
DrishtiGIS — Authoritative Dataset & Processing Job Persistence Service
========================================================================
Thread-safe persistence, background worker lock management, recovery mechanics,
and state-machine enforcement for geospatial datasets.
Stored at data/governance/datasets.json.
"""

import os
import json
import uuid
import time
import asyncio
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timezone
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[3]
GOVERNANCE_DIR = ROOT / "data" / "governance"
DATASETS_FILE = GOVERNANCE_DIR / "datasets.json"
UPLOADS_DIR = ROOT / "data" / "uploads"

class DatasetItem(BaseModel):
    dataset_id: str = Field(default_factory=lambda: f"DS-BHOPAL-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}")
    job_id: str = Field(default_factory=lambda: f"JOB-INGEST-{uuid.uuid4().hex[:8].upper()}")
    name: str
    filename: str
    format: str  # uav_raster, cadastral_vector, ai_footprints, gis_archive
    file_size_bytes: int
    file_path: Optional[str] = ""
    state: str = "Madhya Pradesh"
    city: str = "Bhopal"
    region_id: str = "bhopal_mp"
    uploaded_by: str = "admin@drishtigis.in"
    uploaded_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    processing_started_at: Optional[str] = None
    last_updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    status: str = "REGISTERED"  # REGISTERED, VALIDATING, PROCESSING, QA_REQUIRED, READY, PUBLISHED, FAILED, CANCELLED
    current_stage: str = "File Received & Job Registered"
    progress_percent: int = 10
    completed_steps: List[str] = Field(default_factory=lambda: ["File Received", "Metadata Form Initialized"])
    pending_steps: List[str] = Field(default_factory=lambda: [
        "Spatial CRS Validation",
        "Geospatial Bounds Inspection",
        "Tiling & Index Generation",
        "AI Feature Alignment Check",
        "Quality Assurance Verification"
    ])
    failed_steps: List[str] = Field(default_factory=list)
    error_details: Optional[str] = None
    crs: Optional[str] = "EPSG:4326 (WGS 84)"
    bounds: Optional[List[float]] = Field(default_factory=lambda: [77.412951, 23.254292, 77.422689, 23.256671])
    dimensions: Optional[str] = "2048 x 2048 x 3"
    spatial_resolution_m: Optional[float] = 0.02
    feature_count: Optional[int] = 0
    layer_names: List[str] = Field(default_factory=lambda: ["UAV_Orthomosaic_RGB"])
    outputs: List[Dict[str, Any]] = Field(default_factory=list)
    is_published: bool = False
    retry_eligible: bool = False

class DatasetStore:
    def __init__(self):
        GOVERNANCE_DIR.mkdir(parents=True, exist_ok=True)
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.datasets: Dict[str, DatasetItem] = {}
        self._active_workers: Set[str] = set()
        self._load()

    def _load(self):
        with self._lock:
            if DATASETS_FILE.exists():
                try:
                    with open(DATASETS_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        for item in data.get("datasets", []):
                            ds = DatasetItem(**item)
                            self.datasets[ds.dataset_id] = ds
                except Exception as e:
                    print(f"Warning: Failed to load datasets.json: {e}")

            if not self.datasets:
                self._seed_default_datasets()

    def _seed_default_datasets(self):
        """Seed default validated Bhopal prototype datasets."""
        now = datetime.now(timezone.utc).isoformat()
        seeds = [
            DatasetItem(
                dataset_id="DS-BHOPAL-RASTER-001",
                job_id="JOB-INGEST-20240901-001",
                name="Bhopal_UAV_Orthomosaic_2024",
                filename="bhopal_uav_30tiles.tif",
                format="uav_raster",
                file_size_bytes=228589130,
                file_path="Dataset/geospatial-data/BHOPAL",
                state="Madhya Pradesh",
                city="Bhopal",
                region_id="bhopal_mp",
                uploaded_by="admin@drishtigis.in",
                uploaded_at="2024-09-01T10:00:00Z",
                processing_started_at="2024-09-01T10:00:05Z",
                completed_at="2024-09-01T10:04:12Z",
                last_updated_at=now,
                status="PUBLISHED",
                current_stage="Published & Active on WebGIS",
                progress_percent=100,
                completed_steps=[
                    "File Received",
                    "Spatial CRS Validation",
                    "Geospatial Bounds Inspection",
                    "Tiling & COG Pyramid Generation",
                    "AI Building Feature Extraction",
                    "Quality Assurance Verification",
                    "Publication to XYZ Tile Endpoint"
                ],
                pending_steps=[],
                failed_steps=[],
                error_details=None,
                crs="EPSG:4326 (WGS 84)",
                bounds=[77.412951, 23.254292, 77.422689, 23.256671],
                dimensions="2048 x 2048 x 3 (30 Tiles)",
                spatial_resolution_m=0.02,
                feature_count=30,
                layer_names=["UAV_Orthomosaic_RGB", "DSM_Elevation_Layer"],
                outputs=[
                    {"name": "COG Tile Pyramid", "type": "xyz_tiles", "url": "/api/v1/tiles/bhopal/{z}/{x}/{y}"},
                    {"name": "DSM Elevation Raster", "type": "raster", "url": "/data/geospatial/dsm.tif"}
                ],
                is_published=True,
                retry_eligible=False
            ),
            DatasetItem(
                dataset_id="DS-BHOPAL-VECTOR-002",
                job_id="JOB-INGEST-20240902-002",
                name="Bhopal_Cadastral_Parcels_v1",
                filename="bhopal_parcels.json",
                format="cadastral_vector",
                file_size_bytes=1258900,
                file_path="data/governance/bhopal_parcels.json",
                state="Madhya Pradesh",
                city="Bhopal",
                region_id="bhopal_mp",
                uploaded_by="admin@drishtigis.in",
                uploaded_at="2024-09-02T11:30:00Z",
                processing_started_at="2024-09-02T11:30:02Z",
                completed_at="2024-09-02T11:31:15Z",
                last_updated_at=now,
                status="PUBLISHED",
                current_stage="Published & Active on WebGIS",
                progress_percent=100,
                completed_steps=[
                    "File Received",
                    "JSON Schema Validation",
                    "Spatial Bounds Calculation",
                    "Parcel Topology Verification",
                    "Synthetic Ownership Indexing",
                    "Publication to Vector Endpoint"
                ],
                pending_steps=[],
                failed_steps=[],
                error_details=None,
                crs="EPSG:4326 (WGS 84)",
                bounds=[77.4012, 23.2488, 77.4325, 23.2710],
                dimensions="35 Polygon Features",
                spatial_resolution_m=None,
                feature_count=35,
                layer_names=["Cadastral_Parcels"],
                outputs=[
                    {"name": "Cadastral GeoJSON Feed", "type": "vector", "url": "/api/v1/parcels"}
                ],
                is_published=True,
                retry_eligible=False
            ),
            DatasetItem(
                dataset_id="DS-BHOPAL-AI-003",
                job_id="JOB-INGEST-20240903-003",
                name="Bhopal_AI_Building_Footprints_v1",
                filename="bhopal_ai_buildings.geojson",
                format="ai_footprints",
                file_size_bytes=4718592,
                file_path="data/uavpal/ai_predictions/bhopal_ai_buildings.geojson",
                state="Madhya Pradesh",
                city="Bhopal",
                region_id="bhopal_mp",
                uploaded_by="admin@drishtigis.in",
                uploaded_at="2024-09-03T14:15:00Z",
                processing_started_at="2024-09-03T14:15:03Z",
                completed_at="2024-09-03T14:18:40Z",
                last_updated_at=now,
                status="PUBLISHED",
                current_stage="Published & Active on WebGIS",
                progress_percent=100,
                completed_steps=[
                    "File Received",
                    "GeoJSON Geometry Validation",
                    "UAV PAL Model Segmentation",
                    "Polygon Vectorization & Smoothing",
                    "Property Discrepancy Calculation",
                    "Publication to Feature Endpoint"
                ],
                pending_steps=[],
                failed_steps=[],
                error_details=None,
                crs="EPSG:4326 (WGS 84)",
                bounds=[77.4012, 23.2488, 77.4325, 23.2710],
                dimensions="834 Polygon Features",
                spatial_resolution_m=0.02,
                feature_count=834,
                layer_names=["AI_Building_Footprints"],
                outputs=[
                    {"name": "AI Features Endpoint", "type": "geojson", "url": "/api/v1/features"}
                ],
                is_published=True,
                retry_eligible=False
            )
        ]
        for ds in seeds:
            self.datasets[ds.dataset_id] = ds
        self._save()

    def _save(self):
        with self._lock:
            data = {"datasets": [ds.model_dump() for ds in self.datasets.values()]}
            with open(DATASETS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

    # ── Concurrency Worker Lock Controls ──────────────────────────────────────────

    def acquire_worker_lock(self, dataset_id: str) -> bool:
        """Attempt to acquire worker processing lock for dataset_id."""
        with self._lock:
            if dataset_id in self._active_workers:
                return False
            self._active_workers.add(dataset_id)
            return True

    def release_worker_lock(self, dataset_id: str):
        """Release worker processing lock for dataset_id."""
        with self._lock:
            self._active_workers.discard(dataset_id)

    def is_worker_active(self, dataset_id: str) -> bool:
        with self._lock:
            return dataset_id in self._active_workers

    # ── Startup Interrupted Job Recovery ─────────────────────────────────────────

    def get_interrupted_datasets(self) -> List[DatasetItem]:
        """Find datasets left in active processing state across server restarts."""
        with self._lock:
            return [
                d for d in self.datasets.values()
                if d.status in ["REGISTERED", "VALIDATING", "PROCESSING"] and d.dataset_id not in self._active_workers
            ]

    # ── Queries & Ingestion CRUD ─────────────────────────────────────────────────

    def get_dataset(self, dataset_id: str) -> Optional[DatasetItem]:
        with self._lock:
            return self.datasets.get(dataset_id)

    def list_datasets(
        self,
        status: Optional[str] = None,
        region_id: Optional[str] = None,
        format_type: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "uploaded_at",
        ascending: bool = False
    ) -> List[DatasetItem]:
        with self._lock:
            items = list(self.datasets.values())

            if status and status.upper() != "ALL":
                items = [d for d in items if d.status.upper() == status.upper()]
            if region_id and region_id.lower() != "all":
                items = [d for d in items if d.region_id.lower() == region_id.lower()]
            if format_type and format_type.lower() != "all":
                items = [d for d in items if d.format.lower() == format_type.lower()]
            if search:
                q = search.lower().strip()
                items = [
                    d for d in items
                    if q in d.name.lower() or q in d.dataset_id.lower() or q in d.filename.lower()
                ]

            def get_sort_key(d: DatasetItem):
                if sort_by == "name":
                    return d.name.lower()
                elif sort_by == "status":
                    return d.status
                elif sort_by == "file_size_bytes":
                    return d.file_size_bytes
                return d.uploaded_at

            items.sort(key=get_sort_key, reverse=not ascending)
            return items

    def register_dataset(
        self,
        name: str,
        filename: str,
        format_type: str,
        file_size_bytes: int,
        file_path: str,
        state: str = "Madhya Pradesh",
        city: str = "Bhopal",
        region_id: str = "bhopal_mp",
        uploaded_by: str = "admin@drishtigis.in"
    ) -> DatasetItem:
        with self._lock:
            ds_id = f"DS-INGEST-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            job_id = f"JOB-INGEST-{uuid.uuid4().hex[:8].upper()}"

            ds = DatasetItem(
                dataset_id=ds_id,
                job_id=job_id,
                name=name or filename,
                filename=filename,
                format=format_type,
                file_size_bytes=file_size_bytes,
                file_path=file_path,
                state=state,
                city=city,
                region_id=region_id,
                uploaded_by=uploaded_by,
                uploaded_at=datetime.now(timezone.utc).isoformat(),
                last_updated_at=datetime.now(timezone.utc).isoformat(),
                status="REGISTERED",
                current_stage="File Received — Processing Queued",
                progress_percent=15,
                completed_steps=["File Received & Verified", "Job Metadata Registered"],
                pending_steps=[
                    "Spatial CRS Validation",
                    "Geospatial Bounds Inspection",
                    "Tiling & Index Generation",
                    "AI Feature Alignment Check",
                    "Quality Assurance Verification"
                ],
                failed_steps=[],
                error_details=None,
                is_published=False,
                retry_eligible=False
            )
            self.datasets[ds_id] = ds
            self._save()
            return ds

    def update_dataset_status(
        self,
        dataset_id: str,
        status: str,
        current_stage: str,
        progress_percent: int,
        completed_step: Optional[str] = None,
        failed_step: Optional[str] = None,
        error_details: Optional[str] = None,
        crs: Optional[str] = None,
        bounds: Optional[List[float]] = None,
        dimensions: Optional[str] = None,
        feature_count: Optional[int] = None,
        outputs: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[DatasetItem]:
        with self._lock:
            ds = self.datasets.get(dataset_id)
            if not ds:
                return None

            ds.status = status
            ds.current_stage = current_stage
            ds.progress_percent = progress_percent
            ds.last_updated_at = datetime.now(timezone.utc).isoformat()

            if not ds.processing_started_at and status in ["VALIDATING", "PROCESSING"]:
                ds.processing_started_at = datetime.now(timezone.utc).isoformat()

            if status in ["READY", "PUBLISHED", "FAILED", "CANCELLED"]:
                ds.completed_at = datetime.now(timezone.utc).isoformat()

            if completed_step and completed_step not in ds.completed_steps:
                ds.completed_steps.append(completed_step)
                if completed_step in ds.pending_steps:
                    ds.pending_steps.remove(completed_step)

            if failed_step:
                if failed_step not in ds.failed_steps:
                    ds.failed_steps.append(failed_step)
                ds.retry_eligible = True

            if error_details:
                ds.error_details = error_details

            if crs:
                ds.crs = crs
            if bounds:
                ds.bounds = bounds
            if dimensions:
                ds.dimensions = dimensions
            if feature_count is not None:
                ds.feature_count = feature_count
            if outputs:
                ds.outputs = outputs

            if status == "PUBLISHED":
                ds.is_published = True

            self._save()
            return ds

    # ── State Machine Enforcements ────────────────────────────────────────────────

    def publish_dataset(self, dataset_id: str) -> DatasetItem:
        with self._lock:
            ds = self.datasets.get(dataset_id)
            if not ds:
                raise ValueError(f"Dataset ID '{dataset_id}' not found.")
            if ds.status not in ["READY", "QA_REQUIRED"]:
                raise ValueError(f"Cannot publish dataset '{dataset_id}' in '{ds.status}' status. Must be READY or QA_REQUIRED.")

            ds.status = "PUBLISHED"
            ds.is_published = True
            ds.current_stage = "Published & Active on WebGIS"
            ds.progress_percent = 100
            ds.last_updated_at = datetime.now(timezone.utc).isoformat()
            self._save()
            return ds

    def retry_dataset(self, dataset_id: str) -> DatasetItem:
        with self._lock:
            ds = self.datasets.get(dataset_id)
            if not ds:
                raise ValueError(f"Dataset ID '{dataset_id}' not found.")
            if ds.status not in ["FAILED", "CANCELLED"]:
                raise ValueError(f"Cannot retry dataset in '{ds.status}' status. Only FAILED or CANCELLED jobs can be retried.")

            ds.status = "REGISTERED"
            ds.current_stage = "Retry Enqueued — Processing Pipeline Initiated"
            ds.progress_percent = 15
            ds.error_details = None
            ds.failed_steps = []
            ds.last_updated_at = datetime.now(timezone.utc).isoformat()
            self._save()
            return ds

    def cancel_dataset(self, dataset_id: str) -> DatasetItem:
        with self._lock:
            ds = self.datasets.get(dataset_id)
            if not ds:
                raise ValueError(f"Dataset ID '{dataset_id}' not found.")
            if ds.status not in ["REGISTERED", "VALIDATING", "PROCESSING"]:
                raise ValueError(f"Cannot cancel dataset in '{ds.status}' status. Job is no longer active.")

            ds.status = "CANCELLED"
            ds.current_stage = "Processing Job Cancelled by Admin"
            ds.completed_at = datetime.now(timezone.utc).isoformat()
            ds.last_updated_at = datetime.now(timezone.utc).isoformat()
            self._save()
            return ds

    def get_analytics_summary(self) -> Dict[str, Any]:
        with self._lock:
            items = list(self.datasets.values())
            total_datasets = len(items)
            active_jobs = sum(1 for d in items if d.status in ["REGISTERED", "VALIDATING", "PROCESSING"])
            completed_datasets = sum(1 for d in items if d.status in ["READY", "PUBLISHED"])
            failed_jobs = sum(1 for d in items if d.status == "FAILED")
            qa_required = sum(1 for d in items if d.status == "QA_REQUIRED")
            published_datasets = sum(1 for d in items if d.is_published)
            total_size_bytes = sum(d.file_size_bytes for d in items)
            total_mapped_features = sum(d.feature_count or 0 for d in items)

            by_status = {}
            by_format = {}
            by_region = {}

            for d in items:
                by_status[d.status] = by_status.get(d.status, 0) + 1
                by_format[d.format] = by_format.get(d.format, 0) + 1
                by_region[d.region_id] = by_region.get(d.region_id, 0) + 1

            return {
                "total_datasets": total_datasets,
                "active_processing_jobs": active_jobs,
                "completed_datasets": completed_datasets,
                "failed_jobs": failed_jobs,
                "qa_required_count": qa_required,
                "published_datasets": published_datasets,
                "total_ingested_size_bytes": total_size_bytes,
                "total_mapped_features": total_mapped_features,
                "by_status": by_status,
                "by_format": by_format,
                "by_region": by_region,
                "last_refreshed_at": datetime.now(timezone.utc).isoformat()
            }

dataset_store = DatasetStore()
