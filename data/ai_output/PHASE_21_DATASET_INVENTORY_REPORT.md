# DrishtiGIS — Phase 21 Dataset Inventory Report

## 1. Inventory Interface Overview (`/admin/datasets`)
The Dataset Inventory page ([`drishtigis/app/admin/datasets/page.tsx`](file:///e:/Shubhang/projects/DrishtiGIS(SIH)/drishtigis/app/admin/datasets/page.tsx)) retrieves live, persisted dataset records from `GET /api/v1/admin/datasets`.

### Search, Filter & Sort Controls:
- **Search Query**: Real-time search across dataset name, dataset ID, and original filename.
- **Lifecycle Status Filter**: All, Registered, Validating, Processing, QA Required, Ready, Published, Failed, Cancelled.
- **Format Type Filter**: All, UAV Raster, Cadastral Vector, AI Footprints, GIS Archive.
- **Sorting Controls**: Sort by Upload Date, Dataset Name, Lifecycle Status, File Size (Ascending / Descending).
- **Auto-Polling Mechanism**: 3-second automatic background refresh when active processing jobs exist (`REGISTERED`, `VALIDATING`, `PROCESSING`).

## 2. Dataset Details Modal / Drawer
Clicking any dataset row or "View" button opens a 6-section details drawer:
1. **Overview**: Dataset name, ID, job ID, original filename, format, size, region, admin, upload timestamp, lifecycle status badge.
2. **Geospatial Metadata**: Detected CRS header (`EPSG:4326`), spatial resolution (`0.02 m/px`), dimensions (`2048 x 2048`), feature count (`834`), bounding box, layer names.
3. **Processing Stage Timeline**: Step-by-step progress tracking completed steps (emerald badge), active steps (blue spinner), pending steps (gray dot), and failed steps (red alert).
4. **Quality & Spatial Validation**: Format checks, CRS inspection, byte integrity, topology validation results.
5. **Generated Geospatial Outputs**: Output file paths, XYZ tile feeds, and GeoJSON endpoints.
6. **Administrative Actions**: Retry failed pipeline jobs (`POST /api/v1/admin/datasets/{id}/retry`), Cancel queued jobs, and Publish ready datasets to public WebGIS endpoints.
