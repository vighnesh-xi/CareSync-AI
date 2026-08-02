# CareSync AI

**Post-Discharge Medical AI Assistant for Chronic Kidney Disease (CKD)**

CareSync AI is a multi-agent conversational assistant that supports CKD patients after hospital discharge. It helps patients review their discharge report, answers clinical questions using nephrology reference materials (RAG), and falls back to web search for recent or specialized queries.

> **Disclaimer:** This is an AI assistant for **educational purposes only**. It does **not** provide medical advice, diagnosis, or treatment. Always consult qualified healthcare professionals for medical decisions.

---

## Features

- **Multi-Agent Architecture**
  - **Receptionist Agent:** Greets patients, verifies identity, retrieves discharge reports, and routes medical queries.
  - **Clinical Agent:** Answers CKD-related questions using RAG over nephrology references and provides cited, educational responses.

- **Patient Data Retrieval**
  - Lookup by patient name from a SQLite database seeded with 25+ synthetic CKD discharge reports.
  - Handles "not found" and "multiple matches" gracefully.

- **RAG-Powered Clinical Answers**
  - Uses FAISS + Sentence-Transformers embeddings to retrieve relevant nephrology reference chunks.
  - Responses include citations and indicate `source_type = reference_material`.

- **Web Search Fallback**
  - For queries about recent research or topics outside the reference corpus, the Clinical Agent uses web search.
  - Responses include source titles/domains and indicate `source_type = web_search`.

- **Comprehensive Logging**
  - Centralized logging of all interactions, agent handoffs, retrievals, web searches, and errors.

- **Simple, Clean UI**
  - Streamlit frontend with:
    - Clear agent badges (Receptionist vs. Clinical)
    - Source/citation cards with color-coded tags
    - Sidebar with system info and medical disclaimer

---

## Tech Stack

- **Frontend:** [Streamlit](https://streamlit.io/)
- **Backend:** [FastAPI](https://fastapi.tiangolo.com/)
- **Agents & Orchestration:** [LangChain](https://python.langchain.com/)
- **LLM:** Groq API via `ChatGroq` (e.g., `llama-3.1-8b-instant`)
- **Database:** SQLite (patient discharge reports)
- **Vector Search:** FAISS
- **Embeddings:** Sentence-Transformers (`all-MiniLM-L6-v2`)
- **Web Search:** DuckDuckGo search (`duckduckgo-search`)
- **Logging:** Python `logging` module (file-based)

---

## Project Structure

```text
CareSync-AI/
├─ app/                  # FastAPI backend
├─ agents/               # Receptionist and Clinical agents
├─ tools/                # Patient data tool, web search tool, etc.
├─ data/                 # Synthetic patient data (JSON), nephrology reference text
├─ logs/                 # Log files
├─ frontend/             # Streamlit UI
│  ├─ streamlit_app.py
│  └─ .streamlit/
│     └─ config.toml
├─ report.md             # Detailed architecture and requirements mapping
└─ README.md
```

---

## Quickstart

### Prerequisites

- Python 3.10+
- `pip`, `virtualenv` (or `conda`)
- A Groq API key
- Git

### 1. Clone the repo

```bash
git clone https://github.com/vighnesh-xi/CareSync-AI.git
cd CareSync-AI
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

(If you don't have `requirements.txt` yet, create it with all packages you use: `fastapi`, `uvicorn`, `langchain`, `langchain-groq`, `sentence-transformers`, `faiss-cpu`, `duckduckgo-search`, `streamlit`, etc.)

### 4. Set environment variables

Create a `.env` file in the project root:

```bash
GROQ_API_KEY=your_groq_api_key_here
```

Adjust variable names if your code uses different ones.

### 5. Seed the database (if needed)

If your project includes a script to seed SQLite from the JSON patient data:

```bash
python -m app.db_manager  # or your equivalent seeding command
```

Modify this to match your actual seeding mechanism.

### 6. Run the backend

From the project root:

```bash
uvicorn app.main:app --reload
```

Adjust the module path if your FastAPI app is elsewhere (e.g., `app.api:app`).

### 7. Run the Streamlit frontend

In a new terminal (with the same venv activated):

```bash
streamlit run frontend/streamlit_app.py
```

Open the URL shown in the terminal (usually `http://localhost:8501`) in your browser.

---

## Usage Flow

1. **Greeting**
   - Receptionist Agent: "Hello! I'm your post-discharge care assistant. What's your name?"

2. **Patient provides name**
   - Example: `John Smith`
   - System looks up the discharge report in SQLite.

3. **Discharge summary**
   - Receptionist Agent summarizes diagnosis, medications, follow-up, and warning signs.
   - Asks how the patient is feeling and about medication adherence.

4. **Medical/symptom query**
   - Example: "I'm having swelling in my legs. Should I be worried?"
   - Receptionist Agent detects medical concern and hands off to Clinical Agent.
   - Clinical Agent answers using RAG over nephrology reference, with citations.

5. **Research / latest info query**
   - Example: "What's the latest research on SGLT2 inhibitors for kidney disease?"
   - Clinical Agent uses web search and returns a summarized, cited answer labeled as web-based.

---

## Architecture & Design

For a detailed explanation of:

- LLM and vector DB choices
- RAG pipeline design
- Multi-agent orchestration logic
- Web search fallback behavior
- Logging implementation
- Mapping to assignment requirements

see **[REPORT.md](REPORT.md)**.

---

## Limitations

- Single specialty focus: CKD / nephrology only.
- Educational assistant; not a substitute for professional medical care.
- Reference corpus limited to a single nephrology text.
- Web search uses a general engine, not curated medical databases.

---

## Future Work

- Expand to multiple specialties (cardiology, endocrinology, etc.).
- Add risk stratification and escalation rules for high-risk symptom patterns.
- Build a clinician dashboard to review patient interactions.
- Integrate with specialized medical literature APIs (e.g., PubMed, guidelines).
- Enrich patient context (comorbidities, labs) for more personalized education.

---

## Contributing

This project is primarily a proof-of-concept for a GenAI internship assignment, but contributions and ideas are welcome.

### How to contribute

- **Fork the repo** and create a feature branch:

  ```bash
  git checkout -b feature/your-feature-name
  ```

- **Make your changes** (new features, bug fixes, documentation improvements, etc.).
- **Test locally**:
  - Ensure the backend starts without errors.
  - Verify the frontend chat flow still works.
  - Check that logs are written as expected.
- **Commit with clear messages** describing what you changed and why.
- **Open a pull request** against the `main` branch with:
  - A short description of the change.
  - Any relevant screenshots or example conversations (if UI/logic changed).

### What to contribute

- Bug fixes and stability improvements.
- New tools or agents (e.g., medication-reminder agent, diet assistant).
- Better RAG strategies (chunking, re-ranking, multi-hop retrieval).
- Improved logging, monitoring, or evaluation scripts.
- Documentation enhancements (examples, tutorials, architecture diagrams).
