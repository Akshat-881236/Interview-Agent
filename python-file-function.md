# python-files-function.md: Python Subsystem Architecture & Algorithmic Index

## 1. System Codebase Overview

The **AI Technical Interview Agent** is implemented as a modular, asynchronous Python application built on top of FastAPI, LangChain/LangGraph, OpenCV, Librosa, PyTorch, and ChromaDB. The backend codebase consists of **18 core Python files**, each designed as a self-contained module fulfilling specific operational roles in perception, retrieval, graph orchestration, and real-time streaming.

> **Code Metric Target (Antigravity Specification):** Every core Python file listed below is architected as a production-grade module containing between **700 to 1,500+ lines of code** (including standard boilerplate, Pydantic type specifications, error handlers, inline mathematical formulations, logging, and unit tests).

---

## 2. Directory Index & File Specification

```text
backend/app/
├── main.py                          [File 01]
├── core/
│   ├── config.py                    [File 02]
│   └── security.py                  [File 03]
├── data/
│   ├── json_loader.py               [File 04]
│   └── vector_store.py              [File 05]
├── rag/
│   ├── dense_retriever.py           [File 06]
│   ├── sparse_retriever.py          [File 07]
│   ├── hybrid_fusion.py             [File 08]
│   └── mmr_reranker.py              [File 09]
├── agent/
│   ├── state_machine.py             [File 10]
│   ├── topic_planner.py             [File 11]
│   ├── grounding_evaluator.py       [File 12]
│   └── followup_generator.py        [File 13]
├── perception/
│   ├── vision_analyzer.py           [File 14]
│   ├── audio_analyzer.py            [File 15]
│   └── vad_handler.py               [File 16]
├── websocket/
│   └── stream_manager.py            [File 17]
└── services/
    └── feedback_generator.py        [File 18]

```

---

## 3. Comprehensive File Descriptions

### File 01: `app/main.py`

* **File Path:** `backend/app/main.py`
* **Estimated Lines:** ~850 lines
* **Role in Interview Agent:** Serves as the primary entrypoint for the backend FastAPI application. It initializes middleware (CORS, Request Tracing), mounts REST route handlers, manages startup/shutdown lifecycle hooks, establishes database connection pools, and exposes health/readiness probes.
* **Algorithms Implemented:**
1. *Asynchronous Task Loop Orchestration:* Non-blocking event loop scheduling for continuous perception background tasks.
2. *Token Bucket Rate Limiting:* Protects public endpoints against DDoS attacks and LLM API cost spikes.


* **Workflow:**
`Client Request` $\rightarrow$ `Middleware Sanitization` $\rightarrow$ `JWT / Auth Validation` $\rightarrow$ `Router Dispatch` $\rightarrow$ `Response Streaming`.

---

### File 02: `app/core/config.py`

* **File Path:** `backend/app/core/config.py`
* **Estimated Lines:** ~720 lines
* **Role in Interview Agent:** Centralized settings management utilizing `pydantic-settings`. Loads environment variables, sets threshold parameters for grounding scores, configures vector database parameters, and maintains model endpoints.
* **Algorithms Implemented:**
1. *Dynamic Configuration Hydration:* Validates types, ranges, and schema integrity for system configurations on application startup.


* **Workflow:**
`Environment Variables / .env File` $\rightarrow$ `Pydantic BaseSettings Parser` $\rightarrow$ `System Constant Binding` $\rightarrow$ `In-Memory Singleton Injection`.

---

### File 03: `app/core/security.py`

* **File Path:** `backend/app/core/security.py`
* **Estimated Lines:** ~780 lines
* **Role in Interview Agent:** Controls authentication, authorization, token issuance, and sensitive data encryption. Ensures biometric data (video frames/audio samples) are sanitized and PII/PHI is stripped before prompt injection.
* **Algorithms Implemented:**
1. *AES-256-GCM Encryption/Decryption:* Encrypts session transcripts and candidate profiles at rest.
2. *HMAC-SHA256 Token Validation:* Validates single-use session tokens issued for candidate interviews.


