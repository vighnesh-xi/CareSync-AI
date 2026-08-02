from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Unique session identifier")
    message: str = Field(..., min_length=1, description="User input message")


class CitationItem(BaseModel):
    title: str
    source: str


class ChatResponse(BaseModel):
    session_id: str
    agent: str
    response: str
    patient_verified: bool
    patient_name: Optional[str] = None
    source_type: Optional[str] = None
    citations: List[CitationItem] = Field(default_factory=list)


class PatientRecord(BaseModel):
    patient_name: str
    discharge_date: str
    primary_diagnosis: str
    medications: List[str]
    dietary_restrictions: str
    follow_up: str
    warning_signs: str
    discharge_instructions: str


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str


class ErrorResponse(BaseModel):
    detail: str


class SessionState(BaseModel):
    current_agent: str = "receptionist"
    patient_verified: bool = False
    patient_data: Optional[Dict[str, Any]] = None