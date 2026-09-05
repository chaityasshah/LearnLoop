# Phase 5A: Study Buddy Integration Audit

## 1. Study Buddy Architecture
Study Buddy is currently built as a standalone **monolithic Streamlit application**. It tightly couples the user interface, session state management, and the AI/RAG processing pipeline into a single file. 
- **Runtime:** Python / Streamlit
- **State Management:** In-memory via `st.session_state` (stores LLM instances, FAISS vectorstores, and chat history).
- **Database:** None (ephemeral local FAISS vectorstore).

## 2. Complete Repository Structure
Repository located at: `study-buddy/`
- `rag.py` (30KB) - The single entry point containing all UI and LLM logic.
- `requirements.txt` - Python dependencies.
- `README.md`, `LICENSE`, `.gitignore`, `.devcontainer/`

## 3. Exact Query Flow
When a student asks: *"I don't understand equivalent fractions."*
1. **UI/Input:** The user types the query into `st.chat_input` and it is appended to `st.session_state.messages`.
2. **Preprocessing:** `detect_question_paper_request(prompt)` checks if the user is asking to generate a test (returns `False`).
3. **Vector Retrieval:** `st.session_state.retriever.invoke(prompt)` is called to fetch the top 4 chunks from the FAISS vectorstore.
4. **Context Preparation:** The retrieved documents are formatted into a single string (`format_docs`), and the last 6 messages of `st.session_state.chat_history` are formatted.
5. **Prompt Construction:** A `ChatPromptTemplate` is populated with the `{context}`, `{chat_history}`, and the `{question}`.
6. **LLM Execution:** The LangChain Expression Language (LCEL) chain (`rag_chain`) sends the prompt to the `ChatGroq` instance (`llama-3.3-70b-versatile`).
7. **Response Generation:** `StrOutputParser()` extracts the raw string from the LLM's output.
8. **UI Rendering:** The string is appended to `st.session_state.chat_history` and rendered to the screen using `st.markdown(answer)`. Optionally, sources are rendered in an expander.

## 4. RAG Pipeline
- **Document Ingestion:** `st.file_uploader` → `PyPDFLoader`/`TextLoader` → `RecursiveCharacterTextSplitter` (chunk=3000, overlap=200).
- **Embeddings:** `HuggingFaceEmbeddings` using the `sentence-transformers/all-MiniLM-L6-v2` model.
- **Vector Store:** Local `FAISS` instance (`FAISS.from_documents`).
- **Retriever:** Standard vectorstore retriever (`k=4`).
- **LLM:** `ChatGroq` using `llama-3.3-70b-versatile` (Temperature: 0.7).

## 5. Current Interface/API
**None.** Study Buddy does not expose any HTTP endpoints, REST APIs, or importable Python service classes. Everything is executed procedurally within the Streamlit event loop.

## 6. Recommended Integration Boundary
**Option 2 (Python Service Porting / Refactor)** is the cleanest approach.
Because Study Buddy uses `st.session_state` heavily, it cannot be imported directly into FastAPI, and running it as a separate API microservice would require rewriting it anyway. 
**Recommendation:** Extract the pure LangChain/FAISS logic out of `rag.py` and port it natively into the LearnLoop FastAPI backend (e.g., `backend/app/services/study_buddy_service.py`). This allows LearnLoop to natively manage the LLM connections and persist chat history in PostgreSQL without maintaining two separate web servers.

## 7. Proposed Request Contract
The React frontend will send a POST request to a new FastAPI endpoint (e.g., `POST /api/students/{id}/chat`):
```json
{
  "activity_id": "UUID",
  "topic": "Fractions",
  "question": "I don't understand how to compare them.",
  "current_difficulty": "Intermediate"
}
```
*(Note: Chat history can be maintained by the backend in PostgreSQL, removing the need for the frontend to send it).*

## 8. Proposed Response Contract
```json
{
  "answer": "Here is how you compare fractions...",
  "sources": [
    "Textbook Chapter 4, Page 12"
  ]
}
```

## 9. Dependency Compatibility
LearnLoop Backend vs Study Buddy:
- **FastAPI / SQLAlchemy** (LearnLoop) vs **LangChain / FAISS / Sentence-Transformers** (Study Buddy).
- **Compatibility:** High. There are no direct conflicts. Modern LangChain supports Pydantic V2 (used by FastAPI).
- **Additions Needed:** The LearnLoop backend `requirements.txt` will need to inherit: `langchain`, `langchain-groq`, `langchain-huggingface`, `faiss-cpu`, `sentence-transformers`, `pypdf`.

## 10. Environment Variables Required
- `GROQ_API_KEY` (Must be added to the LearnLoop backend `.env`).

## 11. Security Considerations
- **API Keys:** `GROQ_API_KEY` is currently typed into the Streamlit UI or loaded via `.env`. In the integrated version, it MUST remain securely on the FastAPI backend server. The React frontend should never see this key.
- **Vector Store:** FAISS runs locally in-memory. In a production environment with multiple users, storing embeddings on disk or using a dedicated vector DB (like pgvector) would prevent memory leaks, but FAISS is safe for this phase.

## 12. Files Needing Modification in Phase 5
- `backend/requirements.txt` (To add AI dependencies)
- `backend/app/api/interactions.py` (To add the new POST `/chat` endpoint)
- `backend/app/services/study_buddy_service.py` (NEW - to house the ported LangChain logic)
- `src/services/api.ts` (To add `sendChatMessage()`)
- `src/components/StudyBuddy.tsx` (To wire up the UI to the backend API instead of the local/mock logic)

## 13. Recommended Phase 5 Implementation Sequence
1. **Install Dependencies:** Add LangChain and FAISS to the FastAPI virtual environment.
2. **Port Service Logic:** Create `study_buddy_service.py` in the backend. Copy the `ChatGroq`, `FAISS`, and prompt template logic from `rag.py`. Remove all Streamlit (`st.`) references.
3. **Build API Endpoint:** Create a `POST /api/students/{id}/chat` route that accepts a message, retrieves context, invokes the LLM, and returns the response.
4. **Connect Frontend:** Update React's Study Buddy component to `POST` to the new endpoint and display the AI's response.

## 14. Risks or Blockers
- **In-Memory FAISS:** The current Study Buddy recreates the FAISS index in memory whenever files are uploaded. The backend will need a strategy for loading documents (e.g., initializing FAISS on startup with a predefined set of textbooks) since API requests are stateless.
- **Pydantic V1/V2:** LangChain community packages sometimes throw warnings or minor conflicts with Pydantic V2. This usually doesn't break execution but should be monitored during installation.
