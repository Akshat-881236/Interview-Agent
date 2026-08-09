# The Interview Agent — Executive Architecture & Prompt History

This document details the architectural evolution of **The Interview Agent** across three senior-level engineering prompt-and-response milestones, reflecting production-grade multi-modal AI design patterns.

---

## Milestone 1: Multi-Tier Distributed LLM Pipeline & Hybrid RAG Knowledge Synthesis

### Senior Architect Prompt
> *"Design and engineer a high-throughput, fault-tolerant Technical Interview State Machine powered by a 4-Tier Model Cascade (Ollama API Key as Primary, failing over dynamically to Claude 3.5 Sonnet, Groq Llama 3.3 70B, and Gemini 1.5 Flash). Synthesize internal 31-day curriculum RAG vector embeddings with live real-time web search APIs (DuckDuckGo & Wikipedia REST endpoints) to evaluate candidate technical answers and out-of-bound General Knowledge inquiries with sub-second latency."*

### Senior Agent Response & Implementation
- **FastAPI Async Core (`backend/main.py` & `app/api/`)**: Engineered non-blocking REST APIs utilizing JWT Bearer token authentication, stateful session tracking, and real-time proctor telemetry endpoints.
- **4-Tier LLM Orchestration (`app/agent/llm_client.py`)**: Implemented a multi-provider client executing parallel Pass-1 ensemble analysis (`asyncio.gather`) and 4-tier fallback Pass-2 response generation: **Ollama API Key (Primary)** → **Claude** → **Groq** → **Gemini**.
- **Dynamic Web API Knowledge Sync (`app/agent/strategies/knowledge_sync_strategy.py`)**: Integrated live internet search API querying to augment internal curriculum RAG objectives with real-time web intelligence for technical and General Knowledge (GK) candidate inputs.

---

## Milestone 2: Hands-Free Voice Studio, 10s Smart Silence Buffering & Debate Mode

### Senior Architect Prompt
> *"Build an ultra-responsive, hands-free Web Speech API studio with automated speech-to-text turn taking, a 10-second smart pause buffer that prevents transcript fragmentation or duplication, real-time visualizer canvas orb, telemetry HUD metrics, and an Adversarial Technical Debate Mode that challenges architectural trade-offs."*

### Senior Agent Response & Implementation
- **Smart Speech & Buffer Engine (`frontend/js/audio.js` & `app.js`)**: Implemented Web Speech API STT/TTS integration with a 10-second silence countdown timer. The engine dynamically appends incoming audio transcripts while suppressing repetitive STT artifacts.
- **Interactive Visualizer & Custom Dialogs (`frontend/js/visualizer.js` & `index.html`)**: Built an animated HTML5 Canvas voice orb synchronized with TTS audio playback state, telemetry metrics HUD (Eye Contact, Confidence Index, WPM Cadence), and high-contrast glassmorphic dialogs (`showCustomAlert` / `showCustomConfirm`).
- **Adversarial Debate Mode**: Built a stateful `⚔️ Debate Mode` trigger instructing the LLM engine to assume an aggressive technical adversary stance, probing edge cases and system scaling limitations.

---

## Milestone 3: Continuous Stream Vision Proctoring, Communication Strategy & 15-Tier Media Grid

### Senior Architect Prompt
> *"Implement a continuous 400ms offscreen canvas video stream scanner for real-time face presence and gaze telemetry, backed by a strict 2-strike violation engine (voice warning on 1st, session cancellation on 2nd). Engineer a Communication Strategy Engine that detects candidate technical misconceptions (e.g. HTML iframe vs vector embeddings), mandates direct response evaluation, and wrap the UI in a 15-tier device media responsive grid with 4 theme palettes."*

### Senior Agent Response & Implementation
- **Real-Time Stream Proctoring (`frontend/js/perception.js` & `app/api/interview.py`)**: Offscreen canvas samples video frames every 400ms. Face loss (`face_count == 0`) or off-screen gaze triggers `POST /api/interview/proctor_check` instantly, executing immediate voice warnings and 2-strike session cancellation.
- **Communication Strategy Engine (`app/agent/strategies/communication_strategy.py`)**: Analyzes candidate answers for conceptual errors and enforces that the first 1–2 sentences of the AI's spoken output directly evaluate and correct what the candidate just asserted before issuing follow-ups.
- **15-Tier Responsive Grid & Theme Engine (`frontend/css/style.css` & `app.js`)**: Engineered CSS custom property design tokens supporting 4 themes (`Dark Cyberpunk`, `Deep Oceanic Navy`, `Emerald Aurora`, `Solar Light`), an animated ambient aurora background, and 15 media query breakpoints covering devices from 320px feature phones to 2560px 4K displays.