* **Workflow:**
`Auth Header` $\rightarrow$ `JWT Token Extraction` $\rightarrow$ `Signature Verification` $\rightarrow$ `PII/PHI Anonymization Filter` $\rightarrow$ `Authenticated Context`.

---

### File 04: `app/data/json_loader.py`

* **File Path:** `backend/app/data/json_loader.py`
* **Estimated Lines:** ~910 lines
* **Role in Interview Agent:** Ingests, parses, and validates the external synthetic data files (`backend/data/curriculum.json` and `backend/data/candidates.json`) as well as internal custom schemas (`backend/knowledge/`). Converts unstructured JSON nodes into typed Python models.
* **Algorithms Implemented:**
1. *Recursive Graph Unrolling:* Expands nested curriculum modules and days into a flattened node network.
2. *JSON Schema Validation & Error Recovery:* Recovers gracefully from missing or malformed candidate fields.


* **Workflow:**
`Raw .json Files` $\rightarrow$ `Pydantic Schema Parser` $\rightarrow$ `Data Cleansing & Normalization` $\rightarrow$ `In-Memory Knowledge Graph Creation`.

---

### File 05: `app/data/vector_store.py`

* **File Path:** `backend/app/data/vector_store.py`
* **Estimated Lines:** ~1,100 lines
* **Role in Interview Agent:** Manages local vector storage using ChromaDB and HNSW indexing. Creates collections for curriculum learning objectives, populates embeddings, and provides metadata filtering APIs.
* **Algorithms Implemented:**
1. *Hierarchical Navigable Small World (HNSW):* Graph-based $K$-nearest neighbor vector indexing for fast semantic retrieval.
2. *Incremental Index Updating:* Re-indexes modified curriculum files without rebuilding the vector database from scratch.


* **Workflow:**
`Curriculum Chunks` $\rightarrow$ `Embedding Generation` $\rightarrow$ `HNSW Graph Build` $\rightarrow$ `Persistent Storage`.

---

### File 06: `app/rag/dense_retriever.py`

* **File Path:** `backend/app/rag/dense_retriever.py`
* **Estimated Lines:** ~820 lines
* **Role in Interview Agent:** Executes semantic vector searches over candidate attempts and curriculum objectives using dense embedding vectors.
* **Algorithms Implemented:**
1. *Cosine Similarity Inner Product:*

$$\text{Sim}(\vec{q}, \vec{d}) = \frac{\vec{q} \cdot \vec{d}}{\Vert{}\vec{q}\Vert{}_2 \Vert{}\vec{d}\Vert{}_2}$$




* **Workflow:**
`Transcribed Query` $\rightarrow$ `Vector Embedding` $\rightarrow$ `ChromaDB HNSW Query` $\rightarrow$ `Top-K Dense Vector Results`.

---

### File 07: `app/rag/sparse_retriever.py`

* **File Path:** `backend/app/rag/sparse_retriever.py`
* **Estimated Lines:** ~890 lines
* **Role in Interview Agent:** Performs exact token matching for technical terminology, framework names, and tool identifiers (e.g., `PEFT`, `MCP`, `ChromaDB`) using lexical indexing.
* **Algorithms Implemented:**
1. *Okapi BM25 Lexical Ranking Algorithm:*

$$\text{Score}_{\text{BM25}}(d, q) = \sum_{t \in q} \text{IDF}(t) \cdot \frac{f(t, d) \cdot (k_1 + 1)}{f(t, d) + k_1 \left(1 - b + b \cdot \frac{\vert{}d\vert{}}{\text{avgdl}}\right)}$$




* **Workflow:**
`Raw Query String` $\rightarrow$ `Tokenizer & Stemmer` $\rightarrow$ `Inverted Index Look-up` $\rightarrow$ `Lexical Score Matrix`.

---

### File 08: `app/rag/hybrid_fusion.py`

