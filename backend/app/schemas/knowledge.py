from pydantic import BaseModel, Field


class DocumentItem(BaseModel):
    id: int
    title: str
    file_url: str | None = None
    doc_type: str
    version: str
    status: str
    chunk_count: int = 0
    enabled: bool
    created_at: str | None = None
    updated_at: str | None = None

    model_config = {"from_attributes": True}


class FAQItem(BaseModel):
    id: int
    question: str
    answer: str
    category: str
    priority: int
    enabled: bool
    created_at: str | None = None
    updated_at: str | None = None

    model_config = {"from_attributes": True}


class FAQCreate(BaseModel):
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    category: str = Field(default="通用")
    priority: int = Field(default=0, ge=0, le=100)


class ToggleDocumentRequest(BaseModel):
    enabled: bool
