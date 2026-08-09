"""
Generates data/curriculum.json — a synthetic 31-day AI Cohort curriculum.
Run once: python3 build_curriculum.py
"""
import json

MODULES = [
    {
        "module": "Foundations of Applied AI Engineering",
        "days": [
            (1, "AI Engineering Landscape", ["Distinguish AI engineering from ML research", "Map the modern LLM app stack"], ["Python", "Jupyter"]),
            (2, "LLM Fundamentals & Tokens", ["Explain tokenization and context windows", "Reason about temperature, top_p, and sampling"], ["OpenAI API", "Anthropic API"]),
            (3, "Prompt Engineering I: Structure", ["Write system/user/assistant prompts", "Apply few-shot prompting"], ["Claude", "GPT-4"]),
            (4, "Prompt Engineering II: Reasoning", ["Apply chain-of-thought and self-consistency", "Design structured output prompts (JSON mode)"], ["Claude", "Pydantic"]),
            (5, "Evaluating LLM Outputs", ["Build a rubric-based eval harness", "Compare human vs automated grading"], ["Promptfoo", "pytest"]),
        ],
    },
    {
        "module": "Retrieval-Augmented Generation",
        "days": [
            (6, "RAG Fundamentals", ["Explain why RAG reduces hallucination", "Design a retrieve-then-generate pipeline"], ["LangChain", "LlamaIndex"]),
            (7, "Chunking Strategies", ["Compare fixed-size vs semantic chunking", "Tune chunk size/overlap for a corpus"], ["LangChain TextSplitter"]),
            (8, "Embeddings", ["Explain how embedding models map text to vectors", "Choose an embedding model for a domain"], ["OpenAI Embeddings", "sentence-transformers"]),
            (9, "Vector Databases I", ["Compare HNSW vs IVF indexing", "Stand up a vector DB and load documents"], ["Pinecone", "ChromaDB"]),
            (10, "Vector Databases II: Filtering & Hybrid Search", ["Combine metadata filters with vector search", "Implement hybrid (BM25 + vector) search"], ["Weaviate", "pgvector"]),
            (11, "Re-ranking & Retrieval Quality", ["Apply cross-encoder re-ranking", "Measure retrieval precision/recall@k"], ["Cohere Rerank"]),
            (12, "RAG Evaluation", ["Measure faithfulness and answer relevancy", "Diagnose retrieval vs generation failures"], ["RAGAS"]),
            (13, "Advanced RAG Patterns", ["Implement query rewriting and HyDE", "Design multi-hop retrieval for complex questions"], ["LangChain", "LlamaIndex"]),
            (14, "Capstone: Production RAG System", ["Ship an end-to-end RAG service with citations", "Handle out-of-scope questions gracefully"], ["FastAPI", "ChromaDB"]),
        ],
    },
    {
        "module": "Agentic AI",
        "days": [
            (15, "Agents 101", ["Define the agent loop: plan, act, observe", "Distinguish agents from single-shot chains"], ["LangGraph"]),
            (16, "Tool Use & Function Calling", ["Define tool schemas for an LLM", "Handle tool-call errors and retries"], ["Anthropic Tool Use", "OpenAI Functions"]),
            (17, "Multi-Step Planning", ["Implement a ReAct-style reasoning loop", "Prevent infinite tool-call loops"], ["LangGraph"]),
            (18, "Memory in Agents", ["Differentiate short-term vs long-term agent memory", "Implement conversation summarization"], ["Redis", "LangChain Memory"]),
            (19, "Multi-Agent Systems", ["Design agent-to-agent handoff patterns", "Compare orchestrator vs peer-to-peer topologies"], ["CrewAI", "AutoGen"]),
            (20, "Agent Evaluation & Guardrails", ["Write eval traces for agent trajectories", "Add guardrails against prompt injection"], ["Guardrails AI"]),
        ],
    },
    {
        "module": "Model Context Protocol",
        "days": [
            (21, "MCP Fundamentals", ["Explain the client-server-host MCP architecture", "Compare MCP to raw function calling"], ["MCP SDK"]),
            (22, "Building an MCP Server", ["Expose tools, resources, and prompts via MCP", "Handle MCP request/response lifecycle"], ["MCP Python SDK", "Claude Desktop"]),
            (23, "MCP Clients & Hosts", ["Connect an agent host to multiple MCP servers", "Manage MCP auth and permissions"], ["Claude Code", "MCP SDK"]),
            (24, "MCP in Production Workflows", ["Design an MCP-based internal tool ecosystem", "Debug MCP transport and schema errors"], ["MCP Inspector"]),
        ],
    },
    {
        "module": "AI Deployment & Production Systems",
        "days": [
            (25, "Serving LLM Applications", ["Deploy an LLM-backed API behind FastAPI", "Design for streaming responses"], ["FastAPI", "Docker"]),
            (26, "Latency, Cost & Caching", ["Apply prompt/response caching strategies", "Trade off model choice against latency and cost"], ["Redis", "LiteLLM"]),
            (27, "Observability for AI Systems", ["Instrument LLM calls with tracing", "Detect drift in production prompts"], ["LangSmith", "OpenTelemetry"]),
            (28, "Safety, Security & Guardrails", ["Mitigate prompt injection and jailbreaks", "Apply PII redaction before/after model calls"], ["Guardrails AI", "Presidio"]),
            (29, "Scaling AI Systems", ["Design horizontal scaling for inference workloads", "Apply rate limiting and backpressure"], ["Kubernetes", "NGINX"]),
            (30, "CI/CD for AI Systems", ["Build eval gates into a deployment pipeline", "Version prompts and datasets alongside code"], ["GitHub Actions", "DVC"]),
            (31, "Capstone: Ship a Production AI System", ["Present architecture and engineering trade-offs", "Defend design decisions under technical questioning"], ["Full stack"]),
        ],
    },
]

curriculum = {"program": "The AI Cohort", "duration_days": 31, "modules": []}
for m in MODULES:
    mod_entry = {"module": m["module"], "days": []}
    for day, topic, objectives, tools in m["days"]:
        mod_entry["days"].append({
            "day": day,
            "topic": topic,
            "learning_objectives": objectives,
            "tools": tools,
        })
    curriculum["modules"].append(mod_entry)

with open("curriculum.json", "w") as f:
    json.dump(curriculum, f, indent=2)

print("wrote curriculum.json with",
      sum(len(m["days"]) for m in curriculum["modules"]), "days")
