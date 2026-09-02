"use client";

import React, { useState, useEffect, useRef, KeyboardEvent } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Send,
  Loader2,
  Mic,
  MicOff,
  Volume2,
  Cake,
  Salad,
  Gift,
  Coffee,
  Tag,
  Compass,
} from "lucide-react";
import { VoiceState } from "@/lib/voice-manager";

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  onSuggestionClick?: (suggestion: string) => void;
  suggestions?: string[];
  placeholder?: string;
  isVoiceMode?: boolean;
  voiceState?: VoiceState;
  onToggleVoice?: () => void;
  liveTranscript?: string;
}

const DEFAULT_SUGGESTIONS = [
  "Hey, order me one Manchurian under 500",
  "Chocolate cake under ₹800",
  "Fresh breakfast pastries & croissants",
  "Weekly grocery basket under ₹1000",
  "Explore Bangalore bakeries & restaurants",
];

export function ChatInput({
  onSendMessage,
  isLoading,
  onSuggestionClick,
  suggestions = DEFAULT_SUGGESTIONS,
  placeholder = "Ask for items or budget (e.g. under ₹800)...",
  isVoiceMode = false,
  voiceState = "idle",
  onToggleVoice,
  liveTranscript = "",
}: ChatInputProps) {
  const [input, setInput] = useState("");
  const [isFocused, setIsFocused] = useState(false);

  // Sync live speech transcript to input field
  useEffect(() => {
    if (liveTranscript) {
      setInput(liveTranscript);
    }
  }, [liveTranscript]);

  const handleSubmit = () => {
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;
    onSendMessage(trimmed);
    setInput("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const renderSuggestionIcon = (suggestion: string) => {
    const s = suggestion.toLowerCase();
    if (s.includes("manchurian") || s.includes("chinese") || s.includes("biryani") || s.includes("order")) {
      return <Volume2 className="h-3 w-3 text-emerald-400 shrink-0" />;
    }
    if (s.includes("cake") || s.includes("dessert") || s.includes("birthday") || s.includes("sweet")) {
      return <Cake className="h-3 w-3 text-purple-400 shrink-0" />;
    }
    if (s.includes("groc") || s.includes("veg") || s.includes("apple") || s.includes("salad") || s.includes("fruit")) {
      return <Salad className="h-3 w-3 text-emerald-400 shrink-0" />;
    }
    if (s.includes("shirt") || s.includes("kurta") || s.includes("cloth") || s.includes("gift") || s.includes("dress")) {
      return <Gift className="h-3 w-3 text-pink-400 shrink-0" />;
    }
    if (s.includes("croissant") || s.includes("pastr") || s.includes("coffee") || s.includes("bread") || s.includes("tea")) {
      return <Coffee className="h-3 w-3 text-amber-400 shrink-0" />;
    }
    if (s.includes("store") || s.includes("available") || s.includes("city") || s.includes("explore")) {
      return <Compass className="h-3 w-3 text-cyan-400 shrink-0" />;
    }
    return <Tag className="h-3 w-3 text-[#A78BFA] shrink-0" />;
  };

  return (
    <div className="flex flex-col gap-2.5">
      {/* Dynamic Suggested Prompt Chips */}
      <div className="relative">
        <div className="flex gap-2 overflow-x-auto no-scrollbar pb-1 pt-0.5">
          {suggestions.map((s, idx) => {
            const cleanText = s.replace(/^[^\w\s₹]+/, "").trim();
            return (
              <motion.button
                key={idx}
                whileHover={{ scale: 1.03, y: -1 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => {
                  if (onSuggestionClick) {
                    onSuggestionClick(cleanText);
                  } else {
                    onSendMessage(cleanText);
                  }
                }}
                disabled={isLoading}
                className="shrink-0 inline-flex items-center gap-1.5 rounded-full border border-[#2A2A3E] bg-[#12121E]/90 px-3 py-1 text-xs text-zinc-300 shadow-sm backdrop-blur-md transition-all hover:border-[#7C3AED]/50 hover:bg-[#7C3AED]/15 hover:text-white disabled:opacity-50 cursor-pointer"
              >
                {renderSuggestionIcon(s)}
                <span>{cleanText}</span>
              </motion.button>
            );
          })}
        </div>
        {/* Right edge fade gradient */}
        <div className="pointer-events-none absolute right-0 top-0 h-full w-8 bg-gradient-to-l from-[#0A0A12] to-transparent" />
      </div>

      {/* Voice Listening Wave Indicator */}
      <AnimatePresence>
        {isVoiceMode && (
          <motion.div
            initial={{ opacity: 0, height: 0, scale: 0.95 }}
            animate={{ opacity: 1, height: "auto", scale: 1 }}
            exit={{ opacity: 0, height: 0, scale: 0.95 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            className={`flex items-center justify-between px-3.5 py-2 rounded-xl border text-xs backdrop-blur-md ${
              voiceState === "speaking"
                ? "bg-emerald-950/40 border-emerald-500/40 text-emerald-300"
                : voiceState === "listening"
                ? "bg-amber-950/40 border-amber-500/40 text-amber-300"
                : "bg-[#7C3AED]/15 border-[#7C3AED]/40 text-[#A78BFA]"
            }`}
          >
            <div className="flex items-center gap-2">
              {voiceState === "speaking" ? (
                <Volume2 className="h-3.5 w-3.5 text-emerald-400 animate-pulse" />
              ) : (
                <Mic className="h-3.5 w-3.5 text-amber-400 animate-bounce" />
              )}
              <span className="font-medium">
                {voiceState === "speaking"
                  ? "Speaking response aloud..."
                  : voiceState === "thinking"
                  ? "Processing your request..."
                  : "Listening to your voice..."}
              </span>
              <span className="flex gap-0.5 items-center">
                {[0, 1, 2, 3].map((i) => (
                  <motion.span
                    key={i}
                    className={`w-0.5 rounded-full ${
                      voiceState === "speaking" ? "bg-emerald-400" : "bg-amber-400"
                    }`}
                    animate={{ height: ["4px", "14px", "4px"] }}
                    transition={{
                      duration: 0.6,
                      repeat: Infinity,
                      delay: i * 0.12,
                      ease: "easeInOut",
                    }}
                  />
                ))}
              </span>
            </div>
            {onToggleVoice && (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={onToggleVoice}
                className="text-[11px] font-semibold text-rose-400 hover:text-rose-300 cursor-pointer"
              >
                Mute Voice ✕
              </motion.button>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input Field Bar with subtle glow */}
      <motion.div
        animate={{
          borderColor: isFocused ? "#7C3AED" : isVoiceMode ? "#06B6D4" : "#2A2A3E",
          boxShadow: isFocused
            ? "0 0 24px -2px rgba(124, 58, 237, 0.35)"
            : isVoiceMode
            ? "0 0 20px -2px rgba(6, 182, 212, 0.25)"
            : "0 4px 20px -2px rgba(0, 0, 0, 0.4)",
        }}
        transition={{ duration: 0.2 }}
        className="relative flex items-center gap-2 rounded-2xl border bg-[#12121E]/95 p-1.5 shadow-lg backdrop-blur-xl transition-all"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={isVoiceMode ? "🎙️ Voice Active — Speak or type..." : placeholder}
          disabled={isLoading}
          className="flex-1 bg-transparent px-3.5 py-2 text-xs sm:text-sm text-[#F0EEFF] placeholder-zinc-500 focus:outline-none disabled:opacity-50"
        />

        {/* Ambient Voice Orb / Mic Toggle Button */}
        {onToggleVoice && (
          <motion.button
            whileHover={{ scale: 1.08 }}
            whileTap={{ scale: 0.92 }}
            type="button"
            onClick={onToggleVoice}
            disabled={isLoading}
            className={`flex h-8 w-8 items-center justify-center rounded-xl transition-all cursor-pointer ${
              isVoiceMode
                ? "bg-gradient-to-tr from-cyan-500 to-emerald-500 text-white shadow-lg shadow-cyan-500/30 animate-pulse"
                : "bg-[#1E1E2E] text-zinc-400 hover:bg-[#2A2A3E] hover:text-white"
            }`}
            title={isVoiceMode ? "Voice mode enabled" : "Enable ambient voice mode"}
          >
            {isVoiceMode ? (
              <Mic className="h-4 w-4 text-white" />
            ) : (
              <MicOff className="h-3.5 w-3.5 text-zinc-400" />
            )}
          </motion.button>
        )}

        {/* Send Action Button */}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={handleSubmit}
          disabled={!input.trim() || isLoading}
          className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-[#7C3AED] to-[#0891B2] text-white shadow-md shadow-[#7C3AED]/20 transition-all hover:from-[#6D28D9] hover:to-[#0e7490] hover:shadow-lg hover:shadow-[#7C3AED]/30 disabled:opacity-30 disabled:hover:scale-100 disabled:cursor-not-allowed cursor-pointer"
          title="Send message"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </motion.button>
      </motion.div>
    </div>
  );
}
