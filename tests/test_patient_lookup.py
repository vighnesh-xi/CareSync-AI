import json
import logging
import tempfile

from db.sqlite_manager import SQLiteManager


def build_logger():
    logger = logging.getLogger("test_patient_lookup")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        logger.addHandler(logging.StreamHandler())
    return logger


def sample_patient(name="John Smith"):
    return {
        "patient_name": name,
        "discharge_date": "2024-01-15",
        "primary_diagnosis": "Chronic Kidney Disease Stage 3",
        "medications": ["Lisinopril 10mg daily", "Furosemide 20mg twice daily"],
        "dietary_restrictions": "Low sodium (2g/day), fluid restriction (1.5L/day)",
        "follow_up": "Nephrology clinic in 2 weeks",
        "warning_signs": "Swelling, shortness of breath, decreased urine output",
        "discharge_instructions": "Monitor blood pressure daily, weigh yourself daily"
    }


def test_find_patient_success():
    with tempfile.NamedTemporaryFile(suffix=".db") as temp_db:
        manager = SQLiteManager(temp_db.name, build_logger())
        manager.insert_patient(sample_patient())

        result = manager.find_patient_by_name("John Smith")

        assert result["success"] is True
        assert result["data"]["patient_name"] == "John Smith"
        assert result["data"]["primary_diagnosis"] == "Chronic Kidney Disease Stage 3"


def test_find_patient_not_found():
    with tempfile.NamedTemporaryFile(suffix=".db") as temp_db:
        manager = SQLiteManager(temp_db.name, build_logger())

        result = manager.find_patient_by_name("Unknown Patient")

        assert result["success"] is False
        assert "No discharge report found" in result["message"]
        assert result["data"] is None


def test_find_patient_duplicate_names():
    with tempfile.NamedTemporaryFile(suffix=".db") as temp_db:
        manager = SQLiteManager(temp_db.name, build_logger())
        manager.insert_patient(sample_patient("Alex Johnson"))
        manager.insert_patient(sample_patient("Alex Johnson"))

        result = manager.find_patient_by_name("Alex Johnson")

        assert result["success"] is False
        assert "Multiple discharge reports found" in result["message"]
        assert result["data"] is None