# DrishtiGIS — Software Requirements Specification

**Product:** DrishtiGIS  
**Version:** 0.1 Prototype  
**Status:** Prototype Development  
**Primary Use Case:** SIH26012  
**Tagline:** A Clearer View of a Brighter Tomorrow.

---

# 1. Purpose

DrishtiGIS is an AI-powered urban geospatial intelligence platform designed to combine:

- High-resolution aerial/UAV imagery
- Cadastral and GIS data
- AI-based feature extraction
- Parcel intelligence
- Spatial analysis
- Discrepancy detection
- Historical imagery analysis
- Interactive WebGIS
- Grounded AI assistance

The prototype must demonstrate a complete workflow from aerial imagery to actionable parcel-level intelligence.

---

# 2. Problem Statement

Urban land information is often distributed across different datasets and systems.

Aerial imagery can show the physical state of an area, while cadastral GIS can represent official/reference parcel boundaries and identifiers.

DrishtiGIS brings these sources together and uses AI to identify physical features such as:

- Buildings
- Roads
- Trees
- Water
- Other relevant structures

The resulting AI-derived features are spatially associated with cadastral parcels to support:

- Parcel intelligence
- Area comparison
- Potential discrepancy identification
- Historical change analysis
- Urban planning insights

The system must clearly distinguish between:

1. Official/reference GIS information
2. AI-derived information
3. Potential discrepancies
4. Human-verified findings

---

# 3. Primary Objective

The prototype must demonstrate:

