// The Interview Agent — Main Application Controller (AI Cohort)

const API_BASE = window.location.protocol === "file:"
  ? "http://localhost:8000/api"
  : `${window.location.origin}/api`;

const state = {
  sessionId: null,
  candidateName: null,
  progress: { questions_asked: 0, min_questions: 8, days_covered: 0, min_days: 4, done: false },
  currentQuestion: null,
  hudInterval: null,
  silenceTimer: null,
  countdownInterval: null,
  currentTurnBuffer: "",
  debateMode: false,
  violationsCount: 0,
  lastProctorCheckTime: 0
};

const el = (id) => document.getElementById(id);
const show = (id) => el(id).classList.remove("d-none");
const hide = (id) => el(id).classList.add("d-none");

// ---------- Custom Glassmorphism Dialog Helpers (High-Contrast Text) ----------
function showCustomAlert(title, message) {
  el("customAlertTitle").textContent = title || "System Notification";
  el("customAlertMessage").textContent = message;
  const modal = new bootstrap.Modal(el("customAlertModal"));
  modal.show();
}

function showCustomConfirm(title, message, onConfirm) {
  el("customConfirmTitle").textContent = title || "Confirm Action";
  el("customConfirmMessage").textContent = message;
  const modalEl = el("customConfirmModal");
  const modal = new bootstrap.Modal(modalEl);

  const confirmBtn = el("customConfirmActionBtn");
  const newBtn = confirmBtn.cloneNode(true);
  confirmBtn.parentNode.replaceChild(newBtn, confirmBtn);

  newBtn.addEventListener("click", () => {
    modal.hide();
    if (onConfirm) onConfirm();
  });

  modal.show();
}

async function api(path, opts = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...Auth.getAuthHeader(),
    ...(opts.headers || {})
  };
  const res = await fetch(`${API_BASE}${path}`, {
    method: opts.method || "GET",
    headers: headers,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.detail || err.error || `Request failed (${res.status})`);
  }
  return res.json();
}

// ---------- Boot ----------
(async function init() {
  AudioEngine.init();
  VisualizerEngine.init("aiVisualizerCanvas");
  setupAuthEvents();
  setupControlEvents();

  try {
    await api("/health");
    el("apiStatus").textContent = "Interview Agent Online";
    el("apiStatus").className = "badge bg-success";
  } catch (e) {
    el("apiStatus").textContent = "Agent Offline";
    el("apiStatus").className = "badge bg-danger";
  }

  checkCandidateAccess();
})();

async function checkCandidateAccess() {
  Auth.updateUI();
  if (Auth.isLoggedIn()) {
    hide("authWall");
    show("candidateGrid");
    try {
      const data = await api("/candidates");
      renderCandidateGrid(data.candidates);
    } catch (e) {
      if (e.message.includes("401") || e.message.includes("Authentication required") || e.message.includes("Unauthorized")) {
        Auth.clearAuth();
        show("authWall");
        hide("candidateGrid");
      } else {
        el("candidateGrid").innerHTML = `<div class="text-center text-muted p-4">Error loading candidates: ${e.message}</div>`;
      }
    }
  } else {
    show("authWall");
    hide("candidateGrid");
  }
}

function setupAuthEvents() {
  el("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const email = el("loginEmail").value;
      const password = el("loginPass").value;
      const res = await api("/auth/login", { method: "POST", body: { email, password } });
      Auth.setAuth(res.access_token, res.user);
      bootstrap.Modal.getInstance(el("authModal")).hide();
      await checkCandidateAccess();
    } catch(err) {
      showCustomAlert("Authentication Error", "Login failed: " + err.message);
    }
  });

  el("registerForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const full_name = el("regName").value;
      const email = el("regEmail").value;
      const password = el("regPass").value;
      const res = await api("/auth/register", { method: "POST", body: { full_name, email, password } });
      Auth.setAuth(res.access_token, res.user);
      bootstrap.Modal.getInstance(el("authModal")).hide();
      await checkCandidateAccess();
    } catch(err) {
      showCustomAlert("Registration Error", "Registration failed: " + err.message);
    }
  });

  el("navLogoutBtn").addEventListener("click", () => {
    Auth.clearAuth();
    checkCandidateAccess();
  });
}

