from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Post Discharge Medical AI Assistant"
    app_version: str = "1.0.0"

    sqlite_db_path: str = "db/patients.db"
    patient_json_path: str = "data/patients/patient_reports.json"
    nephrology_reference_path: str = "data/references/nephrology_reference.txt"
    faiss_index_path: str = "vector_store/faiss_index"

    log_file_path: str = "logs/system.log"

    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"
    temperature: float = 0.2

    receptionist_prompt_path: str = "prompts/receptionist_prompt.txt"
    clinical_prompt_path: str = "prompts/clinical_prompt.txt"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


def get_settings() -> Settings:
    return Settings()