"use client";

import React, { useState, useEffect, useRef, KeyboardEvent } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Send,
  Loader2,
  Mic,
  MicOff,
  Volume2,
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

export function ChatInput({
  onSendMessage,
  isLoading,
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

  return (
    <div className="flex flex-col gap-2.5">

      {/* Voice Listening Wave Indicator (21st.dev Audio Visualizer) */}
      <AnimatePresence>
        {isVoiceMode && (
          <motion.div
            initial={{ opacity: 0, height: 0, scale: 0.96 }}
            animate={{ opacity: 1, height: "auto", scale: 1 }}
            exit={{ opacity: 0, height: 0, scale: 0.96 }}
            transition={{ duration: 0.22, ease: "easeOut" }}
            className={`flex items-center justify-between px-3.5 py-2 rounded-2xl border text-xs backdrop-blur-md ${
              voiceState === "speaking"
                ? "bg-emerald-950/40 border-emerald-500/40 text-emerald-300 shadow-[0_0_20px_-3px_rgba(16,185,129,0.2)]"
                : voiceState === "listening"
                ? "bg-amber-950/40 border-amber-500/40 text-amber-300 shadow-[0_0_20px_-3px_rgba(245,158,11,0.2)]"
                : "bg-indigo-950/40 border-indigo-500/40 text-indigo-300 shadow-[0_0_20px_-3px_rgba(99,102,241,0.2)]"
            }`}
          >
            <div className="flex items-center gap-2">
              {voiceState === "speaking" ? (
                <Volume2 className="h-3.5 w-3.5 text-emerald-400 animate-pulse" />
              ) : (
                <Mic className="h-3.5 w-3.5 text-amber-400 animate-pulse" />
              )}
              <span className="font-medium">
                {voiceState === "speaking"
                  ? "Speaking response aloud..."
                  : voiceState === "thinking"
                  ? "Processing order request..."
                  : "Listening for your order..."}
              </span>
              <span className="flex gap-0.5 items-center ml-1">
                {[0, 1, 2, 3, 4].map((i) => (
                  <motion.span
                    key={i}
                    className={`w-0.5 rounded-full ${
                      voiceState === "speaking" ? "bg-emerald-400" : "bg-amber-400"
                    }`}
                    animate={{ height: ["4px", "14px", "4px"] }}
                    transition={{
                      duration: 0.55,
                      repeat: Infinity,
                      delay: i * 0.1,
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
                Mute ✕
              </motion.button>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input Field Bar (21st.dev Floating Dock) */}
      <motion.div
        animate={{
          borderColor: isFocused
            ? "rgba(99, 102, 241, 0.6)"
            : isVoiceMode
            ? "rgba(6, 182, 212, 0.5)"
            : "rgba(255, 255, 255, 0.08)",
          boxShadow: isFocused
            ? "0 0 25px -2px rgba(99, 102, 241, 0.25)"
            : isVoiceMode
            ? "0 0 20px -2px rgba(6, 182, 212, 0.2)"
            : "0 10px 30px -5px rgba(0, 0, 0, 0.5)",
        }}
        transition={{ duration: 0.2 }}
        className="relative flex items-center gap-2 rounded-2xl border bg-[#0E1019]/90 p-1.5 backdrop-blur-2xl transition-all"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={isVoiceMode ? "🎙️ Voice Active — Tell me what you'd like to order..." : placeholder}
          disabled={isLoading}
          className="flex-1 bg-transparent px-3.5 py-2 text-xs sm:text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none disabled:opacity-50 font-normal"
        />

        {/* Ambient Voice Orb / Mic Toggle Button */}
        {onToggleVoice && (
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            type="button"
            onClick={onToggleVoice}
            disabled={isLoading}
            className={`flex h-8.5 w-8.5 items-center justify-center rounded-xl transition-all cursor-pointer ${
              isVoiceMode
                ? "bg-gradient-to-tr from-cyan-500 to-emerald-500 text-white shadow-lg shadow-cyan-500/30 animate-pulse"
                : "bg-white/[0.04] text-zinc-400 hover:bg-white/[0.08] hover:text-white border border-white/[0.06]"
            }`}
            title={isVoiceMode ? "Voice active (Click to mute)" : "Click to enable voice"}
          >
            {isVoiceMode ? (
              <Mic className="h-4 w-4 text-white" />
            ) : (
              <MicOff className="h-3.5 w-3.5 text-zinc-400" />
            )}
          </motion.button>
        )}

        {/* Send Action Button (21st.dev Style Pill) */}
        <motion.button
          whileHover={{ scale: 1.04, y: -0.5 }}
          whileTap={{ scale: 0.95 }}
          transition={{ type: "spring", stiffness: 400, damping: 25 }}
          onClick={handleSubmit}
          disabled={!input.trim() || isLoading}
          className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-r from-indigo-500 to-violet-600 hover:from-indigo-400 hover:to-violet-500 text-white shadow-[0_0_18px_-2px_rgba(99,102,241,0.4),inset_0_1px_0_0_rgba(255,255,255,0.25)] border border-indigo-400/30 transition-all disabled:opacity-30 disabled:hover:scale-100 disabled:cursor-not-allowed cursor-pointer"
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
