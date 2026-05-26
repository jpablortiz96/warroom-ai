from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class AgentName(str, Enum):
    planner = "planner"
    researcher = "researcher"
    skeptic = "skeptic"
    verifier = "verifier"
    commander = "commander"


class AgentEventType(str, Enum):
    started = "started"
    thinking = "thinking"
    tool_call = "tool_call"
    tool_result = "tool_result"
    completed = "completed"
    failed = "failed"


class AgentEvent(BaseModel):
    mission_id: UUID
    agent: AgentName
    event_type: AgentEventType
    message: str
    payload: dict | None = None
