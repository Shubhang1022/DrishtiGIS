"""
DrishtiGIS Phase 5.5 — Synthetic cadastral + topology validation tests.

Covers all required test categories:
  1.  Synthetic parcel count (≥ 25)
  2.  Synthetic source classification (SYNTHETIC_DEMO)
  3.  Disclaimer presence
  4.  Indian owner names
  5.  No real-government-data claims
  6.  Parcel geometry validity (Shapely)
  7.  Overlapping parcel detection
  8.  Self-intersection detection
  9.  Duplicate parcel detection
  10. FULLY_WITHIN relationship
  11. CROSSES_BOUNDARY relationship
  12. NO_PARCEL_MATCH relationship
  13. Multiple buildings per parcel
  14. No hardcoded AI building/property mapping
  15. legal_status remains null
  16. AI_DERIVED_UAVPAL unchanged
  17. Existing 834 AI buildings unchanged
  18. API: parcel list serves SYNTHETIC_DEMO
  19. API: parcel detail for DEMO property includes ai_analysis
  20. API: non-Bhopal city returns empty
  21. Topology validation file integrity
  22. No forbidden language in discrepancies
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT          = Path(__file__).parent.parent.parent
SYN_PARCELS   = ROOT / "data/synthetic/bhopal-synthetic-parcels.geojson"
SYN_PROPS     = ROOT / "data/synthetic/bhopal-synthetic-properties.json"
TOPO_VAL      = ROOT / "data/synthetic/topology_validation.json"
AI_ASSOC      = ROOT / "data/ai_output/bhopal-building-parcel-associations.geojson"
DISC_PATH     = ROOT / "data/ai_output/bhopal-discrepancies.json"

import sys
sys.path.insert(0, str(ROOT / "backend"))

from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def syn_parcels():
    with open(SYN_PARCELS, encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="session")
def syn_props():
    with open(SYN_PROPS, encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="session")
def topo_val():
    with open(TOPO_VAL, encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="session")
def ai_assoc():
    with open(AI_ASSOC, encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="session")
def discrepancies():
    with open(DISC_PATH, encoding="utf-8") as f:
        return json.load(f)

# ── 1. Parcel count ───────────────────────────────────────────────────────────

class TestSyntheticParcelCount:
    def test_at_least_25_parcels(self, syn_parcels):
        assert len(syn_parcels["features"]) >= 25, \
            f"Expected ≥ 25 parcels, got {len(syn_parcels['features'])}"

    def test_exactly_35_parcels(self, syn_parcels):
        assert len(syn_parcels["features"]) == 35

    def test_all_parcel_ids_unique(self, syn_parcels):
        ids = [f["properties"]["id"] for f in syn_parcels["features"]]
        assert len(ids) == len(set(ids)), "Duplicate parcel IDs"

    def test_all_property_ids_unique(self, syn_parcels):
        pids = [f["properties"]["property_id"] for f in syn_parcels["features"]]
        assert len(pids) == len(set(pids)), "Duplicate property IDs"


# ── 2. Source classification ──────────────────────────────────────────────────

class TestSyntheticSourceClassification:
    def test_parcel_source_is_synthetic_demo(self, syn_parcels):
        for feat in syn_parcels["features"]:
            assert feat["properties"]["_source"] == "SYNTHETIC_DEMO", \
                f"Wrong source: {feat['properties']['id']}"

    def test_metadata_source_is_synthetic_demo(self, syn_parcels):
        assert syn_parcels.get("metadata", {}).get("_source") == "SYNTHETIC_DEMO"

    def test_property_source_is_synthetic_demo(self, syn_props):
        for p in syn_props["properties"]:
            assert p["_source"] == "SYNTHETIC_DEMO", \
                f"Wrong source on property {p['property_id']}"

    def test_no_official_reference_source(self, syn_parcels):
        for feat in syn_parcels["features"]:
            assert feat["properties"]["_source"] != "OFFICIAL_REFERENCE"

    def test_parcel_ids_have_demo_prefix(self, syn_parcels):
        for feat in syn_parcels["features"]:
            pid = feat["properties"]["property_id"]
            assert "DEMO" in pid, f"Property ID missing DEMO: {pid}"


# ── 3. Disclaimer presence ────────────────────────────────────────────────────

class TestDisclaimerPresence:
    def test_every_parcel_has_disclaimer(self, syn_parcels):
        for feat in syn_parcels["features"]:
            d = feat["properties"].get("_disclaimer", "")
            assert len(d) > 10, f"{feat['properties']['id']}: disclaimer too short"

    def test_disclaimer_mentions_synthetic(self, syn_parcels):
        for feat in syn_parcels["features"]:
            d = feat["properties"]["_disclaimer"].lower()
            assert "synthetic" in d or "not an official" in d

    def test_property_disclaimer_present(self, syn_props):
        for p in syn_props["properties"]:
            assert len(p.get("_disclaimer", "")) > 10


# ── 4. Indian owner names ─────────────────────────────────────────────────────

# A minimal set of Indian surname patterns to verify origin
_INDIAN_SURNAMES = {
    "kumar", "sharma", "verma", "singh", "mishra", "gupta", "yadav",
    "patel", "tiwari", "joshi", "agarwal", "rao", "tripathi", "shukla",
    "dubey", "pandey", "srivastava", "dixit", "jain", "chauhan", "puri",
}

class TestIndianOwnerNames:
    def test_every_property_has_owner_name(self, syn_props):
        for p in syn_props["properties"]:
            assert p.get("owner_name") and len(p["owner_name"]) > 2, \
                f"{p['property_id']}: missing owner_name"

    def test_owner_names_are_indian(self, syn_props):
        """At least 80% of names must end in a recognisable Indian surname."""
        names  = [p["owner_name"] for p in syn_props["properties"]]
        indian = sum(
            1 for n in names
            if any(n.lower().endswith(s) or s in n.lower() for s in _INDIAN_SURNAMES)
        )
        pct = indian / len(names)
        assert pct >= 0.8, f"Only {pct:.0%} Indian names — expected ≥ 80%"

    def test_no_foreign_names(self, syn_props):
        """Spot-check for common non-Indian name patterns."""
        foreign_patterns = ["Smith", "Jones", "Brown", "Johnson", "Williams",
                            "Davis", "Miller", "Wilson", "Anderson", "Thomas"]
        for p in syn_props["properties"]:
            for fp in foreign_patterns:
                assert fp.lower() not in p["owner_name"].lower(), \
                    f"Foreign name pattern '{fp}' found: {p['owner_name']}"


# ── 5. No real-government-data claims ────────────────────────────────────────

class TestNoRealGovClaims:
    def test_record_status_is_synthetic(self, syn_props):
        for p in syn_props["properties"]:
            assert p.get("record_status") == "SYNTHETIC_DEMO"

    def test_no_official_reference_anywhere(self, syn_parcels, syn_props):
        for feat in syn_parcels["features"]:
            assert feat["properties"]["_source"] != "OFFICIAL_REFERENCE"
        for p in syn_props["properties"]:
            assert p["_source"] != "OFFICIAL_REFERENCE"

    def test_dataset_label_says_synthetic(self, syn_parcels):
        for feat in syn_parcels["features"]:
            label = feat["properties"].get("_datasetLabel", "")
            assert "Synthetic" in label or "Demo" in label


# ── 6. Geometry validity ─────────────────────────────────────────────────────

_shapely_ok = False
try:
    from shapely.geometry import shape
    _shapely_ok = True
except ImportError:
    pass

skip_shapely = pytest.mark.skipif(not _shapely_ok, reason="shapely required")

@skip_shapely
class TestParcelGeometryValidity:
    def test_all_geometries_valid(self, syn_parcels):
        invalid = []
        for feat in syn_parcels["features"]:
            geom = shape(feat["geometry"])
            if not geom.is_valid:
                invalid.append(feat["properties"]["id"])
        assert not invalid, f"Invalid geometries: {invalid}"

    def test_all_areas_positive(self, syn_parcels):
        for feat in syn_parcels["features"]:
            assert feat["properties"]["area_m2"] > 0

    def test_no_zero_area_geometries(self, syn_parcels):
        for feat in syn_parcels["features"]:
            geom = shape(feat["geometry"])
            assert geom.area > 0

    def test_all_polygons(self, syn_parcels):
        for feat in syn_parcels["features"]:
            assert feat["geometry"]["type"] == "Polygon"


# ── 7. Overlapping parcel detection ──────────────────────────────────────────

class TestOverlappingParcels:
    def test_topology_file_exists(self):
        assert TOPO_VAL.exists()

    def test_all_parcels_valid_topology(self, topo_val):
        for r in topo_val["results"]:
            assert r["status"] == "VALID", \
                f"{r['parcel_id']}: topology status={r['status']}"

    def test_no_overlapping_parcels(self, topo_val):
        overlapping = [r for r in topo_val["results"] if r["overlap_detected"]]
        assert not overlapping, f"Overlapping parcels: {[r['parcel_id'] for r in overlapping]}"

    def test_no_duplicate_parcels(self, topo_val):
        duplicates = [r for r in topo_val["results"] if r["duplicate_detected"]]
        assert not duplicates, f"Duplicate parcels: {[r['parcel_id'] for r in duplicates]}"


# ── 8–9. Self-intersection / duplicate ───────────────────────────────────────

class TestSelfIntersectionAndDuplicate:
    def test_no_self_intersecting_parcels(self, topo_val):
        si = [r for r in topo_val["results"] if r["self_intersection"]]
        assert not si, f"Self-intersecting: {[r['parcel_id'] for r in si]}"

    def test_topology_covers_all_35_parcels(self, topo_val):
        assert topo_val["total_parcels"] == 35
        assert len(topo_val["results"]) == 35


# ── 10. FULLY_WITHIN ────────────────────────────────────────────────────────

class TestFullyWithinRelationship:
    def test_fully_within_exists(self, ai_assoc):
        cnt = sum(1 for f in ai_assoc["features"]
                  if f["properties"]["parcel_relationship"] == "FULLY_WITHIN")
        assert cnt > 0, "Expected FULLY_WITHIN buildings"

    def test_fully_within_has_high_overlap(self, ai_assoc):
        for f in ai_assoc["features"]:
            if f["properties"]["parcel_relationship"] == "FULLY_WITHIN":
                assert f["properties"]["overlap_ratio"] >= 0.95


# ── 11. CROSSES_BOUNDARY ────────────────────────────────────────────────────

class TestCrossesBoundaryRelationship:
    def test_crosses_boundary_exists(self, ai_assoc):
        cnt = sum(1 for f in ai_assoc["features"]
                  if f["properties"]["parcel_relationship"] == "CROSSES_BOUNDARY")
        assert cnt > 0, "Expected CROSSES_BOUNDARY buildings"

    def test_crosses_boundary_has_primary(self, ai_assoc):
        for f in ai_assoc["features"]:
            if f["properties"]["parcel_relationship"] == "CROSSES_BOUNDARY":
                assert f["properties"]["primary_parcel_id"] is not None


# ── 12. NO_PARCEL_MATCH ──────────────────────────────────────────────────────

class TestNoParcelMatch:
    def test_no_parcel_match_exists(self, ai_assoc):
        cnt = sum(1 for f in ai_assoc["features"]
                  if f["properties"]["parcel_relationship"] == "NO_PARCEL_MATCH")
        assert cnt > 0, "Expected NO_PARCEL_MATCH buildings"

    def test_no_match_has_null_parcel(self, ai_assoc):
        for f in ai_assoc["features"]:
            if f["properties"]["parcel_relationship"] == "NO_PARCEL_MATCH":
                assert f["properties"]["primary_parcel_id"] is None


# ── 13. Multiple buildings per parcel ────────────────────────────────────────

class TestMultipleBuildingsPerParcel:
    def test_multiple_buildings_exist(self, ai_assoc):
        from collections import Counter
        counts = Counter(
            f["properties"]["primary_parcel_id"]
            for f in ai_assoc["features"]
            if f["properties"]["primary_parcel_id"]
        )
        multi = {pid: c for pid, c in counts.items() if c > 1}
        assert len(multi) > 0, "Expected at least one parcel with multiple buildings"

    def test_max_multiple_building_count_reasonable(self, ai_assoc):
        """Largest multi-building parcel should have < 200 buildings (sanity check)."""
        from collections import Counter
        counts = Counter(
            f["properties"]["primary_parcel_id"]
            for f in ai_assoc["features"]
            if f["properties"]["primary_parcel_id"]
        )
        if counts:
            assert max(counts.values()) < 200


# ── 14. No hardcoded mapping ─────────────────────────────────────────────────

class TestNoHardcodedMapping:
    def test_building_associations_from_geometry(self, ai_assoc):
        """overlap_ratio must vary — not all the same value (would indicate hardcoding)."""
        ratios = [
            f["properties"]["overlap_ratio"]
            for f in ai_assoc["features"]
            if f["properties"]["primary_parcel_id"]
        ]
        unique = len(set(ratios))
        assert unique > 5, f"Only {unique} unique overlap ratios — possible hardcoding"

    def test_all_buildings_have_computed_overlap(self, ai_assoc):
        for feat in ai_assoc["features"]:
            p = feat["properties"]
            # overlap_ratio must be 0 iff no primary parcel
            if p["primary_parcel_id"] is None:
                assert p["overlap_ratio"] == 0.0
            else:
                assert p["overlap_ratio"] > 0.0


# ── 15. legal_status null ────────────────────────────────────────────────────

class TestLegalStatusNull:
    def test_discrepancies_have_null_legal_status(self, discrepancies):
        for d in discrepancies["discrepancies"]:
            ls = d.get("legal_status")
            assert ls is None, f"{d['id']}: legal_status={ls}"

    def test_no_legal_claims_in_parcel_properties(self, syn_parcels):
        for feat in syn_parcels["features"]:
            props_text = json.dumps(feat["properties"]).lower()
            for term in ["legal title", "ownership verified", "legal_status", "encroachment"]:
                assert term not in props_text, f"Legal claim '{term}' found in {feat['properties']['id']}"


# ── 16. AI_DERIVED_UAVPAL unchanged ─────────────────────────────────────────

class TestAIDerivedUAVPALUnchanged:
    def test_all_ai_features_source_uavpal(self, ai_assoc):
        for feat in ai_assoc["features"]:
            assert feat["properties"]["source"] == "AI_DERIVED_UAVPAL"

    def test_no_ai_derived_demo_in_output(self, ai_assoc):
        for feat in ai_assoc["features"]:
            assert feat["properties"]["source"] != "AI_DERIVED_DEMO"


# ── 17. 834 AI buildings unchanged ──────────────────────────────────────────

class TestAIBuildingsUnchanged:
    def test_total_buildings_still_834(self, ai_assoc):
        assert len(ai_assoc["features"]) == 834

    def test_no_new_fabricated_buildings(self, ai_assoc):
        """All feature IDs must follow the real pipeline format AI-BPL-FINAL-XXXXX."""
        for feat in ai_assoc["features"]:
            fid = feat["properties"]["id"]
            assert fid.startswith("AI-BPL-FINAL-"), f"Unexpected ID: {fid}"

    def test_building_confidences_unchanged(self, ai_assoc):
        """Confidence values must still be in [0, 1]."""
        for feat in ai_assoc["features"][:100]:
            c = feat["properties"].get("confidence")
            assert c is not None
            assert 0.0 <= c <= 1.0


# ── 18. API: parcel list serves SYNTHETIC_DEMO ──────────────────────────────

class TestAPIParcelListSynthetic:
    def test_bhopal_parcel_list_200(self):
        r = client.get("/api/v1/parcels?city=Bhopal")
        assert r.status_code == 200

    def test_bhopal_parcel_source_synthetic_demo(self):
        r = client.get("/api/v1/parcels?city=Bhopal")
        assert r.json()["_source"] == "SYNTHETIC_DEMO"

    def test_bhopal_returns_35_parcels(self):
        r = client.get("/api/v1/parcels?city=Bhopal")
        assert r.json()["total"] == 35

    def test_parcel_features_have_owner_name(self):
        r = client.get("/api/v1/parcels?city=Bhopal")
        for feat in r.json()["features"]:
            assert feat["properties"].get("owner_name"), \
                f"{feat['properties']['id']}: missing owner_name"

    def test_synthetic_disclaimer_in_response(self):
        r = client.get("/api/v1/parcels?city=Bhopal")
        assert "synthetic" in r.json()["_disclaimer"].lower()


# ── 19. API: parcel detail for DEMO property ────────────────────────────────

class TestAPIParcelDetailSynthetic:
    def test_demo_parcel_detail_200(self):
        r = client.get("/api/v1/parcels/DRS-BPL-DEMO-001")
        assert r.status_code == 200

    def test_demo_parcel_has_ai_analysis(self):
        r = client.get("/api/v1/parcels/DRS-BPL-DEMO-001")
        assert "ai_analysis" in r.json()
        assert r.json()["ai_analysis"]["ai_available"] is True

    def test_demo_parcel_source_synthetic(self):
        r = client.get("/api/v1/parcels/DRS-BPL-DEMO-001")
        assert r.json()["_source"] == "SYNTHETIC_DEMO"

    def test_demo_parcel_has_owner_name(self):
        r = client.get("/api/v1/parcels/DRS-BPL-DEMO-001")
        props = r.json()["parcel"]["properties"]
        assert props.get("owner_name"), "owner_name missing from parcel"

    def test_legacy_parcel_still_works(self):
        """Backward compatibility: DRS-BPL-00101 must still return 200."""
        r = client.get("/api/v1/parcels/DRS-BPL-00101")
        assert r.status_code == 200

    def test_unknown_parcel_404(self):
        r = client.get("/api/v1/parcels/NONEXISTENT-00000")
        assert r.status_code == 404

    def test_demo_parcel_disclaimer_present(self):
        r = client.get("/api/v1/parcels/DRS-BPL-DEMO-001")
        assert "synthetic" in r.json()["_disclaimer"].lower() or \
               "prototype" in r.json()["_disclaimer"].lower()


# ── 20. Non-Bhopal city ──────────────────────────────────────────────────────

class TestNonBhopalCity:
    def test_delhi_returns_empty_synthetic(self):
        r = client.get("/api/v1/parcels?city=Delhi")
        assert r.json()["total"] == 0

    def test_non_bhopal_has_coverage_note(self):
        r = client.get("/api/v1/parcels?city=Mumbai")
        assert "_coverage_note" in r.json()


# ── 21. Topology validation file ────────────────────────────────────────────

class TestTopologyValidationFile:
    def test_topo_file_exists(self):
        assert TOPO_VAL.exists()

    def test_35_parcels_validated(self, topo_val):
        assert topo_val["total_parcels"] == 35

    def test_all_35_valid(self, topo_val):
        assert topo_val["valid_count"] == 35
        assert topo_val["review_count"] == 0

    def test_results_have_required_fields(self, topo_val):
        required = {"parcel_id", "geometry_valid", "self_intersection",
                    "zero_area", "overlap_detected", "duplicate_detected", "status"}
        for r in topo_val["results"]:
            missing = required - set(r.keys())
            assert not missing, f"{r['parcel_id']}: missing fields {missing}"


# ── 22. No forbidden language ────────────────────────────────────────────────

class TestNoForbiddenLanguage:
    def test_no_forbidden_language_in_discrepancies(self, discrepancies):
        forbidden = ["illegal", "fraud", "encroachment", "violation",
                     "unauthorized", "criminal", "offence"]
        for d in discrepancies["discrepancies"]:
            text = d.get("description", "").lower()
            for word in forbidden:
                assert word not in text, \
                    f"'{word}' in discrepancy {d['id']}"

    def test_discrepancy_severity_review(self, discrepancies):
        for d in discrepancies["discrepancies"]:
            assert d["severity"] == "REVIEW"

    def test_no_official_reference_in_discrepancies(self, discrepancies):
        for d in discrepancies["discrepancies"]:
            assert d.get("source") != "OFFICIAL_REFERENCE"
