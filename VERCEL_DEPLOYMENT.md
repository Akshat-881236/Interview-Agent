# The Interview Agent — Vercel Deployment Guide

This guide provides step-by-step instructions to deploy **The Interview Agent** (FastAPI Serverless Backend + Glassmorphism Frontend + 4-Tier LLM Pipeline) on **[Vercel](https://vercel.com)**.

---

## ⚡ 1-Click Deployment via Vercel CLI or Vercel Dashboard

The repository includes a root [`vercel.json`](file:///c:/Users/HP/OneDrive/Desktop/Firebase%20Projects/interview-agent/vercel.json) configuration mapping API routes `/api/*` to Python Serverless Functions and serving the static frontend interface seamlessly.

---

### Option A: Deploy via Vercel Web Dashboard (Recommended)

1. Go to your **[Vercel Dashboard](https://vercel.com/dashboard)** and click **Add New... → Project**.
2. Import your GitHub repository:
   `https://github.com/Akshat-881236/Interview-Agent.git`
3. In the **Configure Project** screen:
   - **Framework Preset**: Select `Other` (or leave default).
   - **Root Directory**: `./` (leave default).
4. Expand the **Environment Variables** section and add your secrets:

| Environment Variable | Description / Sample Value | Required |
| :--- | :--- | :--- |
| `OLLAMA_API_KEY` | Your Ollama API Key | Yes |
| `CLAUDE_API_KEY` | Your Anthropic Claude API Key | Yes |
| `GROQ_API_KEY` | Your Groq API Key | Yes |
| `GEMINI_API_KEY` | Your Google Gemini API Key | Yes |
| `JWT_SECRET_KEY` | Secret JWT Signing Key | Yes |
| `OLLAMA_HOST` | `http://localhost:11434` *(or Ollama Cloud Endpoint)* | Yes |

5. Click **Deploy**. Vercel will automatically build the Python serverless backend and deploy your static assets.

---

### Option B: Deploy via Vercel CLI

If you have Vercel CLI installed locally:

```bash
# 1. Install Vercel CLI
npm install -g vercel

# 2. Login to Vercel
vercel login

# 3. Deploy to Preview
vercel

# 4. Deploy to Production
vercel --prod
```

---

## 🔍 Verification & Testing

Once Vercel assigns your production URL (e.g., `https://interview-agent.vercel.app`):

1. **Verify Health Endpoint**:
   ```bash
   curl https://interview-agent.vercel.app/api/health
   ```
   **Response**:
   ```json
   {"status": "ok", "service": "The Interview Agent API", "version": "2.1.0"}
   ```
2. **Access Web App**:
   Visit `https://interview-agent.vercel.app` in any modern browser to launch the AI Technical Interview Studio.
