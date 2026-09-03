/**
 * Ambient Voice & Audio Engine for MerchantMind
 * High-Fidelity Indian English Speech Engine with Phonetic Indian Pronunciation Normalizer,
 * Web Speech API SpeechRecognition (STT), SpeechSynthesis (TTS), Barge-In Interruption,
 * and Silence Auto-Dispatch.
 */

export type VoiceState = "idle" | "listening" | "thinking" | "speaking";

export interface VoiceManagerOptions {
  onTranscript?: (transcript: string, isFinal: boolean) => void;
  onAutoSubmit?: (transcript: string) => void;
  onStateChange?: (state: VoiceState) => void;
  onError?: (error: string) => void;
}

// Indian Food, Geography, Currency, and Cultural Phonetic Dictionary for Natural TTS
const PHONETIC_DICTIONARY: Array<[RegExp, string]> = [
  // Food & Dishes
  [/\bmanchurian\b/gi, "Man-choorian"],
  [/\bgobi\b/gi, "Go-bee"],
  [/\bpaneer\b/gi, "Puh-neer"],
  [/\bbiryani\b/gi, "Beer-yaani"],
  [/\bpulao\b/gi, "Poo-lao"],
  [/\btandoori\b/gi, "Tun-doori"],
  [/\btikka\b/gi, "Tik-kaa"],
  [/\bmasala\b/gi, "Muh-saa-laa"],
  [/\bdosa\b/gi, "Dho-saa"],
  [/\bidli\b/gi, "Id-lee"],
  [/\bvada\b/gi, "Vuh-daa"],
  [/\bsambar\b/gi, "Saam-baar"],
  [/\bchutney\b/gi, "Chut-nee"],
  [/\bchaat\b/gi, "Chaa-t"],
  [/\bnaan\b/gi, "Naan"],
  [/\bkulcha\b/gi, "Kul-chaa"],
  [/\bparotta\b/gi, "Puh-ro-tah"],
  [/\bparatha\b/gi, "Puh-raa-thaa"],
  [/\bgulab jamun\b/gi, "Goo-laab Jaa-moon"],
  [/\brasgulla\b/gi, "Rus-gool-laa"],
  [/\bkulfi\b/gi, "Kool-fee"],
  [/\bchai\b/gi, "Chai"],
  [/\blassi\b/gi, "Lus-see"],

  // Bangalore Locations & Neighborhoods
  [/\bindiranagar\b/gi, "Indira Nagar"],
  [/\bkoramangala\b/gi, "Kora-mangala"],
  [/\bmarathahalli\b/gi, "Maratha-halli"],
  [/\bhsr\b/gi, "H S R"],
  [/\bwhitefield\b/gi, "White-field"],
  [/\bjayanagar\b/gi, "Jaya Nagar"],
  [/\bbasavanagudi\b/gi, "Basa-vana-gudi"],
  [/\bmalleshwaram\b/gi, "Mallesh-waram"],
  [/\bbanashankari\b/gi, "Bana-shankari"],
  [/\belectronic city\b/gi, "Electronic City"],
  [/\bhebbal\b/gi, "Heb-baal"],
  [/\byelahanka\b/gi, "Yela-hunka"],
  [/\bfrazer town\b/gi, "Frazer Town"],
  [/\bsarjapur\b/gi, "Sarja-pur"],
  [/\bbhavan\b/gi, "Bhu-vun"],

  // Currency & Formats
  [/₹\s*([0-9,]+(\.[0-9]{1,2})?)/g, "$1 rupees"],
  [/Rs\.?\s*([0-9,]+(\.[0-9]{1,2})?)/gi, "$1 rupees"],
  [/\binr\s*([0-9,]+)/gi, "$1 rupees"],

  // Terms & Abbreviations
  [/\bnon-veg\b/gi, "non-vegetarian"],
  [/\bveg\b/gi, "vegetarian"],
  [/\bmins\b/gi, "minutes"],
  [/\bmin\b/gi, "minute"],
  [/\beta\b/gi, "estimated time of arrival"],
  [/\brzp\b/gi, "Razorpay"],
  [/\bqty\b/gi, "quantity"],
  [/\bapprox\b/gi, "approximately"],
];

class VoiceManager {
  private recognition: any = null;
  private isSupported: boolean = false;
  private state: VoiceState = "idle";
  private silenceTimer: NodeJS.Timeout | null = null;
  private currentTranscript: string = "";
  private isVoiceModeEnabled: boolean = false;
  private options: VoiceManagerOptions = {};
  private activeUtterance: SpeechSynthesisUtterance | null = null;
  private cachedVoices: SpeechSynthesisVoice[] = [];

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
        this.recognition.lang = "en-IN"; // Set Indian English speech recognition

