"""
agent.py — The Interview Agent's brain.

Responsible for:
  1. Building a personalized interview plan from a candidate profile
     (which days to ask about, and in what spirit — probe strength,
     verify skipped topics, or push on a struggle area).
  2. Generating the next question given interview state.
  3. Deciding, from the candidate's last answer, whether to ask an
     intelligent follow-up (grounded via rag.py) or move on.
  4. Producing structured, evidence-based feedback at the end.

This is intentionally template + retrieval driven rather than a single
opaque model call, so every question and every score can be traced back to
*why* the agent asked it — which is exactly what we'd want to audit in an
interview tool. The `NOTE` in each generator shows where a real LLM call
(Claude/GPT) would slot in to paraphrase/vary the template output, using the
same grounding context, if you want more linguistic variety.
"""
import random
import uuid

from rag import RagIndex

MIN_QUESTIONS = 8
MIN_DAYS = 4
TARGET_DAYS = 6

OPENERS = [
    "Let's dig into {topic}.",
    "I'd like to walk through {topic} with you.",
    "Next, let's talk about {topic}.",
    "Shifting gears — {topic}.",
]

STRUCTURE_TEMPLATES = {
    "why": "Walk me through how you would {objective_lc}. Why does that matter in a real system?",
    "howwould": "Suppose you had to {objective_lc} on a live project — how would you approach it, concretely?",
    "tradeoff": "What trade-offs did you run into when you had to {objective_lc}?",
    "compare": "How would you {objective_lc}, and what would you do differently on your second attempt?",
}

SKIPPED_TEMPLATES = [
    "I noticed {topic} isn't in your completed missions yet. In plain terms, what do you understand about it, and where would you start?",
    "You haven't logged {topic} as completed — no penalty for that. What's your working mental model of it, even if incomplete?",
]

FOLLOWUP_TEMPLATES = {
    "missing_concept": "You didn't mention {term} — where does that fit into your answer?",
    "push_deeper": "That's a fair start. Push one level deeper — what would break if {topic_lc} were implemented that way at scale?",
    "concrete_example": "Can you make that concrete with a specific example from something you built?",
    "counterpoint": "What's the strongest argument *against* the approach you just described?",
    "short_answer": "Say a bit more — what's actually happening under the hood when you {objective_lc}?",
}

HEDGE_WORDS = ["not sure", "i don't know", "no idea", "i guess", "maybe", "not really sure", "i'm not certain"]


def _lc_first(s: str) -> str:
    return s[0].lower() + s[1:] if s else s