function renderCandidateGrid(candidates) {
  if (!candidates || candidates.length === 0) {
    el("candidateGrid").innerHTML = `<div class="text-center text-muted p-4">No candidates available.</div>`;
    return;
  }

  el("candidateGrid").innerHTML = candidates.map(c => `
    <button class="candidate-card" data-id="${c.candidate_id}">
      <div class="fw-bold fs-5 text-light mb-1">${c.name}</div>
      <div class="text-muted small mb-2">${c.cohort_progress_pct}% Cohort Curriculum Complete</div>
      <div class="progress" style="height: 6px; background: rgba(255,255,255,0.1);">
        <div class="progress-bar" style="width: ${c.cohort_progress_pct}%; background:#6366f1;"></div>
      </div>
    </button>
  `).join("");

  el("candidateGrid").querySelectorAll(".candidate-card").forEach(btn => {
    btn.addEventListener("click", () => startInterview(btn.dataset.id, btn.querySelector(".fw-bold").textContent));
  });
}

// ---------- Interview Studio ----------
async function startInterview(candidateId, name) {
  if (!Auth.isLoggedIn()) {
    showCustomAlert("Access Denied", "Please sign in or register to start an interview session.");
    bootstrap.Modal.getInstance(el("authModal")).show();
    return;
  }

  hide("view-select");
  show("view-interview");
  hide("proctorWarningAlert");
  hide("proctorCancelAlert");
  el("transcriptBody").innerHTML = "";
  el("candidateLabel").textContent = name;
  state.violationsCount = 0;
  state.currentTurnBuffer = "";
  state.lastProctorCheckTime = 0;
  
  // Start camera with continuous real-time proctor event callback
  await PerceptionEngine.startCamera("candidateVideo", handleLiveProctorEvent);
  startHudTimer();

  addSystemMsg("Technical Interview Studio Active · AI Proctoring Engine Online");

  try {
    const data = await api("/interview/start", { method: "POST", body: { candidate_id: candidateId } });
    state.sessionId = data.session_id;
    state.candidateName = data.candidate_name;
    state.progress = data.progress;
    state.currentQuestion = data.question;
    updateProgressUI();

    addAgentMsg(data.question);
    speakQuestion(data.question.text);
  } catch (e) {
    addSystemMsg(`Session Error: ${e.message}`);
  }
}

// Live Real-Time Multi-Agent Proctor Event Trigger (Face Loss / Off-Screen Gaze)
async function handleLiveProctorEvent(metrics) {
  const now = Date.now();
  if (!state.sessionId || (now - state.lastProctorCheckTime < 2500)) return;
  state.lastProctorCheckTime = now;

  try {
    const res = await api("/interview/proctor_check", {
      method: "POST",
      body: { session_id: state.sessionId, metrics: metrics }
    });

    if (res.status === "warning") {
      show("proctorWarningAlert");
      el("proctorWarningText").textContent = res.reason;
      AudioEngine.speak(res.reason);
    } else if (res.status === "cancelled") {
      handleInterviewCancellation(res.reason);
    }
  } catch (e) {
    console.warn("Live proctor check notice:", e);
  }
}

function speakQuestion(text) {
  el("aiVoiceStatus").textContent = state.debateMode ? "DEBATE AGENT SPEAKING" : "AGENT SPEAKING";
  VisualizerEngine.setSpeaking(true);
  
  AudioEngine.speak(
    text,
    () => { VisualizerEngine.setSpeaking(true); },
    () => {
      VisualizerEngine.setSpeaking(false);
      el("aiVoiceStatus").textContent = state.debateMode ? "DEBATE MODE: LIVE LISTENING" : "LIVE LISTENING";
      startAutoListening();
    }
  );
}

