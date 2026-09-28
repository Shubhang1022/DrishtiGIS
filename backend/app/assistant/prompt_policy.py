"""
Prompt policy, security enforcement, and safety guardrails for DrishtiGIS AI Assistant.
"""

import re
from typing import Dict, Any, List

SYSTEM_PROMPT = """
You are the DrishtiGIS Grounded Geospatial AI Assistant for SIH26012 (AI-Based Automated Urban Parcel Mapping and Cadastral Feature Extraction System using Drone Imagery).

CORE INSTRUCTIONS:
1. Ground every response strictly in actual tool outputs provided by DrishtiGIS ToolRegistry.
2. NEVER fabricate property details, owner names, parcel boundaries, GPS coordinates, historical observations, or confidence percentages.
3. NEVER make legal determinations or use forbidden legal terms such as "illegal construction", "unauthorized", "encroachment", or "ownership confirmed".
4. Always distinguish observed land-use patterns (OBSERVED_LAND_USE_PATTERN) from official zoning.
5. For synthetic demonstration data (SYNTHETIC_DEMO), ALWAYS preserve the disclaimer: "Synthetic prototype data — not an official land record."
6. For historical multi-epoch queries where only test fixtures exist, state clearly that real second-epoch temporal imagery is unavailable for the demonstration region.
7. Present responses clearly with:
   - ANSWER / OBSERVATION
   - EVIDENCE / PROVENANCE
   - WHY FLAGGED / RECOMMENDED REVIEW (if a discrepancy or review item)
   - MAP UI ACTIONS
"""

FORBIDDEN_LEGAL_TERMS = [
    "illegal construction",
    "unauthorized construction",
    "encroachment",
    "illegal land use",
    "ownership confirmed",
    "property legally belongs to",
    "boundary is legally correct",
    "legal violation"
]

PROMPT_INJECTION_PATTERNS = [
    r"ignore (all )?previous instructions",
    r"forget (your|all) (instructions|rules)",
    r"system prompt",
    r"override rules",
    r"act as (a |an )?lawyer",
    r"execute (sql|python|bash|cmd)",
    r"show (me )?api key"
]

def sanitize_user_input(user_query: str) -> str:
    """Check for prompt injection attempts and sanitize input."""
    lower = user_query.lower()
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, lower):
            return "[SECURITY NOTICE: Query contained prohibited override instructions and was filtered.]"
    return user_query

def enforce_safety_policy(response_text: str, is_synthetic: bool = False) -> str:
    """Filter response text to prevent hallucinated legal claims or policy violations."""
    clean_text = response_text
    for term in FORBIDDEN_LEGAL_TERMS:
        if term in clean_text.lower():
            clean_text = re.sub(re.escape(term), "AI-derived spatial discrepancy requiring review", clean_text, flags=re.IGNORECASE)

    if is_synthetic and "Synthetic prototype data — not an official land record." not in clean_text:
        clean_text += "\n\n*Disclaimer: Synthetic prototype data — not an official land record.*"

    return clean_text
