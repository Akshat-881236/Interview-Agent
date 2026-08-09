import json
import os
import uuid
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from app.models.schemas import StartRequest, AnswerRequest, PerceptionMetrics
from app.agent.state_machine import InterviewStateMachine
from app.api.auth import get_current_user
from agent import InterviewAgent, MIN_QUESTIONS, MIN_DAYS
from rag import RagIndex

router = APIRouter(prefix="/api", tags=["Interview"])

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")

with open(os.path.join(DATA_DIR, "curriculum.json")) as f:
    CURRICULUM = json.load(f)

def normalize_candidate(raw):
    if "candidate_id" in raw:
        return raw

    member = raw.get("member", {})
    candidate_id = member.get("id", str(uuid.uuid4()))
    name = member.get("name", "Candidate")
    role = member.get("jobRole", "AI Engineer")

    missions = raw.get("missions", [])
    completed_days = [m["day"] for m in missions if m.get("passed") is True]
    struggled_days = [m["day"] for m in missions if m.get("passed") is False or m.get("attempts", 0) > 2]
    skipped_days = [m["day"] for m in missions if m.get("skipped") is True]

    pct = round((len(completed_days) / 31) * 100)

    return {
        "candidate_id": candidate_id,
        "name": name,
        "role": role,
        "cohort_progress_pct": pct,
        "completed_days": completed_days,
        "attempted_but_struggled_days": struggled_days,
        "skipped_days": skipped_days,
        "learning_signals": {
            "strong_topics": [f"Day {d}" for d in completed_days if d not in struggled_days]
        }
    }

with open(os.path.join(DATA_DIR, "candidates.json")) as f:
    raw_list = json.load(f)["candidates"]
    CANDIDATES = {}
    for item in raw_list:
        norm = normalize_candidate(item)
        CANDIDATES[norm["candidate_id"]] = norm

RAG = RagIndex(CURRICULUM)
LEGACY_AGENT = InterviewAgent(CURRICULUM, RAG)
STATE_MACHINE = InterviewStateMachine(CURRICULUM, RAG)

SESSIONS = {}

def _progress(session):
    asked = sum(1 for t in session["turns"] if t["role"] == "agent")
    days_covered = len({t["day"] for t in session["turns"] if t["role"] == "agent"})
    done = session["status"] == "completed"
    return {
        "questions_asked": asked,
        "min_questions": MIN_QUESTIONS,
        "days_covered": days_covered,
        "min_days": MIN_DAYS,
        "done": done,
    }

def _serialize_question(q):
    if q is None:
        return None
    return {k: q[k] for k in ("id", "type", "day", "topic", "module", "text") if k in q}

@router.get("/curriculum")
@router.get("/v1/curriculum")
def get_curriculum():
    return CURRICULUM

