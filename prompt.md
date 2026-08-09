# The Interview Agent — Project Prompt & Architecture Journey

This document summarizes the overall engineering journey of **The Interview Agent** across three primary prompt and response evolutions.

---

## Prompt 1: Core System Architecture & 4-Tier Multi-LLM Pipeline

### User Prompt
> "Build a multi-modal AI Technical Interview Agent for AI Cohort graduates featuring RAG knowledge indexing, JWT authentication, and a 4-Tier model fallback hierarchy using Ollama as primary, followed by Claude, Groq (Grok), and Gemini, enriched with real-time web search."

### Agent Response & Implementation
- **FastAPI Core (`backend/main.py` & `app/api/`)**: Built RESTful API endpoints for authentication (`/api/auth/login`, `/api/auth/register`), candidate management, session state machine (`/api/interview/start`, `/api/interview/answer`), and report generation (`/api/interview/{id}/report`).
- **4-Tier LLM Pipeline (`app/agent/llm_client.py`)**: Implemented a resilient multi-model client executing **Ollama (Primary)** -> **Claude (Secondary)** -> **Groq (Grok Secondary Fallback)** -> **Gemini (Tertiary Fallback)**.
- **RAG + Web Search Knowledge Sync (`app/agent/strategies/knowledge_sync_strategy.py`)**: Vector search over the 31-day curriculum corpus (`rag.py`) combined with live real-time web knowledge retrieval via DuckDuckGo Instant Answer and Wikipedia REST APIs.

---

## Prompt 2: Hands-Free Voice Studio & Interactive Debate Mode

### User Prompt
> "Upgrade the frontend to a high-end dark glassmorphism Voice & Video Studio featuring Web Speech API hands-free auto turn-taking, 10-second smart pause accumulation without text duplication, animated AI voice orb, and collapsible Adversarial Debate Mode."

### Agent Response & Implementation
- **Voice & Speech Engine (`frontend/js/audio.js` & `app.js`)**: Integrated Web Speech API SpeechRecognition (STT) and SpeechSynthesis (TTS). Built a 10-second smart pause countdown timer that auto-submits upon silence or appends new speech seamlessly to the buffer if the candidate resumes speaking within 10 seconds.
- **Visualizer & UI (`frontend/js/visualizer.js`, `index.html`, `style.css`)**: Built a pulsing canvas AI Voice Orb visualizer, telemetry HUD (Eye Contact %, Confidence Index, WPM Cadence), and high-contrast custom glassmorphism modal dialogs (`showCustomAlert` & `showCustomConfirm`).
- **Adversarial Debate Mode**: Added a toggleable `⚔️ Debate Mode` state sending `debate_mode: true` to the state machine, causing the AI to act as a sharp technical adversary challenging candidate trade-offs and edge cases.

---

## Prompt 3: Strict Real-Time Perception Proctoring & Communication Strategy

### User Prompt
> "Implement strict camera perception rules that automatically detect face loss or off-screen gaze (looking left/right/away) during live webcam stream, issue instant out-of-loud voice warnings, and cancel on 2nd violation. Make sure the AI directly evaluates candidate misconceptions rather than blindly asking scripted questions."

### Agent Response & Implementation
- **Real-Time Camera Stream Scanner (`frontend/js/perception.js`)**: An offscreen canvas samples video stream frames every 400ms. If face count drops to 0 or gaze turns off-screen, it triggers `POST /api/interview/proctor_check` instantly.
- **Strict Proctor Rules (`app/agent/state_machine.py`)**:
  - **Violation 1**: Triggers spoken out-of-loud AI voice warning (*"Proctor Warning: Candidate face lost from camera frame. Please remain seated facing your camera."*) and displays warning banner.
  - **Violation 2**: Immediately terminates session out-of-loud (*"Proctor Notice: Multiple camera proctoring violations detected. Interview terminated due to non-compliance."*) and locks studio.
- **Communication Strategy Engine (`app/agent/strategies/communication_strategy.py`)**: Evaluates candidate responses for misconceptions (e.g. confusing HTML iframe embedding with AI vector embeddings) and enforces that the **first 1–2 sentences of the AI's spoken response MUST directly address and correct what the candidate just said** before asking a follow-up.
