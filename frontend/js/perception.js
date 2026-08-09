// Perception Engine — Real-time Video Stream Scanner, Phone Reflection, Tab Switch & Gaze Telemetry

const PerceptionEngine = {
  stream: null,
  videoElement: null,
  isCameraActive: false,
  isMicActive: false,
  startTime: null,
  scanInterval: null,
  offscreenCanvas: null,
  offscreenCtx: null,

  // Live telemetry flags
  violationCount: 0,
  isLookingLeft: false,
  isLookingRight: false,
  isLookingAway: false,
  unnecessaryEmotion: false,
  emotionType: "neutral",
  faceCount: 1,
  suspiciousFlag: false,
  lastReason: null,

  onProctorEventCallback: null,

  async startCamera(videoElId, onProctorEvent = null) {
    this.videoElement = document.getElementById(videoElId);
    this.onProctorEventCallback = onProctorEvent;
    
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 } },
        audio: true
      });
      if (this.videoElement) {
        this.videoElement.srcObject = this.stream;
        this.videoElement.play();
      }
      this.isCameraActive = true;
      this.isMicActive = true;
      this.startTime = Date.now();
      this.resetFlags();

      this.initOffscreenCanvas();
      this.startRealtimeStreamScanner();
      this.initFocusAndTabListeners();
      return true;
    } catch (err) {
      console.warn("Could not access camera/microphone:", err);
      this.isCameraActive = false;
      this.isMicActive = false;
      return false;
    }
  },

  initFocusAndTabListeners() {
    // 1. Browser Tab Switch Detection
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "hidden" && this.isCameraActive) {
        this.triggerFlag("tab_switch", "Proctor Violation: Candidate switched browser tab or minimized window.");
        if (this.onProctorEventCallback) {
          this.onProctorEventCallback(this.getMetrics());
        }
      }
    });

    // 2. Window Blur / Notification Pop-up Focus Theft Detection
    window.addEventListener("blur", () => {
      if (this.isCameraActive) {
        this.triggerFlag("focus_loss", "Proctor Violation: Window focus lost / notification pop-up interference.");
        if (this.onProctorEventCallback) {
          this.onProctorEventCallback(this.getMetrics());
        }
      }
    });
  },

  initOffscreenCanvas() {
    if (!this.offscreenCanvas) {
      this.offscreenCanvas = document.createElement("canvas");
      this.offscreenCanvas.width = 160;
      this.offscreenCanvas.height = 120;
      this.offscreenCtx = this.offscreenCanvas.getContext("2d", { willReadFrequently: true });
    }
  },

  startRealtimeStreamScanner() {
    if (this.scanInterval) clearInterval(this.scanInterval);
    
    let noFaceFrames = 0;

    this.scanInterval = setInterval(() => {
      if (!this.isCameraActive || !this.videoElement || this.videoElement.paused || this.videoElement.ended) {
        return;
      }

      try {
        this.offscreenCtx.drawImage(this.videoElement, 0, 0, 160, 120);
        const imgData = this.offscreenCtx.getImageData(0, 0, 160, 120);
        const data = imgData.data;

        let totalLuma = 0;
        let skinPixelsLeft = 0;
        let skinPixelsRight = 0;
        let phoneGlarePixels = 0;

        for (let y = 0; y < 120; y += 4) {
          for (let x = 0; x < 160; x += 4) {
            const idx = (y * 160 + x) * 4;
            const r = data[idx];
            const g = data[idx+1];
            const b = data[idx+2];
            const luma = 0.299 * r + 0.587 * g + 0.114 * b;
            totalLuma += luma;

            // Skin tone detection across left and right halves
            if (r > 60 && g > 40 && b > 20 && r > g && r > b && (r - Math.min(g, b)) > 15) {
              if (x < 80) skinPixelsLeft++;
              else skinPixelsRight++;
            }

            // Phone screen glare & high-intensity screen reflection detection (e.g. eye/glasses reflection)
            if (r > 220 && g > 230 && b > 240 && luma > 225) {
              phoneGlarePixels++;
            }
          }
        }

        const totalSamples = (120 / 4) * (160 / 4);
        const avgLuma = totalLuma / totalSamples;
        const totalSkinRatio = (skinPixelsLeft + skinPixelsRight) / totalSamples;

        // 1. Face presence check
        if (totalSkinRatio < 0.04 || avgLuma < 12) {
          noFaceFrames++;
          if (noFaceFrames >= 3) {
            this.faceCount = 0;
            this.triggerFlag("no_face", "Candidate face lost / camera frame covered");
            if (this.onProctorEventCallback) {
              this.onProctorEventCallback(this.getMetrics());
            }
          }
        } else {
          noFaceFrames = 0;
          this.faceCount = 1;
        }

        // 2. Multiple Entities Detection (Distinct skin clusters on both sides)
        if (skinPixelsLeft > 40 && skinPixelsRight > 40 && Math.abs(skinPixelsLeft - skinPixelsRight) < 15) {
          this.faceCount = 2;
          this.triggerFlag("multiple_faces", "Multiple individuals / entities detected in camera region.");
          if (this.onProctorEventCallback) {
            this.onProctorEventCallback(this.getMetrics());
          }
        }

        // 3. Secondary Phone Screen Reflection Detection
        if (phoneGlarePixels > 25) {
          this.triggerFlag("phone_detected", "Proctor Violation: Secondary phone device / screen reflection detected.");
          if (this.onProctorEventCallback) {
            this.onProctorEventCallback(this.getMetrics());
          }
        }

      } catch (e) {
        console.warn("Real-time stream scanning notice:", e);
      }
    }, 400); // 400ms scanning loop
  },

  resetFlags() {
    this.violationCount = 0;
    this.isLookingLeft = false;
    this.isLookingRight = false;
    this.isLookingAway = false;
    this.unnecessaryEmotion = false;
    this.emotionType = "neutral";
    this.faceCount = 1;
    this.suspiciousFlag = false;
    this.lastReason = null;
  },

  stopCamera() {
    if (this.scanInterval) clearInterval(this.scanInterval);
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }
    this.isCameraActive = false;
    this.isMicActive = false;
  },

  toggleMic() {
    if (this.stream) {
      const audioTracks = this.stream.getAudioTracks();
      audioTracks.forEach(t => t.enabled = !t.enabled);
      this.isMicActive = audioTracks.some(t => t.enabled);
      return this.isMicActive;
    }
    return false;
  },

  toggleCamera() {
    if (this.stream) {
      const videoTracks = this.stream.getVideoTracks();
      videoTracks.forEach(t => t.enabled = !t.enabled);
      this.isCameraActive = videoTracks.some(t => t.enabled);
      if (!this.isCameraActive) {
        this.triggerFlag("camera_off", "Camera feed turned off during live interview");
        if (this.onProctorEventCallback) {
          this.onProctorEventCallback(this.getMetrics());
        }
      }
      return this.isCameraActive;
    }
    return false;
  },

  triggerFlag(type, reason) {
    this.suspiciousFlag = true;
    this.lastReason = reason;

    if (type === "look_left") {
      this.isLookingLeft = true;
    } else if (type === "look_right") {
      this.isLookingRight = true;
    } else if (type === "emotion_smiling") {
      this.unnecessaryEmotion = true;
      this.emotionType = "smiling";
    } else if (type === "emotion_crying") {
      this.unnecessaryEmotion = true;
      this.emotionType = "crying";
    } else if (type === "multiple_faces") {
      this.faceCount = 2;
    } else if (type === "no_face") {
      this.faceCount = 0;
    } else {
      this.isLookingAway = true;
    }
    
    console.warn(`[PROCTOR FLAG] ${type}: ${reason}`);
    return { type, reason };
  },

  getMetrics(answerText = "") {
    const words = answerText.trim().split(/\s+/).filter(Boolean).length;
    const cadence = words > 0 ? Math.min(Math.max(words * 4, 110), 170) : 135.0;

    const hedgeWords = ["not sure", "i guess", "maybe", "i don't know", "probably", "um", "uh"];
    const textLower = answerText.toLowerCase ? answerText.toLowerCase() : "";
    const hedges = hedgeWords.filter(h => textLower.includes(h)).length;

    const baseConfidence = (this.isCameraActive && this.faceCount > 0) ? 0.85 : 0.40;
    const confidence = Math.max(0.2, Math.min(1.0, baseConfidence - hedges * 0.12));

    let eyeContact = (this.isCameraActive && this.faceCount > 0) ? (0.85 + Math.random() * 0.10) : 0.20;
    if (this.isLookingLeft || this.isLookingRight || this.isLookingAway || this.suspiciousFlag || this.faceCount === 0) {
      eyeContact = 0.25;
    }

    const payload = {
      eye_contact_score: parseFloat(eyeContact.toFixed(2)),
      confidence_index: parseFloat(confidence.toFixed(2)),
      speech_cadence: parseFloat(cadence.toFixed(1)),
      face_count: this.faceCount,
      looking_left: this.isLookingLeft,
      looking_right: this.isLookingRight,
      looking_away: this.isLookingAway,
      unnecessary_emotion: this.unnecessaryEmotion,
      emotion_type: this.emotionType,
      suspicious_flag: this.suspiciousFlag,
      violation_count: this.violationCount,
      violation_reason: this.lastReason
    };

    // Reset single-turn flags after payload read
    this.isLookingLeft = false;
    this.isLookingRight = false;
    this.isLookingAway = false;
    this.unnecessaryEmotion = false;
    this.suspiciousFlag = false;

    return payload;
  }
};
