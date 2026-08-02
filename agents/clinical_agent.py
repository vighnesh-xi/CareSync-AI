from typing import Dict, Any, List

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


class ClinicalAgent:
    DISCLAIMER = (
        "\n\nMedical Disclaimer: This is an AI assistant for educational purposes only. "
        "Always consult healthcare professionals for medical advice."
    )

    def __init__(self, rag_tool, web_search_tool, logger, llm, prompt_text: str):
        self.rag_tool = rag_tool
        self.web_search_tool = web_search_tool
        self.logger = logger
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_text),
            ("human", "{input_text}")
        ])
        self.chain = self.prompt | self.llm | StrOutputParser()

    def handle_medical_query(self, user_query: str, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.info(
            f"ClinicalAgent: Received medical query for patient '{patient_data.get('patient_name', 'unknown')}'."
        )

        rag_result = self.rag_tool.search(user_query, patient_data)

        if rag_result.get("success") and rag_result.get("sources"):
            input_text = (
                f"Patient context:\n{patient_data}\n\n"
                f"User medical query:\n{user_query}\n\n"
                f"RAG answer draft:\n{rag_result.get('answer', '')}\n\n"
                f"Sources:\n{rag_result.get('sources', [])}\n\n"
                f"Generate the final clinical answer with citation mention and safe tone."
            )

            final_answer = self.chain.invoke({"input_text": input_text})

            return {
                "success": True,
                "agent": "clinical",
                "response": final_answer + self.DISCLAIMER,
                "source_type": "reference_material",
                "citations": rag_result.get("sources", []),
            }

        web_result = self.web_search_tool.search(user_query)

        if web_result.get("success"):
            input_text = (
                f"Patient context:\n{patient_data}\n\n"
                f"User medical query:\n{user_query}\n\n"
                f"Web search summary:\n{web_result.get('summary', '')}\n\n"
                f"Web sources:\n{web_result.get('sources', [])}\n\n"
                f"Generate a concise clinical response that clearly states the information came from web search."
            )

            final_answer = self.chain.invoke({"input_text": input_text})

            return {
                "success": True,
                "agent": "clinical",
                "response": final_answer + self.DISCLAIMER,
                "source_type": "web_search",
                "citations": web_result.get("sources", []),
            }

        return {
            "success": False,
            "agent": "clinical",
            "response": (
                "I couldn't retrieve enough reliable information to answer that safely right now."
                + self.DISCLAIMER
            ),
            "source_type": "none",
            "citations": [],
        }