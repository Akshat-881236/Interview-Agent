"""
Communication Strategy Engine:
Directs how AI evaluates candidate answers, corrects misconceptions, answers GK & out-of-bound queries (e.g. World History), and forms spoken responses.
"""

import re
import logging
from typing import Dict, Any

logger = logging.getLogger("strategy.communication")

class CommunicationStrategyEngine:
    def __init__(self):
        self.misconception_pairs = [
            (r"\b(iframe|cors|website|embed another website|html)\b", "HTML iframe website embedding", "AI Vector Embeddings"),
            (r"\b(database|sql|table|relational)\b", "Relational SQL database", "Vector Databases & ANN Search"),
            (r"\b(http|api endpoint|rest|json)\b", "REST Web APIs", "LLM Neural Architecture")
        ]

        self.gk_keywords = [
            "history of world", "world war", "who is", "who was", "tell me about",
            "what is the history", "general knowledge", "capital of", "who invented",
            "who discovered", "geography", "quantum computing", "einstein", "newton"
        ]

    def analyze_candidate_response(self, candidate_answer: str, current_topic: str) -> Dict[str, Any]:
        """
        Analyzes the candidate's answer for technical misconceptions, GK / out-of-bound queries, or core correctness.
        """
        text_lower = candidate_answer.lower()

        # 1. Check for general knowledge (GK) or out-of-bound queries
        is_general_query = any(k in text_lower for k in self.gk_keywords)

        # 2. Check for technical term misconceptions
        detected_misconception = None
        for pattern, confused_term, actual_term in self.misconception_pairs:
            if re.search(pattern, text_lower) and "embedding" in current_topic.lower():
                detected_misconception = {
                    "confused_term": confused_term,
                    "actual_term": actual_term,
                    "guidance": f"Candidate appears to confuse {confused_term} with {actual_term}. Politely clarify the distinction before proceeding."
                }
                break

        return {
            "is_general_query": is_general_query,
            "query_type": "GENERAL_KNOWLEDGE" if is_general_query else "TECHNICAL_ANSWER",
            "detected_misconception": detected_misconception,
            "answer_word_count": len(candidate_answer.split())
        }

communication_engine = CommunicationStrategyEngine()
