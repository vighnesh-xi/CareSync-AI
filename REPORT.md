# CareSync AI – Post Discharge Medical AI Assistant

## 1. Overview

CareSync AI is a multi-agent post-discharge assistant for patients with Chronic Kidney Disease (CKD). It combines a Receptionist Agent and a Clinical Agent to support name-based patient lookup, discharge-report review, symptom triage, and educational clinical guidance using Retrieval-Augmented Generation (RAG) over nephrology reference materials, plus web-search fallback for recent research queries.

The system is implemented as a FastAPI backend with a Streamlit frontend, backed by SQLite for patient data and FAISS for vector search over nephrology reference text. All data used in the POC is synthetic; no real patient information is stored or processed.

---

## 2. Architecture Justification

### 2.1 LLM Selection

CareSync AI uses the Groq API via the `ChatGroq` integration in LangChain for both agents. A shared chat model instance (e.g., `llama-3.1-8b-instant`) is configured with a low temperature to provide consistent, conservative, and deterministic outputs suitable for a medical educational assistant.

Using Groq + LangChain was chosen because:

- It offers fast inference suitable for interactive chat.
- It avoids direct dependency on OpenAI while still supporting modern LLMs.
- LangChain makes it straightforward to compose tools, agents, and RAG pipelines.

### 2.2 Vector Database and Embeddings

For RAG, the system uses FAISS as the vector store and Sentence-Transformers embeddings (e.g., `all-MiniLM-L6-v2`) to index and search the nephrology reference text.

FAISS was selected because:

- It is lightweight and easy to integrate for a single reference corpus.
- It supports fast similarity search even on modest hardware.

Sentence-Transformers were chosen because:

- They provide high-quality semantic embeddings without external API calls.
- They are well supported in Python and integrate cleanly with LangChain.

### 2.3 RAG Implementation

The nephrology reference material is loaded from text, chunked into manageable segments, embedded, and indexed in FAISS. When the Clinical Agent receives a medical question that is suitable for reference-based answering (e.g., "What is chronic kidney disease?", "What does leg swelling mean in CKD?"), it:

1. Uses a retriever to query the FAISS index for the top relevant chunks.
2. Passes the question and retrieved context to the LLM.
3. Generates an answer grounded in the reference material.
4. Attaches citations to the response, including chunk titles and source file name.
5. Labels the response with `source_type = reference_material`.

This pipeline ensures that standard clinical guidance is anchored in the nephrology reference rather than pure model hallucination.

### 2.4 Multi-Agent Orchestration

The system implements a custom two-agent architecture using LangChain and an Orchestrator class:

- **Receptionist Agent**
  - Asks the patient for their name.
  - Uses an explicit patient data retrieval tool to query SQLite.
  - Retrieves the patient's discharge report and summarizes key fields (diagnosis, medications, follow-up date, warning signs, instructions).
  - Asks follow-up questions based on the discharge information.
  - Detects medical/symptom/"worried" style queries and routes them to the Clinical Agent.

- **Clinical Agent**
  - Handles medical questions and clinical advice in an educational manner.
  - Uses RAG over the nephrology reference book to answer CKD-related questions.
  - Uses a web search tool when queries are outside the reference scope or explicitly ask for "latest" or "recent" research.
  - Provides citations and clearly indicates whether the answer is based on reference material or web search.
  - Logs patient interactions, including retrieval results.

The **Agent Orchestrator** maintains session state (including `patient_verified` and cached patient data) and decides, for each message, whether to:

- Send it to the Receptionist Agent (name intake, discharge follow-up, non-medical logistics).
- Send it to the Clinical Agent (symptoms, medications, research questions).

This orchestrator ensures clean agent handoff and matches the expected workflow described in the assignment.

### 2.5 Web Search Integration

CareSync AI integrates a web search tool (e.g., DuckDuckGo search via `duckduckgo-search`) into the Clinical Agent workflow. The Clinical Agent uses web search when:

- The query includes freshness cues such as "latest", "recent", "new research", "guideline update".
- The nephrology reference RAG retrieval either does not return adequate context or the question is clearly about up-to-date literature (e.g., SGLT2 inhibitors).

For web-search answers, the Clinical Agent:

1. Calls the web search tool with the user query.
2. Selects a small set of relevant, high-level sources.
3. Summarizes the findings into an educational answer.
4. Includes source titles and domains in the citations.
5. Labels the response with `source_type = web_search`.

This behavior matches the assignment requirement to "Clearly indicate when information comes from web search vs. reference materials" and to "Handle fallback when specialized information is needed".

### 2.6 Patient Data Retrieval