@router.get("/candidates")
@router.get("/v1/candidates")
def get_candidates(user: Optional[dict] = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required to view candidate profiles")
    return {
        "candidates": [
            {"candidate_id": c["candidate_id"], "name": c["name"], "cohort_progress_pct": c["cohort_progress_pct"]}
            for c in CANDIDATES.values()
        ]
    }

@router.post("/interview/start")
@router.post("/v1/interview/start")
def start_interview(req: StartRequest, user: Optional[dict] = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required to start an interview session")

    candidate = CANDIDATES.get(req.candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Unknown candidate_id")

    plan = LEGACY_AGENT.build_plan(candidate)
    if len(plan) < MIN_DAYS:
        raise HTTPException(status_code=400, detail="Candidate profile has too few days to plan an interview")

    session_id = str(uuid.uuid4())
    session = {
        "session_id": session_id,
        "candidate_id": candidate["candidate_id"],
        "plan": plan,
        "plan_index": 0,
        "turns": [],
        "status": "in_progress",
        "current_question": None,
        "current_day_followed_up": False,
        "proctor_violations": 0,
        "proctor_warned": False
    }
    SESSIONS[session_id] = session

    day_plan = plan[0]
    q = LEGACY_AGENT.opening_question(day_plan["day"], day_plan["stance"])
    session["current_question"] = q

    return {
        "session_id": session_id,
        "candidate_name": candidate["name"],
        "question": _serialize_question(q),
        "progress": _progress(session),
        "initial_agent_message": q["text"]
    }

@router.post("/interview/proctor_check")
@router.post("/v1/interview/proctor_check")
async def proctor_check(req: dict, user: Optional[dict] = Depends(get_current_user)):
    """
    Strict Live Real-time Camera Perception Check Endpoint.
    Evaluates face presence, off-screen gaze (left/right/away), multiple faces, tab switches, and secondary devices.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    session_id = req.get("session_id")
    session = SESSIONS.get(session_id)
    if not session or session["status"] != "in_progress":
        return {"status": "ignored"}

    metrics_raw = req.get("metrics", {})
    metrics = PerceptionMetrics(**metrics_raw) if metrics_raw else PerceptionMetrics()

    is_flagged = False
    reason = None

    if metrics.face_count == 0:
        is_flagged = True
        reason = "Proctor Warning: Candidate face lost from camera frame. Please remain seated facing your camera."
    elif metrics.looking_left:
        is_flagged = True
        reason = "Proctor Warning: Off-screen gaze detected looking left. Please maintain direct eye contact with the camera."
    elif metrics.looking_right:
        is_flagged = True
        reason = "Proctor Warning: Off-screen gaze detected looking right. Please look straight at the main screen."
    elif metrics.face_count > 1:
        is_flagged = True
        reason = "Proctor Warning: Multiple individuals / entities detected in camera frame. The interview must be taken alone."
    elif metrics.suspicious_flag or metrics.looking_away:
        is_flagged = True
        reason = f"Proctor Warning: Off-screen distraction / tab switch detected ({metrics.violation_reason or 'looking away'})."

    if is_flagged:
        current_v = session.get("proctor_violations", 0) + 1
        session["proctor_violations"] = current_v

        if current_v >= 2:
            session["status"] = "cancelled"
            return {
                "status": "cancelled",
                "violation_count": current_v,
                "reason": reason
            }
        else:
            session["proctor_warned"] = True
            return {
                "status": "warning",
                "violation_count": current_v,
                "reason": reason
            }

    return {
        "status": "ok",
        "violation_count": session.get("proctor_violations", 0)
    }

@router.post("/interview/answer")
@router.post("/v1/interview/answer")
@router.post("/v1/interview/chat")
async def answer(req: AnswerRequest, user: Optional[dict] = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required to submit an answer")

    session = SESSIONS.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Unknown session_id")
    if session["status"] == "completed":
        raise HTTPException(status_code=400, detail="Interview already completed; fetch the report")

    candidate = CANDIDATES[session["candidate_id"]]
    metrics = req.perception_metrics or PerceptionMetrics()

    score, next_q = await STATE_MACHINE.execute_turn(
        session, candidate, req.answer, metrics, debate_mode=req.debate_mode
    )

    return {
        "session_id": req.session_id,
        "evaluation": {
            "score_5": score["score_5"],
            "coverage_ratio": score["coverage_ratio"],
            "missing_terms": score["missing_terms"],
            "confidence": score.get("confidence", 1.0)
        },
        "question": _serialize_question(next_q),
        "agent_message": next_q["text"] if next_q else "Interview complete.",
        "is_completed": next_q is None,
        "progress": _progress(session),
    }

@router.get("/interview/{session_id}/report")
@router.get("/v1/interview/feedback/{session_id}")
def report(session_id: str, user: Optional[dict] = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required to view feedback report")

    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Unknown session_id")
    candidate = CANDIDATES[session["candidate_id"]]
    if not any(t["role"] == "candidate" for t in session["turns"]):
        raise HTTPException(status_code=400, detail="No answers submitted yet")
    return LEGACY_AGENT.build_feedback(session, candidate)
