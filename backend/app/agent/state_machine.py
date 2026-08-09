import json
import logging
from typing import Dict, Any, Tuple

from app.agent.prompts import MASTER_SYSTEM_PROMPT
from app.agent.llm_client import llm_client
from app.agent.strategies.communication_strategy import communication_engine
from app.agent.strategies.knowledge_sync_strategy import knowledge_sync_engine
from app.models.schemas import PerceptionMetrics
from agent import InterviewAgent, MIN_QUESTIONS, MIN_DAYS
from rag import RagIndex

logger = logging.getLogger("interview.state_machine")

class InterviewStateMachine:
    def __init__(self, curriculum: dict, rag_index: RagIndex):
        self.curriculum = curriculum
        self.rag = rag_index
        self.agent = InterviewAgent(curriculum, rag_index)
        self.rl_q_weights = {}

    async def execute_turn(
        self,
        session: Dict[str, Any],
        candidate: Dict[str, Any],
        user_answer: str,
        metrics: PerceptionMetrics,
        debate_mode: bool = False
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Executes interview turn with Smart Strategy Engine, Dynamic Web API Knowledge Sync,
        and 4-Tier Model Cascade (Ollama -> Claude -> Groq -> Gemini).
        """
        plan = session["plan"]
        idx = session["plan_index"]
        current_question = session["current_question"]
        current_day = current_question["day"] if current_question else plan[idx]["day"]

        day_doc = self.rag.by_day.get(current_day, {})
        topic_name = day_doc.get("topic", "")
        objectives = day_doc.get("objectives", [])
        rag_context_str = f"Topic: {topic_name}\nModule: {day_doc.get('module', '')}\nObjectives:\n" + "\n".join(f"- {o}" for o in objectives)

        # ---------------------------------------------------------------------
        # 1. COMMUNICATION STRATEGY & DYNAMIC WEB KNOWLEDGE SEARCH
        # ---------------------------------------------------------------------
        strategy_analysis = communication_engine.analyze_candidate_response(user_answer, topic_name)
        web_knowledge_context = await knowledge_sync_engine.fetch_dynamic_knowledge(user_answer, topic_name)

        # ---------------------------------------------------------------------
        # 2. PARALLEL PASS 1 ENSEMBLE: Ollama, Claude, Groq & Gemini
        # ---------------------------------------------------------------------
        pass1_ensemble = await llm_client.generate_concurrent_pass1_ensemble(rag_context_str, user_answer)

        # ---------------------------------------------------------------------
        # 3. PYTHON INTERMEDIATE DSA LAYER & STRICT PROCTOR RULES
        # ---------------------------------------------------------------------
        score = self.agent.score_answer(user_answer, current_day)
        
        # RL Weight Update Algorithm
        cand_id = candidate.get("candidate_id", "default")
        rl_weight = self.rl_q_weights.get(cand_id, 1.0)
        if score["coverage_ratio"] > 0.7:
            rl_weight = min(rl_weight + 0.1, 1.5)
        else:
            rl_weight = max(rl_weight - 0.1, 0.7)
        self.rl_q_weights[cand_id] = rl_weight

        # Strict Camera Perception Rules
        current_violations = session.get("proctor_violations", 0)
        specific_proctor_warning = None

        if metrics.face_count == 0:
            current_violations += 1
            specific_proctor_warning = "Proctor Warning: Candidate face lost from camera frame. Please remain seated facing your camera."
        elif metrics.looking_left:
            current_violations += 1
            specific_proctor_warning = "Proctor Warning: Off-screen gaze detected looking left. Please maintain direct eye contact with the camera."
        elif metrics.looking_right:
            current_violations += 1
            specific_proctor_warning = "Proctor Warning: Off-screen gaze detected looking right. Please look straight at the main screen."
        elif metrics.face_count > 1:
            current_violations += 1
            specific_proctor_warning = "Proctor Warning: Multiple individuals detected in camera frame. The interview must be taken alone."
        elif metrics.unnecessary_emotion:
            current_violations += 1
            emotion_label = metrics.emotion_type or "distracted"
            specific_proctor_warning = f"Proctor Warning: Unnecessary emotional expression ({emotion_label}) detected. Please maintain professional focus."
        elif metrics.suspicious_flag or metrics.looking_away:
            current_violations += 1
            specific_proctor_warning = f"Proctor Warning: Off-screen camera distraction detected ({metrics.violation_reason or 'looking away'})."

        session["proctor_violations"] = current_violations

        # Termination on 2nd Violation
        if current_violations >= 2:
            session["status"] = "cancelled"
            session["current_question"] = None
            cancellation_q = {
                "id": "cancellation_notice",
                "type": "cancellation",
                "day": current_day,
                "topic": "Proctoring Integrity Failure",
                "text": specific_proctor_warning or "Proctor Notice: Multiple camera proctoring violations detected. Interview terminated due to non-compliance.",
                "action": "CANCEL_INTERVIEW",
                "proctor_violation": current_violations
            }
            return score, cancellation_q

        # First Violation Warning
        if specific_proctor_warning and current_violations == 1 and not session.get("proctor_warned", False):
            session["proctor_warned"] = True
            warning_q = {
                "id": f"warning_{current_day}",
                "type": "proctor_warning",
                "day": current_day,
                "topic": "Proctor Warning",
                "text": specific_proctor_warning,
                "action": "WARN_PROCTOR_VIOLATION",
                "proctor_violation": 1
            }
            session["current_question"] = warning_q
            return score, warning_q

        # ---------------------------------------------------------------------
        # 4. PASS 2 LLM: Ollama (Primary) -> Claude -> Groq -> Gemini
        # ---------------------------------------------------------------------
        questions_asked = sum(1 for t in session["turns"] if t["role"] == "agent")
        days_covered = len({t["day"] for t in session["turns"] if t["role"] == "agent"})

        system_prompt = MASTER_SYSTEM_PROMPT.format(
            candidate_profile_json=json.dumps({
                "candidate_id": candidate["candidate_id"],
                "name": candidate["name"],
                "role": candidate.get("role", "AI Software Engineer"),
                "learning_signals": candidate.get("learning_signals", {})
            }, indent=2),
            rag_retrieved_objectives=rag_context_str,
            web_knowledge_context=web_knowledge_context,
            strategy_analysis_json=json.dumps(strategy_analysis, indent=2),
            perception_metrics_json=json.dumps(metrics.dict(), indent=2),
            questions_count=questions_asked,
            days_covered_count=days_covered,
            current_curriculum_day=current_day,
            interview_mode="DEBATE_CHALLENGE" if debate_mode else "STANDARD_INTERVIEW"
        )

        user_message = (
            f"Previous Question Asked: {current_question.get('text', '')}\n"
            f"Candidate's Exact Spoken Answer: {user_answer}\n"
            f"Debate Mode: {debate_mode}\n"
            f"INSTRUCTION: First sentence MUST directly address/evaluate/correct the candidate's answer. Second sentence ask follow-up."
        )

        pass2_result = await llm_client.generate_pass2_final_response(system_prompt, user_message)

        if pass2_result and "spoken_response" in pass2_result:
            action = pass2_result.get("action", "DEBATE_CHALLENGE" if debate_mode else "ASK_NEW_TOPIC")
            thought = pass2_result.get("internal_thought_process", "")
            spoken = pass2_result.get("spoken_response", "")

            if action == "CONCLUDE_INTERVIEW" or (questions_asked >= MIN_QUESTIONS and days_covered >= MIN_DAYS and idx >= len(plan) - 1):
                session["status"] = "completed"
                session["current_question"] = None
                next_q = None
            elif debate_mode or action == "DEBATE_CHALLENGE":
                next_q = {
                    "id": f"deb_{current_day}_{questions_asked}",
                    "type": "debate",
                    "day": current_day,
                    "topic": f"Day {current_day} Debate Challenge",
                    "module": day_doc.get("module", ""),
                    "text": spoken,
                    "thought": thought
                }
                session["current_question"] = next_q
            elif action == "ASK_FOLLOW_UP" and not session.get("current_day_followed_up", False):
                session["current_day_followed_up"] = True
                next_q = {
                    "id": f"fu_{current_day}",
                    "type": "followup",
                    "day": current_day,
                    "topic": day_doc.get("topic", ""),
                    "module": day_doc.get("module", ""),
                    "text": spoken,
                    "thought": thought
                }
                session["current_question"] = next_q
            else:
                session["plan_index"] = min(session["plan_index"] + 1, len(plan) - 1)
                next_day_plan = plan[session["plan_index"]]
                next_day = next_day_plan["day"]
                session["current_day_followed_up"] = False
                next_doc = self.rag.by_day.get(next_day, {})
                next_q = {
                    "id": f"q_{next_day}",
                    "type": "primary",
                    "day": next_day,
                    "topic": next_doc.get("topic", ""),
                    "module": next_doc.get("module", ""),
                    "text": spoken,
                    "thought": thought
                }
                session["current_question"] = next_q
        else:
            # Smart Rule Fallback responding directly to candidate answer
            followed_up = session.get("current_day_followed_up", False)
            misconception = strategy_analysis.get("detected_misconception")
            
            if misconception:
                prefix = f"That sounds like {misconception['confused_term']} rather than {misconception['actual_term']}. "
            elif strategy_analysis.get("is_general_query"):
                prefix = "Here is a brief overview from web sources. "
            else:
                prefix = ""

            if debate_mode:
                next_q = {
                    "id": f"deb_{current_day}",
                    "type": "debate",
                    "day": current_day,
                    "topic": day_doc.get("topic", ""),
                    "text": f"{prefix}What specific trade-off breaks first if you scale {day_doc.get('topic', 'this system')} 100-fold under high latency?"
                }
                session["current_question"] = next_q
            elif current_question.get("type") == "primary" and self.agent.should_follow_up(score, followed_up):
                fu = self.agent.followup_question(current_day, user_answer, score["missing_terms"])
                fu["text"] = prefix + fu["text"]
                session["current_question"] = fu
                session["current_day_followed_up"] = True
                next_q = fu
            else:
                session["plan_index"] += 1
                if session["plan_index"] >= len(plan) or (questions_asked >= MIN_QUESTIONS and days_covered >= MIN_DAYS):
                    session["status"] = "completed"
                    session["current_question"] = None
                    next_q = None
                else:
                    next_day_plan = plan[session["plan_index"]]
                    next_q = self.agent.opening_question(next_day_plan["day"], next_day_plan["stance"])
                    next_q["text"] = prefix + next_q["text"]
                    session["current_question"] = next_q
                    session["current_day_followed_up"] = False

        session["turns"].append({"role": "agent", "day": current_day, "question": current_question})
        session["turns"].append({
            "role": "candidate",
            "day": current_day,
            "text": user_answer,
            "score": score,
            "strategy_analysis": strategy_analysis,
            "pass1_ensemble": pass1_ensemble,
            "perception": metrics.dict(),
            "proctor_violations": current_violations
        })

        return score, next_q
