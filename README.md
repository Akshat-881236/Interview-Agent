# The Interview Agent

> Build the interviewer, not the interview.

A personalized technical interview agent for **The AI Cohort**. It reads a
candidate's real progress through the 31‑day curriculum — what they
completed, struggled with, or skipped — plans a multi‑turn interview around
it, asks intelligent follow‑ups grounded in what the candidate actually said,
and produces a structured feedback report at the end.

**Note on attachments:** the hackathon brief references a curriculum JSON,
candidate profiles, and a technical spec as "attached," but nothing was
actually attached to this task. Rather than block on that, I authored
synthetic-but-realistic versions of all three (`backend/data/curriculum.json`,
`backend/data/candidates.json`, `API_SPEC.md`) that match the brief exactly,
so the whole system is real and runnable. Drop in the real files at the same
paths/shape and nothing else needs to change.

## Stack

- **Backend:** Python, FastAPI (the required HTTP endpoints — see `API_SPEC.md`)
- **Retrieval layer:** `backend/rag.py` — a small RAG-style retrieve pipeline
  (chunk → term-vectorize → cosine retrieve) that grounds follow-up questions
  and scoring in the actual curriculum vocabulary. Swappable for a real
  embedding model + vector DB without touching the rest of the app (see the
  docstring in that file).
- **Agent:** `backend/agent.py` — plans the interview from the candidate
  profile, generates primary + follow-up questions, scores answers, and
  builds the final report. Template + retrieval driven so every question is
  traceable to *why* it was asked.
- **Frontend:** HTML/CSS/vanilla JS, Bootstrap (CDN) + a small locally
  authored utility layer (`frontend/vendor/mini-bootstrap.css`), styled as an
  actual interview room (transcript + live scorecard clipboard + a
  certificate-style report).

## Run it

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Open **http://localhost:8000** — the backend serves the frontend directly
(no separate dev server needed). Pick a candidate, answer in the chat, and
you'll land on a structured feedback report at the end.

If you'd rather serve the frontend separately (e.g. a static host), open
`frontend/index.html` directly — `app.js` falls back to
`http://localhost:8000/api` automatically, so just make sure the backend is
running with CORS enabled (already on, `allow_origins=["*"]`).

### Regenerating the synthetic curriculum
```bash
cd backend/data
python3 build_curriculum.py   # rewrites curriculum.json
```

## How it satisfies the minimum requirements

- **Conversational, multi-turn interview:** `/api/interview/start` +
  repeated `/api/interview/answer` calls; full turn history kept server-side
  per session.
- **≥ 8 questions across ≥ 4 curriculum days:** `InterviewAgent.build_plan()`
  targets 6 distinct days spread across modules; `main.py` won't mark a
  session complete until `MIN_QUESTIONS=8` and `MIN_DAYS=4` are both met.
- **Follow-ups generated from previous answers:** `agent.should_follow_up()`
  triggers when an answer is short or has low concept coverage (via
  `rag.coverage_score`); `agent.followup_question()` grounds the follow-up in
  the specific missing concept.
- **Context maintained throughout:** `SESSIONS[session_id]` holds the full
  turn-by-turn history, current plan position, and per-day follow-up state.
- **Structured feedback at the end:** `GET /api/interview/{session_id}/report`
  returns per-day scores + verdicts, overall readiness, strengths, growth
  areas, and recommended next steps pulled straight from the candidate's
  skipped/struggled days.
- **Required HTTP endpoint(s):** see `API_SPEC.md` for the full contract.

## Design notes

The interview deliberately isn't a fixed quiz. The plan-builder favors:
1. one "strength probe" per module the candidate is flagged strong in (verify
   depth, not just recall),
2. a middling "core" day per remaining module (diversity across the
   curriculum, not just day 1),
3. one honest "gap probe" on a day the candidate struggled with or skipped
   (a real interview doesn't only ask what you're good at).

Scoring blends curriculum-vocabulary coverage (55%), answer length as a depth
proxy (30%), and a hedging-language penalty (15%) into a 0–5 score per
answer, which rolls up into per-day and overall verdicts.

## What's out of scope (per the brief)
Voice interaction, authentication, persistent accounts, long-term history
across sessions, and mobile apps were intentionally not built.
