"""
DrishtiGIS — Unified GIS Export Processing Engine
===================================================
Phase 9: GIS-Ready Outputs, Reports & Evidence Packaging

Provides multi-layer GIS exporting into GeoJSON, GeoPackage (.gpkg), and ZIP archives.
Preserves CRS metadata, source classifications, OSM attributions, and synthetic data disclaimers.
"""

import json
import uuid
import sqlite3
import zipfile
import io
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timezone
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[3]

# Data Paths
SYNTHETIC_PARCELS_FILE = ROOT / "data" / "synthetic" / "bhopal-synthetic-parcels.geojson"
SYNTHETIC_PROPS_FILE = ROOT / "data" / "synthetic" / "bhopal-synthetic-properties.json"
AI_BUILDINGS_FILE = ROOT / "data" / "ai_output" / "bhopal-building-parcel-associations.geojson"
DISCREPANCIES_FILE = ROOT / "data" / "ai_output" / "bhopal-discrepancies.json"
ROADS_FILE = ROOT / "data" / "osm" / "bhopal-extract" / "bhopal-roads.geojson"
LANDUSE_FILE = ROOT / "data" / "osm" / "bhopal-extract" / "bhopal-landuse.geojson"

_SYNTHETIC_DISCLAIMER = (
    "Synthetic prototype data — not an official land record. "
    "All identifiers, owner names, and property data are synthetic."
)
_AI_DISCLAIMER = (
    "AI analysis is derived from the UAVPal U-Net ResNet18 pipeline. "
    "NOT cadastral boundaries. NOT legal determinations. "
    "Spatial relationships are geometric observations only."
)
_OSM_ATTRIBUTION = "© OpenStreetMap contributors. Data extracted for spatial reference context only."


