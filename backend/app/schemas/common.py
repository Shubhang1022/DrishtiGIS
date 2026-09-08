"""DrishtiGIS — Common response schemas"""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str
    app: str
    database: str


class DemoDataHeader(BaseModel):
    """Included on every demo placeholder response."""
    is_demo: bool = True
    disclaimer: str = (
        "This response contains prototype demonstration data only. "
        "It is not derived from official government cadastral records."
    )
