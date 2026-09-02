/**
 * Ambient Voice & Audio Engine for MerchantMind
 * Integrates Web Speech API SpeechRecognition (STT) and SpeechSynthesis (TTS)
 * with barge-in interruption, silence auto-dispatch, and natural text cleaning.
 */

export type VoiceState = "idle" | "listening" | "thinking" | "speaking";

export interface VoiceManagerOptions {
  onTranscript?: (transcript: string, isFinal: boolean) => void;
  onAutoSubmit?: (transcript: string) => void;
  onStateChange?: (state: VoiceState) => void;
  onError?: (error: string) => void;
}

class VoiceManager {
  private recognition: any = null;
  private isSupported: boolean = false;
  private state: VoiceState = "idle";
  private silenceTimer: NodeJS.Timeout | null = null;
  private currentTranscript: string = "";
  private isVoiceModeEnabled: boolean = false;
  private options: VoiceManagerOptions = {};
  private activeUtterance: SpeechSynthesisUtterance | null = null;

  constructor() {
    if (typeof window !== "undefined") {
      const SpeechRecognition =
        (window as any).SpeechRecognition ||
        (window as any).webkitSpeechRecognition;

      if (SpeechRecognition) {
        this.isSupported = true;
        this.recognition = new SpeechRecognition();
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.lang = "en-IN"; // English (India) with fallback to en-US

        this.setupRecognitionListeners();
      }
    }
  }

  public init(options: VoiceManagerOptions) {
    this.options = options;
  }

  private setState(state: VoiceState) {
    this.state = state;
    this.options.onStateChange?.(state);
  }

  public getState(): VoiceState {
    return this.state;
  }

  public getIsSupported(): boolean {
    return this.isSupported;
  }

  public isVoiceMode(): boolean {
    return this.isVoiceModeEnabled;
  }

  public toggleVoiceMode(enable?: boolean): boolean {
    const target = enable !== undefined ? enable : !this.isVoiceModeEnabled;
    this.isVoiceModeEnabled = target;

    if (!this.isVoiceModeEnabled) {
      this.stopListening();
      this.stopSpeaking();
      this.setState("idle");
    } else {
      this.startListening();
    }
    return this.isVoiceModeEnabled;
  }

  public startListening() {
    if (!this.isSupported || !this.recognition) return;
    this.stopSpeaking(); // Barge-in interruption: cancel TTS when user wants to talk

    try {
      this.currentTranscript = "";
      this.recognition.start();
      this.setState("listening");
    } catch (e: any) {
      // Recognition may already be running
      if (e.name !== "InvalidStateError") {
        console.warn("SpeechRecognition start error:", e);
      }
      this.setState("listening");
    }
  }

  public stopListening() {
    if (this.silenceTimer) {
      clearTimeout(this.silenceTimer);
      this.silenceTimer = null;
    }
    if (this.recognition) {
      try {
        this.recognition.stop();
      } catch (e) {
        // Ignore
      }
    }
    if (this.state === "listening") {
      this.setState("idle");
    }
  }

  public notifyThinking() {
    this.stopListening();
    this.setState("thinking");
  }

  private setupRecognitionListeners() {
    if (!this.recognition) return;

    this.recognition.onresult = (event: any) => {
      let interim = "";
      let final = "";

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          final += transcript;
        } else {
          interim += transcript;
        }
      }

      const combined = (final || interim).trim();
      if (!combined) return;

      this.currentTranscript = combined;
      this.options.onTranscript?.(combined, !!final);

      // Barge-in: If user speaks, kill any playing audio
      this.stopSpeaking();

      // Reset silence detection timer (auto-submit after 1.6s of silence)
      if (this.silenceTimer) {
        clearTimeout(this.silenceTimer);
      }

      this.silenceTimer = setTimeout(() => {
        if (this.currentTranscript.trim().length > 2 && this.isVoiceModeEnabled) {
          const toSend = this.currentTranscript.trim();
          this.currentTranscript = "";
          this.setState("thinking");
          this.options.onAutoSubmit?.(toSend);
        }
      }, 1600);
    };

    this.recognition.onerror = (event: any) => {
      if (event.error === "no-speech") return;
      console.warn("SpeechRecognition error:", event.error);
      if (event.error === "not-allowed") {
        this.isVoiceModeEnabled = false;
        this.options.onError?.("Microphone permission denied. Please allow microphone access.");
        this.setState("idle");
      }
    };

    this.recognition.onend = () => {
      // Auto-restart if voice mode is on and we are not speaking or thinking
      if (this.isVoiceModeEnabled && this.state === "listening") {
        try {
          this.recognition.start();
        } catch (e) {
          // Ignore
        }
      }
    };
  }

  /**
   * Cleans markdown formatting, emojis, and raw URLs so TTS speaks natural English.
   */
  public cleanTextForSpeech(text: string): string {
    if (!text) return "";
    return text
      .replace(/```[\s\S]*?```/g, "") // remove code blocks
      .replace(/`([^`]+)`/g, "$1") // inline code
      .replace(/\*\*([^*]+)\*\*/g, "$1") // bold
      .replace(/\*([^*]+)\*/g, "$1") // italic
      .replace(/#+\s*/g, "") // headers
      .replace(/https?:\/\/\S+/g, "link on your screen") // URLs
      .replace(/[^\w\s.,?!₹\-'"]/g, " ") // special icons & emojis
      .replace(/\s+/g, " ")
      .trim();
  }

  /**
   * Speaks the response aloud using window.speechSynthesis.
   */
  public speak(text: string, onEnd?: () => void) {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      onEnd?.();
      return;
    }

    this.stopSpeaking();
    this.stopListening();

    const cleanText = this.cleanTextForSpeech(text);
    if (!cleanText) {
      if (this.isVoiceModeEnabled) this.startListening();
      onEnd?.();
      return;
    }

    const utterance = new SpeechSynthesisUtterance(cleanText);
    this.activeUtterance = utterance;

    // Pick best English voice
    const voices = window.speechSynthesis.getVoices();
    const preferredVoice =
      voices.find((v) => v.lang === "en-IN" || v.name.includes("India")) ||
      voices.find((v) => v.lang.startsWith("en") && (v.name.includes("Google") || v.name.includes("Samantha") || v.name.includes("Natural"))) ||
      voices.find((v) => v.lang.startsWith("en"));

    if (preferredVoice) {
      utterance.voice = preferredVoice;
    }

    utterance.rate = 1.05; // slightly upbeat conversational pace
    utterance.pitch = 1.0;

    this.setState("speaking");

    utterance.onend = () => {
      this.activeUtterance = null;
      if (this.isVoiceModeEnabled) {
        this.startListening();
      } else {
        this.setState("idle");
      }
      onEnd?.();
    };

    utterance.onerror = (e) => {
      console.warn("SpeechSynthesis error:", e);
      this.activeUtterance = null;
      if (this.isVoiceModeEnabled) {
        this.startListening();
      } else {
        this.setState("idle");
      }
      onEnd?.();
    };

    window.speechSynthesis.speak(utterance);
  }

  public stopSpeaking() {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      this.activeUtterance = null;
    }
  }
}

export const voiceManager = new VoiceManager();
