import os

def _load_env_file(filepath: str):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'").strip('"')
                    if k not in os.environ:
                        os.environ[k] = v

env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
_load_env_file(env_path)

class Settings:
    PROJECT_NAME: str = "The Interview Agent · AI Cohort"
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    ENV: str = os.getenv("ENV", "development")

    # Authentication
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "interview-agent-11143443")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    # LLM Priority 1: Ollama API (Primary)
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")
    OLLAMA_API_KEY: str = os.getenv("OLLAMA_API_KEY", "")

    # LLM Priority 2: Claude API (Secondary)
    CLAUDE_API_KEY: str = os.getenv("CLAUDE_API_KEY", "")
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")

    # LLM Priority 3: Groq API (Grok Secondary)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # LLM Priority 4: Gemini API (Tertiary Fallback)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    ALLOW_RULE_BASED_FALLBACK: bool = os.getenv("ALLOW_RULE_BASED_FALLBACK", "true").lower() == "true"

settings = Settings()
