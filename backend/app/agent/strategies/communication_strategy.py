"""
Communication Strategy Engine:
Directs how AI evaluates candidate answers, corrects misconceptions, answers general queries (e.g. World History), and forms follow-up responses.
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

    def analyze_candidate_response(self, candidate_answer: str, current_topic: str) -> Dict[str, Any]:
        """
        Analyzes the candidate's answer for technical misconceptions, off-topic general queries, or core correctness.
        """
        text_lower = candidate_answer.lower()

        # 1. Check for general knowledge queries (e.g. "history of world", "what is war", etc.)
        is_general_query = any(k in text_lower for k in [
            "history of world", "world war", "who is", "tell me about", "what is the history", "general knowledge"
        ])

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
            "detected_misconception": detected_misconception,
            "answer_word_count": len(candidate_answer.split())
        }

communication_engine = CommunicationStrategyEngine()
