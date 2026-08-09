// Audio Engine — Web Speech API Speech Recognition (STT) & Speech Synthesis (TTS)

const AudioEngine = {
  recognition: null,
  isListening: false,
  synth: window.speechSynthesis,
  selectedVoice: null,
  onSpeechStart: null,
  onSpeechEnd: null,
  onTranscriptUpdate: null,
  lastInterimResult: "",

  init() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = true;
      this.recognition.interimResults = true;
      this.recognition.lang = "en-US";

      this.recognition.onresult = (event) => {
        let finalSpeech = "";
        let interimSpeech = "";

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcriptChunk = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalSpeech += transcriptChunk + " ";
          } else {
            interimSpeech += transcriptChunk;
          }
        }

        const deliveredText = finalSpeech.trim() || interimSpeech.trim();
        if (deliveredText && deliveredText !== this.lastInterimResult) {
          this.lastInterimResult = deliveredText;
          if (this.onTranscriptUpdate) {
            this.onTranscriptUpdate(deliveredText, !!finalSpeech.trim());
          }
        }
      };

      this.recognition.onerror = (err) => {
        if (err.error !== "no-speech") {
          console.warn("Speech recognition notice:", err.error);
        }
      };

      this.recognition.onend = () => {
        if (this.isListening) {
          try { this.recognition.start(); } catch(e) {}
        }
      };
    } else {
      console.warn("Web SpeechRecognition API not supported in this browser.");
    }

    if (this.synth) {
      const loadVoices = () => {
        const voices = this.synth.getVoices();
        this.selectedVoice = voices.find(v => v.lang.startsWith("en") && (v.name.includes("Natural") || v.name.includes("Google") || v.name.includes("Samantha") || v.name.includes("Daniel"))) || voices[0];
      };
      loadVoices();
      if (this.synth.onvoiceschanged !== undefined) {
        this.synth.onvoiceschanged = loadVoices;
      }
    }
  },

  startListening(onUpdate) {
    if (!this.recognition) return false;
    this.onTranscriptUpdate = onUpdate;
    this.isListening = true;
    this.lastInterimResult = "";
    try {
      this.recognition.start();
      return true;
    } catch(e) {
      return false;
    }
  },

  stopListening() {
    if (!this.recognition) return;
    this.isListening = false;
    try {
      this.recognition.stop();
    } catch(e) {}
  },

  speak(text, onStart, onEnd) {
    if (!this.synth) {
      if (onEnd) onEnd();
      return;
    }
    this.synth.cancel();

    const cleanText = text.replace(/<[^>]*>?/gm, '');
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    if (this.selectedVoice) {
      utterance.voice = this.selectedVoice;
    }

    utterance.onstart = () => {
      if (onStart) onStart();
      if (this.onSpeechStart) this.onSpeechStart();
    };

    utterance.onend = () => {
      if (onEnd) onEnd();
      if (this.onSpeechEnd) this.onSpeechEnd();
    };

    utterance.onerror = (e) => {
      console.warn("TTS error:", e);
      if (onEnd) onEnd();
    };

    this.synth.speak(utterance);
  },

  stopSpeaking() {
    if (this.synth) {
      this.synth.cancel();
    }
  }
};
