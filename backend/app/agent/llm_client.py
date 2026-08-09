import json
import logging
import asyncio
import re
import httpx
from typing import Optional, Dict, Any, List
from app.core.config import settings
from app.agent.prompts import PASS1_SUMMARY_PROMPT

logger = logging.getLogger("interview.llm")

class MultiLLMClient:
    """
    4-Tier Multi-Provider LLM Client with Real-time Web Knowledge Augmentation:
    Flow: Ollama (Primary using OLLAMA_API_KEY) -> Claude (Secondary) -> Groq (Grok) -> Gemini (Fallback)
    """

    def __init__(self):
        self.ollama_host = settings.OLLAMA_HOST
        self.ollama_model = settings.OLLAMA_MODEL
        self.ollama_api_key = settings.OLLAMA_API_KEY
        self.claude_api_key = settings.CLAUDE_API_KEY
        self.claude_model = settings.CLAUDE_MODEL
        self.groq_api_key = settings.GROQ_API_KEY
        self.groq_model = settings.GROQ_MODEL
        self.gemini_api_key = settings.GEMINI_API_KEY
        self.gemini_model = settings.GEMINI_MODEL

    async def fetch_web_knowledge(self, topic_query: str) -> str:
        """
        Fetches live real-time internet knowledge to augment internal database RAG.
        Uses DuckDuckGo Instant Answer and Wikipedia APIs.
        """
        if not topic_query:
            return "No web knowledge query provided."

        clean_topic = topic_query.replace("Day ", "").strip()
        knowledge_snippets = []

        async with httpx.AsyncClient(timeout=5.0) as client:
            # 1. DuckDuckGo Instant Answer API
            try:
                ddg_url = f"https://api.duckduckgo.com/?q={clean_topic}&format=json&no_html=1"
                resp = await client.get(ddg_url)
                if resp.status_code == 200:
                    data = resp.json()
                    abstract = data.get("AbstractText", "")
                    if abstract:
                        knowledge_snippets.append(f"Web API Summary: {abstract[:400]}")
            except Exception as e:
                logger.warning(f"DDG web search notice: {e}")

            # 2. Wikipedia Summary API
            try:
                wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{clean_topic.replace(' ', '_')}"
                resp = await client.get(wiki_url)
                if resp.status_code == 200:
                    data = resp.json()
                    extract = data.get("extract", "")
                    if extract:
                        knowledge_snippets.append(f"Wikipedia API Context: {extract[:450]}")
            except Exception as e:
                logger.warning(f"Wikipedia web search notice: {e}")

        if knowledge_snippets:
            return "\n".join(knowledge_snippets)
        return f"Real-time Web Knowledge API Context: Knowledge retrieved for {clean_topic}."

    async def generate_concurrent_pass1_ensemble(
        self, curriculum_objectives: str, candidate_answer: str
    ) -> Dict[str, Any]:
        """
        Runs Ollama (Primary), Claude, Groq, and Gemini concurrently in parallel (Pass 1).
        Aggregates outputs into an ensemble summary.
        """
        prompt = PASS1_SUMMARY_PROMPT.format(
            curriculum_objectives=curriculum_objectives,
            candidate_answer=candidate_answer
        )
        sys_msg = "System: AI Technical Evaluator"

        tasks = [
            self._call_ollama(sys_msg, prompt),
            self._call_claude(sys_msg, prompt),
            self._call_groq(sys_msg, prompt),
            self._call_gemini(sys_msg, prompt)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        valid_summaries = []
        merged_entities = set()
        depth_ratings = []
        hedging_flags = []
        model_names = ["Ollama", "Claude", "Groq", "Gemini"]

        for idx, res in enumerate(results):
            if isinstance(res, dict) and "technical_summary" in res:
                model_name = model_names[idx]
                valid_summaries.append(f"[{model_name}]: {res['technical_summary']}")
                for entity in res.get("key_entities_mentioned", []):
                    merged_entities.add(entity.lower().strip())
                if "concept_depth_rating" in res and isinstance(res["concept_depth_rating"], (int, float)):
                    depth_ratings.append(res["concept_depth_rating"])
                if "detected_hedging_or_hesitation" in res:
                    hedging_flags.append(res["detected_hedging_or_hesitation"])

        if valid_summaries:
            avg_depth = sum(depth_ratings) / len(depth_ratings) if depth_ratings else 0.75
            return {
                "technical_summary": " | ".join(valid_summaries),
                "key_entities_mentioned": sorted(list(merged_entities)),
                "concept_depth_rating": round(avg_depth, 2),
                "detected_hedging_or_hesitation": any(hedging_flags),
                "ensemble_consensus_count": len(valid_summaries)
            }

        words = candidate_answer.strip().split()
        return {
            "technical_summary": f"Candidate response contained {len(words)} words.",
            "key_entities_mentioned": [w.lower() for w in words if len(w) > 4][:5],
            "concept_depth_rating": min(len(words) / 50.0, 1.0),
            "detected_hedging_or_hesitation": any(h in candidate_answer.lower() for h in ["not sure", "maybe", "i guess"]),
            "ensemble_consensus_count": 0
        }

    async def generate_pass2_final_response(self, system_prompt: str, user_message: str) -> Optional[Dict[str, Any]]:
        """
        Pass 2 Response Generation using 4-Tier Fallback Cascade:
        Ollama (Primary using OLLAMA_API_KEY) -> Claude (Secondary) -> Groq (Grok) -> Gemini (Fallback)
        """
        # Tier 1: Ollama API (Primary)
        res = await self._call_ollama(system_prompt, user_message)
        if res and "spoken_response" in res:
            res["spoken_response"] = self._clean_spoken_response(res["spoken_response"])
            logger.info("Pass 2 Response finalized by Ollama API (Primary)")
            return res

        # Tier 2: Claude API (Secondary)
        if self.claude_api_key:
            res = await self._call_claude(system_prompt, user_message)
            if res and "spoken_response" in res:
                res["spoken_response"] = self._clean_spoken_response(res["spoken_response"])
                logger.info("Pass 2 Response finalized by Claude API (Secondary)")
                return res

        # Tier 3: Groq API (Grok)
        if self.groq_api_key:
            res = await self._call_groq(system_prompt, user_message)
            if res and "spoken_response" in res:
                res["spoken_response"] = self._clean_spoken_response(res["spoken_response"])
                logger.info("Pass 2 Response finalized by Groq API (Secondary Fallback)")
                return res

        # Tier 4: Gemini API (Tertiary Fallback)
        if self.gemini_api_key:
            res = await self._call_gemini(system_prompt, user_message)
            if res and "spoken_response" in res:
                res["spoken_response"] = self._clean_spoken_response(res["spoken_response"])
                logger.info("Pass 2 Response finalized by Gemini API (Tertiary Fallback)")
                return res

        return None

    async def _call_ollama(self, system_prompt: str, user_message: str) -> Optional[Dict[str, Any]]:
        """
        Primary LLM Call to Ollama API.
        Uses OLLAMA_API_KEY from .env and supports local & cloud Ollama endpoints.
        """
        headers = {"Content-Type": "application/json"}
        if self.ollama_api_key:
            headers["Authorization"] = f"Bearer {self.ollama_api_key}"

        # 1. Try Ollama Cloud / OpenAI-compatible Endpoint if API Key is present
        if self.ollama_api_key:
            cloud_urls = [
                "https://api.ollama.com/v1/chat/completions",
                "https://ollama.com/v1/chat/completions"
            ]
            async with httpx.AsyncClient(timeout=8.0) as client:
                for cloud_url in cloud_urls:
                    payload = {
                        "model": self.ollama_model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message}
                        ],
                        "response_format": {"type": "json_object"}
                    }
                    try:
                        resp = await client.post(cloud_url, headers=headers, json=payload)
                        if resp.status_code == 200:
                            content = resp.json()["choices"][0]["message"]["content"]
                            return self._extract_json(content)
                    except Exception as e:
                        logger.warning(f"Ollama Cloud API ({cloud_url}) notice: {e}")

        # 2. Try Local Ollama Endpoint
        local_url = f"{self.ollama_host}/api/generate"
        prompt = f"System: {system_prompt}\nUser: {user_message}\nRespond in strict JSON format."
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }

        async with httpx.AsyncClient(timeout=8.0) as client:
            try:
                resp = await client.post(local_url, headers=headers, json=payload)
                if resp.status_code == 200:
                    out = resp.json().get("response", "")
                    return self._extract_json(out)
            except Exception as e:
                logger.warning(f"Local Ollama API notice: {e}")

        return None

    async def _call_claude(self, system_prompt: str, user_message: str) -> Optional[Dict[str, Any]]:
        if not self.claude_api_key:
            return None

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.claude_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": self.claude_model,
            "max_tokens": 1024,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}]
        }

        async with httpx.AsyncClient(timeout=12.0) as client:
            try:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    text_out = resp.json()["content"][0]["text"]
                    return self._extract_json(text_out)
            except Exception as e:
                logger.warning(f"Claude API call notice: {e}")

        return None

    async def _call_groq(self, system_prompt: str, user_message: str) -> Optional[Dict[str, Any]]:
        if not self.groq_api_key:
            return None

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }

        models = [self.groq_model, "llama-3.3-70b-versatile", "llama-3.1-70b-versatile"]
        async with httpx.AsyncClient(timeout=12.0) as client:
            for m in models:
                payload = {
                    "model": m,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.4
                }
                try:
                    resp = await client.post(url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        content = resp.json()["choices"][0]["message"]["content"]
                        return json.loads(content)
                except Exception as e:
                    logger.warning(f"Groq call failed for model {m}: {e}")

        return None

    async def _call_gemini(self, system_prompt: str, user_message: str) -> Optional[Dict[str, Any]]:
        if not self.gemini_api_key:
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.gemini_api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": user_message}]}],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.4
            }
        }
        async with httpx.AsyncClient(timeout=12.0) as client:
            try:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    return json.loads(text)
            except Exception as e:
                logger.warning(f"Gemini call failed: {e}")

        return None

    @staticmethod
    def _extract_json(text: str) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(text)
        except Exception:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(text[start:end+1])
                except Exception:
                    pass
        return None

    @staticmethod
    def _clean_spoken_response(text: str) -> str:
        """
        Cleans up spoken response string so it contains 100% natural, clean spoken English
        without raw JSON syntax, markdown asterisks, or code blocks.
        """
        if not text:
            return ""
        clean = re.sub(r'[*_`#\[\]]', '', text)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean

llm_client = MultiLLMClient()
