from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class RecommendedMove(str, Enum):
    attack = "ATTACK"
    defend = "DEFEND"
    wait = "WAIT"
    escalate = "ESCALATE"
    monitor = "MONITOR"


class Citation(BaseModel):
    claim: str
    source_url: str
    confidence: int = Field(..., ge=0, le=100)
    agent: str


class AgentSummary(BaseModel):
    agent: str
    headline: str
    detail: str
    confidence: int = Field(..., ge=0, le=100)


class ExecutiveBattleBrief(BaseModel):
    mission_id: UUID
    market_move_score: int = Field(..., ge=0, le=100, description="Composite risk/opportunity score 0–100")
    recommended_move: RecommendedMove
    headline: str = Field(..., description="One-sentence executive summary")
    situation: str = Field(..., description="2–3 sentence situation assessment")
    key_findings: list[AgentSummary]
    action_pack: list[str] = Field(..., description="3–5 concrete recommended actions")
    citations: list[Citation]
    commander_rationale: str = Field(..., description="Commander's reasoning for the recommended move")