class InterviewAgent:
    def __init__(self, curriculum: dict, rag_index: RagIndex):
        self.curriculum = curriculum
        self.rag = rag_index
        self.days_by_id = self.rag.by_day

    # ---------- Plan building ----------

    def build_plan(self, candidate: dict) -> list:
        """
        Choose which curriculum days to interview on, and the *stance* for
        each: 'strength' (verify depth on something they're strong in),
        'core' (a completed day, standard depth check), or 'gap' (a skipped
        or struggled day, testing baseline awareness + growth mindset).
        Ensures topic diversity across modules and >= TARGET_DAYS days.
        """
        completed = set(candidate.get("completed_days", []))
        struggled = set(candidate.get("attempted_but_struggled_days", []))
        skipped = set(candidate.get("skipped_days", []))
        strong_topics = set(candidate.get("learning_signals", {}).get("strong_topics", []))

        plan = []
        used_modules = set()

        # Pass 1: one strength-probe per distinct module, from completed days
        # whose topic is flagged as a strong topic.
        for module in self.curriculum["modules"]:
            mod_title = module.get("title", module.get("module", ""))
            for day_id in module["days"]:
                doc = self.days_by_id.get(day_id, {})
                topic = doc.get("topic", "")
                if day_id in completed and (topic in strong_topics or f"Day {day_id}" in strong_topics) and mod_title not in used_modules:
                    plan.append({"day": day_id, "stance": "strength"})
                    used_modules.add(mod_title)
                    break

        # Pass 2: fill remaining module diversity with 'core' completed days.
        for module in self.curriculum["modules"]:
            mod_title = module.get("title", module.get("module", ""))
            if mod_title in used_modules:
                continue
            candidates_in_module = [d for d in module["days"] if d in completed]
            if candidates_in_module:
                pick = candidates_in_module[len(candidates_in_module) // 2]
                plan.append({"day": pick, "stance": "core"})
                used_modules.add(mod_title)

        # Pass 3: add one 'gap' probe (struggled first, else skipped) to test
        # growth areas honestly — real interviews don't only ask what you're good at.
        gap_pool = list(struggled) or list(skipped)
        if gap_pool:
            gap_day = sorted(gap_pool)[0]
            if not any(p["day"] == gap_day for p in plan):
                plan.append({"day": gap_day, "stance": "gap"})

        # Pass 4: top up to TARGET_DAYS using any remaining completed days, in day order.
        if len(plan) < TARGET_DAYS:
            already = {p["day"] for p in plan}
            for d in sorted(completed):
                if len(plan) >= TARGET_DAYS:
                    break
                if d not in already:
                    plan.append({"day": d, "stance": "core"})
                    already.add(d)

        # Sort the plan into a sensible chronological interview arc (fundamentals -> advanced).
        plan.sort(key=lambda p: p["day"])
        return plan[:TARGET_DAYS] if len(plan) > TARGET_DAYS else plan

    # ---------- Question generation ----------

    def opening_question(self, day: int, stance: str) -> dict:
        doc = self.days_by_id[day]
        objective = random.choice(doc["objectives"])
        topic = doc["topic"]

        if stance == "gap":
            text = random.choice(SKIPPED_TEMPLATES).format(topic=topic)
        else:
            style = random.choice(list(STRUCTURE_TEMPLATES.keys()))
            opener = random.choice(OPENERS).format(topic=topic)
            text = f"{opener} {STRUCTURE_TEMPLATES[style].format(objective_lc=_lc_first(objective))}"

        return {
            "id": str(uuid.uuid4())[:8],
            "type": "primary",
            "day": day,
            "topic": topic,
            "module": doc["module"],
            "stance": stance,
            "text": text,
        }

    def followup_question(self, day: int, prior_answer: str, missing_terms: list) -> dict:
        doc = self.days_by_id[day]
        objective = random.choice(doc["objectives"])

        if len(prior_answer.split()) < 12:
            text = FOLLOWUP_TEMPLATES["short_answer"].format(objective_lc=_lc_first(objective))
        elif missing_terms:
            # Ground the follow-up in an actual missing concept from the curriculum (RAG-lite signal).
            term = missing_terms[0]
            text = FOLLOWUP_TEMPLATES["missing_concept"].format(term=term)
        else:
            text = random.choice([
                FOLLOWUP_TEMPLATES["push_deeper"].format(topic_lc=_lc_first(doc["topic"])),
                FOLLOWUP_TEMPLATES["concrete_example"],
                FOLLOWUP_TEMPLATES["counterpoint"],
            ])

        return {
            "id": str(uuid.uuid4())[:8],
            "type": "followup",
            "day": day,
            "topic": doc["topic"],
            "module": doc["module"],
            "stance": "followup",
            "text": text,
        }

    # ---------- Scoring ----------

    def score_answer(self, answer_text: str, day: int) -> dict:
        ratio, missing, matched = self.rag.coverage_score(answer_text, day)
        words = answer_text.strip().split()
        length_signal = min(len(words) / 60.0, 1.0)  # saturates around ~60 words
        hedges = sum(1 for h in HEDGE_WORDS if h in answer_text.lower())
        confidence = max(0.0, 1.0 - 0.35 * hedges)

        # blended 0-5 score
        raw = (0.55 * ratio + 0.30 * length_signal + 0.15 * confidence)
        score_5 = round(raw * 5, 1)

        return {
            "coverage_ratio": round(ratio, 2),
            "matched_terms": matched,
            "missing_terms": missing,
            "length_words": len(words),
            "confidence": round(confidence, 2),
            "score_5": score_5,
        }

    def should_follow_up(self, score: dict, already_followed_up: bool) -> bool:
        if already_followed_up:
            return False
        return score["coverage_ratio"] < 0.6 or score["length_words"] < 20

    # ---------- Final feedback ----------

    def build_feedback(self, session: dict, candidate: dict) -> dict:
        per_day = {}
        for turn in session["turns"]:
            if turn["role"] != "candidate":
                continue
            d = turn["day"]
            per_day.setdefault(d, []).append(turn["score"]["score_5"])

        day_reports = []
        for d, scores in sorted(per_day.items()):
            doc = self.days_by_id[d]
            avg = round(sum(scores) / len(scores), 1)
            verdict = (
                "Strong" if avg >= 4 else
                "Solid" if avg >= 3 else
                "Developing" if avg >= 2 else
                "Needs review"
            )
            day_reports.append({
                "day": d,
                "topic": doc["topic"],
                "module": doc["module"],
                "avg_score": avg,
                "verdict": verdict,
            })

        overall = round(sum(r["avg_score"] for r in day_reports) / len(day_reports), 2) if day_reports else 0.0
        strengths = [r for r in day_reports if r["avg_score"] >= 3.5]
        growth = [r for r in day_reports if r["avg_score"] < 3.0]

        readiness = (
            "Interview-ready" if overall >= 4 else
            "Close, with a few gaps to close" if overall >= 3 else
            "Needs focused review before interviewing" if overall >= 2 else
            "Not yet ready — revisit fundamentals"
        )

        recommended_next = []
        for d in sorted(candidate.get("skipped_days", []))[:3]:
            doc = self.days_by_id.get(d)
            if doc:
                recommended_next.append(f"Day {d}: {doc['topic']}")
        for r in growth:
            label = f"Day {r['day']}: {r['topic']} (revisit)"
            if label not in recommended_next:
                recommended_next.append(label)

        return {
            "candidate_id": candidate["candidate_id"],
            "candidate_name": candidate["name"],
            "days_covered": [r["day"] for r in day_reports],
            "questions_asked": sum(1 for t in session["turns"] if t["role"] == "agent"),
            "overall_score": overall,
            "readiness": readiness,
            "day_reports": day_reports,
            "strengths": [f"{r['topic']} (Day {r['day']}) — avg {r['avg_score']}/5" for r in strengths] or ["No section scored above 3.5 yet — see growth areas."],
            "growth_areas": [f"{r['topic']} (Day {r['day']}) — avg {r['avg_score']}/5" for r in growth] or ["No significant gaps surfaced in this session."],
            "recommended_next_steps": recommended_next[:5] or ["Keep reinforcing current strengths with mock system-design walkthroughs."],
            "narrative": self._narrative(candidate["name"], overall, strengths, growth, day_reports),
        }

    @staticmethod
    def _narrative(name, overall, strengths, growth, day_reports) -> str:
        s = f"{name} was interviewed across {len(day_reports)} curriculum days and answered with an overall score of {overall}/5. "
        if strengths:
            s += f"The strongest section was {strengths[0]['topic']} (Day {strengths[0]['day']}), where answers were specific and used the correct technical vocabulary. "
        if growth:
            s += f"The clearest area to revisit is {growth[0]['topic']} (Day {growth[0]['day']}) — answers there were shorter or missed key concepts. "
        s += "Overall, this reads as a candidate who can build these systems; the gap between doing and explaining is the main thing to close before a live interview."
        return s
