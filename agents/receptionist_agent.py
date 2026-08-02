from typing import Dict, Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


class ReceptionistAgent:
    def __init__(self, patient_lookup_tool, logger, llm, prompt_text: str):
        self.patient_lookup_tool = patient_lookup_tool
        self.logger = logger
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_text),
            ("human", "{input_text}")
        ])
        self.chain = self.prompt | self.llm | StrOutputParser()

    def welcome_message(self) -> str:
        message = "Hello! I'm your post-discharge care assistant. What's your name?"
        self.logger.info("ReceptionistAgent: Sent welcome message.")
        return message

    def handle_name_input(self, patient_name: str) -> Dict[str, Any]:
        self.logger.info(f"ReceptionistAgent: Looking up patient '{patient_name}'.")
        result = self.patient_lookup_tool.get_patient_by_name(patient_name)

        if not result["success"]:
            return {
                "success": False,
                "agent": "receptionist",
                "response": result["message"],
                "patient_data": None,
                "route_to": None,
            }

        patient = result["data"]

        input_text = (
            f"Patient name provided: {patient_name}\n"
            f"Retrieved discharge report:\n"
            f"- Patient: {patient['patient_name']}\n"
            f"- Discharge date: {patient['discharge_date']}\n"
            f"- Diagnosis: {patient['primary_diagnosis']}\n"
            f"- Medications: {', '.join(patient['medications'])}\n"
            f"- Follow up: {patient['follow_up']}\n"
            f"- Warning signs: {patient['warning_signs']}\n"
            f"- Instructions: {patient['discharge_instructions']}\n"
            f"Generate a short receptionist response that confirms retrieval and asks a follow-up question."
        )

        response = self.chain.invoke({"input_text": input_text})

        return {
            "success": True,
            "agent": "receptionist",
            "response": response,
            "patient_data": patient,
            "route_to": None,
        }

    def process_followup(self, user_message: str, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.info("ReceptionistAgent: Processing follow-up message.")

        if self._is_medical_query(user_message):
            return {
                "success": True,
                "agent": "receptionist",
                "response": "This sounds like a medical concern. Let me connect you with our Clinical AI Agent.",
                "patient_data": patient_data,
                "route_to": "clinical",
            }

        input_text = (
            f"Patient message: {user_message}\n"
            f"Patient discharge context:\n"
            f"- Diagnosis: {patient_data.get('primary_diagnosis', '')}\n"
            f"- Medications: {', '.join(patient_data.get('medications', []))}\n"
            f"- Follow up: {patient_data.get('follow_up', '')}\n"
            f"- Warning signs: {patient_data.get('warning_signs', '')}\n"
            f"Generate a short receptionist-style follow-up response without giving medical advice."
        )

        response = self.chain.invoke({"input_text": input_text})

        return {
            "success": True,
            "agent": "receptionist",
            "response": response,
            "patient_data": patient_data,
            "route_to": None,
        }

    def _is_medical_query(self, text: str) -> bool:
        medical_keywords = [
            "pain", "swelling", "fever", "vomiting", "dizziness", "weakness",
            "breathing", "urine", "blood pressure", "medication", "dose",
            "side effect", "worried", "symptom", "shortness of breath",
            "research", "latest", "treatment", "disease", "sglt2", "kidney"
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in medical_keywords)