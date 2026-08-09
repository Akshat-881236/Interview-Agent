// Visualizer Engine — Canvas Animated AI Voice Waveform Orb

const VisualizerEngine = {
  canvas: null,
  ctx: null,
  animationId: null,
  isSpeaking: false,
  phase: 0,

  init(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext("2d");
    this.resize();
    window.addEventListener("resize", () => this.resize());
    this.startLoop();
  },

  resize() {
    if (!this.canvas) return;
    this.canvas.width = this.canvas.offsetWidth || 300;
    this.canvas.height = this.canvas.offsetHeight || 200;
  },

  setSpeaking(speaking) {
    this.isSpeaking = speaking;
  },

  startLoop() {
    const draw = () => {
      this.phase += 0.05;
      this.render();
      this.animationId = requestAnimationFrame(draw);
    };
    draw();
  },

  render() {
    if (!this.ctx || !this.canvas) return;
    const width = this.canvas.width;
    const height = this.canvas.height;
    const cx = width / 2;
    const cy = height / 2;

    this.ctx.clearRect(0, 0, width, height);

    // Glowing background aura
    const glowRadius = this.isSpeaking ? 70 + Math.sin(this.phase * 2) * 15 : 45;
    const grad = this.ctx.createRadialGradient(cx, cy, 10, cx, cy, glowRadius + 30);
    grad.addColorStop(0, this.isSpeaking ? "rgba(99, 102, 241, 0.6)" : "rgba(217, 119, 6, 0.3)");
    grad.addColorStop(0.5, this.isSpeaking ? "rgba(168, 85, 247, 0.3)" : "rgba(180, 83, 9, 0.15)");
    grad.addColorStop(1, "rgba(0, 0, 0, 0)");

    this.ctx.fillStyle = grad;
    this.ctx.beginPath();
    this.ctx.arc(cx, cy, glowRadius + 30, 0, Math.PI * 2);
    this.ctx.fill();

    // Concentric pulsating glassmorphic waves
    const waveCount = 3;
    for (let i = 0; i < waveCount; i++) {
      this.ctx.beginPath();
      this.ctx.lineWidth = 2.5 - i * 0.5;
      this.ctx.strokeStyle = this.isSpeaking 
        ? `rgba(168, 85, 247, ${0.8 - i * 0.2})` 
        : `rgba(217, 119, 6, ${0.5 - i * 0.15})`;

      const points = 60;
      for (let j = 0; j <= points; j++) {
        const angle = (j / points) * Math.PI * 2;
        const amp = this.isSpeaking ? 12 + Math.sin(this.phase * 3 + i + j * 0.2) * 8 : 4;
        const r = glowRadius + Math.sin(angle * 4 + this.phase + i) * amp;
        const x = cx + Math.cos(angle) * r;
        const y = cy + Math.sin(angle) * r;

        if (j === 0) this.ctx.moveTo(x, y);
        else this.ctx.lineTo(x, y);
      }
      this.ctx.closePath();
      this.ctx.stroke();
    }

    // Core pulsing AI orb
    this.ctx.beginPath();
    const coreR = this.isSpeaking ? 28 + Math.sin(this.phase * 4) * 4 : 22;
    const coreGrad = this.ctx.createRadialGradient(cx - 5, cy - 5, 2, cx, cy, coreR);
    coreGrad.addColorStop(0, "#ffffff");
    coreGrad.addColorStop(0.4, this.isSpeaking ? "#a855f7" : "#d97706");
    coreGrad.addColorStop(1, this.isSpeaking ? "#4f46e5" : "#78350f");

    this.ctx.fillStyle = coreGrad;
    this.ctx.arc(cx, cy, coreR, 0, Math.PI * 2);
    this.ctx.fill();
  }
};
