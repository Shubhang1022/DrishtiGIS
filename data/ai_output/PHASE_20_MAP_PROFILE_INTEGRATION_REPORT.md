# DrishtiGIS — Phase 20 Map Profile Integration Report

## 1. Consolidated Building Layer
The layer selection control provides a single, intuitive **Buildings** layer entry.

### Visual Styling & Source Distinction:
- **Outline & Contrast**: High-contrast emerald (`#10B981`) and cyan (`#00F0FF`) stroke outlines with 15% opacity fill, making boundaries clearly visible over aerial satellite imagery.
- **Source Toggle**: Single toggle with sub-selection badge:
  - `AI Building Footprints (0.02m UAV)` (834 high-resolution extracted polygons)
  - `OSM Reference Geometry` (Reference basemap features)
- **Clear Legend & Provenance**: Disambiguates AI-derived geometries from reference GIS data in map popups and property cards.

## 2. User Profile Dashboard & 3-Tier Privacy Opt-Ins
Located at `/app/profile` (`drishtigis/app/app/profile/page.tsx`).

### Supported Profile Fields:
- Full Name
- Phone Number
- House / Flat / Building Number
- Street / Locality / Landmark
- City, State, PIN Code
- Organization / Department

### 3-Tier Privacy Opt-In Controls:
- `show_name_publicly` (Default: `false`) — Opt-in to show name on building click.
- `show_address_publicly` (Default: `false`) — Opt-in to show address details.
- `show_phone_publicly` (Default: `false`) — Opt-in to expose phone contact method.
- **Master Kill Switch**: "Disable All Public Visibility" button resets all opt-ins to `false` instantly.

## 3. Building & Property Association
- Allows users to link their registered profile details with their mapped property location (`/api/v1/user/properties`).
- Displays clear synthetic disclaimers stating user profile data does not constitute legal land title or official ownership records.
