"""
DrishtiGIS — India City Static Data
======================================
Static list of major Indian cities used for location search and
coverage lookups.

This file is intentionally static — it does not call any external geocoding
API. Extensible by adding entries to INDIA_CITIES without touching the
search endpoint.

DO NOT add coverage flags here — coverage availability is managed
separately in coverage_registry.py.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class IndiaCity:
    name:  str
    state: str
    lat:   float
    lon:   float
    zoom:  int = 12  # default city-level zoom


INDIA_CITIES: list[IndiaCity] = [
    # Madhya Pradesh
    IndiaCity("Bhopal",        "Madhya Pradesh",  23.2599,  77.4126),
    IndiaCity("Indore",        "Madhya Pradesh",  22.7196,  75.8577),
    IndiaCity("Jabalpur",      "Madhya Pradesh",  23.1815,  79.9864),
    IndiaCity("Gwalior",       "Madhya Pradesh",  26.2183,  78.1828),
    # Delhi / NCR
    IndiaCity("Delhi",         "Delhi",           28.6139,  77.2090),
    IndiaCity("New Delhi",     "Delhi",           28.6139,  77.2090),
    IndiaCity("Noida",         "Uttar Pradesh",   28.5355,  77.3910),
    IndiaCity("Gurgaon",       "Haryana",         28.4595,  77.0266),
    # Maharashtra
    IndiaCity("Mumbai",        "Maharashtra",     19.0760,  72.8777),
    IndiaCity("Pune",          "Maharashtra",     18.5204,  73.8567),
    IndiaCity("Nagpur",        "Maharashtra",     21.1458,  79.0882),
    IndiaCity("Nashik",        "Maharashtra",     19.9975,  73.7898),
    # Uttar Pradesh
    IndiaCity("Lucknow",       "Uttar Pradesh",   26.8467,  80.9462),
    IndiaCity("Kanpur",        "Uttar Pradesh",   26.4499,  80.3319),
    IndiaCity("Agra",          "Uttar Pradesh",   27.1767,  78.0081),
    IndiaCity("Varanasi",      "Uttar Pradesh",   25.3176,  82.9739),
    IndiaCity("Allahabad",     "Uttar Pradesh",   25.4358,  81.8463),
    IndiaCity("Meerut",        "Uttar Pradesh",   28.9845,  77.7064),
    # Tamil Nadu
    IndiaCity("Chennai",       "Tamil Nadu",      13.0827,  80.2707),
    IndiaCity("Coimbatore",    "Tamil Nadu",      11.0168,  76.9558),
    IndiaCity("Madurai",       "Tamil Nadu",       9.9252,  78.1198),
    # Jammu & Kashmir
    IndiaCity("Jammu",         "Jammu & Kashmir", 32.7266,  74.8570),
    IndiaCity("Srinagar",      "Jammu & Kashmir", 34.0837,  74.7973),
    # Telangana / Andhra Pradesh
    IndiaCity("Hyderabad",     "Telangana",       17.3850,  78.4867),
    IndiaCity("Visakhapatnam", "Andhra Pradesh",  17.6868,  83.2185),
    IndiaCity("Vijayawada",    "Andhra Pradesh",  16.5062,  80.6480),
    # Karnataka
    IndiaCity("Bengaluru",     "Karnataka",       12.9716,  77.5946),
    IndiaCity("Mysuru",        "Karnataka",       12.2958,  76.6394),
    IndiaCity("Hubli",         "Karnataka",       15.3647,  75.1240),
    # West Bengal
    IndiaCity("Kolkata",       "West Bengal",     22.5726,  88.3639),
    # Gujarat
    IndiaCity("Ahmedabad",     "Gujarat",         23.0225,  72.5714),
    IndiaCity("Vadodara",      "Gujarat",         22.3072,  73.1812),
    IndiaCity("Surat",         "Gujarat",         21.1702,  72.8311),
    # Rajasthan
    IndiaCity("Jaipur",        "Rajasthan",       26.9124,  75.7873),
    IndiaCity("Jodhpur",       "Rajasthan",       26.2389,  73.0243),
    IndiaCity("Udaipur",       "Rajasthan",       24.5854,  73.7125),
    # Bihar
    IndiaCity("Patna",         "Bihar",           25.5941,  85.1376),
    # Punjab / Haryana / Chandigarh
    IndiaCity("Chandigarh",    "Chandigarh",      30.7333,  76.7794),
    IndiaCity("Ludhiana",      "Punjab",          30.9010,  75.8573),
    IndiaCity("Amritsar",      "Punjab",          31.6340,  74.8723),
    # Odisha
    IndiaCity("Bhubaneswar",   "Odisha",          20.2961,  85.8245),
    # Assam
    IndiaCity("Guwahati",      "Assam",           26.1445,  91.7362),
    # Kerala
    IndiaCity("Kochi",         "Kerala",           9.9312,  76.2673),
    IndiaCity("Thiruvananthapuram", "Kerala",       8.5241,  76.9366),
]

# Build lookup indexes
_NAME_INDEX:  dict[str, IndiaCity] = {c.name.lower(): c for c in INDIA_CITIES}
_STATE_INDEX: dict[str, list[IndiaCity]] = {}
for _city in INDIA_CITIES:
    _STATE_INDEX.setdefault(_city.state.lower(), []).append(_city)


def get_city(name: str) -> Optional[IndiaCity]:
    """Case-insensitive exact name lookup. Returns None if not found."""
    return _NAME_INDEX.get(name.strip().lower())


def search_cities(query: str, limit: int = 10) -> list[IndiaCity]:
    """
    Substring search across city names and state names.
    Case-insensitive. Returns at most `limit` results.
    """
    q = query.strip().lower()
    if not q:
        return []
    results = [
        c for c in INDIA_CITIES
        if q in c.name.lower() or q in c.state.lower()
    ]
    return results[:limit]