Patient data is stored in SQLite, seeded from a JSON file containing **25+ dummy discharge reports**. A typical patient record includes:

- `patient_name`: e.g., "John Smith"
- `discharge_date`: e.g., `2024-01-15`
- `primary_diagnosis`: e.g., "Chronic Kidney Disease Stage 3"
- `medications`, `dietary_restrictions`, `follow_up`, `warning_signs`, `discharge_instructions`

The dedicated Patient Data Retrieval Tool:

- Performs lookup by patient name.
- Returns structured discharge report data to the Receptionist Agent.
- Handles error cases:
  - **Patient not found** (e.g., "Jane Smith").
  - **Multiple patients with the same name** (e.g., multiple "Alex Johnson" records).
- Logs all database access attempts and outcomes.

This tool fulfills the "Patient Data Retrieval Tool" requirements in the assignment.

### 2.7 Logging Implementation

A centralized logger (`medical_ai_assistant`) writes logs to a file (e.g., `logs/system.log`) with timestamps and context fields. Logged events include:

- Session start / end.
- User messages received by the API.
- Agent decisions in the Orchestrator (which agent was invoked, whether patient is verified).
- Patient lookup attempts and results (success, not found, multiple matches).
- RAG retrieval calls and number of chunks retrieved.
- Web search calls and whether web fallback was used.
- Errors in backend communication or model calls.

This logging satisfies the assignment requirement for a "comprehensive logging system" showing complete system flow.

---

## 3. System Workflow

This section documents how CareSync AI matches the expected workflow from the assignment.

### 3.1 Initial Interaction

1. **System greeting**
   - The Receptionist Agent welcomes the user: 
     > "Hello! I'm your post-discharge care assistant. What's your name?"

2. **Patient provides name**
   - Example: `John Smith`.

3. **Patient lookup and discharge summary**
   - The Receptionist Agent calls the Patient Data Retrieval Tool.
   - SQLite returns John Smith's discharge record.
   - The Receptionist Agent summarizes it, e.g.: 
     > "Hi John! I found your discharge report from January 15th, 2024 for Chronic Kidney Disease Stage 3. You're currently taking Lisinopril 10mg daily and Furosemide 20mg twice daily, with a nephrology follow-up in two weeks. How are you feeling today? Are you following your medication schedule?"

This directly mirrors the example workflow in the assignment.

### 3.2 Medical Query Routing

4. **Patient asks a symptom question**
   - Example: `I'm having swelling in my legs. Should I be worried?`

5. **Receptionist Agent detects medical concern and hands off**
   - The Receptionist Agent classifies this as a medical/symptom query and responds:
     > "This sounds like a medical concern. Let me connect you with our Clinical AI Agent."

6. **Clinical Agent responds using RAG**
   - The Clinical Agent receives the query and patient context.
   - It uses the RAG pipeline to retrieve relevant nephrology reference chunks (e.g., warning signs, edema in CKD Stage 3).
   - It generates an educational clinical answer, such as:
     > "Based on your CKD diagnosis and nephrology guidelines, leg swelling can indicate fluid retention..." 
   - The response includes citations and `source_type = reference_material`.

This matches the "Medical Query Routing" section of the expected workflow.

### 3.3 Web Search Fallback

7. **Patient asks for latest research**
   - Example: `What's the latest research on SGLT2 inhibitors for kidney disease?`

8. **Clinical Agent uses web search fallback**
   - The Clinical Agent identifies the query as research/freshness-oriented.
   - It invokes the web search tool with the SGLT2/CKD query.
   - It synthesizes a summary of recent findings from search results.
   - It responds along the lines of:
     > "This requires recent information. Let me search for you... According to recent medical literature, SGLT2 inhibitors have shown renoprotective effects and reduced progression of CKD in multiple trials..." 
   - The response lists sources (e.g., trial names, journals) and labels `source_type = web_search`.

This behavior aligns with the "Web Search Fallback Example" in the assignment.

### 3.4 Error Handling in Patient Lookup

The system also demonstrates:

- **Patient not found**
  - Input: `Jane Smith`.
  - Receptionist Agent: 
    > "No discharge report found for patient name: Jane Smith."

- **Multiple patients with same name**
  - Input: `Alex Johnson`.
  - Receptionist Agent: 
    > "Multiple discharge reports found for patient name: Alex Johnson. Please refine the lookup."

These cases satisfy the error-handling requirements for the patient data retrieval tool.

---

## 4. UI and UX Design

The frontend is built with Streamlit and intentionally kept simple, focusing on clarity and demo readiness.

Key UI elements:

