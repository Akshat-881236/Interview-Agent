# Technical Specification — The Interview Agent API

> Note: No curriculum JSON, candidate profiles, or technical spec were actually
> attached to this request. This document, `backend/data/curriculum.json`, and
> `backend/data/candidates.json` are synthetic stand-ins built to match the
> hackathon brief exactly, so the app is fully runnable end-to-end. Swap in
> the real files at the same paths/shape and everything downstream works
> unchanged.

Base URL: `http://localhost:8000/api`
Content type: `application/json` for all requests/responses.

## `GET /api/candidates`
Returns the list of available candidate profiles (id + display info only).

**200**
```json
{ "candidates": [ { "candidate_id": "cand_001", "name": "Aisha Verma", "cohort_progress_pct": 90 } ] }
```

## `GET /api/curriculum`
Returns the full 31-day curriculum JSON as provided.

## `POST /api/interview/start`
Starts a new interview session for a candidate and returns the first question.

**Request**
```json
{ "candidate_id": "cand_001" }
```
**200**
```json
{
  "session_id": "b3f1...",
  "candidate_name": "Aisha Verma",
  "question": { "id": "a1b2c3d4", "type": "primary", "day": 6, "topic": "RAG Fundamentals", "text": "..." },
  "progress": { "questions_asked": 1, "min_questions": 8, "days_covered": 1, "min_days": 4, "done": false }
}
```

## `POST /api/interview/answer`
Submits the candidate's answer to the current question and returns the next
question (a follow-up or a new day's primary question), or signals the
interview is complete.

**Request**
```json
{ "session_id": "b3f1...", "answer": "RAG grounds generation in retrieved documents so the model isn't relying purely on parametric memory..." }
```
**200 (in progress)**
```json
{
  "session_id": "b3f1...",
  "evaluation": { "score_5": 4.2, "coverage_ratio": 0.71, "missing_terms": ["hallucination"] },
  "question": { "id": "e5f6g7h8", "type": "followup", "day": 6, "topic": "RAG Fundamentals", "text": "..." },
  "progress": { "questions_asked": 2, "min_questions": 8, "days_covered": 1, "min_days": 4, "done": false }
}
```
**200 (interview complete — no more question, use the report endpoint)**
```json
{
  "session_id": "b3f1...",
  "evaluation": { "score_5": 3.8, "coverage_ratio": 0.6, "missing_terms": [] },
  "question": null,
  "progress": { "questions_asked": 11, "min_questions": 8, "days_covered": 6, "min_days": 4, "done": true }
}
```

## `GET /api/interview/{session_id}/report`
Returns structured, evidence-based final feedback. Available once `done: true`
(also computable mid-interview as a progress snapshot).

**200**
```json
{
  "candidate_id": "cand_001",
  "candidate_name": "Aisha Verma",
  "days_covered": [2, 6, 9, 16, 21, 27],
  "questions_asked": 11,
  "overall_score": 3.6,
  "readiness": "Close, with a few gaps to close",
  "day_reports": [ { "day": 6, "topic": "RAG Fundamentals", "module": "Retrieval-Augmented Generation", "avg_score": 4.2, "verdict": "Strong" } ],
  "strengths": ["RAG Fundamentals (Day 6) — avg 4.2/5"],
  "growth_areas": ["Observability for AI Systems (Day 27) — avg 2.1/5"],
  "recommended_next_steps": ["Day 20: Agent Evaluation & Guardrails", "Day 27: Observability for AI Systems (revisit)"],
  "narrative": "Aisha was interviewed across 6 curriculum days ..."
}
```

## `GET /api/health`
Liveness check: `{ "status": "ok" }`

## Error shape
Non-2xx responses return `{ "error": "message" }` with an appropriate status
code (`404` unknown candidate/session, `400` malformed body, `422` validation).

## Minimum-requirements traceability
| Requirement | Where it's implemented |
|---|---|
| Conversational, multi-turn interview | `/interview/start` + repeated `/interview/answer` |
| ≥ 8 questions, ≥ 4 curriculum days | `agent.build_plan` targets 6 days; loop enforces `MIN_QUESTIONS`/`MIN_DAYS` in `main.py` before allowing completion |
| Follow-ups from previous responses | `agent.should_follow_up` + `agent.followup_question`, grounded by `rag.coverage_score` |
| Context maintained across turns | Server-side `SESSIONS[session_id]` holds full turn history + per-day state |
| Structured end-of-interview feedback | `agent.build_feedback` via `/interview/{id}/report` |