// -----------------------------------------------------------------------------
// 10-Second Smart Voice Pause & Clean Speech Buffer Accumulation Engine
// -----------------------------------------------------------------------------
function startAutoListening() {
  show("dictationStatus");
  state.currentTurnBuffer = el("answerInput").value.trim();
  
  AudioEngine.startListening((deliveredSpeech, isFinal) => {
    let combined = state.currentTurnBuffer;
    if (combined && !combined.endsWith(" ") && deliveredSpeech) {
      combined += " ";
    }
    combined += deliveredSpeech;
    
    el("answerInput").value = combined;

    if (isFinal) {
      state.currentTurnBuffer = combined;
    }

    resetPauseTimer(10);
  });
}

function resetPauseTimer(secondsRemaining) {
  if (state.silenceTimer) clearTimeout(state.silenceTimer);
  if (state.countdownInterval) clearInterval(state.countdownInterval);

  let timeLeft = secondsRemaining;
  el("dictationStatus").textContent = `🎙️ Listening... Paused? ${timeLeft}s remaining to resume speaking before auto-submitting`;

  state.countdownInterval = setInterval(() => {
    timeLeft -= 1;
    if (timeLeft > 0) {
      el("dictationStatus").textContent = `🎙️ Listening... Paused? ${timeLeft}s remaining to resume speaking before auto-submitting`;
    } else {
      clearInterval(state.countdownInterval);
    }
  }, 1000);

  state.silenceTimer = setTimeout(() => {
    clearInterval(state.countdownInterval);
    if (el("answerInput").value.trim().length > 3) {
      submitAnswer();
    }
  }, secondsRemaining * 1000);
}

function stopAutoListening() {
  if (state.silenceTimer) clearTimeout(state.silenceTimer);
  if (state.countdownInterval) clearInterval(state.countdownInterval);
  hide("dictationStatus");
  AudioEngine.stopListening();
}

function startHudTimer() {
  if (state.hudInterval) clearInterval(state.hudInterval);
  state.hudInterval = setInterval(() => {
    const currentInput = el("answerInput").value;
    const metrics = PerceptionEngine.getMetrics(currentInput);
    el("hudEyeContact").textContent = `${Math.round(metrics.eye_contact_score * 100)}%`;
    el("hudConfidence").textContent = `${Math.round(metrics.confidence_index * 100)}%`;
    el("hudCadence").textContent = `${Math.round(metrics.speech_cadence)} WPM`;
  }, 1000);
}

function setupControlEvents() {
  el("btnMic").addEventListener("click", () => {
    const active = PerceptionEngine.toggleMic();
    el("btnMic").classList.toggle("active", active);
  });

  el("btnCamera").addEventListener("click", () => {
    const active = PerceptionEngine.toggleCamera();
    el("btnCamera").classList.toggle("active", active);
  });

  el("btnDebateToggle").addEventListener("click", () => {
    state.debateMode = !state.debateMode;
    el("btnDebateToggle").classList.toggle("btn-danger", state.debateMode);
    el("btnDebateToggle").classList.toggle("btn-outline-warning", !state.debateMode);
    el("btnDebateToggle").textContent = state.debateMode ? "🔥 Debate Mode: ON" : "⚔️ Debate Mode: OFF";
    addSystemMsg(state.debateMode ? "Switched to Technical Debate Mode. The Agent will challenge your trade-offs!" : "Switched to Standard Interview Mode.");
  });

  el("btnEndCall").addEventListener("click", () => {
    showCustomConfirm(
      "End Interview Session",
      "Are you sure you want to end the technical interview session?",
      () => {
        endSession();
        location.reload();
      }
    );
  });

  el("sendBtn").addEventListener("click", submitAnswer);
  el("answerInput").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submitAnswer();
    }
  });
}

