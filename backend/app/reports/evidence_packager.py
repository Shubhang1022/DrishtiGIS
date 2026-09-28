"""
DrishtiGIS — Evidence Packaging Service
==========================================
Phase 9: GIS-Ready Outputs, Reports & Evidence Packaging

Builds structured Evidence Package zip archives containing metadata, layers,
reports, review logs, and README disclaimers.
"""

import json
import zipfile
import io
from pathlib import Path
from typing import Tuple, Dict, Any
from datetime import datetime, timezone

from backend.app.gis.export_engine import build_gis_export, _SYNTHETIC_DISCLAIMER, _AI_DISCLAIMER
from backend.app.reports.report_engine import generate_area_report, generate_parcel_report
from backend.app.services.review_store import review_store

ROOT = Path(__file__).resolve().parents[3]


def create_evidence_package(
    dataset_id: str = "DATASET-BHOPAL-UAV",
    region_id: str = "REGION-BPL-01",
    city: str = "Bhopal"
) -> Tuple[bytes, str]:
    """
    Creates a structured Evidence Package ZIP archive.

    Contents:
      /metadata/
        dataset.json
        processing.json
        crs.json
      /layers/
        parcels.geojson
        buildings.geojson
        roads.geojson
        landuse.geojson
        discrepancies.geojson
        reviews.geojson
      /reports/
        area_intelligence_report.json
        parcel_sample_dossier.json
      /review/
        review_history.json
      README.md
    """
    pkg_timestamp = datetime.now(timezone.utc).isoformat()
    pkg_id = f"EVID-PKG-{city.upper()}-{datetime.now().strftime('%Y%m%d')}"

    # Build GIS export layers
    _, _, export_meta = build_gis_export(dataset_id=dataset_id, region_id=region_id, city=city)

    # Build area report
    area_report = generate_area_report(city=city, region_id=region_id)

    # Build sample parcel report
    sample_parcel_report = generate_parcel_report("DRS-BPL-DEMO-001")

    # Fetch review history
    reviews = review_store.list_reviews(city=city)
    reviews_payload = [r.dict() for r in reviews]

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. Metadata
        zf.writestr("metadata/dataset.json", json.dumps({
            "dataset_id": dataset_id,
            "region_id": region_id,
            "city": city,
            "state": "Madhya Pradesh",
            "country": "India",
            "imagery_source": "UAVPal RGB GeoTIFF (30 tiles)",
            "acquisition_date": "2024-01-15",
            "resolution_m": 0.02,
        }, indent=2))

        zf.writestr("metadata/processing.json", json.dumps({
            "ai_pipeline": "U-Net + ResNet18",
            "model_version": "1.0.0",
            "building_extractions": 834,
            "discrepancies_detected": 243,
            "synthetic_parcels": 35,
        }, indent=2))

        zf.writestr("metadata/crs.json", json.dumps({
            "display_crs": "EPSG:4326 (WGS 84)",
            "metric_analysis_crs": "EPSG:32643 (UTM Zone 43N) / EPSG:3857",
            "geographic_extent": [77.38, 23.23, 77.42, 23.27],
        }, indent=2))

        # 2. Layers
        # Import individual layer GeoJSONs
        parcels_bytes, _, _ = build_gis_export(layers=["parcels"], output_format="GeoJSON", city=city)
        buildings_bytes, _, _ = build_gis_export(layers=["buildings"], output_format="GeoJSON", city=city)
        roads_bytes, _, _ = build_gis_export(layers=["roads"], output_format="GeoJSON", city=city)
        landuse_bytes, _, _ = build_gis_export(layers=["landuse"], output_format="GeoJSON", city=city)
        discrepancies_bytes, _, _ = build_gis_export(layers=["discrepancies"], output_format="GeoJSON", city=city)
        reviews_bytes, _, _ = build_gis_export(layers=["reviews"], output_format="GeoJSON", city=city)

        zf.writestr("layers/parcels.geojson", parcels_bytes)
        zf.writestr("layers/buildings.geojson", buildings_bytes)
        zf.writestr("layers/roads.geojson", roads_bytes)
        zf.writestr("layers/landuse.geojson", landuse_bytes)
        zf.writestr("layers/discrepancies.geojson", discrepancies_bytes)
        zf.writestr("layers/reviews.geojson", reviews_bytes)

        # 3. Reports
        zf.writestr("reports/area_intelligence_report.json", json.dumps(area_report, indent=2))
        zf.writestr("reports/parcel_sample_dossier.json", json.dumps(sample_parcel_report, indent=2))

        # 4. Review
        zf.writestr("review/review_history.json", json.dumps({"total": len(reviews_payload), "reviews": reviews_payload}, indent=2))

        # 5. README.md
        readme = f"""# DrishtiGIS Evidence Package
Package ID: {pkg_id}
Generated At: {pkg_timestamp}
Dataset ID: {dataset_id}
Region: {city}, Madhya Pradesh, India

## Package Structure
- `/metadata`: Dataset, processing model, and CRS specifications.
- `/layers`: GIS-ready GeoJSON feature layers (Parcels, Buildings, Roads, Landuse, Discrepancies, Reviews).
- `/reports`: Area-level intelligence report and sample parcel dossier.
- `/review`: Complete surveyor review queue and audit log state.

## Source Classifications
- Parcels: `SYNTHETIC_DEMO`
- AI Buildings: `AI_DERIVED_UAVPAL` / `REVIEWED_AI_GEOMETRY`
- Roads & Land-Use: `REFERENCE_GIS` (OpenStreetMap)

## Disclaimers
{_SYNTHETIC_DISCLAIMER}
{_AI_DISCLAIMER}
"""
        zf.writestr("README.md", readme)

    zip_buffer.seek(0)
    filename = f"DrishtiGIS_EvidencePackage_{dataset_id}_{city}.zip"
    return zip_buffer.getvalue(), filename