        this.setupRecognitionListeners();
      }

      this.initVoices();
    }
  }

  private initVoices() {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      this.cachedVoices = window.speechSynthesis.getVoices();
      window.speechSynthesis.onvoiceschanged = () => {
        this.cachedVoices = window.speechSynthesis.getVoices();
      };
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
    this.stopSpeaking(); // Barge-in interruption: cancel TTS when user starts talking

    try {
      this.currentTranscript = "";
      this.recognition.start();
      this.setState("listening");
    } catch (e: any) {
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

      // Barge-in: If user speaks, immediately cancel any playing TTS
      this.stopSpeaking();

      // Reset silence detection timer
      if (this.silenceTimer) {
        clearTimeout(this.silenceTimer);
      }

      // Smart Adaptive Silence Buffer:
      // Gives users generous speaking time (2.2s - 3.0s) so natural pauses never cut them off mid-sentence.
      const words = combined.toLowerCase().split(/\s+/);
      const lastWord = words[words.length - 1];
      const incompleteConnectors = [
        "and", "or", "with", "for", "under", "from", "to", "in", "of", "the", "a", "an",
        "please", "can", "could", "also", "want", "like", "order", "get", "need", "about",
        "around", "between", "less", "more", "my", "me", "some", "any", "at", "rupees", "rs"
      ];

      let silenceDelay = 2200; // Default 2.2 seconds natural breathing pause

      // If speech ends with an incomplete connector or preposition, grant 3.0 seconds
      if (incompleteConnectors.includes(lastWord)) {
        silenceDelay = 3000;
      } else if (words.length < 4) {
        // Short fragment (e.g. "Hey please", "I want"), wait 2.6 seconds for the main request
        silenceDelay = 2600;
      }

      this.silenceTimer = setTimeout(() => {
        if (this.currentTranscript.trim().length > 2 && this.isVoiceModeEnabled) {
          const toSend = this.currentTranscript.trim();
          this.currentTranscript = "";
          this.setState("thinking");
          this.options.onAutoSubmit?.(toSend);
        }
      }, silenceDelay);
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
   * Cleans markdown, formatting, emojis, extracts concise conversational speech,
   * and applies Indian English phonetic pronunciation normalizer for sub-150ms TTS synthesis.
   */
  public cleanTextForSpeech(text: string): string {
    if (!text) return "";

    let cleaned = text
      .replace(/```[\s\S]*?```/g, "") // remove code blocks
      .replace(/`([^`]+)`/g, "$1") // inline code
      .replace(/\*\*([^*]+)\*\*/g, "$1") // bold
      .replace(/\*([^*]+)\*/g, "$1") // italic
      .replace(/#+\s*/g, "") // headers
      .replace(/https?:\/\/\S+/g, "link on your screen") // URLs
      .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1") // markdown links -> anchor text only
      .replace(/•/g, ", ") // bullet points -> natural breath pause
      .replace(/[-*]\s+/g, "") // remove markdown list dashes
      .replace(/[^\w\s.,?!₹\-'"]/g, " ") // special icons & emojis
      .replace(/\s+/g, " ")
      .trim();

    // For voice mode: pick the concise 1-2 core sentences for rapid <100ms TTS response
    const sentences = cleaned.match(/[^.!?]+[.!?]+/g);
    if (sentences && sentences.length > 2) {
      cleaned = sentences.slice(0, 2).join(" ").trim();
    } else if (cleaned.length > 250) {
      cleaned = cleaned.substring(0, 250).replace(/\s+\S*$/, "") + ".";
    }

    // Apply Indian English phonetic replacements
    for (const [pattern, replacement] of PHONETIC_DICTIONARY) {
      cleaned = cleaned.replace(pattern, replacement);
    }

    return cleaned.trim();
  }

  /**
   * Finds the most natural, authentic Indian English voice available in the client environment.
   */
  private getBestIndianVoice(): SpeechSynthesisVoice | null {
    const voices = this.cachedVoices.length > 0 ? this.cachedVoices : (typeof window !== "undefined" && "speechSynthesis" in window ? window.speechSynthesis.getVoices() : []);
    if (!voices || voices.length === 0) return null;

    // 1. First priority: Dedicated Indian English voices
    const indianVoices = [
      // Chrome / Edge Natural Indian English
      voices.find((v) => v.lang === "en-IN" && (v.name.includes("Google") || v.name.includes("Natural"))),
      voices.find((v) => v.name.includes("Neerja") || v.name.includes("Prabhat")),
      // macOS / iOS High-Fidelity Indian English Voices
      voices.find((v) => v.name.includes("Rishi")),
      voices.find((v) => v.name.includes("Sangeeta")),
      voices.find((v) => v.name.includes("Veena")),
      // Generic en-IN
      voices.find((v) => v.lang === "en-IN" || v.lang === "en_IN"),
      voices.find((v) => v.lang.startsWith("en-IN") || v.lang.startsWith("en_IN")),
      // Hindi fallback with English capability
      voices.find((v) => v.lang === "hi-IN" || v.lang === "hi_IN" || v.name.includes("India")),
    ];

    for (const v of indianVoices) {
      if (v) return v;
    }

    // 2. Second priority: High-quality natural English voice
    const naturalVoices = [
      voices.find((v) => v.lang.startsWith("en") && v.name.includes("Google")),
      voices.find((v) => v.lang.startsWith("en") && (v.name.includes("Samantha") || v.name.includes("Serena"))),
      voices.find((v) => v.lang.startsWith("en") && v.name.includes("Natural")),
      voices.find((v) => v.lang.startsWith("en")),
    ];

    for (const v of naturalVoices) {
      if (v) return v;
    }

    return voices[0] || null;
  }

  private activeAudioElement: HTMLAudioElement | null = null;

  public unlockAudio() {
    if (typeof window !== "undefined" && !this.activeAudioElement) {
      this.activeAudioElement = new Audio();
    }
  }

  /**
   * Speaks the response aloud using Deepgram Flux TTS with graceful fallback to browser speech synthesis.
   */
  public async speak(text: string, onEnd?: () => void) {
    this.stopSpeaking();
    this.stopListening();

    const cleanText = this.cleanTextForSpeech(text);
    if (!cleanText) {
      if (this.isVoiceModeEnabled) this.startListening();
      onEnd?.();
      return;
    }

    // 1. Try Deepgram Studio Flux TTS first
    try {
      const { fetchDeepgramVoiceAudio } = await import("./api");
      console.log("[VoiceManager] Requesting Deepgram Flux Meena audio for:", cleanText);
      const audioBlob = await fetchDeepgramVoiceAudio(cleanText);

      if (audioBlob && typeof window !== "undefined") {
        const audioUrl = URL.createObjectURL(audioBlob);

        if (!this.activeAudioElement) {
          this.activeAudioElement = new Audio();
        }

        const audio = this.activeAudioElement;
        audio.src = audioUrl;
        audio.load();

        this.setState("speaking");

        audio.onended = () => {
          URL.revokeObjectURL(audioUrl);
          if (this.isVoiceModeEnabled) {
            this.startListening();
          } else {
            this.setState("idle");
          }
          onEnd?.();
        };

        audio.onerror = (e) => {
          console.warn("[VoiceManager] Deepgram Audio playback error, falling back to speech synthesis:", e);
          URL.revokeObjectURL(audioUrl);
          this.fallbackSpeak(cleanText, onEnd);
        };

        try {
          await audio.play();
          console.log("[VoiceManager] Playing Deepgram audio successfully 🎙️");
          return;
        } catch (playErr) {
          console.warn("[VoiceManager] Audio play() failed:", playErr);
          this.fallbackSpeak(cleanText, onEnd);
          return;
        }
      }
    } catch (dgErr) {
      console.warn("[VoiceManager] Deepgram TTS not available, using browser speech synthesis:", dgErr);
    }

    // 2. Fallback to Enhanced Browser SpeechSynthesis
    this.fallbackSpeak(cleanText, onEnd);
  }

  private fallbackSpeak(cleanText: string, onEnd?: () => void) {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      onEnd?.();
      return;
    }

    const utterance = new SpeechSynthesisUtterance(cleanText);
    this.activeUtterance = utterance;

    // Explicitly set language to en-IN for authentic Indian prosody & phonology
    utterance.lang = "en-IN";

    const preferredVoice = this.getBestIndianVoice();
    if (preferredVoice) {
      utterance.voice = preferredVoice;
    }

    // Optimal warm, articulate Indian conversational pace and pitch
    utterance.rate = 0.98;
    utterance.pitch = 1.02;

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
    if (this.activeAudioElement) {
      try {
        this.activeAudioElement.pause();
        this.activeAudioElement.currentTime = 0;
      } catch (e) {
        // Ignore
      }
      this.activeAudioElement = null;
    }

    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      this.activeUtterance = null;
    }
  }
}

export const voiceManager = new VoiceManager();
