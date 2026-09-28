# DrishtiGIS — Phase 24 MapLibre GL JS Dynamic Raster Integration

> **Document ID:** `PHASE_24_MAPLIBRE_INTEGRATION`  
> **Timestamp:** `2026-09-24T17:03:00+05:30`  
> **Status:** `IMPLEMENTED & VERIFIED`

---

## Executive Summary

Phase 24 establishes dynamic discovery and rendering of published raster datasets within the MapLibre GL JS engine. Instead of relying on static hardcoded tile sources, the WebGIS client dynamically fetches published datasets, registers MapLibre raster sources/layers on demand, and integrates layer toggling and automated camera fitting (`fitBounds`).

---

## Technical Integration Details

### 1. Dynamic Dataset Discovery
* **Client Function:** `fetchPublishedDatasets()` in `drishtigis/lib/api/datasets.ts`
* **Endpoint:** `GET /api/v1/datasets/published`
* **Data Model:**
```ts
export interface PublishedDatasetItem {
  dataset_id: str;
  name: str;
  crs: str;
  bounds: [number, number, number, number];
  minzoom: number;
  maxzoom: number;
  tilejson_url: str;
  tiles_url: str;
  is_published: boolean;
}
```

### 2. MapLibre Source & Layer Lifecycle
* **File:** `drishtigis/components/map/MapLibreMap.tsx`
* **Source Pattern:**
```ts
map.addSource(`dataset-raster-source-${dataset.dataset_id}`, {
  type: "raster",
  tiles: [
    `${API_BASE}/api/v1/datasets/${dataset.dataset_id}/tiles/{z}/{x}/{y}.png`
  ],
  tileSize: 256,
  minzoom: dataset.minzoom || 12,
  maxzoom: dataset.maxzoom || 22,
  bounds: dataset.bounds
});
```
* **Layer Pattern:**
```ts
map.addLayer({
  id: `dataset-raster-layer-${dataset.dataset_id}`,
  type: "raster",
  source: `dataset-raster-source-${dataset.dataset_id}`,
  paint: {
    "raster-opacity": 1.0,
    "raster-resampling": "linear"
  }
}, "building-layer-3d"); // Inserted below 3D buildings for correct ordering
```

### 3. Layer Control Panel & Camera Fitting
* **File:** `drishtigis/components/map/LayerControl.tsx`
* Renders a dedicated "Published Aerial Imagery" section listing each active published dataset.
* Toggling a checkbox adds or removes the dataset ID from `activePublishedDatasetIds`, controlling layer visibility.
* Clicking **"Zoom to extent"** executes MapLibre camera transition:
```ts
map.fitBounds([
  [bounds[0], bounds[1]], // [min_lon, min_lat]
  [bounds[2], bounds[3]]  // [max_lon, max_lat]
], { padding: 40, maxZoom: 19 });
```

---

## Admin "View on Map" Link Integration

* **File:** `drishtigis/app/admin/datasets/page.tsx`
* Administrators viewing published datasets in the Dataset Inventory can click **"View on Map"**, which navigates directly to `/app/map?dataset_id={dataset_id}`.
* `MapCanvas.tsx` reads the query parameter on mount, selects the target dataset, and automatically centers/zooms the map to the dataset bounds.
