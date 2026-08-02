import json
from typing import List, Dict, Any

from app.config import get_settings
from app.dependencies import get_logger
from db.sqlite_manager import SQLiteManager


REQUIRED_FIELDS = [
    "patient_name",
    "discharge_date",
    "primary_diagnosis",
    "medications",
    "dietary_restrictions",
    "follow_up",
    "warning_signs",
    "discharge_instructions",
]


def load_patient_json(json_path: str) -> List[Dict[str, Any]]:
    with open(json_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("Patient JSON file must contain a list of patient records.")

    return data


def validate_patient_record(patient: Dict[str, Any]) -> None:
    missing_fields = [field for field in REQUIRED_FIELDS if field not in patient]
    if missing_fields:
        raise ValueError(
            f"Patient record missing required fields: {', '.join(missing_fields)}"
        )

    if not isinstance(patient["medications"], list):
        raise ValueError("Field 'medications' must be a list.")


def seed_database() -> None:
    settings = get_settings()
    logger = get_logger()

    logger.info("Seeding patient database started.")

    patients = load_patient_json(settings.patient_json_path)
    logger.info(f"Loaded {len(patients)} patient records from JSON.")

    db_manager = SQLiteManager(settings.sqlite_db_path, logger)

    db_manager.clear_patients()

    inserted_count = 0
    for patient in patients:
        validate_patient_record(patient)
        db_manager.insert_patient(patient)
        inserted_count += 1

    logger.info(f"Seeding completed successfully. Inserted {inserted_count} patients.")


if __name__ == "__main__":
    seed_database()