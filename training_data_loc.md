# training-data-loc.md: Data Location & Ingestion Architecture

## 1. Overview

This document outlines the directory structure, purpose, and usage of all static `.json` files acting as the foundational knowledge base for the AI Technical Interview Agent. It specifies where the hackathon-provided datasets are located, where custom developer-created knowledge files are stored, and how the Retrieval-Augmented Generation (RAG) pipeline ingests them to drive the interview logic.

---

## 2. Directory Structure

All training and evaluation data is securely isolated within the backend application structure. The file tree is organized as follows to separate external provider data from internal custom knowledge:

```text
backend/
|
│── main.py
│── agent/
│── pipeline/
├── data/                       <-- Provider / Hackathon Data
│   ├── curriculum.json
│   └── candidates.json
└── knowledge/                  <-- Custom Developer Data
    ├── rag_rules.json
    ├── interview_rubric.json
    └── custom_faqs.json

```

---

## 3. Provided Hackathon Data (Provider JSONs)

The core data files provided by the hackathon organizers are located in the `backend/data/` directory. These files govern the boundaries of the interview and candidate profiles.

### 3.1. `backend/data/curriculum.json`

* **Description:** The authoritative source of truth for the 31-day AI Cohort. It contains module breakdowns, daily learning objectives, and the specific toolsets taught (e.g., RAG, LangChain, Docker).
* **Usage:** The RAG pipeline queries this file to generate technically accurate questions. If the agent needs to ask about Day 7, it retrieves the "Embeddings Explained" objectives from this file to ensure it tests the candidate *only* on what they learned.

### 3.2. `backend/data/candidates.json`

* **Description:** Contains synthetic profiles of the cohort graduates (e.g., "Sarah Johnson", "Alex Turner"). It tracks their job roles, years of experience, and historical pass/fail metrics across all 31 missions.
* **Usage:** Used by the "Profile & Curriculum Analyzer" prior to the interview. The system loads this JSON to identify the candidate's weak points (missions that took multiple attempts to pass) and skipped topics, using this data to construct a personalized "Interview Blueprint" targeting exactly 4 distinct days.

---

## 4. Custom Knowledge Base (User-Created JSONs)

To enhance the agent's conversational ability and evaluation strictness, additional domain-specific data is stored in the `backend/knowledge/` directory.

### 4.1. `backend/knowledge/rag_rules.json`

* **Description:** A custom configuration file containing the mathematical weights for the Grounding Score, threshold parameters for triggering follow-up questions, and logic rules for the Multi-Agent state machine.
* **Usage:** Loaded into memory on server startup. It dictates how strict the AI should be when grading a candidate's transcribed audio response.

### 4.2. `backend/knowledge/interview_rubric.json`

* **Description:** Contains predefined grading schemas (e.g., what constitutes a "shallow" vs. "comprehensive" answer for Vector Databases vs. Prompt Engineering).
* **Usage:** Passed as structured context to the LLM during the post-interview feedback generation phase (via `GET /api/v1/interview/feedback/{session_id}`) to ensure standardized scoring across all candidates.

---

## 5. How to Use the JSON Data (The Ingestion Pipeline)

The backend does not pass these raw JSON files directly into the LLM context window, as that would exceed token limits and increase latency. Instead, the data is processed through the following pipeline:

### Step 1: Parsing and Chunking (Startup)

When the FastAPI server initializes, a data loader script reads `curriculum.json` and the custom `.json` files from the `knowledge/` directory. The JSON arrays are parsed into Python `Pydantic` models for strict type validation.

* The 31 days of the curriculum are chunked into individual document nodes.

### Step 2: Vectorization (Embedding)

* The parsed text chunks (e.g., objectives from Day 16: "Chatbot Backend & API Integration") are passed through an embedding model (e.g., `text-embedding-3-small` or a local Sentence Transformer).
* These vectors are stored in an in-memory vector database (like ChromaDB or an HNSW index) alongside their metadata (Day Number, Topic).

### Step 3: Retrieval (Runtime)

* When candidate `CAND-001` starts an interview, their profile is fetched from `candidates.json`. The agent identifies that they struggled with Day 10.
* The agent queries the Vector DB for "Day 10 Objectives".
* The Vector DB returns the specific JSON chunk related to the "Retrieval & Matching Engine".
* This specific chunk is injected into the prompt as *System Context*, allowing the AI to ask a highly specific, localized question without reading the entire 31-day curriculum.

---

## 6. Security & Access Control

* **Immutability:** The JSON files in `backend/data/` and `backend/knowledge/` are treated as **read-only** by the application during runtime. The agent cannot modify the curriculum or the candidate's historical grades.
* **Privacy Guardrails:** The `candidates.json` file is never exposed directly via a public API endpoint. It is only accessed server-side to orchestrate the internal state machine and customize the RAG prompts.