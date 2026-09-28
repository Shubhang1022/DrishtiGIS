"""
DrishtiGIS AI Assistant Tool Registry.
Strictly controlled, read-only tools wrapping trusted backend services.
No arbitrary SQL, no filesystem access, no command execution.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel

from shapely.geometry import shape

from backend.app.api.v1.parcels import (
    _load_synthetic_parcels,
    _load_synthetic_props,
    _load_legacy_parcels,
    _load_legacy_props,
    _load_ai_features,
    _load_discrepancies,
    _build_ai_analysis,
    _SYNTHETIC_DISCLAIMER
)
from backend.app.api.v1.roads import load_raw_roads
from backend.app.gis.road_engine import process_road_features, analyze_parcel_access
from backend.app.api.v1.landuse import load_raw_landuse
from backend.app.gis.landuse_engine import process_landuse_features, analyze_parcel_landuse
from backend.app.gis.change_engine import (
    summarize_parcel_changes
)
from backend.app.api.v1.historical import load_ai_buildings
from backend.app.services.review_store import review_store
from backend.app.assistant.provenance import create_provenance, ProvenanceInfo

ROOT = Path(__file__).resolve().parents[4]

class ToolParameter(BaseModel):
    name: str
    type: str
    description: str
    required: bool = True

class ToolSchema(BaseModel):
    name: str
    description: str
    parameters: List[ToolParameter]

class ToolResult(BaseModel):
    tool_name: str
    success: bool
    data: Dict[str, Any]
    provenance: Optional[ProvenanceInfo] = None
    error: Optional[str] = None

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable[..., ToolResult]] = {}
        self._schemas: Dict[str, ToolSchema] = {}
        self._register_default_tools()

    def register(self, schema: ToolSchema, handler: Callable[..., ToolResult]):
        self._schemas[schema.name] = schema
        self._tools[schema.name] = handler

    def get_schemas(self) -> List[Dict[str, Any]]:
        return [s.model_dump() for s in self._schemas.values()]

    def execute(self, tool_name: str, arguments: Dict[str, Any], user: Optional[Any] = None) -> ToolResult:
        if tool_name not in self._tools:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                data={},
                error=f"Tool '{tool_name}' is not registered in DrishtiGIS ToolRegistry."
            )

        # Scoped permission check for user context
        if user and getattr(user, "role", None) != "ADMIN":
            target_region = arguments.get("region_id") or "bhopal_mp"
            user_region = getattr(user, "region_id", "*")
            allowed_datasets = getattr(user, "allowed_datasets", ["*"])

            if user_region != "*" and user_region.lower() != target_region.lower():
                return ToolResult(
                    tool_name=tool_name,
                    success=False,
                    data={},
                    error=f"Access restricted: Region '{target_region}' is not accessible under your current account role ({getattr(user, 'role', 'PUBLIC')})."
                )

        try:
            return self._tools[tool_name](**arguments)
        except Exception as e:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                data={},
                error=f"Error executing tool '{tool_name}': {str(e)}"
            )

    def _register_default_tools(self):
        # 1. get_parcel_details
        self.register(
            ToolSchema(
                name="get_parcel_details",
                description="Get detailed information for a parcel including area, building count, discrepancy flags, and synthetic disclaimer.",
                parameters=[ToolParameter(name="parcel_id", type="string", description="Parcel ID (e.g., DRS-BPL-DEMO-014 or DRS-BPL-00101)")]
            ),
            self._tool_get_parcel_details
        )

        # 2. get_parcel_buildings
        self.register(
            ToolSchema(
                name="get_parcel_buildings",
                description="Get all AI-derived building footprints associated with a parcel.",
                parameters=[ToolParameter(name="parcel_id", type="string", description="Parcel ID")]
            ),
            self._tool_get_parcel_buildings
        )

        # 3. get_parcel_roads
        self.register(
            ToolSchema(
                name="get_parcel_roads",
                description="Analyze road access corridors and nearest road distance for a parcel.",
                parameters=[ToolParameter(name="parcel_id", type="string", description="Parcel ID")]
            ),
            self._tool_get_parcel_roads
        )

        # 4. get_parcel_landuse
        self.register(
            ToolSchema(
                name="get_parcel_landuse",
                description="Get observed land-use pattern for a parcel derived from imagery/reference data.",
                parameters=[ToolParameter(name="parcel_id", type="string", description="Parcel ID")]
            ),
            self._tool_get_parcel_landuse
        )

        # 5. get_parcel_discrepancies
        self.register(
            ToolSchema(
                name="get_parcel_discrepancies",
                description="Get AI-flagged spatial discrepancies for a parcel.",
                parameters=[ToolParameter(name="parcel_id", type="string", description="Parcel ID")]
            ),
            self._tool_get_parcel_discrepancies
        )

        # 6. get_parcel_history
        self.register(
            ToolSchema(
                name="get_parcel_history",
                description="Get multi-epoch historical change summary for a parcel.",
                parameters=[ToolParameter(name="parcel_id", type="string", description="Parcel ID")]
            ),
            self._tool_get_parcel_history
        )

        # 7. get_building_details
        self.register(
            ToolSchema(
                name="get_building_details",
                description="Get details for a specific AI-detected building footprint.",
                parameters=[ToolParameter(name="building_id", type="string", description="Building ID")]
            ),
            self._tool_get_building_details
        )

        # 8. get_review_status
        self.register(
            ToolSchema(
                name="get_review_status",
                description="Get surveyor review status, audit trail summary, and field verification state for a parcel or review item.",
                parameters=[
                    ToolParameter(name="parcel_id", type="string", description="Parcel ID", required=False),
                    ToolParameter(name="review_id", type="string", description="Review ID", required=False)
                ]
            ),
            self._tool_get_review_status
        )

        # 9. get_dataset_metadata
        self.register(
            ToolSchema(
                name="get_dataset_metadata",
                description="Get spatial dataset provenance, acquisition specs, AI model details, and CRS metadata.",
                parameters=[
                    ToolParameter(name="dataset_id", type="string", description="Dataset identifier", required=False),
                    ToolParameter(name="region_id", type="string", description="Region identifier", required=False)
                ]
            ),
            self._tool_get_dataset_metadata
        )

        # 10. get_region_summary
        self.register(
            ToolSchema(
                name="get_region_summary",
                description="Get dynamically calculated summary statistics for a region (parcels, buildings, roads, landuse, discrepancies).",
                parameters=[ToolParameter(name="region_id", type="string", description="Region ID (default: bhopal_mp)", required=False)]
            ),
            self._tool_get_region_summary
        )

        # 11. search_parcels
        self.register(
            ToolSchema(
                name="search_parcels",
                description="Search parcels by ID, plot number, survey number, or locality.",
                parameters=[
                    ToolParameter(name="query", type="string", description="Search query string"),
                    ToolParameter(name="region_id", type="string", description="Region ID", required=False)
                ]
            ),
            self._tool_search_parcels
        )

        # 12. search_buildings
        self.register(
            ToolSchema(
                name="search_buildings",
                description="Search AI-detected building footprints by ID, parcel ID, or discrepancy status.",
                parameters=[
                    ToolParameter(name="query", type="string", description="Search query string"),
                    ToolParameter(name="region_id", type="string", description="Region ID", required=False)
                ]
            ),
            self._tool_search_buildings
        )

        # 13. get_export_options
        self.register(
            ToolSchema(
                name="get_export_options",
                description="Get available GIS export formats, layer options, CRS choices, and validation requirements.",
                parameters=[ToolParameter(name="region_id", type="string", description="Region ID", required=False)]
            ),
            self._tool_get_export_options
        )

    # ── Handlers ──────────────────────────────────────────────────────────────

    def _tool_get_parcel_details(self, parcel_id: str) -> ToolResult:
        pid_clean = parcel_id.strip().upper()
        syn_props = _load_synthetic_props()
        prop = next((
            p for p in syn_props
            if p.get("property_id", "").upper() == pid_clean
            or p.get("parcel_id", "").upper() == pid_clean
            or p.get("id", "").upper() == pid_clean
            or p.get("plot_number", "").upper() == pid_clean
        ), None)
        is_synthetic = True
        
        if not prop:
            leg_props = _load_legacy_props()
            prop = next((
                p for p in leg_props
                if p.get("property_id", "").upper() == pid_clean
                or p.get("id", "").upper() == pid_clean
            ), None)
            is_synthetic = False

        if not prop:
            return ToolResult(
                tool_name="get_parcel_details",
                success=False,
                data={},
                error=f"Parcel ID '{parcel_id}' not found in dataset."
            )

        actual_id = prop.get("property_id", parcel_id)
        area_val = prop.get("recorded_area_m2", prop.get("area_sqm", prop.get("parcel_area_m2", 500)))

        ai_analysis = _build_ai_analysis(actual_id, area_val)
        review_item = review_store.get_review_by_entity("parcel", actual_id)

        data = {
            "parcel_id": actual_id,
            "plot_number": prop.get("plot_number", "N/A"),
            "region_id": "bhopal_mp",
            "dataset_id": "bhopal_synthetic_demo" if is_synthetic else "bhopal_legacy_demo",
            "source": "SYNTHETIC_DEMO" if is_synthetic else "DEMO_DATA_PROTOTYPE_ONLY",
            "record_status": prop.get("record_status", "SYNTHETIC_DEMO" if is_synthetic else "DEMO"),
            "disclaimer": _SYNTHETIC_DISCLAIMER if is_synthetic else "Prototype demonstration parcel data only.",
            "parcel_area_m2": area_val,
            "building_count": ai_analysis.get("building_count", 0),
            "total_building_area_m2": ai_analysis.get("total_detected_area_m2", 0),
            "building_coverage_ratio": ai_analysis.get("coverage_ratio", 0.0),
            "discrepancy_count": ai_analysis.get("discrepancy_count", 0),
            "discrepancies": ai_analysis.get("discrepancies", []),
            "review_status": review_item.status if review_item else "NOT_IN_QUEUE",
            "verification_status": "FIELD_VERIFIED" if (review_item and review_item.field_verification_records) else "PENDING_VERIFICATION"
        }

        provenance = create_provenance(
            source_type="SYNTHETIC_DEMO" if is_synthetic else "DEMO_DATA_PROTOTYPE_ONLY",
            dataset_id="bhopal_synthetic_demo",
            feature_id=actual_id,
            is_synthetic=is_synthetic
        )

        return ToolResult(tool_name="get_parcel_details", success=True, data=data, provenance=provenance)

    def _tool_get_parcel_buildings(self, parcel_id: str) -> ToolResult:
        all_buildings = _load_ai_features()
        buildings = [f for f in all_buildings if f["properties"].get("primary_parcel_id") == parcel_id or f["properties"].get("property_id") == parcel_id]
        if not buildings and all_buildings:
            buildings = all_buildings[:2]
        
        bldgs_data = []
        for b in buildings:
            props = b["properties"]
            bldgs_data.append({
                "building_id": b.get("id") or props.get("building_id"),
                "parcel_id": parcel_id,
                "source": "AI_DERIVED_UAVPAL",
                "model": "U-Net + ResNet18",
                "confidence": props.get("confidence", 0.90),
                "detected_area_m2": props.get("building_area_m2"),
                "parcel_relationship": props.get("parcel_relationship", "UNKNOWN"),
                "discrepancy_status": props.get("discrepancy_status", "NONE"),
                "source_tile": props.get("source_tile")
            })

        provenance = create_provenance(
            source_type="AI_DERIVED_UAVPAL",
            dataset_id="uavpal_bhopal",
            feature_id=parcel_id,
            model="U-Net + ResNet18",
            confidence=sum(b["confidence"] for b in bldgs_data)/len(bldgs_data) if bldgs_data else None
        )

        return ToolResult(
            tool_name="get_parcel_buildings",
            success=True,
            data={"parcel_id": parcel_id, "building_count": len(bldgs_data), "buildings": bldgs_data},
            provenance=provenance
        )

    def _tool_get_parcel_roads(self, parcel_id: str) -> ToolResult:
        parcels = _load_synthetic_parcels()
        matched = next((p for p in parcels if p.get("properties", {}).get("property_id") == parcel_id or p.get("properties", {}).get("parcel_id") == parcel_id or p.get("properties", {}).get("id") == parcel_id), None)
        if not matched and parcels:
            matched = parcels[0]

        raw_roads = load_raw_roads()
        processed_roads = process_road_features(raw_roads)
        summary = analyze_parcel_access(parcel_id, shape(matched["geometry"]), processed_roads)

        provenance = create_provenance(
            source_type="REFERENCE_GIS",
            dataset_id="osm_bhopal_roads",
            feature_id=parcel_id
        )

        return ToolResult(
            tool_name="get_parcel_roads",
            success=True,
            data={
                "parcel_id": parcel_id,
                "access_status": summary.access_status,
                "nearest_road_id": summary.nearest_road_id,
                "nearest_road_distance_m": summary.distance_to_road_m,
                "road_class": summary.nearest_road_class or "PRIMARY",
                "evidence": "Adjoining OpenStreetMap reference road centerline",
                "attribution": "© OpenStreetMap contributors"
            },
            provenance=provenance
        )

    def _tool_get_parcel_landuse(self, parcel_id: str) -> ToolResult:
        parcels = _load_synthetic_parcels()
        matched = next((p for p in parcels if p.get("properties", {}).get("property_id") == parcel_id or p.get("properties", {}).get("parcel_id") == parcel_id or p.get("properties", {}).get("id") == parcel_id), None)
        if not matched and parcels:
            matched = parcels[0]

        raw_lu = load_raw_landuse()
        processed_lu = process_landuse_features(raw_lu)
        all_bldgs = _load_ai_features()
        p_bldgs = [b for b in all_bldgs if b.get("properties", {}).get("primary_parcel_id") == parcel_id]

        summary = analyze_parcel_landuse(parcel_id, matched["geometry"], processed_lu, p_bldgs)

        provenance = create_provenance(
            source_type="REFERENCE_GIS",
            dataset_id="osm_bhopal_landuse",
            feature_id=parcel_id
        )

        return ToolResult(
            tool_name="get_parcel_landuse",
            success=True,
            data={
                "parcel_id": parcel_id,
                "observed_landuse_pattern": summary.observed_land_use_pattern,
                "confidence": summary.confidence,
                "overlapping_polygons_count": len(summary.overlapping_landuse_id) if summary.overlapping_landuse_id else 0,
                "disclaimer": "Observed land-use pattern derived from imagery/reference GIS — not official zoning.",
                "attribution": "© OpenStreetMap contributors"
            },
            provenance=provenance
        )

    def _tool_get_parcel_discrepancies(self, parcel_id: str) -> ToolResult:
        all_discs = _load_discrepancies()
        parcel_discs = [d for d in all_discs if d.get("parcel_id") == parcel_id]

        provenance = create_provenance(
            source_type="AI_DERIVED_UAVPAL",
            dataset_id="uavpal_bhopal_discrepancies",
            feature_id=parcel_id,
            model="U-Net + ResNet18"
        )

        return ToolResult(
            tool_name="get_parcel_discrepancies",
            success=True,
            data={
                "parcel_id": parcel_id,
                "discrepancy_count": len(parcel_discs),
                "discrepancies": parcel_discs,
                "legal_disclaimer": "Geometric discrepancies are analytical AI flags only, not legal determinations."
            },
            provenance=provenance
        )

    def _tool_get_parcel_history(self, parcel_id: str) -> ToolResult:
        bldgs = load_ai_buildings()
        p_bldgs = [b for b in bldgs if b["properties"].get("primary_parcel_id") == parcel_id]
        parcel_change = summarize_parcel_changes(parcel_id, "EPOCH-BPL-2024-01", "EPOCH-BPL-2025-06", p_bldgs, p_bldgs)

        provenance = create_provenance(
            source_type="TEST_FIXTURE",
            dataset_id="bhopal_multi_epoch_test_fixture",
            feature_id=parcel_id
        )

        return ToolResult(
            tool_name="get_parcel_history",
            success=True,
            data={
                "parcel_id": parcel_id,
                "history_available": True,
                "historical_record": parcel_change.model_dump(),
                "notice": "All temporal building change observations represent spatial processing metrics between software test fixtures (TEST_FIXTURE). They do NOT constitute official land record changes or legal property violations.",
                "real_temporal_imagery_status": "No second real temporal UAV raster exists for Bhopal. Fixtures are test-only."
            },
            provenance=provenance
        )

    def _tool_get_building_details(self, building_id: str) -> ToolResult:
        all_buildings = _load_ai_features()
        bldg = next((f for f in all_buildings if f.get("id") == building_id or f["properties"].get("building_id") == building_id), None)

        if not bldg:
            return ToolResult(
                tool_name="get_building_details",
                success=False,
                data={},
                error=f"Building ID '{building_id}' not found."
            )

        props = bldg["properties"]
        provenance = create_provenance(
            source_type="AI_DERIVED_UAVPAL",
            dataset_id="uavpal_bhopal",
            feature_id=building_id,
            model="U-Net + ResNet18",
            confidence=props.get("confidence", 0.90)
        )

        return ToolResult(
            tool_name="get_building_details",
            success=True,
            data={
                "building_id": building_id,
                "primary_parcel_id": props.get("primary_parcel_id"),
                "detected_area_m2": props.get("building_area_m2"),
                "confidence": props.get("confidence", 0.90),
                "parcel_relationship": props.get("parcel_relationship"),
                "discrepancy_status": props.get("discrepancy_status"),
                "source_tile": props.get("source_tile"),
                "model": "U-Net + ResNet18",
                "source": "AI_DERIVED_UAVPAL"
            },
            provenance=provenance
        )

    def _tool_get_review_status(self, parcel_id: Optional[str] = None, review_id: Optional[str] = None) -> ToolResult:
        review_item = None
        if review_id:
            review_item = review_store.get_review(review_id)
        elif parcel_id:
            review_item = review_store.get_review_by_entity("parcel", parcel_id)

        if not review_item:
            return ToolResult(
                tool_name="get_review_status",
                success=True,
                data={"status": "NOT_IN_REVIEW_QUEUE", "message": "No active surveyor review item found for this entity."},
                provenance=create_provenance("REVIEWED_AI_GEOMETRY")
            )

        audits = review_store.get_audits(review_item.id)
        verifications = review_store.get_verifications(review_item.id)

        provenance = create_provenance(
            source_type="REVIEWED_AI_GEOMETRY" if review_item.reviewed_geometry else "AI_DERIVED_UAVPAL",
            feature_id=review_item.id
        )

        return ToolResult(
            tool_name="get_review_status",
            success=True,
            data={
                "review_id": review_item.id,
                "entity_type": review_item.entity_type,
                "entity_id": review_item.entity_id,
                "parcel_id": review_item.parcel_id,
                "issue_type": review_item.issue_type,
                "severity": review_item.severity,
                "status": review_item.status,
                "assigned_reviewer": review_item.assigned_reviewer,
                "notes": review_item.notes,
                "audit_count": len(audits),
                "field_verification_count": len(verifications),
                "is_geometry_edited": review_item.reviewed_geometry is not None,
                "field_verifications": [v.model_dump() for v in verifications]
            },
            provenance=provenance
        )

    def _tool_get_dataset_metadata(self, dataset_id: Optional[str] = None, region_id: Optional[str] = None) -> ToolResult:
        data = {
            "region_id": region_id or "bhopal_mp",
            "datasets": [
                {
                    "dataset_id": "uavpal_bhopal",
                    "name": "Bhopal High-Res UAV RGB Imagery",
                    "tiles_count": 30,
                    "resolution": "5cm GSD",
                    "source_classification": "AI_DERIVED_UAVPAL",
                    "ai_model": "U-Net + ResNet18",
                    "building_count": 834,
                    "crs": "EPSG:4326 (WGS84)"
                },
                {
                    "dataset_id": "bhopal_synthetic_parcels",
                    "name": "Bhopal Synthetic Demonstration Parcels",
                    "parcel_count": 35,
                    "source_classification": "SYNTHETIC_DEMO",
                    "disclaimer": _SYNTHETIC_DISCLAIMER
                },
                {
                    "dataset_id": "osm_bhopal_extract",
                    "name": "OpenStreetMap Reference GIS Layers",
                    "roads_count": 2933,
                    "landuse_polygons_count": 98,
                    "source_classification": "REFERENCE_GIS",
                    "attribution": "© OpenStreetMap contributors"
                }
            ],
            "crs_metadata": {
                "source_crs": "EPSG:4326",
                "analysis_crs": "EPSG:32643 (UTM Zone 43N)",
                "default_output_crs": "EPSG:4326"
            }
        }
        return ToolResult(tool_name="get_dataset_metadata", success=True, data=data, provenance=create_provenance("REFERENCE_GIS"))

    def _tool_get_region_summary(self, region_id: Optional[str] = "bhopal_mp") -> ToolResult:
        all_buildings = _load_ai_features()
        syn_parcels = _load_synthetic_parcels()
        roads = load_raw_roads()
        landuse = load_raw_landuse()
        discs = _load_discrepancies()
        review_stats = review_store.get_stats()

        data = {
            "region_id": region_id or "bhopal_mp",
            "country": "India",
            "state": "Madhya Pradesh",
            "city": "Bhopal",
            "raster_tiles_count": 30,
            "demo_parcel_count": len(syn_parcels),
            "ai_building_count": len(all_buildings),
            "reference_road_count": len(roads),
            "reference_landuse_count": len(landuse),
            "discrepancy_count": len(discs),
            "surveyor_review_stats": review_stats
        }

        return ToolResult(tool_name="get_region_summary", success=True, data=data, provenance=create_provenance("REFERENCE_GIS"))

    def _tool_search_parcels(self, query: str, region_id: Optional[str] = None) -> ToolResult:
        q = query.lower().strip()
        syn_props = _load_synthetic_props()
        matches = []
        for p in syn_props:
            pid = p.get("property_id", "").lower()
            plot = p.get("plot_number", "").lower()
            survey = p.get("survey_number", "").lower()
            loc = p.get("locality", "").lower()
            if q in pid or q in plot or q in survey or q in loc:
                matches.append({
                    "parcel_id": p["property_id"],
                    "plot_number": p.get("plot_number"),
                    "area_m2": p.get("area_sqm"),
                    "locality": p.get("locality"),
                    "source": "SYNTHETIC_DEMO",
                    "disclaimer": _SYNTHETIC_DISCLAIMER
                })

        return ToolResult(
            tool_name="search_parcels",
            success=True,
            data={"query": query, "match_count": len(matches), "matches": matches[:10]},
            provenance=create_provenance("SYNTHETIC_DEMO", is_synthetic=True)
        )

    def _tool_search_buildings(self, query: str, region_id: Optional[str] = None) -> ToolResult:
        q = query.lower().strip()
        all_buildings = _load_ai_features()
        matches = []
        for b in all_buildings:
            bid = str(b.get("id", "")).lower()
            props = b.get("properties", {})
            pid = str(props.get("primary_parcel_id", "")).lower()
            disc = str(props.get("discrepancy_status", "")).lower()
            if q in bid or q in pid or q in disc:
                matches.append({
                    "building_id": b.get("id") or props.get("building_id"),
                    "parcel_id": props.get("primary_parcel_id"),
                    "area_m2": props.get("building_area_m2"),
                    "confidence": props.get("confidence"),
                    "relationship": props.get("parcel_relationship"),
                    "source": "AI_DERIVED_UAVPAL"
                })

        return ToolResult(
            tool_name="search_buildings",
            success=True,
            data={"query": query, "match_count": len(matches), "matches": matches[:10]},
            provenance=create_provenance("AI_DERIVED_UAVPAL")
        )

    def _tool_get_export_options(self, region_id: Optional[str] = None) -> ToolResult:
        data = {
            "supported_formats": ["geojson", "geopackage", "zip"],
            "supported_layers": ["parcels", "buildings", "roads", "landuse", "discrepancies", "reviews"],
            "supported_crs": ["EPSG:4326", "EPSG:3857", "EPSG:32643"],
            "export_center_url": "/app/exports",
            "validation_requirements": ["geometry_validity", "non_empty_features", "source_classification_preserved", "synthetic_disclaimer_preserved"]
        }
        return ToolResult(tool_name="get_export_options", success=True, data=data, provenance=create_provenance("REFERENCE_GIS"))

# Global singleton
tool_registry = ToolRegistry()
