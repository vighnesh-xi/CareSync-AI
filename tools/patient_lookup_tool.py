from db.sqlite_manager import SQLiteManager


class PatientLookupTool:
    def __init__(self, sqlite_db_path: str, patient_json_path: str, logger):
        self.sqlite_db_path = sqlite_db_path
        self.patient_json_path = patient_json_path
        self.logger = logger
        self.db_manager = SQLiteManager(sqlite_db_path, logger)

    def get_patient_by_name(self, patient_name: str):
        self.logger.info(f"PatientLookupTool: Searching for patient '{patient_name}'.")

        if not patient_name or not patient_name.strip():
            self.logger.warning("PatientLookupTool: Empty patient name provided.")
            return {
                "success": False,
                "message": "Please provide a valid patient name.",
                "data": None,
            }

        result = self.db_manager.find_patient_by_name(patient_name.strip())

        self.logger.info(
            f"PatientLookupTool: Lookup result for '{patient_name}' -> success={result['success']}"
        )
        return result