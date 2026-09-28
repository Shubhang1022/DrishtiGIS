"""
DrishtiGIS — Geographic Coverage Registry
==========================================
Defines what intelligence data is available for each geographic area.

Architecture principle (from spec core-india-webgis):
  DrishtiGIS is India-scale. Bhopal is the first and currently ONLY
  prototype intelligence area. All other cities have base map context only.

  NEVER claim imagery, parcel, or AI coverage for a city that does not
  have real or prototype data. This is a data integrity rule.

  historical_data_available is always False for Bhopal — no second
  time epoch exists. Do NOT fabricate this.
"""

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional

from app.gis.india_cities import get_city, INDIA_CITIES


class CoverageSource(str, Enum):
    PROTOTYPE  = "prototype"   # Prototype/demo intelligence data available
    PRODUCTION = "production"  # Real production intelligence data available
    NONE       = "none"        # Map context only — no intelligence data


@dataclass(frozen=True)
class CoverageAvailability:
    city:                    str
    state:                   str
    country:                 str
    center_lat:              float
    center_lon:              float
    map_available:           bool   # Always True for any Indian location
    osm_available:           bool   # OSM context (always True for India)
    imagery_available:       bool   # UAV / satellite imagery served by this app
    parcel_data_available:   bool   # Cadastral / parcel intelligence
    ai_analysis_available:   bool   # AI feature detection results
    historical_data_available: bool # Multi-temporal comparison
    coverage_source:         CoverageSource
    disclaimer:              Optional[str] = None


# ── Bhopal — the ONLY prototype intelligence city ─────────────────────────
# All values grounded in real verified data from Phases 1–4.
# historical_data_available=False: only one time epoch exists; do not fabricate.

BHOPAL_COVERAGE = CoverageAvailability(
    city                    = "Bhopal",
    state                   = "Madhya Pradesh",
    country                 = "India",
    center_lat              = 23.2599,
    center_lon              = 77.4126,
    map_available           = True,
    osm_available           = True,
    imagery_available       = True,   # Verified Phase 2 UAV XYZ tiles (379 tiles)
    parcel_data_available   = True,   # Phase 4 demo parcels (3 records, DEMO_DATA_PROTOTYPE_ONLY)
    ai_analysis_available   = True,   # Phase 5: real UAVPal AI buildings (834 features)
    historical_data_available = False,  # No second epoch — NEVER fabricate as True
    coverage_source         = CoverageSource.PROTOTYPE,
    disclaimer=(
        "Parcel and AI analysis data for Bhopal are prototype demonstration records only. "
        "They are not official government cadastral data and have no legal status."
    ),
)


def _make_map_only_coverage(city_name: str) -> CoverageAvailability:
    """
    Return a map-only coverage record for any city without intelligence data.
    Never claims imagery, parcel, or AI availability.
    """
    city = get_city(city_name)
    return CoverageAvailability(
        city                     = city.name if city else city_name.title(),
        state                    = city.state if city else "India",
        country                  = "India",
        center_lat               = city.lat if city else 20.5937,
        center_lon               = city.lon if city else 78.9629,
        map_available            = True,
        osm_available            = True,
        imagery_available        = False,
        parcel_data_available    = False,
        ai_analysis_available    = False,
        historical_data_available = False,
        coverage_source          = CoverageSource.NONE,
        disclaimer               = None,
    )


def get_coverage(city_name: str) -> CoverageAvailability:
    """
    Return coverage availability for a city name.

    Only Bhopal has prototype intelligence data.
    All other cities return map-only coverage.
    No intelligence is ever fabricated for non-Bhopal cities.
    """
    if city_name.strip().lower() == "bhopal":
        return BHOPAL_COVERAGE
    return _make_map_only_coverage(city_name)


def coverage_to_dict(c: CoverageAvailability) -> dict:
    """Serialize CoverageAvailability to a JSON-safe dict."""
    d = asdict(c)
    # Convert enum to its string value
    d["coverage_source"] = c.coverage_source.value
    return d


# ── Bhopal dataset registry (used by /api/v1/coverage/bhopal) ─────────────

BHOPAL_DATASETS: list[dict] = [
    {
        "id":                "dataset-bpl-uav-001",
        "type":              "orthomosaic",
        "name":              "Bhopal UAV Prototype",
        "tile_url_template": "/api/v1/tiles/bhopal/{z}/{x}/{y}.png",
        "zoom_min":          18,
        "zoom_max":          21,
        "bounds":            [77.41299311, 23.25573135, 77.42267457, 23.25667101],
        "resolution_m":      0.021713,
        "tile_count":        379,
        "source":            "PROCESSED_RASTER",
        "_disclaimer":       "Prototype UAV imagery. Not a production surveying product.",
    },
    {
        "id":               "dataset-bpl-osm-001",
        "type":             "osm_extract",
        "name":             "Bhopal OSM Extract",
        "extraction_bbox":  [77.38, 23.24, 77.44, 23.27],
        "layers":           ["buildings", "roads", "waterways", "landuse"],
        "source":           "OSM_OPENSTREETMAP",
        "_attribution":     "\u00a9 OpenStreetMap contributors, ODbL",
        "_disclaimer":      "OSM data is supplementary context only. NOT authoritative cadastral data.",
    },
    {
        "id":               "dataset-bpl-parcels-001",
        "type":             "parcel_prototype",
        "name":             "Bhopal Prototype Parcels (Legacy)",
        "record_count":     3,
        "source":           "DEMO_DATA_PROTOTYPE_ONLY",
        "_disclaimer":      "3 legacy prototype parcels. Superseded by synthetic dataset.",
    },
    {
        "id":               "dataset-bpl-synthetic-parcels-001",
        "type":             "synthetic_parcel",
        "name":             "Bhopal Synthetic Demo Properties",
        "record_count":     35,
        "source":           "SYNTHETIC_DEMO",
        "_disclaimer": (
            "35 synthetic prototype parcel/property records within the Bhopal UAVPal coverage area. "
            "NOT official government cadastral records. "
            "Identifiers, owner names, and property data are synthetic."
        ),
    },
    {
        "id":               "dataset-bpl-ai-buildings-001",
        "type":             "ai_buildings",
        "name":             "Bhopal AI Building Footprints",
        "record_count":     834,
        "source":           "AI_DERIVED_UAVPAL",
        "model":            "UNet-ResNet18-UAVPal",
        "model_version":    "phase3-epoch25-bld_iou0.587",
        "building_class_id": 4,
        "_disclaimer": (
            "AI-derived building footprints from UAVPal semantic segmentation. "
            "NOT cadastral boundaries. NOT legal property boundaries. "
            "For research and visualization purposes only."
        ),
    },
]
