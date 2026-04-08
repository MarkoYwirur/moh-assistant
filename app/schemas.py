from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class UserRequestV2(BaseModel):
    message: str
    state: Dict[str, Any] = Field(default_factory=dict)


class ConversationStateV2(BaseModel):
    family: Optional[str] = None
    pending_field: Optional[str] = None
    collected_fields: Dict[str, Any] = Field(default_factory=dict)
    audit: List[Dict[str, Any]] = Field(default_factory=list)


class DecisionV2(BaseModel):
    family: str
    action: str
    missing_fields: List[str] = Field(default_factory=list)
    workflow_branch: str
    evidence_refs: List[str] = Field(default_factory=list)


class FinalPayloadV2(BaseModel):
    action: str
    answer: str
    follow_up_question: Optional[str] = None
    next_step: Optional[str] = None
    state: Dict[str, Any] = Field(default_factory=dict)
    matched_family: str
    cited_sources: List[str] = Field(default_factory=list)