```text
Aerial Imagery
      ↓
AI Feature Extraction
      ↓
Geospatial Feature Generation
      ↓
Cadastral Spatial Association
      ↓
Parcel Intelligence
      ↓
AI vs Official Comparison
      ↓
Potential Discrepancy
      ↓
Human Verification


4. Prototype Scope
4.1 Included

The prototype MUST include:

Premium landing page
Authentication
Location selection
Interactive WebGIS
City search
Property/parcel search
Parcel visualization
Property details
AI feature visualization
AI analysis
Discrepancy analysis
Historical imagery interface
AI property assistant
Property reports
Basic admin dataset workflow
Dataset validation interface
Processing workflow interface
Responsive design
4.2 Not Required for Prototype

The following are OUT OF SCOPE for the first prototype:

Nationwide production-scale processing
Complete Indian cadastral database
Government authentication
Legal ownership verification
Legal property ownership determination
Production billing/subscriptions
Real-time government record synchronization
Fully automated cadastral boundary creation
Nationwide AI model training
Complex enterprise RBAC
24/7 GPU infrastructure
Production-grade disaster recovery

These may be implemented later.

5. Design Requirements
5.1 Landing Page

The existing approved landing page is LOCKED.

The landing page MUST NOT be redesigned.

It must retain the approved visual direction:

Warm cream
Soft beige
Forest green
Muted olive
Warm gold/ochre
Charcoal
Editorial serif typography
Modern sans-serif interface typography
Premium spacing
Subtle cartographic details
Aerial/geospatial visual language
Refined cards
Soft shadows
Minimalist controls

The landing page should feel:

Premium
Creative
Editorial
Geospatial
Trustworthy
Modern
Human-designed

The landing page MUST NOT become:

Generic AI SaaS
Purple gradient-heavy
Neon
Cyberpunk
Blue enterprise dashboard
Excessively glassmorphic
Excessively rounded
Over-animated
6. Typography

The design MUST use two primary typography roles.

Display Typography

Used for:

Hero headline
Major section headings
Important campaign statements
Selected highlighted words

The display typeface should feel:

Editorial
Elegant
Distinctive
Premium
Interface Typography

Used for:

Navigation
Forms
Map controls
Property information
Tables
Buttons
Body text

The interface font should be:

Highly readable
Modern
Clean
Professional

Do not use decorative typography for technical information.

7. Application Structure

The application MUST contain the following routes.

Public
/
 /login
 /register
User Application
/app/location
/app/map
/app/property/[id]
/app/history
/app/reports
/app/assistant
Administration
/admin
/admin/datasets
/admin/datasets/upload
/admin/processing
/admin/review
8. User Journey

The primary user journey MUST be:

Landing Page
      ↓
Get Started
      ↓
Login / Register
      ↓
Location Selection
      ↓
City Selection
      ↓
Interactive WebGIS
      ↓
Parcel Selection
      ↓
Property Details
      ↓
AI Analysis
      ↓
Potential Discrepancy
      ↓
Historical Analysis
      ↓
AI Assistant
      ↓
Property Report

The entire journey should be demonstrable without requiring an evaluator to understand GIS technology beforehand.

9. Authentication Requirements
Login

The system MUST provide:

Email
Password
Sign in
Registration navigation

Optional prototype feature:

Google authentication
Registration

The system MUST provide:

Name
Email
Password
Confirm password

Authentication implementation should be structured so it can later connect to Supabase Auth or another production authentication provider.

10. Location Onboarding

After authentication, the user MUST reach:

/app/location

The screen MUST provide:

Where would you like to explore?

Search must support cities and locations.

Initial target locations:

Lucknow
Delhi
Chennai
Jammu
Srinagar
Bhopal

The system MUST support:

Search
Autocomplete
Location selection
Current-location option
11. Ownership Relationship

Location or GPS information MUST NOT automatically imply property ownership.

When interacting with a property, the system MUST allow the user to select:

I am the Owner
I am a Tenant
I live with the Owner
I represent the Owner / Organization
Other

The selected relationship should be treated as user-provided context, not verified ownership.

12. WebGIS Requirements

The main application MUST be map-first.

Route:

/app/map

The map should occupy approximately:

75–85% of the primary viewport

The interface MUST NOT become a traditional dashboard dominated by KPI cards.

13. Map Technology

The prototype MUST use:

MapLibre GL JS

The map should support:

Zoom
Pan
Location
Fullscreen
Layer control
Feature selection
Parcel highlighting
Popup/contextual information
GeoJSON visualization
14. Map Layers

The application MUST provide a unified Layers control.

Initial layers:

Properties / Parcels
Buildings
Roads
Land Use
Terrain
Historical Imagery
AI Discrepancies
Infrastructure

Each layer should be independently toggleable.

The UI should avoid scattering layer controls across the map.

15. City Search

The city search MUST work contextually.

Example:

User enters:

Lu

The system should show:

Lucknow, Uttar Pradesh
Ludhiana, Punjab
Latur, Maharashtra

After selecting:

Lucknow, Uttar Pradesh

the map MUST zoom to the selected location.

16. Property Search

After selecting a city, the search context MUST become property-oriented.

Supported searches:

Property ID
Plot Number
Survey Number
House Number
Sector
Locality

Owner name should NOT be the primary property search mechanism.

17. Parcel Requirements

Users MUST be able to select a parcel on the map.

Selected parcel should:

Highlight visually
Open property information
Show parcel geometry
Display available attributes

The system MUST distinguish parcel/reference geometry from AI-derived geometry.

18. Property Details

The property sidebar MUST contain:

Basic Information
Property ID
Plot Number
Survey Number
Area
Location
Land Type
Status
Coordinates
Record Information
Record Status
Source
Last Updated
AI Analysis
AI Building Detection
AI Measured Area
Official Area
Difference
Difference Percentage
Potential Discrepancy
Confidence
19. AI Feature Extraction

The prototype MUST support AI-derived features.

Initial feature categories:

Building
Road
Tree
Water

Each AI feature SHOULD contain:

Feature Type
Confidence
Geometry
Area
Model
Dataset
Timestamp

AI features MUST be visually distinguishable from official/reference GIS data.

20. AI/Cadastral Relationship

The system MUST follow this conceptual architecture:

Aerial Image
      ↓
AI Detection
      ↓
Pixel/Mask
      ↓
Geographic Geometry
      ↓
Spatial Association
      ↓
Cadastral Parcel
      ↓
Property/Plot Identifier

AI MUST NOT independently invent:

Parcel boundaries
Plot numbers
Survey numbers
Property IDs
Legal ownership
Official areas

Cadastral/reference GIS provides authoritative/reference parcel geometry when available.

21. Discrepancy Detection

The system MUST be able to demonstrate a comparison between:

Official / Reference Value

and:

AI-Derived Value

Example:

Official Area
1,245 m²

AI-Derived Area
1,311 m²

Difference
66 m²

Difference
5.3%

The system should display:

Potential discrepancy
Requires verification

It MUST NOT automatically state:

Illegal construction
Fraud
Unauthorized property
Legal violation

unless supported by authoritative evidence.

22. Confidence

AI findings SHOULD expose confidence information.

Example:

Building Detection
Confidence: 94%

Confidence must be clearly labeled as model confidence.

It must not be represented as legal certainty.

23. Historical Analysis

Route:

/app/history

The system MUST provide a historical timeline.

Example:

2022
2023
2024
2025
2026

The user should be able to compare imagery.

Possible AI-derived findings:

New building detected
Potential boundary change
Road expansion
Land-use change

All automated findings must be labeled as AI-derived or potential findings.

24. AI Assistant

Route:

/app/assistant

Name:

Ask DrishtiGIS

The assistant is a GIS/property intelligence assistant.

It MUST answer questions about:

Properties
Parcels
AI detections
Historical imagery
Discrepancies
Mapped infrastructure
Dataset information

Example questions:

What is the recorded area of Plot 101?

Plot 101 ka official area kitna hai?

What did the AI detect on this parcel?

What changed between 2023 and 2026?

Why was this property flagged?

The assistant MUST use retrieved project data.

It MUST NOT hallucinate property information.

If information is unavailable:

I don't have that information in the current dataset.
25. Reports

Route:

/app/reports

The system MUST support generating a property report.

Report sections:

Property Information
Map Snapshot
Official Data
AI Findings
Detected Features
Potential Discrepancies
Historical Changes
Data Sources
Verification Disclaimer
26. Admin Dataset Management

Admin MUST be separated from normal user experience.

Routes:

/admin
/admin/datasets
/admin/datasets/upload
/admin/processing
/admin/review
27. Dataset Upload

Admin MUST be able to select:

Orthomosaic
DSM
Cadastral GIS
Other

Prototype-supported formats:

GeoTIFF
GeoJSON
Shapefile ZIP
GeoPackage
CSV

The system should reject unsupported formats gracefully.

28. Dataset Validation

After upload, the system MUST validate:

File readability
CRS
Geographic bounds
Resolution
Raster dimensions
Band count
Data type
Geometry validity
Required metadata

For vector data:

Geometry type
CRS
Feature count
Validity
Bounding box

For raster data:

CRS
Dimensions
Resolution
Band count
Data type
Bounds
NoData

The system MUST NOT assume CRS.

29. Processing Pipeline

The prototype processing workflow MUST be represented as:

Upload
   ↓
Validation
   ↓
Preprocessing
   ↓
AI Feature Extraction
   ↓
Geometry Generation
   ↓
Spatial Association
   ↓
Discrepancy Analysis
   ↓
Review
   ↓
Publish

Processing states:

Queued
Preparing
Processing
Analyzing
Ready for Review
Published
Failed
30. Admin Review

Admin MUST be able to inspect:

Original imagery
AI detections
Reference/cadastral geometry
Potential discrepancies

Actions:

Approve
Reject
Needs Review
31. Prototype Data

The prototype currently has verified high-resolution UAV imagery from a Bhopal-based dataset.

The dataset includes:

RGB aerial imagery
DSM/surface information
semantic annotations

The Bhopal dataset MUST be labeled honestly as:

Prototype Dataset — Bhopal

It MUST NOT be presented as Lucknow, Delhi, Chennai or J&K imagery.

The application architecture must allow additional city datasets to be added later.

32. OSM Data

OpenStreetMap data may be used for supplementary GIS information such as:

Roads
Buildings
Places
Waterways
Infrastructure
Administrative/reference information

OSM MUST NOT be represented as authoritative cadastral data.

The 1.5 GB India OSM PBF MUST NOT be loaded directly into the browser.

Use processed subsets or a backend GIS pipeline.

33. GIS Requirements

The GIS layer should support:

GeoJSON
GeoTIFF
GeoPackage
Shapefile-derived data
PostGIS geometry

Coordinate systems MUST be preserved.

Reprojection should occur explicitly when required.

The system MUST preserve the source CRS.

34. Database Requirements

The prototype data model should support:

users
properties
parcels
datasets
ai_features
discrepancies
processing_jobs
historical_snapshots
35. Parcel Entity

Minimum fields:

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
36. AI Feature Entity

Minimum fields:

id
dataset_id
feature_type
confidence
area
geometry
model
created_at
37. Discrepancy Entity

Minimum fields:

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
38. Processing Job Entity

Minimum fields:

id
dataset_id
status
progress
started_at
completed_at
error
result

Progress should only be shown if the backend can provide meaningful progress.

Do not fabricate progress.

39. Historical Snapshot Entity

Minimum fields:

id
property_id
dataset_id
timestamp
imagery_source
geometry
change_type
confidence
40. Source Attribution

Every dataset must have a source.

The UI should distinguish:

Official / Reference
AI Derived
OpenStreetMap
Prototype Dataset
User Uploaded

Data source should be available in property/data details.

41. Security Requirements

The system MUST NOT expose frontend:

Database passwords
API keys
Gemini API keys
AWS credentials
Supabase service-role keys

All secrets must remain server-side.

Uploaded files MUST be validated.

42. Performance Requirements

The prototype should:

Avoid loading huge datasets into the browser
Lazy-load heavy components
Lazy-load map resources where possible
Avoid unnecessary MapLibre re-renders
Use simplified/demo geospatial data
Use spatial indexes when PostGIS is used
Avoid processing large raster datasets in the browser

Target:

Initial UI should feel responsive.

Exact production performance targets can be defined later.

43. Accessibility Requirements

The application MUST:

Support keyboard navigation
Provide visible focus states
Use semantic HTML
Provide accessible labels
Maintain sufficient contrast
Provide meaningful error messages
Support reduced motion
Avoid relying solely on color to communicate state
44. Responsive Requirements

Desktop is the primary presentation environment.

Tablet:

Map + collapsible property panel

Mobile:

Map
↓
Bottom sheet
↓
Property details

The mobile layout must be intentionally designed rather than being a scaled desktop interface.

45. Animation Requirements

Use Anime.js.

Animations should communicate:

State
Hierarchy
Spatial transitions
Selection
Processing

Recommended durations:

Micro interactions: 120–180ms
Normal transitions: 200–300ms
Map transitions: 400–700ms
Major transitions: 500–800ms

Respect:

prefers-reduced-motion

Avoid decorative animation overload.

46. Error States

Every important feature MUST have:

Loading
Success
Empty
Error

Example GIS error:

Unable to read this dataset.
The file may be corrupted or missing geospatial metadata.
47. Demo Data

When real backend data is not yet connected:

Use clearly isolated demo data.

Recommended:

/lib/demo-data

Demo data MUST NOT be mixed with production API logic.

The architecture should allow demo data to later be replaced by FastAPI/PostGIS.

48. Non-Functional Design Requirements

The system should feel:

Premium
Precise
Trustworthy
Calm
Professional
Geospatial
Civic-tech oriented
Indian
Technically sophisticated

The interface should avoid looking like:

Generic AI SaaS
Cryptocurrency application
Gaming dashboard
Marketing template
Generic admin panel
49. Primary Demo Scenario

The prototype must support the following evaluator scenario:

1. Open DrishtiGIS

2. Understand the product from the landing page

3. Click Get Started

4. Login

5. Select Bhopal prototype dataset

6. Open WebGIS

7. Explore aerial imagery

8. Toggle Buildings layer

9. Toggle AI Analysis

10. Select a parcel/property

11. Open Property Details

12. Compare official/reference information
    with AI-derived information

13. Display potential discrepancy

14. Open historical imagery

15. Compare imagery

16. Ask DrishtiGIS Assistant a question

17. Generate property report

The complete journey should be achievable quickly and without technical knowledge.

50. MVP Definition of Done

The prototype is considered complete when:

Landing page matches approved design
Authentication works
Location selection works
WebGIS loads
Map interaction works
Layers can be toggled
Parcel selection works
Property sidebar works
AI features can be visualized
AI analysis can be displayed
Potential discrepancy can be displayed
Historical comparison works
Assistant interface works
Reports can be generated
Admin dataset workflow exists
Dataset validation UI exists
Responsive layouts work
No critical console errors exist
No TypeScript errors exist
No broken routes exist
No unsupported claims are presented as facts
51. Data Integrity Rules

These rules are NON-NEGOTIABLE.

Never invent coordinates.
Never invent property IDs.
Never invent parcel boundaries.
Never invent ownership.
Never invent survey numbers.
Never invent official area.
Never label AI findings as official.
Never label Bhopal data as Lucknow.
Never claim OSM is authoritative cadastral data.
Never claim AI output is legally verified.
Never silently change CRS.
Never treat a normal JPG/PNG as georeferenced unless metadata confirms it.
Always identify the source of important geospatial information.
Clearly distinguish demo/mock data from real data.
52. Future Expansion

After MVP:

Phase 2
- Real cadastral integration
- More Indian cities
- Real AI inference pipeline
- PostGIS production integration
- Improved spatial association
- Historical datasets

Phase 3
- AWS GPU worker
- Automated dataset ingestion
- Advanced change detection
- 3D terrain
- Advanced reports
- Human review workflow
- Government/institution integrations

Phase 4
- Production-scale national infrastructure
- Advanced AI models
- Large-scale vector tiles
- Automated retraining
- Enterprise access control
53. Final Product Principle

DrishtiGIS must communicate:

See the land. Understand the change. Make better decisions.

The product should combine:

Aerial Intelligence
+
GIS
+
AI
+
Human Verification
=
Actionable Urban Intelligence

AI should assist decisions, not pretend to replace authoritative records or human verification.


### Recommended project structure

```text
drishtigis/
│
├── CLAUDE.md
├── requirements.md
├── README.md
│
├── app/
├── components/
├── lib/
│   ├── demo-data/
│   ├── gis/
│   └── utils/
│
├── public/
│
├── backend/
│
└── data/
    ├── demo/
    ├── imagery/
    ├── dsm/
    └── annotations/