* **File Path:** `backend/app/rag/hybrid_fusion.py`
* **Estimated Lines:** ~750 lines
* **Role in Interview Agent:** Merges rankings from both the dense vector retriever and sparse lexical retriever to produce a unified context candidate list without requiring normalized scores.
* **Algorithms Implemented:**
1. *Reciprocal Rank Fusion (RRF):*

$$\text{RRF}(d) = \sum_{m \in \{\text{Dense}, \text{Sparse}\}} \frac{1}{k + r_m(d)} \quad (k=60)$$




* **Workflow:**
`Dense Rank List + Sparse Rank List` $\rightarrow$ `RRF Formula Evaluation` $\rightarrow$ `Fused Rank Array`.

---

### File 09: `app/rag/mmr_reranker.py`

* **File Path:** `backend/app/rag/mmr_reranker.py`
* **Estimated Lines:** ~710 lines
* **Role in Interview Agent:** Re-ranks fused retrieval results to maximize information diversity, preventing the AI agent from repeating questions on the same narrow objective.
* **Algorithms Implemented:**
1. *Maximal Marginal Relevance (MMR):*

$$\text{MMR} = \arg\max_{d_i \in \mathcal{R} \setminus \mathcal{S}} \left[ \lambda \cdot \text{Sim}_1(d_i, q) - (1 - \lambda) \cdot \max_{d_j \in \mathcal{S}} \text{Sim}_2(d_i, d_j) \right]$$




* **Workflow:**
`Fused Candidate List` $\rightarrow$ `Iterative Diversity Selection` $\rightarrow$ `Final Re-ranked Context Array`.

---

### File 10: `app/agent/state_machine.py`

* **File Path:** `backend/app/agent/state_machine.py`
* **Estimated Lines:** ~1,350 lines
* **Role in Interview Agent:** Implements the core state machine governing the multi-turn interview flow. Enforces system constraints (e.g., minimum 8 questions, minimum 4 curriculum days covered) and coordinates agent turn transitions.
* **Algorithms Implemented:**
1. *Finite State Transducer (FST):* Governs deterministic state transitions based on candidate activity and system metrics.
2. *Dynamic Context Window Pruning:* Uses a sliding window with automated transcript summarization to keep context size bounded.


* **Workflow:**
`State Evaluation` $\rightarrow$ `Check Business Rules` $\rightarrow$ `Execute Action Node` $\rightarrow$ `Update Session Memory in Redis`.

---

### File 11: `app/agent/topic_planner.py`

* **File Path:** `backend/app/agent/topic_planner.py`
* **Estimated Lines:** ~1,120 lines
* **Role in Interview Agent:** Pre-computes and dynamically adjusts the optimal target path of 4 curriculum days for a candidate based on their historical signals (skipped topics, multiple attempt counts).
* **Algorithms Implemented:**
1. *Dynamic Programming Graph Traversal:*

$$DP(i, m) = \max \left( DP(i-1, m), \max_{(v_j, v_i) \in E} \left\{ DP(j, m-1) \right\} + w_i \right)$$




* **Workflow:**
`Candidate Profile Input` $\rightarrow$ `Curriculum DAG Construction` $\rightarrow$ `DP Path Matrix Solution` $\rightarrow$ `Target 4-Day Interview Blueprint`.

---

### File 12: `app/agent/grounding_evaluator.py`

* **File Path:** `backend/app/agent/grounding_evaluator.py`
* **Estimated Lines:** ~980 lines
* **Role in Interview Agent:** Grades candidate responses in real-time by comparing transcribed text against target learning objectives, producing a Grounding Score ($G$).
* **Algorithms Implemented:**
1. *Semantic Vector Alignment + Entity Precision Weighting:*

$$G(A, \mathcal{K}) = \mu_1 \cdot \text{Cosine}(\vec{e}_A, \vec{e}_{\mathcal{K}}) + \mu_2 \cdot \frac{\vert{}\text{Entities}(A) \cap \text{Entities}(\mathcal{K})\vert{}}{\vert{}\text{Entities}(\mathcal{K})\vert{}}$$




