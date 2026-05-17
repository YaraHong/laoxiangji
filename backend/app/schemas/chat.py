from datetime import datetime

from pydantic import BaseModel, Field


# ===== Request Schemas =====

class CreateSessionRequest(BaseModel):
    channel: str = Field(default="web", max_length=32)
    visitor_id: str | None = Field(default=None, max_length=64)


class CreateMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)


# ===== Sub-schemas =====

class CitationSchema(BaseModel):
    title: str
    url: str | None = None
    snippet: str | None = None


class LeadHintSchema(BaseModel):
    should_ask: bool = False
    message: str = "方便留一下联系方式吗？我们安排招商经理给您详细介绍加盟详情。"
    suggested_questions: list[str] = []


# ===== Response Schemas =====

class CreateSessionResponse(BaseModel):
    session_id: int
    session_no: str


class SessionInfo(BaseModel):
    id: int
    session_no: str
    channel: str
    visitor_id: str | None
    lead_id: int | None = None
    status: str
    summary: str | None
    last_message_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    message_type: str
    confidence: float | None = None
    citations: list[CitationSchema] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionDetailResponse(BaseModel):
    session: SessionInfo
    messages: list[MessageResponse]
    lead: dict | None = None


class SendMessageResponse(BaseModel):
    message_id: int
    answer: str
    citations: list[CitationSchema]
    lead_hint: LeadHintSchema
