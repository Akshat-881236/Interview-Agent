Here is a comprehensive `implementation.md` document written from the perspective of an engineering team building this product. It focuses on architecture, technical decisions, and system design, reflecting how human developers would construct and deploy a production-ready AI agent.

---

# Implementation Document: AI Technical Interview Agent

## 1. Overview

This document outlines the technical implementation, system architecture, and engineering decisions for the **AI Technical Interview Agent**. The system is designed to conduct dynamic, multi-turn technical interviews for graduates of the 31-day AI Cohort.

Rather than a static Q&A bot, this system utilizes an agentic orchestration layer to dynamically generate questions, adapt to candidate responses, track curriculum coverage, and evaluate technical competency, all while exposing a stateless, scalable HTTP API.

---

## 2. System Architecture

To meet the requirements of low latency, context retention within a session, and modularity, we have adopted a microservices-oriented architecture using a modern Python stack.

### 2.1. High-Level Components

* **API Gateway / Server (FastAPI):** Handles incoming HTTP requests, session management, and request validation.
* **Agent Orchestrator:** The brain of the application. Manages the state machine of the interview, deciding when to ask a new question, when to follow up, and when to conclude.
* **Context Manager (Redis):** Stores temporary conversation history, current curriculum coverage, and question counts for active interview sessions.
* **Data Loaders:** Parses the `Curriculum JSON` and `Candidate Profiles` into optimized, in-memory representations for rapid retrieval during prompt assembly.
* **LLM Gateway:** An abstraction layer handling communication with the foundational LLM, including retry logic, fallback models, and rate limiting.

### 2.2. Tech Stack

* **Backend Framework:** Python 3.11 + FastAPI (Chosen for native `async/await` support, crucial for I/O bound LLM calls).
* **Agent Framework:** LangGraph / Custom State Machine (Allows explicit control over conversational flow, ensuring we hit the minimum requirements without the agent going off-script).
* **Session State:** Redis (In-memory datastore for fast context retrieval. Aligns with the "no persistent user accounts" constraint by expiring sessions after the interview concludes).
* **LLM:** GPT-4o / Claude 3.5 Sonnet (Optimized for reasoning and coding evaluation).
* **Deployment:** Docker, deployed via AWS ECS / Google Cloud Run.

---

## 3. Core Modules & Logic

### 3.1. Profile & Curriculum Analyzer

Before the interview begins, this module crosses the `Candidate Profile` with the `Curriculum JSON`.

* **Logic:** It identifies `completed missions` (areas of strength to test deeply), `skipped topics` (areas to probe for baseline understanding), and `learning signals`.
* **Output:** Generates a structured "Interview Blueprint" targeting at least 4 distinct days of the 31-day curriculum.

### 3.2. The Interview Engine (State Machine)

The core agent operates on a loop evaluated after every candidate response. We implemented specific constraints to guarantee the business logic:

* **Constraint Tracker:** Monitors the number of questions asked and the unique days covered.
* **Action Router:** Determines the next step:
1. *Follow-up:* If the candidate's answer is shallow, the router triggers a specific prompt to drill down.
2. *Next Topic:* If the topic is sufficiently covered, it shifts to the next node in the Interview Blueprint.
3. *Conclude:* Triggered when the candidate meets the criteria (≥ 8 questions, ≥ 4 curriculum days covered) or explicitly ends the interview.



### 3.3. Evaluation & Feedback Generator

Runs asynchronously after the interview terminates.

* It ingests the full transcript via the Context Manager.
* Uses a highly structured prompt forcing JSON output to evaluate the candidate against the specific learning objectives of the topics discussed.

---

## 4. API Contract & Data Flow

The system exposes RESTful endpoints adhering strictly to the provided Technical Specification.

### `POST /api/v1/interview/start`

Initializes the interview session.

* **Payload:** `candidate_id`
* **Action:** Loads candidate profile and curriculum, generates the blueprint, initializes Redis session, and generates the opening greeting.
* **Response:** `session_id`, `message` (Initial greeting).

### `POST /api/v1/interview/chat`

Handles the multi-turn conversation.

* **Payload:** `session_id`, `candidate_message`
* **Action:**
1. Retrieves context from Redis.
2. Agent Orchestrator evaluates the message.
3. Generates response/follow-up.
4. Updates question count and curriculum coverage metrics in Redis.


* **Response:** `agent_message`, `is_completed` (boolean).

### `GET /api/v1/interview/feedback/{session_id}`

Retrieves the final structured feedback.

* **Action:** Compiles the transcript and generates actionable feedback based on the AI Cohort concepts (RAG, Vector DBs, MCP, etc.).
* **Response:** JSON object containing `strengths`, `areas_for_improvement`, `technical_score`, and `detailed_summary`.

---

## 5. Engineering Decisions & Trade-offs

1. **State Machine vs. Autonomous Agent:**
We opted for a deterministic state machine (directed graph) controlling the LLM rather than a fully autonomous ReAct agent. Fully autonomous agents can hallucinate or fail to meet strict business constraints (e.g., "Must cover 4 days"). The state machine guarantees we meet the 8-question / 4-day minimum requirement while allowing the LLM to handle the natural language generation natively.
2. **Stateless API Design:**
While the conversation has state, the API itself is stateless. All state is hydrated from Redis using the `session_id`. This allows the application to scale horizontally behind a load balancer without sticky sessions.
3. **Prompt Engineering Strategy:**
We use dynamic system prompts. Rather than passing the entire 31-day curriculum into the context window (which wastes tokens and degrades LLM focus), we use RAG to inject *only* the specific learning objectives for the current topic into the prompt dynamically.

---

## 6. Implementation Phases

* **Phase 1: Data Modeling & Pipeline:** Parse the synthetic JSON data, define Pydantic models for type safety, and build the Curriculum Tracker logic.
* **Phase 2: Agent Orchestration:** Build the core LangGraph state machine. Develop the routing logic (Follow-up vs. New Question).
* **Phase 3: API & Context Management:** Wrap the agent in FastAPI, implement Redis for session state management, and ensure latency is under 3 seconds per turn.
* **Phase 4: Feedback Generation:** Design the structured output extraction for the feedback payload.
* **Phase 5: Testing & Refinement:** Conduct edge-case testing (e.g., candidate asks unrelated questions, candidate gives one-word answers) to ensure the agent maintains control of the interview.

---

## 7. Future Considerations (Out of Scope for V1)

While out of scope for this hackathon build, the architecture supports easy integration of future features:

* **Audio/Voice Integration:** The decoupled REST API allows a WebRTC or WebSockets middleware to be placed in front of the HTTP endpoints for voice-to-text and text-to-voice streaming.
* **Persistent Storage:** Replacing Redis with PostgreSQL to store historical interview transcripts for longitudinal candidate analysis.