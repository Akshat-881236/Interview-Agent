# The Interview Agent — Render.com Deployment Guide

This guide provides step-by-step instructions to deploy **The Interview Agent** (FastAPI backend + Glassmorphism frontend + 4-Tier LLM pipeline) to [Render.com](https://render.com).

---

## 🚀 Option 1: 1-Click Deployment via Render Blueprint (Recommended)

Because a `render.yaml` Blueprint file is included in the repository, you can deploy the full application in 1 click.

### Steps:
1. Log in to your [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** in the top right corner and select **Blueprint**.
3. Connect your GitHub account and select the repository:
   `https://github.com/Akshat-881236/Interview-Agent.git`
4. Render will detect `render.yaml` automatically.
5. Fill in your environment secret values:
   - `CLAUDE_API_KEY`: Your Anthropic Claude API Key.
   - `GROQ_API_KEY`: Your Groq API Key.
   - `GEMINI_API_KEY`: Your Google Gemini API Key.
6. Click **Apply**. Render will build and deploy your service automatically.

---

## 🛠️ Option 2: Manual Web Service Deployment on Render

If you prefer to configure the Web Service manually on Render:

### Step 1: Create a New Web Service
1. In the Render Dashboard, click **New +** -> **Web Service**.
2. Select your GitHub repository: `Akshat-881236/Interview-Agent`.

### Step 2: Configure Service Settings
- **Name**: `interview-agent` (or your preferred name)
- **Language / Environment**: `Python`
- **Region**: Select your closest region (e.g. `Oregon, USA` or `Frankfurt`)
- **Branch**: `main`
- **Root Directory**: *(leave blank)*
- **Build Command**:
  ```bash
  pip install -r backend/requirements.txt
  ```
- **Start Command**:
  ```bash
  cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
  ```

### Step 3: Configure Environment Variables
In the **Environment** tab, add the following key-value pairs:

| Variable Name | Value / Description | Required |
| :--- | :--- | :--- |
| `PYTHON_VERSION` | `3.10.12` | Yes |
| `PORT` | `10000` *(Render sets this automatically)* | Auto |
| `JWT_SECRET_KEY` | Generate a random 32-character string | Yes |
| `CLAUDE_API_KEY` | `sk-ant-api03-...` | Recommended |
| `GROQ_API_KEY` | `gsk_...` | Recommended |
| `GEMINI_API_KEY` | `AIzaSy...` | Recommended |
| `OLLAMA_HOST` | `http://localhost:11434` *(or cloud endpoint)* | Optional |

---

## 🔍 Step 4: Verification & Health Check

Once deployment completes:
1. Render will assign a public HTTPS URL (e.g., `https://interview-agent.onrender.com`).
2. Test the API health endpoint:
   ```bash
   curl https://interview-agent.onrender.com/api/health
   ```
   **Response**:
   ```json
   {"status": "ok", "service": "The Interview Agent API", "version": "2.1.0"}
   ```
3. Open `https://interview-agent.onrender.com` in your browser to start using the live voice & video studio!

---

## 📌 Troubleshooting & Tips

- **Free Tier Cold Starts**: Render's free web services spin down after 15 minutes of inactivity. The first request after a sleep period may take ~30 seconds.
- **Microphone & Camera Permissions**: Ensure your domain uses `https://` (Render provides SSL automatically) so browser Web Speech API & MediaDevices work seamlessly.
