"""
DrishtiGIS — Review Store & Audit Trail Persistence Service
==============================================================
Phase 8: Surveyor Review, Ground-Truthing & Cadastral Geometry Editing

Manages persistence, seeding, filtering, audit logging, field verifications,
and GeoJSON export for reviewer activities.
"""

import json
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone

from backend.app.models.review import (
    ReviewItem,
    ReviewAuditTrail,
    FieldVerificationRecord,
    ReviewStatus,
    ReviewIssueType,
    ReviewSeverity,
    VerificationMethod,
    ReviewSource,
    ReviewStats,
)
from backend.app.gis.review_engine import (
    validate_edited_geometry,
    recompute_parcel_building_relationships,
)

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data" / "reviews"
REVIEWS_FILE = DATA_DIR / "reviews.json"
AUDITS_FILE = DATA_DIR / "audits.json"
VERIFICATIONS_FILE = DATA_DIR / "verifications.json"

DISCREPANCIES_FILE = ROOT / "data" / "ai_output" / "bhopal-discrepancies.json"
SYNTHETIC_PARCELS_FILE = ROOT / "data" / "synthetic" / "bhopal-synthetic-parcels.geojson"
AI_BUILDINGS_FILE = ROOT / "data" / "ai_output" / "bhopal-building-parcel-associations.geojson"

_SYNTHETIC_DISCLAIMER = (
    "Synthetic prototype data — not an official land record. "
    "All identifiers, owner names, and property data are synthetic."
)
_AI_DISCLAIMER = (
    "AI analysis is derived from the UAVPal U-Net ResNet18 pipeline. "
    "NOT cadastral boundaries. NOT legal determinations. "
    "Spatial relationships are geometric observations only."
)


