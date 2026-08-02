from typing import Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.dependencies import get_orchestrator, get_logger
from app.schemas import (
    ChatRequest,
    ChatResponse,
    CitationItem,
    HealthResponse,
    SessionState,
)

settings = get_settings()
logger = get_logger()
orchestrator = get_orchestrator()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="POC multi-agent AI system for post-discharge nephrology patient support."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_store: Dict[str, dict] = {}


@app.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        version=settings.app_version
    )


@app.post("/start-session")
def start_session(session_id: str):
    logger.info(f"API: Starting session '{session_id}'.")

    initial_state = orchestrator.start_conversation()

    session_store[session_id] = {
        "current_agent": initial_state["current_agent"],
        "patient_verified": initial_state["patient_verified"],
        "patient_data": initial_state["patient_data"],
    }

    return {
        "session_id": session_id,
        "agent": initial_state["current_agent"],
        "response": initial_state["response"],
        "patient_verified": initial_state["patient_verified"],
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    logger.info(f"API: Received chat message for session '{request.session_id}'.")

    if request.session_id not in session_store:
        raise HTTPException(status_code=404, detail="Session not found. Start a session first.")

    session_state = session_store[request.session_id]

    try:
        result = orchestrator.handle_message(
            user_message=request.message,
            session_state=session_state
        )

        session_store[request.session_id] = {
            "current_agent": result["current_agent"],
            "patient_verified": result["patient_verified"],
            "patient_data": result["patient_data"],
        }

        patient_name = None
        if result.get("patient_data"):
            patient_name = result["patient_data"].get("patient_name")

        citations = []
        for item in result.get("citations", []):
            if isinstance(item, dict):
                citations.append(
                    CitationItem(
                        title=item.get("title", "Untitled Source"),
                        source=item.get("source", item.get("url", "Unknown Source"))
                    )
                )

        return ChatResponse(
            session_id=request.session_id,
            agent=result["current_agent"],
            response=result["response"],
            patient_verified=result["patient_verified"],
            patient_name=patient_name,
            source_type=result.get("source_type"),
            citations=citations,
        )

    except Exception as exc:
        logger.exception(f"API: Error while processing chat for session '{request.session_id}': {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/")
def root():
    return {
        "message": "Post Discharge Medical AI Assistant API is running.",
        "docs": "/docs"
    }