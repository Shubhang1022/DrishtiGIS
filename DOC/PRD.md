DrishtiGIS — Prototype PRD
1. Product

DrishtiGIS

Tagline

A Clearer View of a Brighter Tomorrow.

Product description

DrishtiGIS is an AI-powered urban geospatial intelligence platform that combines aerial imagery, cadastral/GIS information, AI feature extraction, spatial analysis, historical comparison, and natural-language assistance into a single WebGIS interface.

The prototype should demonstrate:

Aerial imagery → AI feature extraction → GIS context → parcel intelligence → discrepancy detection → human-readable insight

2. Primary SIH objective

The prototype is aligned with SIH26012 — AI-Based Automated Urban Parcel Mapping and Cadastral Feature Extraction System using Drone Imagery.

The prototype should demonstrate:

High-resolution aerial imagery visualization.
Building/road/feature extraction.
Parcel visualization.
Spatial association between detected features and parcels.
AI-vs-record comparison.
Potential discrepancy detection.
Historical imagery/change visualization.
WebGIS interaction.
AI assistant grounded in project data.
Important trust rule

The system must never claim that AI has legally determined ownership or cadastral boundaries.

Instead:

AI detected → spatially associated → potential discrepancy → requires verification

This distinction should be reflected throughout the UI.

3. Prototype scope
Build now

Landing → Authentication → Location → WebGIS → Parcel → AI Analysis → History → Assistant

Do NOT build yet
Full nationwide cadastral database
Real production drone ingestion
Complex billing
Real government authentication
Live ownership verification
Advanced ML training pipeline
AWS GPU orchestration
Complex admin permissions
Market valuation engine

Those belong to later phases.

4. Design direction — LOCKED
Approved landing page

Claude must not redesign the landing page.

Use the previously approved visual language:

Colors

Primary:

Warm cream
Soft beige
Deep forest green
Muted olive
Warm ochre/gold
Charcoal
Soft gray

Avoid:

Purple AI gradients
Neon
Cyberpunk
Blue SaaS dashboards
Excessive glassmorphism
Huge gradient blobs
Typography

Use two-font hierarchy:

Display/headline

Elegant editorial serif with personality.

UI/body

Clean modern sans-serif.

Important words can use the display font selectively.

Don't turn the entire UI into a serif interface.

5. Landing page

Route:

/

Keep the approved design.

Header

Logo:

DrishtiGIS

Navigation:

Platform
Intelligence
Use Cases
About

Right side:

Search
Location
Sign In
Get Started
Hero

Primary headline:

A Clearer View of a Brighter Tomorrow.

Supporting message around:

aerial intelligence
parcel mapping
urban planning
transparent geospatial information

Hero visual:

aerial imagery
parcel overlays
subtle GIS interface
Plot 101
map controls
CTA

Primary:

Explore DrishtiGIS →

Secondary:

See How It Works

Sections
AI Feature Extraction
Cadastral Intelligence
Discrepancy Detection
Historical Analysis
Interactive WebGIS
AI Assistant
Impact statistics
How it works
Use cases
CTA
Footer
6. Authentication

Routes:

/login
/register

Keep authentication visually consistent with landing page.

Login

Fields:

Email
Password

Actions:

Sign In

Secondary:

Continue with Google

Register
Name
Email
Password
Confirm Password

Do not overbuild authentication for the prototype.

7. Location onboarding

After authentication:

/app/location
Screen

Headline:

Where would you like to explore?

Search:

Search city, district or locality...

Suggestions:

Lucknow
Delhi
Chennai
Jammu
Srinagar
Current location

Button:

Use my location

But:

Location does not imply property ownership.

8. Relationship selection

If user chooses a property:

How are you connected to this property?

Options:

I am the Owner
I am a Tenant
I live with the Owner
I represent the Owner / Organization
Other

This is important because simply using GPS must never imply ownership.

9. Main WebGIS

Route:

/app/map

This is the heart of DrishtiGIS.

Philosophy

Map first. Data second. AI third.

Do NOT turn this into a conventional dashboard with 15 KPI cards.

The map should occupy approximately:

75–85% of the viewport.

10. WebGIS layout
┌─────────────────────────────────────────────────────────┐
│ DrishtiGIS   Search location...       Profile           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Layers                                               │
│  ┌───────┐                         ┌──────────────────┐ │
│  │       │                         │ Property Details │ │
│  │       │                         │                  │ │
│  │  MAP  │                         │ Plot 101         │ │
│  │       │                         │                  │ │
│  │       │                         │ Area             │ │
│  │       │                         │ Land use         │ │
│  │       │                         │ AI Analysis      │ │
│  │       │                         │                  │ │
│  │       │                         │ View History     │ │
│  │       │                         └──────────────────┘ │
│  │       │                                             │
└─────────────────────────────────────────────────────────┘
11. Map technology

