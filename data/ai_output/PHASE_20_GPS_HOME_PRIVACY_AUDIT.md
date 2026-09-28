# DrishtiGIS — Phase 20 GPS & HOME Marker Privacy Audit Report

## 1. Feature Architecture & Persistence
The user HOME location feature allows authenticated users to pin and save their primary residence location on the WebGIS map.

### Key Workflows:
1. **Explicit Geolocation Consent**: Device location permission is requested only upon user action (clicking "Use My Location").
2. **Current Location Pin & Accuracy Circle**: Displays reported accuracy radius (meters) and temporary location marker.
3. **Location Correction & Fine-Tuning**: Users can drag the temporary pin to align with their entrance or building rooftop before saving.
4. **Backend Persistence**: `POST /api/v1/user/home` saves coordinates strictly under the authenticated user's ID (`user_store.user_home[user.user_id]`).
5. **Automatic Retrieval**: On login, `GET /api/v1/user/home` retrieves and automatically renders the saved purple HOME marker without re-asking for device GPS permissions.

## 2. Privacy & Security Isolation Controls
- **Account Isolation**: HOME location is bound strictly to `user_id` derived from verified JWT token (`get_current_user`). Client-provided `user_id` parameters are ignored.
- **Cross-Account Protection**: User A cannot read, edit, or delete User B's HOME location.
- **Zero Public Exposure**: HOME coordinates are excluded from public parcel datasets, AI assistant tool context, PDF exports, and public API feeds.
- **Data Cleanup On Logout**: Logging out clears active HOME map markers and resets map state.
