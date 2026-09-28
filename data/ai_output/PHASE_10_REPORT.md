# Phase 10 Technical Report — Grounded Geospatial AI Assistant & GIS Tool Calling

## 1. Executive Summary
Phase 10 introduces a **Grounded Geospatial AI Assistant** to **DrishtiGIS (SIH26012)**. The assistant provides a natural-language interface to the underlying spatial intelligence, AI building extractions, road access analysis, land-use patterns, surveyor review workflows, and export capabilities.

Rather than relying on ungrounded LLM text generation, all factual GIS data is retrieved dynamically via a **controlled, read-only Tool Registry** wrapping trusted backend services.

---

## 2. Architecture & Design Principles

```
USER NATURAL-LANGUAGE QUESTION
              ↓
  ASSISTANT PROMPT POLICY
  (Injection Defense & Safety Rules)
              ↓
   TOOL SELECTION & ROUTING
 (Grounded Tool Engine / LLM Provider)
              ↓
      DRISHTIGIS TOOL REGISTRY
 (Strict Read-Only GIS Tool Execution)
              ↓
  TRUSTED BACKEND SERVICES / GIS ENGINES
  (Area, Relationships, Roads, Land-Use, Reviews)
              ↓
   STRUCTURED PROVENANCE & EVIDENCE
              ↓
 GROUNDED EXPLANATION & MAP UI ACTIONS
```

### Core Architecture Components (`backend/app/assistant/`)
- `tool_registry.py`: Controlled registry exposing 13 read-only GIS tools with strict input/output schemas.
- `llm_provider.py`: Provider abstraction supporting OpenRouter, Gemini, OpenAI-compatible REST endpoints, and a deterministic **Grounded Tool Engine** fallback when no LLM key is set.
- `prompt_policy.py`: System safety guardrails, prompt injection defenses, legal term filtering, and synthetic data disclaimer enforcement.
- `provenance.py`: Data provenance builder capturing `source_type`, `dataset_id`, `region_id`, `feature_id`, `model`, `confidence`, and `disclaimer`.
- `assistant_service.py`: Orchestration engine managing conversation history, context entities, request tracing, and execution logging.
- `backend/app/api/v1/assistant_router.py`: FastAPI endpoints for assistant queries, tool listings, history, and logs.

---

## 3. Tool Registry & Schemas

The assistant can ONLY execute registered read-only DrishtiGIS tools. Arbitrary SQL, filesystem access, Python code execution, and shell commands are strictly prohibited.

| Tool Name | Parameters | Target Capability |
| :--- | :--- | :--- |
| `get_parcel_details` | `parcel_id` | Returns area, building count, coverage ratio, discrepancy count, review status, and synthetic disclaimer. |
| `get_parcel_buildings` | `parcel_id` | Returns associated AI building footprints (`AI_DERIVED_UAVPAL`), confidence scores, and relationships. |
| `get_parcel_roads` | `parcel_id` | Computes road access corridor status, nearest road ID, distance ($m$), and road class (`REFERENCE_GIS`). |
| `get_parcel_landuse` | `parcel_id` | Analyzes `OBSERVED_LAND_USE_PATTERN` from reference GIS polygons and imagery features. |
| `get_parcel_discrepancies` | `parcel_id` | Retrieves AI-flagged spatial discrepancies (`BUILDING_CROSSES_PARCEL_BOUNDARY`, `MULTIPLE_BUILDINGS_IN_PARCEL`). |
| `get_parcel_history` | `parcel_id` | Returns multi-epoch change summary; explicitly notes `TEST_FIXTURE` status for Bhopal. |
| `get_building_details` | `building_id` | Retrieves AI building footprint geometry metadata, model (`U-Net + ResNet18`), and confidence. |
| `get_review_status` | `parcel_id`, `review_id` | Queries surveyor review queue status, audit history, and field verification records. |
| `get_dataset_metadata` | `dataset_id`, `region_id` | Returns dataset provenance, acquisition specs, AI model details, and CRS metadata (`EPSG:4326`, `EPSG:32643`). |
| `get_region_summary` | `region_id` | Computes live dynamic region statistics for parcels, buildings, roads, land-use, and review queues. |
| `search_parcels` | `query`, `region_id` | Searches parcels by property ID, plot number, survey number, or locality. |
| `search_buildings` | `query`, `region_id` | Searches AI-detected building footprints by building ID or parcel ID. |
| `get_export_options` | `region_id` | Returns available export formats (GeoJSON, GeoPackage `.gpkg`, ZIP), layers, and CRS choices. |

---

## 4. Safety Guardrails & Provenance

1. **Prompt Injection Defense**: Filters inputs attempting to override system prompts or bypass safety rules (`sanitize_user_input`).
2. **Legal & Ownership Safety**: Prohibits forbidden legal terms (`illegal construction`, `encroachment`, `unauthorized`, `ownership confirmed`). Replaces them with `"AI-derived spatial discrepancy requiring review"`.
3. **Land-Use Classification**: Explicitly labels results as `OBSERVED_LAND_USE_PATTERN` and warns that they do NOT constitute official municipal zoning.
4. **Synthetic Data Protection**: Every synthetic parcel query preserves the mandatory disclaimer: `"Synthetic prototype data — not an official land record."`
5. **Historical Data Transparency**: Multi-epoch queries clearly disclose `TEST_FIXTURE` status and confirm that no second real temporal UAV raster exists for Bhopal.

---

## 5. WebGIS Integration

- **Assistant UI Page (`/app/assistant`)**: Features conversation thread, collapsible **"GIS Tools Executed"** log, **Evidence / Source Chips** (`AI_DERIVED_UAVPAL`, `SYNTHETIC_DEMO`, `REFERENCE_GIS`), Map UI Action Buttons (`View on Map`, `Open Review Queue`, `Export Center`), and prompt suggestion pills.
- **ContextSidebar Integration**: Added direct **"Ask AI Assistant About This Parcel"** button when selecting parcels or buildings on the map, preserving active context parameters.

---

## 6. Classification Matrix

- **`IMPLEMENTED`**: Grounded Geospatial AI Assistant, ToolRegistry, Grounded Tool Engine, Provenance Engine, Prompt Policy, Assistant API, WebGIS Assistant Page, ContextSidebar Integration.
- **`AI_DERIVED`**: 834 UAVPal AI Building Footprints (`U-Net + ResNet18`), Discrepancies.
- **`REFERENCE_GIS`**: 2,933 OpenStreetMap Roads, 98 OpenStreetMap Land-Use Polygons.
- **`REVIEWED`**: Surveyor Review Queue Items, Audit Trails.
- **`FIELD_VERIFIED`**: Ground Verification Records.
- **`SYNTHETIC_DEMO`**: 35 Demonstration Parcels (`"Synthetic prototype data — not an official land record."`).
- **`TEST_FIXTURE`**: Multi-epoch historical change detection test fixtures.
