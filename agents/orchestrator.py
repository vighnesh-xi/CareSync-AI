from typing import Dict, Any


class AgentOrchestrator:
    def __init__(self, receptionist_agent, clinical_agent, logger):
        self.receptionist_agent = receptionist_agent
        self.clinical_agent = clinical_agent
        self.logger = logger

    def start_conversation(self):
        return {
            "response": self.receptionist_agent.welcome_message(),
            "current_agent": "receptionist",
            "patient_data": None,
            "patient_verified": False,
            "citations": [],
            "source_type": None,
        }

    def handle_message(self, user_message: str, session_state: dict):
        self.logger.info(f"Orchestrator: Received user message: {user_message}")

        patient_verified = session_state.get("patient_verified", False)
        patient_data = session_state.get("patient_data")

        if not patient_verified:
            self.logger.info("Orchestrator: No verified patient yet. Sending to ReceptionistAgent.")
            result = self.receptionist_agent.handle_name_input(user_message)

            if result.get("success") and result.get("patient_data"):
                return {
                    "response": result["response"],
                    "current_agent": "receptionist",
                    "patient_data": result["patient_data"],
                    "patient_verified": True,
                    "citations": [],
                    "source_type": None,
                }

            return {
                "response": result["response"],
                "current_agent": "receptionist",
                "patient_data": None,
                "patient_verified": False,
                "citations": [],
                "source_type": None,
            }

        self.logger.info("Orchestrator: Patient verified. Checking whether query should go to clinical.")
        receptionist_result = self.receptionist_agent.process_followup(user_message, patient_data)

        if receptionist_result.get("route_to") == "clinical":
            self.logger.info("Orchestrator: Routing to ClinicalAgent.")
            clinical_result = self.clinical_agent.handle_medical_query(user_message, patient_data)

            return {
                "response": clinical_result["response"],
                "current_agent": "clinical",
                "patient_data": patient_data,
                "patient_verified": True,
                "citations": clinical_result.get("citations", []),
                "source_type": clinical_result.get("source_type"),
            }

        return {
            "response": receptionist_result["response"],
            "current_agent": "receptionist",
            "patient_data": patient_data,
            "patient_verified": True,
            "citations": [],
            "source_type": None,
        }