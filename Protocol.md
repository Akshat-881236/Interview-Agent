# Protocol.md: Communication & State Management Protocol

## 1. Overview

This document defines the **Agent Communication Protocol (ACP)** for the AI Technical Interview Agent. It outlines the interaction contracts, real-time transport mechanisms, and state transitions required to orchestrate a seamless, multi-modal (voice/video) technical interview for the 31-day AI Cohort.

The protocol ensures that the frontend client, the backend orchestration engine, and the perception processing streams (computer vision and NLP) remain perfectly synchronized.

---

## 2. Transport Layer Architecture

To support real-time, multi-modal interactions alongside structured technical assessments, the system utilizes a tri-protocol architecture:

* **REST (HTTPS):** Used for session initialization, static data retrieval, and final feedback generation.
* **WebRTC:** Handles ultra-low latency, peer-to-peer streaming of the candidate's raw video and audio feeds to the backend perception servers.
* **WebSocket (WSS):** Maintains a persistent, bi-directional event channel for telemetry, transcriptions, agent state updates, and interruption handling.

---

## 3. Session Lifecycle & State Machine

The Interview Agent operates strictly within a defined state machine to ensure it meets the minimum requirements (8 questions, 4 curriculum days) without hallucinating or losing control of the conversation.

### 3.1. Valid States

1. `SESSION_INIT`: Loading candidate profile and curriculum blueprints.
2. `AGENT_SPEAKING`: Synthesizing and streaming audio to the candidate.
3. `CANDIDATE_LISTENING`: Processing incoming audio/video streams; evaluating micro-expressions.
4. `PROCESSING_RESPONSE`: Running RAG pipeline and calculating the Grounding Score.
5. `EVALUATING_ROUTING`: Deciding whether to ask a follow-up or transition to the next curriculum node.
6. `SESSION_CONCLUDED`: Interview finished; generating the final evaluation payload.

### 3.2. Interruption Protocol

If the candidate interrupts the AI while it is in the `AGENT_SPEAKING` state:

1. The Voice Activity Detection (VAD) module detects continuous candidate speech (>400ms).
2. A `CANDIDATE_INTERRUPTION` event is fired via WebSocket.
3. The agent halts audio synthesis, clears the current playback buffer, and transitions immediately to `CANDIDATE_LISTENING`.

---

## 4. REST API Contract (Core Operations)

These endpoints satisfy the minimum required HTTP contract for the system.

### 4.1. Initialize Interview

Creates a new interview session and returns the initial agent greeting.

* **Endpoint:** `POST /api/v1/interview/start`
* **Headers:** `Authorization: Bearer <token>`
* **Request Body:**
```json
{
  "candidate_id": "CAND-001",
  "interview_mode": "video_voice",
  "curriculum_version": "v1"
}

```


* **Response (201 Created):**
```json
{
  "session_id": "sess_8f92a1b",
  "webrtc_ice_servers": [ ... ],
  "websocket_url": "wss://api.interview.ai/stream/sess_8f92a1b",
  "initial_agent_message": "Hello Sarah, welcome to your technical interview for the AI Cohort. I see you have extensive experience as a Senior Data Engineer. Let's start by discussing your work on Vector Databases. Are you ready?"
}

```



### 4.2. Chat / Text Fallback (Optional / Debugging)

Allows for text-based interaction if media streams fail.

* **Endpoint:** `POST /api/v1/interview/chat`
* **Request Body:**
```json
{
  "session_id": "sess_8f92a1b",
  "candidate_message": "Yes, I am ready. I built a hybrid router using Pinecone and ChromaDB."
}

```


* **Response (200 OK):**
```json
{
  "agent_message": "That's excellent. Can you explain how you handled merging and deduplicating the results from those two different retrieval sources?",
  "is_completed": false,
  "metrics": {
    "questions_asked": 1,
    "days_covered": 1
  }
}

```



### 4.3. Final Feedback Generation

Retrieves the structured evaluation post-interview.

* **Endpoint:** `GET /api/v1/interview/feedback/{session_id}`
* **Response (200 OK):**
```json
{
  "session_id": "sess_8f92a1b",
  "status": "COMPLETED",
  "technical_score": 88,
  "curriculum_days_covered": [8, 10, 12, 22, 28],
  "total_questions": 9,
  "strengths": [
    "Strong conceptual grasp of RAG evaluation metrics.",
    "Clear articulation of Docker deployment strategies."
  ],
  "areas_for_improvement": [
    "Struggled slightly with the nuances of Maximum Marginal Relevance (MMR) tuning."
  ],
  "detailed_summary": "..."
}

```



---

## 5. WebSocket Event Specification

The persistent WebSocket connection acts as the nervous system of the interview, carrying lightweight JSON payloads.

### 5.1. Client-to-Server Events

* `webrtc_ready`: Signals that the peer connection is established.
* `candidate_speaking_started`: Fired by local client VAD.
* `candidate_speaking_stopped`: Fired by local client VAD.
* `video_telemetry`: Client-side diagnostic data (fps, packet loss).

### 5.2. Server-to-Client Events

* `agent_state_change`: Notifies the UI to update visual indicators (e.g., "Agent is thinking...", "Agent is speaking...").
```json
{
  "event": "agent_state_change",
  "state": "PROCESSING_RESPONSE",
  "timestamp": "2026-08-08T12:40:00Z"
}

```


* `transcription_delta`: Real-time streaming text of what the AI hears (closed captions).
* `perception_insight` (Internal/Admin only): Real-time output from the visual/audio stream.
```json
{
  "event": "perception_insight",
  "metrics": {
    "eye_contact_score": 0.85,
    "confidence_index": 0.92,
    "posture": "engaged"
  }
}

```


* `interview_milestone`: Triggered when a new curriculum day objective is successfully covered.

---

## 6. Error Handling & Recovery Protocols

To maintain a professional interview environment, the protocol defines strict recovery procedures for common network or processing failures.

| Failure Mode | Detection Mechanism | Recovery Protocol |
| --- | --- | --- |
| **WebRTC Stream Drop** | ICE connection state changes to `disconnected` or `failed`. | AI Agent pauses. WS emits `connection_unstable` event. UI prompts candidate. If > 15 seconds, gracefully fallback to text-only mode via `/api/v1/interview/chat`. |
| **LLM Latency Spike** | Generation takes > 3.0 seconds. | Trigger `filler_audio` payload (e.g., "That's an interesting approach, let me think about that...") to buy time and maintain conversational flow. |
| **VAD False Positive** | Audio picked up, but NLP transcription returns empty or ambient noise. | Ignore payload. Do not trigger a state transition. Maintain `CANDIDATE_LISTENING` state. |
| **Context Limit Reached** | Token counter nears model maximum. | System triggers an asynchronous summarization task on the first half of the transcript, seamlessly updating the context window without interrupting the active turn. |