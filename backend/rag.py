import re
import math
from collections import Counter

STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with",
    "is", "are", "was", "were", "be", "as", "at", "by", "it", "this",
    "that", "your", "you", "i", "we", "our", "how", "what", "why", "do",
    "does", "did", "so", "can", "could", "would", "should", "into", "vs",
}

INSTRUCTIONAL_VERBS = {
    "explain", "design", "build", "apply", "compare", "implement", "measure",
    "choose", "differentiate", "expose", "handle", "define", "mitigate",
    "instrument", "detect", "present", "defend", "reason", "stand", "load",
    "tune", "combine", "diagnose", "ship", "distinguish", "map", "write",
    "manage", "connect", "add", "prevent", "trade", "off", "make", "run",
    "reduce", "walk", "through", "stack", "based", "app", "modern", "using",
}

def tokenize(text: str):
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9\-\+]*", text.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 1]

class RagIndex:
    """TF-based retrieval index over curriculum days."""

    def __init__(self, curriculum: dict):
        self.docs = []
        days_list = curriculum.get("days", [])
        
        # Build module mapping for each day
        module_map = {}
        for mod in curriculum.get("modules", []):
            mod_title = mod.get("title", f"Module {mod.get('n', '')}")
            for d in mod.get("days", []):
                module_map[d] = mod_title

        for day in days_list:
            topic = day.get("title") or day.get("topic") or ""
            objectives = day.get("objectives") or day.get("learning_objectives") or []
            tools = day.get("tools") or []
            day_num = day.get("day", 0)

            text = " ".join([topic] + objectives + tools)
            self.docs.append({
                "day": day_num,
                "module": module_map.get(day_num, "General"),
                "topic": topic,
                "objectives": objectives,
                "tools": tools,
                "tf": Counter(tokenize(text)),
                "tokens": set(tokenize(text)),
            })
        self.by_day = {d["day"]: d for d in self.docs}

    @staticmethod
    def _cosine(a: Counter, b: Counter) -> float:
        common = set(a) & set(b)
        num = sum(a[t] * b[t] for t in common)
        if num == 0:
            return 0.0
        mag_a = math.sqrt(sum(v * v for v in a.values()))
        mag_b = math.sqrt(sum(v * v for v in b.values()))
        return num / (mag_a * mag_b + 1e-9)

    def retrieve(self, query_text: str, top_k: int = 3, exclude_day: int = None):
        q_tf = Counter(tokenize(query_text))
        scored = []
        for d in self.docs:
            if exclude_day is not None and d["day"] == exclude_day:
                continue
            score = self._cosine(q_tf, d["tf"])
            if score > 0:
                scored.append((score, d))
        scored.sort(key=lambda x: -x[0])
        return [d for _, d in scored[:top_k]]

    def coverage_score(self, answer_text: str, day: int):
        doc = self.by_day.get(day)
        if not doc:
            return 0.0, [], []
        key_terms = tokenize(" ".join(doc["objectives"] + doc["tools"] + [doc["topic"]]))
        key_terms = [t for t in key_terms if t not in INSTRUCTIONAL_VERBS]
        key_terms = list(dict.fromkeys(key_terms))
        if not key_terms:
            return 0.0, [], []
        answer_tokens = set(tokenize(answer_text))
        matched = [t for t in key_terms if t in answer_tokens]
        missing = [t for t in key_terms if t not in answer_tokens]
        ratio = len(matched) / len(key_terms)
        return ratio, missing, matched