Use:

MapLibre GL JS

MapLibre is specifically suited to interactive WebGL maps, and its current documentation includes Next.js/SSR considerations.

Use:

Next.js
+
MapLibre
+
GeoJSON initially

Don't prematurely build vector-tile infrastructure for the prototype.

Later:

PostGIS → vector tiles → MapLibre

can be introduced when the dataset becomes large. PostGIS-backed vector tiles are a common scaling approach.

12. Map controls
Top-left

Search:

Search Lucknow...
Right

Controls:

Zoom +
Zoom -
Locate
Fullscreen
Reset bearing
Layers

Single dropdown:

Layers

☑ Properties / Parcels
☑ Buildings
☑ Roads
☐ Land Use
☐ Terrain
☐ Historical Imagery
☐ AI Discrepancies
☐ Infrastructure

Don't scatter layer buttons everywhere.

13. City search

Search must work in two steps.

Step 1

Search city:

Lu

Results:

Lucknow, Uttar Pradesh
Ludhiana, Punjab
Latur, Maharashtra

User chooses:

Lucknow, Uttar Pradesh

Map zooms there.

Step 2

Search property:

Search property...

Supported:

Property ID
Plot number
Survey number
House number
Sector
Locality

Do NOT make owner name the primary search.

14. Parcel interaction

Click parcel:

Plot 101

Parcel highlights.

Right sidebar opens.

15. Property Details

Sidebar:

Header

Plot 101

Status:

🟢 Verified record

Basic information
Property ID
DRS-LKO-00101

Survey Number
LKO-101

Area
1,245 m²

Land Type
Residential

Location
Gomti Nagar, Lucknow
Record information
Record Status
Available

Last Updated
2026

Source
Cadastral Dataset
16. AI Analysis

Show:

AI detected building
Detected
Yes
Official area
1,245 m²
AI measured area
1,311 m²
Difference
+66 m²
+5.3%

Then:

Potential discrepancy

The AI-derived footprint differs from the recorded property area.

Status:

🟠 Requires verification

Never say:

“Illegal construction detected.”

unless actual authoritative evidence exists.

17. AI feature visualization

When AI Analysis is enabled:

Building
Road
Tree
Water

Different map layers can be toggled.

Detected geometry should have subtle animated appearance.

Use Anime.js for UI transitions rather than unnecessary animation everywhere.

18. Historical imagery

Route:

/app/history

or open from property:

View History

Timeline:

2022 ───── 2023 ───── 2024 ───── 2025 ───── 2026

Comparison:

Before                    After

[ imagery ]              [ imagery ]

Possible findings:

New building detected
Boundary change
Road expansion
Land-use change

Always label AI findings as potential changes.

19. AI Property Assistant

Route:

/app/assistant

This should not look like generic ChatGPT.

Heading:

Ask DrishtiGIS

Subtitle:

Ask about properties, parcels, imagery and detected changes.

Example questions:

What is the recorded area of Plot 101?

What did the AI detect on this parcel?

Why was this property flagged?

What changed between 2023 and 2026?

Show me nearby mapped infrastructure.
Language

Support:

English + natural Hinglish

Example:

“Plot 101 ka official area kitna hai?”

Answer should come from actual project data.

Critical rule

The assistant must never invent:

property IDs
areas
coordinates
ownership
survey numbers
AI findings

If information isn't available:

“I don't have that information in the current dataset.”

20. Reports

Route:

/app/reports

Allow:

Generate Property Report

Report contains:

Property information
Map snapshot
Official data
AI findings
Detected features
Potential discrepancies
Historical changes
Data sources
Verification disclaimer
21. Insights

Don't make this a permanent dashboard.

Use:

Insights

inside a panel/dropdown.

Possible statistics:

Mapped parcels
Detected buildings
Potential discrepancies
Mapped area
Recent changes
22. Admin prototype

Routes:

/admin
/admin/datasets
/admin/processing
/admin/review

Admin is completely separate from normal user experience.

Dataset upload
Upload Dataset

Dataset name
Location
Dataset type

○ Orthomosaic
○ DSM
○ Cadastral GIS
○ Other

Upload

Accepted initially:

GeoTIFF
GeoJSON
Shapefile ZIP
GeoPackage
CSV
23. Dataset validation