async function submitAnswer() {
  const input = el("answerInput");
  const text = input.value.trim();
  if (!text || !state.sessionId) return;

  stopAutoListening();
  AudioEngine.stopSpeaking();
  VisualizerEngine.setSpeaking(false);

  addCandidateMsg(text);
  state.currentTurnBuffer = "";
  input.value = "";
  input.disabled = true;
  el("sendBtn").disabled = true;

  const metrics = PerceptionEngine.getMetrics(text);

  try {
    const data = await api("/interview/answer", {
      method: "POST",
      body: {
        session_id: state.sessionId,
        answer: text,
        perception_metrics: metrics,
        debate_mode: state.debateMode
      }
    });

    state.progress = data.progress;
    updateProgressUI();

    if (data.question && (data.question.type === "cancellation" || data.question.action === "CANCEL_INTERVIEW")) {
      handleInterviewCancellation(data.question.text);
      return;
    }

    if (data.question && (data.question.type === "proctor_warning" || data.question.action === "WARN_PROCTOR_VIOLATION")) {
      show("proctorWarningAlert");
      el("proctorWarningText").textContent = data.question.text;
      addAgentMsg(data.question);
      speakQuestion(data.question.text);
      input.disabled = false;
      el("sendBtn").disabled = false;
      return;
    }

    if (data.progress.done || !data.question) {
      addSystemMsg("Interview concluded. Preparing comprehensive feedback report...");
      await pause(1000);
      await showReport();
    } else {
      state.currentQuestion = data.question;
      addAgentMsg(data.question);
      speakQuestion(data.question.text);
    }
  } catch (e) {
    addSystemMsg(`Submission Error: ${e.message}`);
  } finally {
    if (state.progress.done || !state.currentQuestion) return;
    input.disabled = false;
    el("sendBtn").disabled = false;
  }
}

function handleInterviewCancellation(reasonText) {
  stopAutoListening();
  if (state.hudInterval) clearInterval(state.hudInterval);
  VisualizerEngine.setSpeaking(false);
  el("aiVoiceStatus").textContent = "SESSION CANCELLED";
  el("aiVoiceStatus").className = "text-danger fw-bold";
  
  hide("proctorWarningAlert");
  show("proctorCancelAlert");
  el("proctorCancelText").textContent = reasonText;
  
  el("answerInput").disabled = true;
  el("sendBtn").disabled = true;
  
  addSystemMsg(`❌ INTERVIEW CANCELLED: ${reasonText}`);
  
  AudioEngine.speak(
    reasonText,
    () => {},
    () => { PerceptionEngine.stopCamera(); }
  );
}

function addAgentMsg(q) {
  const wrap = document.createElement("div");
  wrap.className = "msg agent";
  const isWarn = q.type === "proctor_warning" || q.type === "cancellation";
  const isDebate = q.type === "debate" || q.action === "DEBATE_CHALLENGE";
  const tag = isWarn ? `⚠️ ${q.topic}` : (isDebate ? `⚔️ DEBATE CHALLENGE · Day ${q.day}` : (q.type === "followup" ? "Follow-up Question" : `Day ${q.day} · ${q.topic}`));
  
  wrap.innerHTML = `<div style="font-size:0.75rem; color:${isWarn ? '#f59e0b' : (isDebate ? '#ef4444' : '#a5b4fc')}; margin-bottom:4px; font-weight:600;">${tag}</div>${escapeHtml(q.text)}`;
  if (isWarn) wrap.style.border = "1px solid #f59e0b";
  if (isDebate) wrap.style.border = "1px solid rgba(239, 68, 68, 0.4)";
  
  el("transcriptBody").appendChild(wrap);
  if (q.day) el("dayBadge").textContent = `Day ${q.day}`;
  scrollToBottom();
}

