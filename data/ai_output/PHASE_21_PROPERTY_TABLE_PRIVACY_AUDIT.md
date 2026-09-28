# DrishtiGIS — Phase 21 Property Table Privacy Audit Report

## 1. Table Architecture & Aggregation (`GET /api/v1/admin/properties`)
The Property & Cadastral Intelligence Table in the Admin Console aggregates demonstration records from:
1. **Synthetic Demo Parcels**: 35 synthetic cadastral parcels (`data/synthetic/bhopal-synthetic-properties.json`)
2. **User-Registered Property Markers**: User-submitted markers (`data/governance/user_properties.json`)

## 2. Table Columns & Financial Formatting
- **Property / Survey ID**: Unique parcel identifier or survey number
- **Property Type**: Residential, Commercial, Vacant Plot, House, Building
- **Parcel Area**: Formatted square meters (m²)
- **Owner Name**: Displays owner name if consented or tagged `[PRIVATE — Opt-in OFF]` when privacy toggle is disabled
- **Valuation Fields**: Purchase Price & Estimated Selling Price formatted in INR (`₹`)
- **AI Analytics**: AI Building Count, AI-Detected Area (m²), Coverage Ratio (%)
- **Data Source Badges**: `SYNTHETIC_DEMO` vs `USER_REGISTERED`

## 3. Privacy & Accuracy Enforcement Rules
- **Privacy Opt-In Enforcement**: User-registered property records respect 3-tier privacy opt-in controls (`show_name_publicly`, `show_address_publicly`, `show_phone_publicly`).
- **Synthetic Disclaimers**: Synthetic demo parcels carry mandatory disclaimer: `"Synthetic prototype data — not an official legal land record."`
- **Ownership Exclusion**: User profile entries and AI building detection results do not imply legal title ownership.