Before processing:

Dataset Validation

✓ File readable
✓ CRS detected
✓ Geographic bounds detected
✓ Resolution detected
✓ Geometry valid
✓ Required metadata present

For raster:

CRS
EPSG:32643

Resolution
0.0217 m/pixel

Bounds
...

This will be particularly useful with your UAVPal imagery.

24. Processing flow

Admin presses:

Run AI Analysis

Show:

Queued
   ↓
Preparing imagery
   ↓
AI feature extraction
   ↓
Geometry generation
   ↓
Spatial association
   ↓
Discrepancy analysis
   ↓
Ready for review

Don't fake processing percentages.

If processing is mocked in prototype, clearly structure the UI so the backend can later replace it.

25. Review screen

Admin sees:

Original imagery
       │
       ▼
AI detections
       │
       ▼
Cadastral overlay
       │
       ▼
Potential discrepancies

Actions:

Approve

Reject

Needs Review

26. Data model

Initial database:

users
properties
parcels
datasets
ai_features
discrepancies
historical_snapshots
processing_jobs
Parcel
id
property_id
plot_number
survey_number
area
land_type
geometry
source
created_at
updated_at
AI feature
id
dataset_id
feature_type
confidence
area
geometry
model
created_at
Discrepancy
id
parcel_id
feature_id
type
official_value
ai_value
difference
difference_percent
severity
status
27. Technology stack
Frontend
Next.js
React
TypeScript
Tailwind CSS
shadcn/ui
MapLibre GL JS
Anime.js

shadcn/ui remains the component foundation.

Backend
Python
FastAPI
GIS
GeoPandas
Shapely
Rasterio
GDAL
Database
PostgreSQL
PostGIS
AI

Prototype:

YOLO segmentation
SAM 2.1

For the assistant:

Gemini
Deployment later
Vercel
Render
Supabase
AWS GPU worker

Do not configure expensive AWS GPU infrastructure during the first prototype.

28. Prototype data strategy

For now:

Primary imagery

Your newly verified Bhopal UAV imagery.

Use it to demonstrate:

RGB imagery
+
DSM
+
annotations
Supporting data

Use the OSM data where appropriate.

Important

Don't call Bhopal data:

Lucknow data.

The UI should say:

Bhopal — Prototype Dataset

until we acquire actual Lucknow imagery.

This protects the credibility of the demo.

29. Landing page → application flow

The final flow should be:

LANDING
   ↓
GET STARTED
   ↓
LOGIN / REGISTER
   ↓
LOCATION
   ↓
SELECT CITY
   ↓
WEBGIS
   ↓
SELECT PARCEL
   ↓
PROPERTY DETAILS
   ↓
AI ANALYSIS
   ↓
DISCREPANCY
   ↓
HISTORY
   ↓
REPORT
   ↓
AI ASSISTANT
30. Animation system

Use Anime.js sparingly.

Landing
Hero image reveal
headline stagger
map line drawing
subtle metric count-up
section reveal
Map
parcel selection pulse
sidebar slide
layer transitions
detection geometry reveal
AI processing

Use meaningful state transitions:

Queued
↓
Processing
↓
Analysis
↓
Complete
Timing
Micro:       120–180ms
Normal:      200–300ms
Map:         400–700ms
Major:       500–800ms

Respect:

prefers-reduced-motion
31. Responsive design

Desktop is the primary SIH presentation mode.

But support:

Tablet

Map + collapsible property panel.

Mobile

Map-first:

Map
 ↓
Bottom sheet
 ↓
Property details

Don't simply shrink the desktop dashboard.

32. Performance rules

Claude must:

lazy-load MapLibre
avoid loading huge GeoJSON directly when unnecessary
simplify geometries where appropriate
avoid rerendering map unnecessarily
use spatial indexes in PostGIS
lazy-load heavy AI views
never load the 1.5 GB India PBF into the browser
never put huge raster files directly into Git
use sample/demo subsets

MapLibre's current documentation specifically notes browser/SSR handling for Next.js, so the map implementation should be isolated to the client side.

33. Prototype definition of done

The prototype is successful when an evaluator can:

In under 2 minutes:
Open DrishtiGIS.
Understand the product.
Click Get Started.
Enter the application.
Select a location.
See an interactive map.
Click a parcel.
See property details.
Toggle AI layer.
See detected building/features.
See AI-vs-record comparison.
See potential discrepancy.
Open historical imagery.
Ask the AI assistant a property question.
Generate a report.

That's the SIH demo path.