* **Workflow:**
`Candidate Response Text` $\rightarrow$ `NER Extraction & Embedding` $\rightarrow$ `Formula Computation` $\rightarrow$ `Grounding Score ($G$)`.

---

### File 13: `app/agent/followup_generator.py`

* **File Path:** `backend/app/agent/followup_generator.py`
* **Estimated Lines:** ~860 lines
* **Role in Interview Agent:** Constructs targeted follow-up questions when a candidate's response is deemed shallow ($G < 0.65$), probing specific missing technical details.
* **Algorithms Implemented:**
1. *Contextual Objective Delta Mapping:* Identifies specific unaddressed technical sub-components in candidate responses.


* **Workflow:**
`Grounding Failure Signal` $\rightarrow$ `Extract Missing Knowledge Nodes` $\rightarrow$ `Prompt Assembly` $\rightarrow$ `Targeted Follow-Up Generation`.

---

### File 14: `app/perception/vision_analyzer.py`

* **File Path:** `backend/app/perception/vision_analyzer.py`
* **Estimated Lines:** ~1,250 lines
* **Role in Interview Agent:** Processes incoming video frames via OpenCV and PyTorch models to extract visual cues: facial expressions, gaze vector tracking (eye contact), and attire presentation classification.
* **Algorithms Implemented:**
1. *Gaze Vector Vectorial Estimate:* Calculates directional deviation of facial landmarks from center screen.
2. *CNN-Based Expression Classification:* Categorizes facial expressions into confidence metrics.


* **Workflow:**
`WebRTC Video Frame` $\rightarrow$ `Landmark Detection` $\rightarrow$ `Expression & Attire Inference` $\rightarrow$ `JSON Vision Telemetry Payload`.

---

### File 15: `app/perception/audio_analyzer.py`

* **File Path:** `backend/app/perception/audio_analyzer.py`
* **Estimated Lines:** ~1,050 lines
* **Role in Interview Agent:** Analyzes the candidate's incoming audio stream for vocal characteristics: fundamental frequency ($F_0$), pitch stability, pacing (words per minute), and filler word frequency.
* **Algorithms Implemented:**
1. *Autocorrelation Pitch Tracking ($F_0$ Detection):*

$$R(\tau) = \sum_{n} x(n) x(n + \tau)$$


2. *Spectral Flux Audio Segmentation:* Detects pauses, speech cadence, and vocal hesitation.


* **Workflow:**
`Raw PCM Audio Buffer` $\rightarrow$ `Librosa Feature Extraction` $\rightarrow$ `Acoustic Metrics Calculation` $\rightarrow$ `Vocal Quality Metrics Output`.

---

### File 16: `app/perception/vad_handler.py`

* **File Path:** `backend/app/perception/vad_handler.py`
* **Estimated Lines:** ~790 lines
* **Role in Interview Agent:** Real-time Voice Activity Detection (VAD) module using Silero VAD. Responsible for detecting candidate interruptions during agent speech playback.
* **Algorithms Implemented:**
1. *Recurrent Neural Network (RNN) VAD Classification:* Classifies audio chunks into speech vs. non-speech probabilities.
2. *Sliding Hysteresis Thresholding:* Prevents momentary ambient noises from triggering speech interruption events.


* **Workflow:**
`Audio Chunk Stream` $\rightarrow$ `Silero Neural Inference` $\rightarrow$ `Speech Probability > 0.85 Check` $\rightarrow$ `Trigger Interruption Protocol`.

---

### File 17: `app/websocket/stream_manager.py`

* **File Path:** `backend/app/websocket/stream_manager.py`
* **Estimated Lines:** ~1,180 lines
* **Role in Interview Agent:** Manages bidirectional WebSocket client connections (`wss://`). Routes client events, streams transcription closed-captions, and sends real-time state change events.
* **Algorithms Implemented:**
1. *Asynchronous Connection Multiplexing:* Handles high-frequency real-time event distribution across client sessions.
2. *Heartbeat & Exponential Backoff Reconnection:* Recovers cleanly from transient client network dropouts.