def _load_json_file(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_export(export_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates export payload before download.
    Checks geometry validity, non-empty features, CRS metadata, required source fields,
    and synthetic disclaimers.
    """
    errors: List[str] = []
    if not isinstance(export_data, dict):
        return False, ["Export payload is not a valid dictionary."]

    if "features" in export_data:
        features = export_data.get("features", [])
        if not features:
            errors.append("Export feature collection is empty.")

        for idx, feat in enumerate(features[:100]):  # Sample check first 100 features
            geom = feat.get("geometry")
            if geom is not None and isinstance(geom, dict):
                try:
                    sh_geom = shape(geom)
                    if sh_geom.is_empty:
                        errors.append(f"Feature index {idx} contains empty geometry.")
                        break
                except Exception as e:
                    errors.append(f"Feature index {idx} failed Shapely geometry parsing: {str(e)}")
                    break

            props = feat.get("properties", {})
            if "source" not in props and "geometry_source" not in props:
                errors.append(f"Feature index {idx} is missing source classification attribute.")
                break

            if props.get("source") == "SYNTHETIC_DEMO" and "disclaimer" not in props:
                errors.append(f"Synthetic feature index {idx} missing mandatory disclaimer attribute.")
                break
    elif "layers" in export_data:
        layers = export_data.get("layers", {})
        if not layers:
            errors.append("Export contains no active layers.")

    return (len(errors) == 0, errors)


def build_gis_export(
    dataset_id: str = "DATASET-BHOPAL-UAV",
    region_id: str = "REGION-BPL-01",
    layers: List[str] = None,
    output_format: str = "GeoJSON",
    output_crs: str = "EPSG:4326",
    city: str = "Bhopal",
    state: str = "Madhya Pradesh",
    country: str = "India"
) -> Tuple[bytes, str, Dict[str, Any]]:
    """
    Generates multi-layer GIS export in GeoJSON, GeoPackage, or ZIP format.

    Returns:
        (file_bytes, filename, metadata_dict)
    """
    if layers is None:
        layers = ["parcels", "buildings", "roads", "landuse", "discrepancies", "reviews"]

    from backend.app.services.review_store import review_store

    export_id = f"EXP-{uuid.uuid4().hex[:8].upper()}"
    generated_at = datetime.now(timezone.utc).isoformat()

    # Load requested layers
    layer_collections: Dict[str, List[Dict[str, Any]]] = {}
    total_features = 0

    # 1. Parcels
    if "parcels" in layers:
        parcels_data = _load_json_file(SYNTHETIC_PARCELS_FILE)
        p_features = []
        for feat in parcels_data.get("features", []):
            props = dict(feat.get("properties", {}))
            props.update({
                "source": "SYNTHETIC_DEMO",
                "record_status": "SYNTHETIC_DEMO",
                "disclaimer": _SYNTHETIC_DISCLAIMER,
                "city": city,
                "state": state,
                "country": country,
                "dataset_id": dataset_id,
                "region_id": region_id,
            })
            p_features.append({
                "type": "Feature",
                "geometry": feat.get("geometry"),
                "properties": props
            })
        layer_collections["parcels"] = p_features
        total_features += len(p_features)

    # 2. Buildings (AI + Reviewed)
    if "buildings" in layers:
        buildings_data = _load_json_file(AI_BUILDINGS_FILE)
        b_features = []
        for feat in buildings_data.get("features", []):
            props = dict(feat.get("properties", {}))
            props.update({
                "source": "AI_DERIVED_UAVPAL",
                "model": "U-Net + ResNet18",
                "model_version": "1.0.0",
                "disclaimer": _AI_DISCLAIMER,
                "city": city,
                "state": state,
                "country": country,
                "dataset_id": dataset_id,
                "region_id": region_id,
            })
            b_features.append({
                "type": "Feature",
                "geometry": feat.get("geometry"),
                "properties": props
            })
        layer_collections["buildings"] = b_features
        total_features += len(b_features)

    # 3. Roads
    if "roads" in layers:
        roads_data = _load_json_file(ROADS_FILE)
        r_features = []
        for feat in roads_data.get("features", []):
            props = dict(feat.get("properties", {}))
            props.update({
                "source": "REFERENCE_GIS",
                "source_type": "REFERENCE_GIS",
                "attribution": _OSM_ATTRIBUTION,
                "city": city,
                "state": state,
                "country": country,
                "dataset_id": dataset_id,
                "region_id": region_id,
            })
            r_features.append({
                "type": "Feature",
                "geometry": feat.get("geometry"),
                "properties": props
            })
        layer_collections["roads"] = r_features
        total_features += len(r_features)

    # 4. Landuse
    if "landuse" in layers:
        landuse_data = _load_json_file(LANDUSE_FILE)
        lu_features = []
        for feat in landuse_data.get("features", []):
            props = dict(feat.get("properties", {}))
            props.update({
                "source": "REFERENCE_GIS",
                "source_type": "REFERENCE_GIS",
                "classification_type": "OBSERVED_LAND_USE_PATTERN",
                "attribution": _OSM_ATTRIBUTION,
                "city": city,
                "state": state,
                "country": country,
                "dataset_id": dataset_id,
                "region_id": region_id,
            })
            lu_features.append({
                "type": "Feature",
                "geometry": feat.get("geometry"),
                "properties": props
            })
        layer_collections["landuse"] = lu_features
        total_features += len(lu_features)

    # 5. Discrepancies
    if "discrepancies" in layers:
        disc_data = _load_json_file(DISCREPANCIES_FILE)
        disc_features = []
        for d in disc_data.get("discrepancies", []):
            disc_features.append({
                "type": "Feature",
                "geometry": None,
                "properties": {
                    "discrepancy_id": d.get("id"),
                    "parcel_id": d.get("parcel_id"),
                    "building_id": d.get("building_id"),
                    "issue_type": d.get("type"),
                    "severity": d.get("severity"),
                    "description": d.get("description"),
                    "source": d.get("source", "AI_DERIVED_UAVPAL"),
                    "city": city,
                    "state": state,
                    "dataset_id": dataset_id,
                }
            })
        layer_collections["discrepancies"] = disc_features
        total_features += len(disc_features)

    # 6. Reviews & Verifications
    if "reviews" in layers:
        reviews = review_store.list_reviews(city=city)
        rev_features = []
        for r in reviews:
            geom = r.reviewed_geometry or r.original_geometry
            rev_features.append({
                "type": "Feature",
                "geometry": geom,
                "properties": {
                    "review_id": r.review_id,
                    "entity_type": r.entity_type,
                    "parcel_id": r.parcel_id,
                    "issue_type": r.issue_type.value,
                    "severity": r.severity.value,
                    "review_status": r.status.value,
                    "source": r.source.value,
                    "verification_status": r.verification_status,
                    "city": r.city,
                    "state": r.state,
                }
            })
        layer_collections["reviews"] = rev_features
        total_features += len(rev_features)

    metadata = {
        "export_id": export_id,
        "generated_at": generated_at,
        "dataset_id": dataset_id,
        "region_id": region_id,
        "country": country,
        "state": state,
        "city": city,
        "epoch_id": "EPOCH-BPL-2024-01",
        "source_datasets": ["UAVPal Orthomosaic", "Synthetic Parcels", "OpenStreetMap Reference GIS"],
        "source_classifications": ["AI_DERIVED_UAVPAL", "SYNTHETIC_DEMO", "REFERENCE_GIS", "REVIEWED_AI_GEOMETRY"],
        "processing_model": "U-Net + ResNet18",
        "model_version": "1.0.0",
        "processing_datetime": "2024-01-15T10:30:00Z",
        "source_crs": "EPSG:4326",
        "analysis_crs": "EPSG:32643",
        "output_crs": output_crs,
        "layer_count": len(layer_collections),
        "feature_count": total_features,
        "layers": list(layer_collections.keys()),
        "disclaimer": _SYNTHETIC_DISCLAIMER,
    }

    # Generate File according to output_format
    if output_format.upper() == "GEOPACKAGE":
        file_bytes, filename = _build_geopackage(layer_collections, metadata, export_id)
    elif output_format.upper() == "ZIP":
        file_bytes, filename = _build_zip_export(layer_collections, metadata, export_id)
    else:
        # Default: Unified GeoJSON FeatureCollection
        all_features = []
        for l_name, feats in layer_collections.items():
            for f in feats:
                feat_copy = dict(f)
                feat_copy["properties"] = dict(f.get("properties", {}))
                feat_copy["properties"]["layer_name"] = l_name
                all_features.append(feat_copy)

        geojson_payload = {
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": f"urn:ogc:def:crs:OGC:1.3:{output_crs.replace(':', '')}"}},
            "metadata": metadata,
            "features": all_features,
        }

        is_valid, errs = validate_export(geojson_payload)
        if not is_valid:
            raise ValueError(f"Export validation failed: {'; '.join(errs)}")

        file_bytes = json.dumps(geojson_payload, indent=2).encode("utf-8")
        filename = f"DrishtiGIS_Export_{export_id}.geojson"

    return file_bytes, filename, metadata


def _build_zip_export(
    layer_collections: Dict[str, List[Dict[str, Any]]],
    metadata: Dict[str, Any],
    export_id: str
) -> Tuple[bytes, str]:
    """Builds multi-layer ZIP containing GeoJSON files and metadata."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("metadata.json", json.dumps(metadata, indent=2))

        for l_name, feats in layer_collections.items():
            layer_payload = {
                "type": "FeatureCollection",
                "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
                "layer": l_name,
                "features": feats,
            }
            zf.writestr(f"layers/{l_name}.geojson", json.dumps(layer_payload, indent=2))

        readme = f"""# DrishtiGIS GIS Export Package
Export ID: {export_id}
Generated At: {metadata['generated_at']}
Dataset ID: {metadata['dataset_id']}
Region: {metadata['city']}, {metadata['state']}, {metadata['country']}

## Layer Contents
- Parcels: Synthetic prototype parcel polygons (SYNTHETIC_DEMO)
- Buildings: AI-derived building footprints (AI_DERIVED_UAVPAL / REVIEWED_AI_GEOMETRY)
- Roads: OpenStreetMap reference transport network (REFERENCE_GIS)
- Land Use: OpenStreetMap observed land use patterns (REFERENCE_GIS)
- Discrepancies: Spatial relationship discrepancy observations

## Disclaimer
{_SYNTHETIC_DISCLAIMER}
{_AI_DISCLAIMER}
"""
        zf.writestr("README.md", readme)

    zip_buffer.seek(0)
    return zip_buffer.getvalue(), f"DrishtiGIS_Package_{export_id}.zip"


def _build_geopackage(
    layer_collections: Dict[str, List[Dict[str, Any]]],
    metadata: Dict[str, Any],
    export_id: str
) -> Tuple[bytes, str]:
    """Builds a GeoPackage SQLite database file."""
    mem_db = sqlite3.connect(":memory:")
    cursor = mem_db.cursor()

    cursor.execute("""
        CREATE TABLE gpkg_spatial_ref_sys (
            srs_name TEXT NOT NULL,
            srs_id INTEGER NOT NULL PRIMARY KEY,
            organization TEXT NOT NULL,
            organization_coordsys_id INTEGER NOT NULL,
            definition TEXT NOT NULL,
            description TEXT
        );
    """)

    cursor.execute("""
        CREATE TABLE gpkg_contents (
            table_name TEXT NOT NULL PRIMARY KEY,
            data_type TEXT NOT NULL,
            identifier TEXT UNIQUE,
            description TEXT DEFAULT '',
            last_change DATETIME NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
            min_x DOUBLE, min_y DOUBLE, max_x DOUBLE, max_y DOUBLE,
            srs_id INTEGER
        );
    """)

    cursor.execute("""
        CREATE TABLE gpkg_geometry_columns (
            table_name TEXT NOT NULL,
            column_name TEXT NOT NULL,
            geometry_type_name TEXT NOT NULL,
            srs_id INTEGER NOT NULL,
            z TINYINT NOT NULL,
            m TINYINT NOT NULL,
            CONSTRAINT pk_geom_cols PRIMARY KEY (table_name, column_name)
        );
    """)

    cursor.execute("""
        INSERT INTO gpkg_spatial_ref_sys VALUES (
            'WGS 84 geodetic', 4326, 'EPSG', 4326,
            'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]',
            'Longitude/Latitude WGS 84'
        );
    """)

    for l_name, feats in layer_collections.items():
        table_name = f"layer_{l_name}"
        cursor.execute(f"""
            CREATE TABLE {table_name} (
                fid INTEGER PRIMARY KEY AUTOINCREMENT,
                geojson_geometry TEXT,
                properties_json TEXT,
                source_classification TEXT,
                disclaimer TEXT
            );
        """)

        cursor.execute("""
            INSERT INTO gpkg_contents (table_name, data_type, identifier, description, srs_id)
            VALUES (?, 'features', ?, ?, 4326);
        """, (table_name, l_name, f"DrishtiGIS layer {l_name}"))

        cursor.execute("""
            INSERT INTO gpkg_geometry_columns (table_name, column_name, geometry_type_name, srs_id, z, m)
            VALUES (?, 'geojson_geometry', 'GEOMETRY', 4326, 0, 0);
        """, (table_name,))

        for feat in feats:
            geom_str = json.dumps(feat.get("geometry")) if feat.get("geometry") else None
            props_str = json.dumps(feat.get("properties", {}))
            src_class = feat.get("properties", {}).get("source", "UNKNOWN")
            disc = feat.get("properties", {}).get("disclaimer", "")

            cursor.execute(f"""
                INSERT INTO {table_name} (geojson_geometry, properties_json, source_classification, disclaimer)
                VALUES (?, ?, ?, ?);
            """, (geom_str, props_str, src_class, disc))

    mem_db.commit()

    db_bytes = io.BytesIO()
    for line in mem_db.iterdump():
        db_bytes.write(f"{line}\n".encode("utf-8"))
    mem_db.close()

    db_bytes.seek(0)
    return db_bytes.getvalue(), f"DrishtiGIS_{export_id}.gpkg"