- **Header**
  - A compact header block with a "PD" monogram mark and title/subtitle.
  - Communicates the app's purpose: "Post Discharge Medical AI Assistant" and "Multi-agent POC for post-discharge nephrology support".

- **Sidebar**
  - "System Info" section listing:
    - Frontend: Streamlit
    - Backend: FastAPI
    - Agents: Receptionist + Clinical
    - Database: SQLite
    - Vector Search: FAISS
    - Embeddings: Sentence-Transformers
  - "Medical Disclaimer" section showing:
    - "This is an AI assistant for educational purposes only."
    - "Always consult healthcare professionals for medical advice."
  - A "Start New Session" button to reset session state.

- **Main chat area**
  - Agent-specific badges (Receptionist Agent, Clinical Agent) displayed above responses.
  - Chat bubbles with clear separation between user and assistant messages.
  - Source/citation cards under Clinical Agent responses, with color-coded tags:
    - Green for `Reference Material`.
    - Amber for `Web Search`.

The design intentionally avoids heavy graphics and prioritizes legibility and clear agent/source distinctions, in line with the assignment's "Keep It Simple" and "Basic UI is perfectly acceptable" guidance.

---

## 5. Requirements Mapping

This section maps CareSync AI features to the assignment checklist.

- **25+ dummy patient reports created**
  - Implemented via a JSON dataset seeded into SQLite, all synthetic CKD discharge reports.

- **Nephrology reference materials processed**
  - Reference text is chunked, embedded, and indexed in FAISS; Clinical Agent uses it for CKD guidance.

- **Receptionist Agent implemented**
  - Handles name intake, discharge retrieval, follow-up questions, and routing of medical queries.

- **Clinical AI Agent with RAG implemented**
  - Answers CKD-related questions using RAG and provides citations from nephrology reference material.

- **Patient data retrieval tool implemented**
  - Dedicated SQLite manager with lookup by name, structured discharge data, and error handling (not found, multiple matches).

- **Web search tool integration**
  - Web search tool used by Clinical Agent for recent/specialized queries; responses labeled as web-based.

- **Comprehensive logging system**
  - Central logger records interactions, handoffs, retrievals, web search, and errors with timestamps.

- **Simple web interface working**
  - Streamlit UI with chat, sidebar, disclaimers, and session controls.

- **Agent handoff mechanism functional**
  - Orchestrator routes symptom queries from Receptionist to Clinical and maintains patient verification state.

- **GitHub repo with clean code**
  - Project organized into backend (`app/`), agents (`agents/`), tools (`tools/`), data (`data/`), logs (`logs/`), and frontend (`frontend/`).

- **Brief report with architecture justification**
  - Satisfied by this `report.md`.

- **Demo video recorded**
  - To be produced as a short walkthrough of the key flows (initial intake, symptom routing, RAG, web fallback, error cases).

- **All code commented and documented**
  - Core modules include docstrings and inline comments for clarity.

---

## 6. Limitations and Future Work

### 6.1 Limitations

- **Single specialty (nephrology/CKD)**
  - The system currently focuses only on CKD and nephrology. Other conditions and specialties are not modeled.

- **Educational assistant only**
  - The Clinical Agent is explicitly framed as an educational AI assistant and does not provide personalized medical advice or diagnosis.

- **No authentication or clinician view**
  - There is no login system or separate clinician dashboard; the app is a simple patient-facing chat.

- **Reference corpus scope**
  - RAG is limited to a single nephrology reference text. Additional guidelines or textbooks would improve coverage.

- **Web search quality**
  - Web search uses a general search engine; it is not restricted to curated medical databases, which may affect source quality.

### 6.2 Future Improvements

- **Multi-specialty expansion**
  - Extend the architecture to support additional specialties (e.g., cardiology, endocrinology) with separate reference corpora.

- **Risk stratification and alerts**
  - Implement rules to highlight high-risk symptom patterns and suggest contacting a healthcare provider more urgently.

- **Clinician-facing tools**
  - Add a clinician dashboard to review patient interactions, annotate answers, and adjust prompts.

- **Better medical search integration**
  - Integrate with more specialized medical search APIs or databases (e.g., PubMed, guideline repositories) for higher-quality web-based evidence.

- **Patient personalization**
  - Use more detailed patient context (e.g., comorbidities, lab trends) to tailor educational responses while still keeping the system non-diagnostic.

CareSync AI demonstrates the core capabilities required by the GenAI Intern assignment: multi-agent orchestration, RAG, patient data retrieval, web search fallback, logging, and a simple but thoughtful UI. It provides a solid foundation for future extensions into richer post-discharge care workflows.