* **Workflow:**
`Incoming WS Payload` $\rightarrow$ `JSON Event Dispatcher` $\rightarrow$ `Route to Perception/Agent Subsystems` $\rightarrow$ `Broadcast State Delta`.

---

### File 18: `app/services/feedback_generator.py`

* **File Path:** `backend/app/services/feedback_generator.py`
* **Estimated Lines:** ~1,420 lines
* **Role in Interview Agent:** Compiles overall performance metrics, grounded transcript histories, and perception metrics upon session completion to synthesize a detailed evaluation payload.
* **Algorithms Implemented:**
1. *Weighted Rubric Scoring Model:* Combines technical correctness scores, RAG grounding precision, and communication delivery metrics.
2. *Structured Output Parsing via Pydantic:* Enforces strict JSON schema compliance on generated feedback text.


* **Workflow:**
`Session Concluded Event` $\rightarrow$ `Fetch Complete Session Context from Redis` $\rightarrow$ `LLM Structured Evaluation` $\rightarrow$ `JSON Feedback Output`.

---

## 4. Summary Matrix

| File # | File Path | Line Range | Core Algorithm / Technique | Primary Function |
| --- | --- | --- | --- | --- |
| **01** | `app/main.py` | 700–1000 | Task Loop Scheduling, Token Bucket | Application entrypoint & REST routing |
| **02** | `app/core/config.py` | 700–900 | Type Hydration & Validation | Global environment settings |
| **03** | `app/core/security.py` | 700–900 | AES-256-GCM, HMAC-SHA256 | Auth & PII/PHI data sanitization |
| **04** | `app/data/json_loader.py` | 800–1100 | Recursive Graph Unrolling | Parsing `curriculum.json` & `candidates.json` |
| **05** | `app/data/vector_store.py` | 1000–1300 | HNSW Vector Indexing | ChromaDB storage & vector index lifecycle |
| **06** | `app/rag/dense_retriever.py` | 700–1000 | Cosine Vector Similarity | Semantic dense search |
| **07** | `app/rag/sparse_retriever.py` | 700–1000 | Okapi BM25 Lexical Ranking | Technical keyword exact lookup |
| **08** | `app/rag/hybrid_fusion.py` | 700–900 | Reciprocal Rank Fusion (RRF) | Merging dense + sparse retrieval ranks |
| **09** | `app/rag/mmr_reranker.py` | 700–900 | Maximal Marginal Relevance (MMR) | Context diversity & duplicate removal |
| **10** | `app/agent/state_machine.py` | 1200–1500+ | Finite State Transducer (FST) | Interview state graph & flow control |
| **11** | `app/agent/topic_planner.py` | 1000–1300 | Dynamic Programming | Optimal 4-day curriculum path planning |
| **12** | `app/agent/grounding_evaluator.py` | 800–1100 | Grounding Score ($G$), NER Alignment | Answer correctness evaluation |
| **13** | `app/agent/followup_generator.py` | 700–1000 | Delta Mapping Prompting | Targeted dynamic follow-up creation |
| **14** | `app/perception/vision_analyzer.py` | 1100–1400 | Gaze Vector Estimation, CNN | Face, eye contact, and attire analysis |
| **15** | `app/perception/audio_analyzer.py` | 900–1200 | Autocorrelation ($F_0$), Spectral Flux | Voice quality & acoustic telemetry |
| **16** | `app/perception/vad_handler.py` | 700–1000 | Neural RNN VAD (Silero) | Interruption detection & audio gating |
| **17** | `app/websocket/stream_manager.py` | 1000–1300 | Connection Multiplexing | Real-time WebSocket streaming gateway |
| **18** | `app/services/feedback_generator.py` | 1200–1500+ | Weighted Rubric Evaluation | Post-interview grading & report generation |