class ReviewStore:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.reviews: Dict[str, ReviewItem] = {}
        self.audits: Dict[str, List[ReviewAuditTrail]] = {}
        self.verifications: Dict[str, List[FieldVerificationRecord]] = {}
        self._load_or_seed()

    def _load_or_seed(self):
        """Loads persistent review state or seeds initial items from discrepancies."""
        if REVIEWS_FILE.exists():
            try:
                with open(REVIEWS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item_dict in data.get("reviews", []):
                        item = ReviewItem(**item_dict)
                        self.reviews[item.review_id] = item
            except Exception:
                self._seed_from_discrepancies()
        else:
            self._seed_from_discrepancies()

        if AUDITS_FILE.exists():
            try:
                with open(AUDITS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for rev_id, audit_list in data.items():
                        self.audits[rev_id] = [ReviewAuditTrail(**a) for a in audit_list]
            except Exception:
                pass

        if VERIFICATIONS_FILE.exists():
            try:
                with open(VERIFICATIONS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for rev_id, ver_list in data.items():
                        self.verifications[rev_id] = [FieldVerificationRecord(**v) for v in ver_list]
            except Exception:
                pass

    def _seed_from_discrepancies(self):
        """Seeds review queue from Phase 5.5 discrepancies."""
        if not DISCREPANCIES_FILE.exists():
            return

        try:
            with open(DISCREPANCIES_FILE, "r", encoding="utf-8") as f:
                disc_data = json.load(f)
                discrepancies = disc_data.get("discrepancies", [])
        except Exception:
            return

        # Load synthetic parcels for geometry lookup
        parcel_geoms: Dict[str, Dict[str, Any]] = {}
        if SYNTHETIC_PARCELS_FILE.exists():
            try:
                with open(SYNTHETIC_PARCELS_FILE, "r", encoding="utf-8") as f:
                    p_data = json.load(f)
                    for feat in p_data.get("features", []):
                        pid = feat["properties"].get("id") or feat["properties"].get("property_id")
                        if pid:
                            parcel_geoms[pid] = feat.get("geometry")
            except Exception:
                pass

        # Load AI buildings for geometry lookup
        building_geoms: Dict[str, Dict[str, Any]] = {}
        if AI_BUILDINGS_FILE.exists():
            try:
                with open(AI_BUILDINGS_FILE, "r", encoding="utf-8") as f:
                    b_data = json.load(f)
                    for feat in b_data.get("features", []):
                        bid = feat["properties"].get("id")
                        if bid:
                            building_geoms[bid] = feat.get("geometry")
            except Exception:
                pass

        for disc in discrepancies:
            rev_id = f"REV-{disc['id']}"
            issue_str = disc.get("type", "OTHER_REVIEW")
            try:
                issue_type = ReviewIssueType(issue_str)
            except ValueError:
                issue_type = ReviewIssueType.OTHER_REVIEW

            parcel_id = disc.get("parcel_id")
            building_id = disc.get("building_id")

            orig_geom = parcel_geoms.get(parcel_id) if parcel_id else (building_geoms.get(building_id) if building_id else None)

            item = ReviewItem(
                review_id=rev_id,
                entity_type="PARCEL" if parcel_id else "AI_BUILDING",
                entity_id=parcel_id or building_id or disc['id'],
                parcel_id=parcel_id,
                region_id="REGION-BPL-01",
                dataset_id="DATASET-BHOPAL-UAV",
                epoch_id="EPOCH-BPL-2024-01",
                country="India",
                state="Madhya Pradesh",
                city="Bhopal",
                issue_type=issue_type,
                source=ReviewSource.AI_DERIVED_UAVPAL,
                severity=ReviewSeverity.HIGH if issue_type == ReviewIssueType.BUILDING_CROSSES_PARCEL_BOUNDARY else ReviewSeverity.MEDIUM,
                status=ReviewStatus.OPEN,
                assigned_to=None,
                created_at=disc.get("created_at", datetime.now(timezone.utc).isoformat()),
                updated_at=datetime.now(timezone.utc).isoformat(),
                reviewer_notes=disc.get("description"),
                evidence={
                    "discrepancy_id": disc["id"],
                    "spatial_basis": disc.get("spatial_basis", {}),
                    "building_id": building_id,
                    "parcel_id": parcel_id,
                    "source_dataset": "AI_DERIVED_UAVPAL",
                    "disclaimer": _SYNTHETIC_DISCLAIMER if parcel_id and "demo" in parcel_id else _AI_DISCLAIMER,
                },
                original_geometry=orig_geom,
                before_geometry=orig_geom,
                after_geometry=orig_geom,
                geometry_changed=False,
            )
            self.reviews[rev_id] = item

            # Seed initial audit trail
            audit = ReviewAuditTrail(
                audit_id=f"AUDIT-{uuid.uuid4().hex[:8]}",
                review_id=rev_id,
                action="INITIAL_CREATION",
                previous_status=ReviewStatus.OPEN,
                new_status=ReviewStatus.OPEN,
                reviewer="System",
                notes="Review item automatically generated from discrepancy observation.",
            )
            self.audits[rev_id] = [audit]

        self._save()

    def _save(self):
        """Persists reviews, audit logs, and verifications to disk."""
        try:
            with open(REVIEWS_FILE, "w", encoding="utf-8") as f:
                json.dump({"total": len(self.reviews), "reviews": [item.dict() for item in self.reviews.values()]}, f, indent=2)

            with open(AUDITS_FILE, "w", encoding="utf-8") as f:
                json.dump({rev_id: [a.dict() for a in audit_list] for rev_id, audit_list in self.audits.items()}, f, indent=2)

            with open(VERIFICATIONS_FILE, "w", encoding="utf-8") as f:
                json.dump({rev_id: [v.dict() for v in ver_list] for rev_id, ver_list in self.verifications.items()}, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to persist review store: {str(e)}")

    def list_reviews(
        self,
        status: Optional[ReviewStatus] = None,
        issue_type: Optional[ReviewIssueType] = None,
        severity: Optional[ReviewSeverity] = None,
        region_id: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        dataset_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        assigned_to: Optional[str] = None,
    ) -> List[ReviewItem]:
        """Lists review items matching all applied filters."""
        results = list(self.reviews.values())

        if status:
            results = [r for r in results if r.status == status]
        if issue_type:
            results = [r for r in results if r.issue_type == issue_type]
        if severity:
            results = [r for r in results if r.severity == severity]
        if region_id:
            results = [r for r in results if r.region_id == region_id]
        if city:
            results = [r for r in results if r.city.lower() == city.lower()]
        if state:
            results = [r for r in results if r.state.lower() == state.lower()]
        if dataset_id:
            results = [r for r in results if r.dataset_id == dataset_id]
        if entity_type:
            results = [r for r in results if r.entity_type.upper() == entity_type.upper()]
        if assigned_to:
            results = [r for r in results if r.assigned_to == assigned_to]

        return results

    def get_review(self, review_id: str) -> Optional[ReviewItem]:
        return self.reviews.get(review_id)

    def get_review_by_entity(self, entity_type: str, entity_id: str) -> Optional[ReviewItem]:
        return next(
            (r for r in self.reviews.values() if r.entity_id == entity_id or r.parcel_id == entity_id or r.review_id == entity_id),
            None
        )

    def create_review(self, item: ReviewItem, reviewer: str = "System") -> ReviewItem:
        self.reviews[item.review_id] = item
        audit = ReviewAuditTrail(
            audit_id=f"AUDIT-{uuid.uuid4().hex[:8]}",
            review_id=item.review_id,
            action="CREATE_REVIEW",
            previous_status=item.status,
            new_status=item.status,
            reviewer=reviewer,
            notes=f"Created review item {item.review_id}",
        )
        self.audits.setdefault(item.review_id, []).append(audit)
        self._save()
        return item

    def update_review_status(
        self,
        review_id: str,
        new_status: ReviewStatus,
        reviewer: str,
        notes: Optional[str] = None
    ) -> ReviewItem:
        item = self.reviews.get(review_id)
        if not item:
            raise KeyError(f"Review '{review_id}' not found.")

        prev_status = item.status
        item.status = new_status
        item.updated_at = datetime.now(timezone.utc).isoformat()
        if notes:
            item.reviewer_notes = notes

        audit = ReviewAuditTrail(
            audit_id=f"AUDIT-{uuid.uuid4().hex[:8]}",
            review_id=review_id,
            action="STATUS_CHANGE",
            previous_status=prev_status,
            new_status=new_status,
            reviewer=reviewer,
            notes=notes,
        )
        self.audits.setdefault(review_id, []).append(audit)
        self._save()
        return item

    def update_review_geometry(
        self,
        review_id: str,
        new_geometry: Dict[str, Any],
        reviewer: str,
        notes: Optional[str] = None
    ) -> Tuple[ReviewItem, Dict[str, Any]]:
        """
        Validates, applies, and recomputes spatial relationships for geometry edits.
        Keeps original_geometry immutable; stores adjusted geometry in reviewed_geometry.
        """
        item = self.reviews.get(review_id)
        if not item:
            raise KeyError(f"Review '{review_id}' not found.")

        # Validate geometry
        is_valid, err_msg, meta = validate_edited_geometry(new_geometry)
        if not is_valid:
            raise ValueError(err_msg or "Geometry requires correction before approval.")

        prev_status = item.status
        item.before_geometry = item.after_geometry or item.original_geometry
        item.after_geometry = new_geometry
        item.reviewed_geometry = new_geometry
        item.geometry_changed = True
        item.source = ReviewSource.REVIEWED_AI_GEOMETRY
        item.updated_at = datetime.now(timezone.utc).isoformat()
        if notes:
            item.reviewer_notes = notes

        # Recompute parcel spatial relationships if parcel_id exists
        recomp_results = {}
        if item.parcel_id:
            all_buildings = []
            if AI_BUILDINGS_FILE.exists():
                with open(AI_BUILDINGS_FILE, "r", encoding="utf-8") as f:
                    b_data = json.load(f)
                    all_buildings = b_data.get("features", [])

            parcel_buildings = [
                b for b in all_buildings
                if b.get("properties", {}).get("primary_parcel_id") == item.parcel_id
            ]

            recomp_results = recompute_parcel_building_relationships(
                parcel_geom_dict=new_geometry,
                building_features=parcel_buildings,
                parcel_id=item.parcel_id
            )

        audit = ReviewAuditTrail(
            audit_id=f"AUDIT-{uuid.uuid4().hex[:8]}",
            review_id=review_id,
            action="GEOMETRY_EDITED",
            previous_status=prev_status,
            new_status=item.status,
            reviewer=reviewer,
            notes=notes or "Geometry edited and validated.",
            geometry_changed=True,
            evidence_reference=meta,
        )
        self.audits.setdefault(review_id, []).append(audit)
        self._save()
        return item, recomp_results

    def add_field_verification(
        self,
        review_id: str,
        record: FieldVerificationRecord
    ) -> FieldVerificationRecord:
        """Records a field verification observation and updates review status."""
        item = self.reviews.get(review_id)
        if not item:
            raise KeyError(f"Review '{review_id}' not found.")

        prev_status = item.status
        item.verification_method = record.verification_method
        item.verification_timestamp = record.timestamp
        item.verification_status = "FIELD_VERIFIED"
        item.status = ReviewStatus.FIELD_VERIFICATION_REQUIRED
        item.updated_at = datetime.now(timezone.utc).isoformat()

        self.verifications.setdefault(review_id, []).append(record)

        audit = ReviewAuditTrail(
            audit_id=f"AUDIT-{uuid.uuid4().hex[:8]}",
            review_id=review_id,
            action="FIELD_VERIFICATION_RECORDED",
            previous_status=prev_status,
            new_status=item.status,
            reviewer=record.reviewer,
            notes=record.observation,
            evidence_reference={
                "method": record.verification_method.value,
                "observed_feature": record.observed_feature,
                "photo_filename": record.photo_filename,
            }
        )
        self.audits.setdefault(review_id, []).append(audit)
        self._save()
        return record

    def get_audit_trail(self, review_id: str) -> List[ReviewAuditTrail]:
        return self.audits.get(review_id, [])

    def get_verifications(self, review_id: str) -> List[FieldVerificationRecord]:
        return self.verifications.get(review_id, [])

    def get_parcel_review_history(self, parcel_id: str) -> List[ReviewItem]:
        return [r for r in self.reviews.values() if r.parcel_id == parcel_id]

    def get_stats(self) -> ReviewStats:
        items = list(self.reviews.values())
        return ReviewStats(
            total_issues=len(items),
            open=sum(1 for r in items if r.status == ReviewStatus.OPEN),
            in_review=sum(1 for r in items if r.status == ReviewStatus.IN_REVIEW),
            field_verification_required=sum(1 for r in items if r.status == ReviewStatus.FIELD_VERIFICATION_REQUIRED),
            accepted=sum(1 for r in items if r.status == ReviewStatus.ACCEPTED),
            rejected=sum(1 for r in items if r.status == ReviewStatus.REJECTED),
            resolved=sum(1 for r in items if r.status == ReviewStatus.RESOLVED),
            geometry_adjustments=sum(1 for r in items if r.geometry_changed),
            field_verified=sum(1 for r in items if r.verification_status == "FIELD_VERIFIED"),
            ai_accepted=sum(1 for r in items if r.status == ReviewStatus.ACCEPTED and r.source == ReviewSource.AI_DERIVED_UAVPAL),
            ai_rejected=sum(1 for r in items if r.status == ReviewStatus.REJECTED and r.source == ReviewSource.AI_DERIVED_UAVPAL),
        )

    def export_reviewed_geojson(self, city: Optional[str] = None) -> Dict[str, Any]:
        """Exports reviewed GIS geometry features as GeoJSON with disclaimers and metadata."""
        items = self.list_reviews(city=city)
        features = []

        for item in items:
            geom = item.reviewed_geometry or item.original_geometry
            if not geom:
                continue

            feature = {
                "type": "Feature",
                "geometry": geom,
                "properties": {
                    "review_id": item.review_id,
                    "entity_type": item.entity_type,
                    "entity_id": item.entity_id,
                    "parcel_id": item.parcel_id,
                    "issue_type": item.issue_type.value,
                    "severity": item.severity.value,
                    "review_status": item.status.value,
                    "geometry_source": item.source.value,
                    "verification_status": item.verification_status,
                    "verification_method": item.verification_method.value if item.verification_method else None,
                    "city": item.city,
                    "state": item.state,
                    "country": item.country,
                    "dataset_id": item.dataset_id,
                    "updated_at": item.updated_at,
                    "reviewer_notes": item.reviewer_notes,
                    "disclaimer": _SYNTHETIC_DISCLAIMER if item.parcel_id and "demo" in str(item.parcel_id) else _AI_DISCLAIMER,
                }
            }
            features.append(feature)

        return {
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
            "total_features": len(features),
            "features": features,
            "_source": "REVIEWED_AI_GEOMETRY",
            "_disclaimer": _SYNTHETIC_DISCLAIMER,
        }


# Global singleton instance
review_store = ReviewStore()
