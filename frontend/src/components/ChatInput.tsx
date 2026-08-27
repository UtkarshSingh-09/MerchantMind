"use client";

import React, { useState, KeyboardEvent } from "react";
import { Send, Sparkles, Loader2 } from "lucide-react";

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  onSuggestionClick?: (suggestion: string) => void;
}

const QUICK_SUGGESTIONS = [
  "🎂 Chocolate cake under ₹800 for birthday",
  "🥐 Fresh breakfast pastries",
  "🎉 Party combo with balloons",
  "☕ Cold coffee & sourdough bread",
];

export function ChatInput({
  onSendMessage,
  isLoading,
  onSuggestionClick,
}: ChatInputProps) {
  const [input, setInput] = useState("");

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
    <div className="w-full space-y-2.5">
      {/* Suggestion Chips */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs no-scrollbar">
        <span className="flex shrink-0 items-center gap-1 font-medium text-zinc-400">
          <Sparkles className="h-3 w-3 text-indigo-500" />
          Try:
        </span>
        {QUICK_SUGGESTIONS.map((s, idx) => (
          <button
            key={idx}
            onClick={() => {
              if (onSuggestionClick) onSuggestionClick(s);
              else onSendMessage(s);
            }}
            disabled={isLoading}
            className="shrink-0 rounded-full border border-zinc-200/80 bg-white/80 px-3 py-1 text-zinc-600 shadow-2xs backdrop-blur-sm transition hover:border-indigo-300 hover:bg-indigo-50/60 hover:text-indigo-700 disabled:opacity-50 dark:border-zinc-800 dark:bg-zinc-900/80 dark:text-zinc-300 dark:hover:border-indigo-700 dark:hover:bg-indigo-950/40"
          >
            {s}
          </button>
        ))}
      </div>

      {/* Input Field */}
      <div className="relative flex items-center rounded-2xl border border-zinc-200/90 bg-white shadow-sm transition-all focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-500/20 dark:border-zinc-800 dark:bg-zinc-900">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          placeholder="Ask for items, cakes under a budget, or add to cart..."
          className="w-full rounded-2xl bg-transparent py-3.5 pl-4 pr-12 text-sm text-zinc-800 placeholder-zinc-400 outline-none disabled:opacity-60 dark:text-zinc-100"
        />

        <button
          onClick={handleSubmit}
          disabled={!input.trim() || isLoading}
          className="absolute right-2 flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-sm transition-all hover:bg-indigo-700 active:scale-95 disabled:cursor-not-allowed disabled:bg-zinc-200 disabled:text-zinc-400 dark:bg-indigo-500 dark:disabled:bg-zinc-800 dark:disabled:text-zinc-600"
          title="Send message"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </button>
      </div>
    </div>
  );
}
