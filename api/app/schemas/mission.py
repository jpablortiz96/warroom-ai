from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class MissionType(str, Enum):
    account_pulse = "account_pulse"
    supplier_watch = "supplier_watch"
    threat_surface = "threat_surface"


class MissionStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class MissionCreate(BaseModel):
    mission_type: MissionType
    target: str = Field(..., description="Company name, domain, or natural-language target")
    context: str | None = Field(None, description="Optional additional context for the agents")


class MissionResponse(BaseModel):
    id: UUID
    mission_type: MissionType
    status: MissionStatus
    target: str
    context: str | None
