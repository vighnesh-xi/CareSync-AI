import json
import os
import sqlite3
from typing import List, Dict, Any


class SQLiteManager:
    def __init__(self, db_path: str, logger):
        self.db_path = db_path
        self.logger = logger
        self._ensure_db_directory()
        self._create_patients_table()

    def _ensure_db_directory(self) -> None:
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _create_patients_table(self) -> None:
        query = """
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT NOT NULL,
            discharge_date TEXT NOT NULL,
            primary_diagnosis TEXT NOT NULL,
            medications TEXT NOT NULL,
            dietary_restrictions TEXT NOT NULL,
            follow_up TEXT NOT NULL,
            warning_signs TEXT NOT NULL,
            discharge_instructions TEXT NOT NULL
        );
        """

        with self._get_connection() as conn:
            conn.execute(query)
            conn.commit()

        self.logger.info("SQLiteManager: Patients table ensured.")

    def insert_patient(self, patient: Dict[str, Any]) -> None:
        query = """
        INSERT INTO patients (
            patient_name,
            discharge_date,
            primary_diagnosis,
            medications,
            dietary_restrictions,
            follow_up,
            warning_signs,
            discharge_instructions
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """

        values = (
            patient["patient_name"],
            patient["discharge_date"],
            patient["primary_diagnosis"],
            json.dumps(patient["medications"]),
            patient["dietary_restrictions"],
            patient["follow_up"],
            patient["warning_signs"],
            patient["discharge_instructions"],
        )

        with self._get_connection() as conn:
            conn.execute(query, values)
            conn.commit()

        self.logger.info(f"SQLiteManager: Inserted patient '{patient['patient_name']}'.")

    def clear_patients(self) -> None:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM patients;")
            conn.commit()

        self.logger.info("SQLiteManager: Cleared all patient records.")

    def get_all_patients(self) -> List[Dict[str, Any]]:
        query = """
        SELECT
            patient_name,
            discharge_date,
            primary_diagnosis,
            medications,
            dietary_restrictions,
            follow_up,
            warning_signs,
            discharge_instructions
        FROM patients;
        """

        with self._get_connection() as conn:
            cursor = conn.execute(query)
            rows = cursor.fetchall()

        patients = []
        for row in rows:
            patients.append({
                "patient_name": row[0],
                "discharge_date": row[1],
                "primary_diagnosis": row[2],
                "medications": json.loads(row[3]),
                "dietary_restrictions": row[4],
                "follow_up": row[5],
                "warning_signs": row[6],
                "discharge_instructions": row[7],
            })

        self.logger.info(f"SQLiteManager: Retrieved {len(patients)} patient records.")
        return patients

    def find_patient_by_name(self, patient_name: str) -> Dict[str, Any]:
        self.logger.info(f"SQLiteManager: Looking up patient by name '{patient_name}'.")

        query = """
        SELECT
            patient_name,
            discharge_date,
            primary_diagnosis,
            medications,
            dietary_restrictions,
            follow_up,
            warning_signs,
            discharge_instructions
        FROM patients
        WHERE LOWER(patient_name) = LOWER(?);
        """

        with self._get_connection() as conn:
            cursor = conn.execute(query, (patient_name.strip(),))
            rows = cursor.fetchall()

        if len(rows) == 0:
            self.logger.warning(f"SQLiteManager: No patient found for '{patient_name}'.")
            return {
                "success": False,
                "message": f"No discharge report found for patient name: {patient_name}.",
                "data": None,
            }

        if len(rows) > 1:
            self.logger.warning(f"SQLiteManager: Multiple patients found for '{patient_name}'.")
            return {
                "success": False,
                "message": f"Multiple discharge reports found for patient name: {patient_name}. Please refine the lookup.",
                "data": None,
            }

        row = rows[0]
        patient = {
            "patient_name": row[0],
            "discharge_date": row[1],
            "primary_diagnosis": row[2],
            "medications": json.loads(row[3]),
            "dietary_restrictions": row[4],
            "follow_up": row[5],
            "warning_signs": row[6],
            "discharge_instructions": row[7],
        }

        self.logger.info(f"SQLiteManager: Patient '{patient_name}' retrieved successfully.")
        return {
            "success": True,
            "message": "Patient record retrieved successfully.",
            "data": patient,
        }