function addCandidateMsg(text) {
  const wrap = document.createElement("div");
  wrap.className = "msg candidate";
  wrap.textContent = text;
  el("transcriptBody").appendChild(wrap);
  scrollToBottom();
}

function addSystemMsg(text) {
  const wrap = document.createElement("div");
  wrap.className = "msg system";
  wrap.textContent = text;
  el("transcriptBody").appendChild(wrap);
  scrollToBottom();
}

function updateProgressUI() {
  el("progressLabel").textContent = `${state.progress.questions_asked} / ${state.progress.min_questions} questions`;
}

async function showReport() {
  endSession();
  hide("view-interview");
  show("view-report");
  try {
    const rep = await api(`/interview/${state.sessionId}/report`);
    renderReport(rep);
  } catch (e) {
    el("reportCard").innerHTML = `<div class="text-center text-muted">Error loading report: ${e.message}</div>`;
  }
}

function endSession() {
  if (state.hudInterval) clearInterval(state.hudInterval);
  stopAutoListening();
  AudioEngine.stopSpeaking();
  PerceptionEngine.stopCamera();
}

function renderReport(rep) {
  const dayRows = rep.day_reports.map(d => `
    <div class="d-flex align-items-center justify-content-between p-3 my-2 rounded bg-dark border border-secondary">
      <div>
        <div class="fw-bold text-light">Day ${d.day}: ${d.topic}</div>
        <div class="text-muted small">${d.module}</div>
      </div>
      <div class="text-end">
        <span class="badge bg-primary fs-6 me-2">${d.avg_score} / 5</span>
        <span class="badge bg-info">${d.verdict}</span>
      </div>
    </div>
  `).join("");

  el("reportCard").innerHTML = `
    <div class="d-flex justify-content-between align-items-start mb-4">
      <div>
        <h2 class="display-6 fw-bold" style="font-family:'Fraunces', serif;">${rep.candidate_name}</h2>
        <div class="text-muted">Technical Interview Assessment · AI Cohort</div>
        <span class="badge bg-success fs-6 mt-2">${rep.readiness}</span>
      </div>
      <div class="text-end">
        <div class="display-5 fw-bold" style="color:#6366f1;">${rep.overall_score}<span class="fs-5 text-muted">/5</span></div>
        <div class="text-muted small">Overall Competency</div>
      </div>
    </div>

    <div class="my-4">
      <h5 class="fw-bold">Executive Summary</h5>
      <p class="lead fs-6 text-light" style="line-height:1.7;">${rep.narrative}</p>
    </div>

    <div class="my-4">
      <h5 class="fw-bold">Curriculum Performance</h5>
      ${dayRows}
    </div>

    <div class="row my-4">
      <div class="col-md-6 mb-3">
        <div class="p-3 rounded bg-dark border border-success h-100">
          <h5 class="text-success fw-bold">Strengths</h5>
          <ul class="mb-0 text-light">${rep.strengths.map(s => `<li class="my-1">${s}</li>`).join("")}</ul>
        </div>
      </div>
      <div class="col-md-6 mb-3">
        <div class="p-3 rounded bg-dark border border-warning h-100">
          <h5 class="text-warning fw-bold">Growth Areas</h5>
          <ul class="mb-0 text-light">${rep.growth_areas.map(s => `<li class="my-1">${s}</li>`).join("")}</ul>
        </div>
      </div>
    </div>

    <div class="d-flex gap-3 mt-4">
      <button class="btn btn-primary rounded-pill px-4" onclick="location.reload()">Interview Another Candidate</button>
      <button class="btn btn-outline-light rounded-pill px-4" onclick="window.print()">Print / Export Report</button>
    </div>
  `;
}

function scrollToBottom() {
  const body = el("transcriptBody");
  body.scrollTop = body.scrollHeight;
}
function pause(ms) { return new Promise(r => setTimeout(r, ms)); }
function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
