from typing import Dict, Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from rag.retriever import RAGRetriever


class RAGTool:
    def __init__(self, reference_path: str, faiss_index_path: str, logger, llm):
        self.reference_path = reference_path
        self.faiss_index_path = faiss_index_path
        self.logger = logger
        self.llm = llm
        self.retriever = RAGRetriever(faiss_index_path=faiss_index_path, logger=logger)

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a clinical assistant. Answer only from the provided nephrology context. Include concise citations."),
            ("human", "Patient context:\n{patient_context}\n\nQuestion:\n{question}\n\nRetrieved reference context:\n{retrieved_context}\n\nGenerate a grounded answer.")
        ])
        self.chain = self.prompt | self.llm | StrOutputParser()

    def search(self, query: str, patient_context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        self.logger.info(f"RAGTool: Searching for query: {query}")

        retrieval_result = self.retriever.search(query, top_k=3)

        if not retrieval_result.get("success"):
            return retrieval_result

        patient_context_text = ""
        if patient_context:
            patient_context_text = (
                f"Diagnosis: {patient_context.get('primary_diagnosis', '')}\n"
                f"Medications: {', '.join(patient_context.get('medications', []))}\n"
                f"Warning signs: {patient_context.get('warning_signs', '')}\n"
                f"Instructions: {patient_context.get('discharge_instructions', '')}"
            )

        retrieved_context = "\n\n".join(retrieval_result.get("chunks", []))

        answer = self.chain.invoke({
            "patient_context": patient_context_text,
            "question": query,
            "retrieved_context": retrieved_context
        })

        return {
            "success": True,
            "answer": answer,
            "sources": retrieval_result.get("sources", []),
            "chunks": retrieval_result.get("chunks", [])
        }