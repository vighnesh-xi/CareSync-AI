import logging
import os
from functools import lru_cache

from langchain_groq import ChatGroq

from app.config import get_settings
from agents.receptionist_agent import ReceptionistAgent
from agents.clinical_agent import ClinicalAgent
from agents.orchestrator import AgentOrchestrator
from tools.patient_lookup_tool import PatientLookupTool
from tools.rag_tool import RAGTool
from tools.web_search_tool import WebSearchTool


def setup_logger() -> logging.Logger:
    settings = get_settings()

    log_dir = os.path.dirname(settings.log_file_path)
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger("medical_ai_assistant")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

        file_handler = logging.FileHandler(settings.log_file_path, encoding="utf-8")
        file_handler.setFormatter(formatter)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger


@lru_cache
def get_logger() -> logging.Logger:
    return setup_logger()


def load_prompt(prompt_path: str) -> str:
    with open(prompt_path, "r", encoding="utf-8") as file:
        return file.read()


@lru_cache
def get_llm() -> ChatGroq:
    settings = get_settings()
    return ChatGroq(
        model=settings.groq_model,
        temperature=settings.temperature,
        groq_api_key=settings.groq_api_key
    )


@lru_cache
def get_patient_lookup_tool() -> PatientLookupTool:
    settings = get_settings()
    return PatientLookupTool(
        sqlite_db_path=settings.sqlite_db_path,
        patient_json_path=settings.patient_json_path,
        logger=get_logger()
    )


@lru_cache
def get_rag_tool() -> RAGTool:
    settings = get_settings()
    return RAGTool(
        reference_path=settings.nephrology_reference_path,
        faiss_index_path=settings.faiss_index_path,
        logger=get_logger(),
        llm=get_llm()
    )


@lru_cache
def get_web_search_tool() -> WebSearchTool:
    return WebSearchTool(logger=get_logger())


@lru_cache
def get_receptionist_agent() -> ReceptionistAgent:
    settings = get_settings()
    return ReceptionistAgent(
        patient_lookup_tool=get_patient_lookup_tool(),
        logger=get_logger(),
        llm=get_llm(),
        prompt_text=load_prompt(settings.receptionist_prompt_path)
    )


@lru_cache
def get_clinical_agent() -> ClinicalAgent:
    settings = get_settings()
    return ClinicalAgent(
        rag_tool=get_rag_tool(),
        web_search_tool=get_web_search_tool(),
        logger=get_logger(),
        llm=get_llm(),
        prompt_text=load_prompt(settings.clinical_prompt_path)
    )


@lru_cache
def get_orchestrator() -> AgentOrchestrator:
    return AgentOrchestrator(
        receptionist_agent=get_receptionist_agent(),
        clinical_agent=get_clinical_agent(),
        logger=get_logger()
    )