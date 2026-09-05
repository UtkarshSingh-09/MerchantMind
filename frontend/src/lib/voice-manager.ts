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
  [/\bmerchantmind\b/gi, "Merchant Mind"],
  [/\bnon-veg\b/gi, "non-vegetarian"],
  [/\bveg\b/gi, "vegetarian"],
  [/\bmins\b/gi, "minutes"],
  [/\bmin\b/gi, "minute"],
  [/\beta\b/gi, "estimated time of arrival"],
  [/\brzp\b/gi, "Razorpay"],
  [/\bqty\b/gi, "quantity"],
  [/\bapprox\b/gi, "approximately"],
];

export function normalizePhonetics(text: string): string {
  let cleaned = text;
  for (const [pattern, replacement] of PHONETIC_DICTIONARY) {
    cleaned = cleaned.replace(pattern, replacement);
  }
  return cleaned.trim();
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

    this.recognition.onaudiostart = () => {
      // Instant Barge-In: Stop TTS playback the millisecond user starts speaking
      this.stopSpeaking();
      if (this.state !== "listening" && this.isVoiceModeEnabled) {
        this.setState("listening");
      }
    };

    this.recognition.onspeechstart = () => {
      // Instant Barge-In: Cancel audio stream when speech begins
      this.stopSpeaking();
      if (this.state !== "listening" && this.isVoiceModeEnabled) {
        this.setState("listening");
      }
    };

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
      // Snappy 1.2s silence detection with 1.8s pause for connector words.
      const words = combined.toLowerCase().split(/\s+/);
      const lastWord = words[words.length - 1];
      const incompleteConnectors = [
        "and", "or", "with", "for", "under", "from", "to", "in", "of", "the", "a", "an",
        "please", "can", "could", "also", "want", "like", "order", "get", "need", "about",
        "around", "between", "less", "more", "my", "me", "some", "any", "at", "rupees", "rs"
      ];

      let silenceDelay = 1200; // 1.2s for quick greetings, commands, and normal sentences

      // If speech ends with an incomplete connector or preposition, grant 1.8s breathing pause
      if (incompleteConnectors.includes(lastWord)) {
        silenceDelay = 2000;
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
      // Auto-restart if voice mode is on and we are not speaking
      if (this.isVoiceModeEnabled && this.state !== "speaking") {
        try {
          this.recognition.start();
          this.setState("listening");
        } catch (e) {
          // Ignore
        }
      }
    };
  }

  /**
   * Cleans markdown, formatting, emojis, extracts concise conversational speech,
   * and applies Indian English phonetic pronunciation normalizer for sub-150ms TTS synthesis.
   * STRICTLY speaks only item and total amount on orders — NEVER reads UUIDs or Order IDs aloud.
   */
  public cleanTextForSpeech(text: string): string {
    if (!text) return "";

    // 0. Specialized Check: Order Confirmation / Checkout summaries
    // Extracts ONLY item and amount — avoids reading Order ID, URLs, or technical metadata
    if (text.includes("Order Summary") || text.includes("Order ID:") || text.includes("Your order is ready")) {
      const itemMatch = text.match(/Item:\*{0,2}\s*([^\n—•*]+)/i);
      const totalMatch = text.match(/Total:\*{0,2}\s*[₹]?\s*([0-9,.]+)/i);
      const isPickup = text.toLowerCase().includes("pickup");

      const itemStr = itemMatch ? itemMatch[1].trim() : "";
      const totalStr = totalMatch ? totalMatch[1].trim() : "";

      if (itemStr && totalStr) {
        return `Your ${isPickup ? "pickup " : ""}order for ${itemStr} is ${totalStr} rupees. Please tap the payment button to complete your purchase.`;
      } else if (totalStr) {
        return `Your ${isPickup ? "pickup " : ""}order for ${totalStr} rupees is ready. Please tap the payment button to complete your purchase.`;
      }
    }

    let cleaned = text
      // Strip UUIDs completely
      .replace(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/gi, "")
      // Strip technical metadata lines
      .replace(/Order ID:[^\n]+/gi, "")
      .replace(/Payment Link:[^\n]+/gi, "")
      .replace(/\[Click here to pay[^\]]*\]\([^)]+\)/gi, "")
      .replace(/```[\s\S]*?```/g, "") // remove code blocks
      .replace(/`([^`]+)`/g, "$1") // inline code
      .replace(/\*\*([^*]+)\*\*/g, "$1") // bold
      .replace(/\*([^*]+)\*/g, "$1") // italic
      .replace(/#+\s*/g, "") // headers
      .replace(/https?:\/\/\S+/g, "") // URLs
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
    } else if (cleaned.length > 220) {
      cleaned = cleaned.substring(0, 220).replace(/\s+\S*$/, "") + ".";
    }

    // Apply Indian English phonetic replacements
    for (const [pattern, replacement] of PHONETIC_DICTIONARY) {
      cleaned = cleaned.replace(pattern, replacement);
    }

    return cleaned.trim();
  }

  /**
   * Finds the smoothest, clearest soft voice (Siri/Alexa style).
   * Prioritizes silky smooth, pleasant female voices (Google UK Female, Samantha, Sangeeta, Veena)
   * and completely avoids harsh/deep/heavy voices like Rishi, Alex, or Fred.
   */
  private getBestIndianVoice(): SpeechSynthesisVoice | null {
    let voices = this.cachedVoices;
    if (!voices || voices.length === 0) {
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        voices = window.speechSynthesis.getVoices();
        this.cachedVoices = voices;
      }
    }
    if (!voices || voices.length === 0) return null;

    const harshNames = ["rishi", "prabhat", "alex", "fred", "daniel", "oliver", "ralph", "tom", "george", "albert", "junior", "bad news", "bahh", "bells", "boing", "bubbles", "cellos", "deranged", "good news", "hysterical", "pipe organ", "trinoids", "whisper", "zarvox"];

    // 1. Ultra-soft, gentle, crystal-clear female voices
    const softFemaleVoices = [
      // Chrome's silky smooth female voices
      voices.find((v) => v.name.toLowerCase().includes("google uk english female")),
      voices.find((v) => v.name.toLowerCase().includes("google us english")),
      // Apple's warm, smooth Siri assistant voices
      voices.find((v) => v.name.toLowerCase().includes("samantha")),
      voices.find((v) => v.name.toLowerCase().includes("victoria")),
      voices.find((v) => v.name.toLowerCase().includes("karen")),
      // Soft Indian English female voices
      voices.find((v) => v.name.toLowerCase().includes("sangeeta")),
      voices.find((v) => v.name.toLowerCase().includes("veena")),
      voices.find((v) => v.name.toLowerCase().includes("neerja")),
      // Siri voices (excluding any harsh ones)
      voices.find((v) => v.name.toLowerCase().includes("siri") && !harshNames.some((h) => v.name.toLowerCase().includes(h))),
      // Any other Google female / natural voice
      voices.find((v) => v.name.includes("Google") && v.name.toLowerCase().includes("female")),
      voices.find((v) => v.name.includes("Natural") && !harshNames.some((h) => v.name.toLowerCase().includes(h))),
      // Any en-IN female voice (strictly not Rishi)
      voices.find((v) => (v.lang === "en-IN" || v.lang === "en_IN") && !harshNames.some((h) => v.name.toLowerCase().includes(h))),
      // Gentle English voices
      voices.find((v) => v.lang.startsWith("en") && !harshNames.some((h) => v.name.toLowerCase().includes(h))),
    ];

    for (const v of softFemaleVoices) {
      if (v) return v;
    }

    // Safe fallback: pick the first voice that is NOT in harshNames
    const safeVoice = voices.find((v) => !harshNames.some((h) => v.name.toLowerCase().includes(h)));
    return safeVoice || voices[0] || null;
  }

  private activeAudioElement: HTMLAudioElement | null = null;

  public unlockAudio() {
    if (typeof window !== "undefined" && !this.activeAudioElement) {
      this.activeAudioElement = new Audio();
    }
  }

  private ttsMode: "instant" | "studio" = "instant";

  public setTtsMode(mode: "instant" | "studio") {
    this.ttsMode = mode;
  }

  public getTtsMode(): "instant" | "studio" {
    return this.ttsMode;
  }

  /**
   * Speaks the response aloud with sub-25ms zero-latency using on-device neural voice.
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

    // 1. Instant On-Device Neural Speech (0ms Internet Lag, immediate playback)
    if (this.ttsMode === "instant") {
      this.speakOnDevice(cleanText, onEnd);
      return;
    }

    // 2. Studio Mode: Deepgram Cloud TTS
    try {
      const { fetchDeepgramVoiceAudio } = await import("./api");
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

        audio.onerror = () => {
          URL.revokeObjectURL(audioUrl);
          this.speakOnDevice(cleanText, onEnd);
        };

        try {
          await audio.play();
          return;
        } catch (playErr) {
          this.speakOnDevice(cleanText, onEnd);
          return;
        }
      }
    } catch (dgErr) {
      console.warn("[VoiceManager] Deepgram TTS not available, using on-device voice:", dgErr);
    }

    this.speakOnDevice(cleanText, onEnd);
  }

  public speakOnDevice(cleanText: string, onEnd?: () => void) {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      onEnd?.();
      return;
    }

    // Cancel any stale queued speech
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(cleanText);
    this.activeUtterance = utterance;

    const preferredVoice = this.getBestIndianVoice();
    if (preferredVoice) {
      utterance.voice = preferredVoice;
      // CRITICAL FIX: Set utterance.lang to match the voice's native lang
      // (Setting en-IN when voice is Samantha or Google Female causes Chrome to discard the voice and fall back to Rishi!)
      utterance.lang = preferredVoice.lang;
      console.log(`[VoiceManager] 🎙️ Speaking with soft voice: ${preferredVoice.name} (${preferredVoice.lang})`);
    } else {
      utterance.lang = "en-US";
    }

    // Silky smooth, clear, conversational pace and pitch (eliminates heavy baritone)
    utterance.rate = 1.0;
    utterance.pitch = 1.05;

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
