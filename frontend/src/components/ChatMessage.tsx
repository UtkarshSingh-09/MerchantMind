"use client";

import React from "react";
import { Bot, User, Sparkles, CreditCard, ExternalLink, ShieldCheck } from "lucide-react";
import { ProductCard } from "./ProductCard";
import { ProductRecommendation } from "@/lib/api";

export interface MessageProps {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp?: string;
  recommendations?: ProductRecommendation[];
  action?: string;
  payment_link?: string | null;
  onAddToCart?: (product: ProductRecommendation) => void;
}

export function ChatMessage({
  role,
  content,
  timestamp,
  recommendations = [],
  payment_link,
  onAddToCart,
}: MessageProps) {
  const isUser = role === "user";

  // Simple Markdown bold formatter (**text** -> <strong>text</strong>)
  const formatContent = (text: string) => {
    const parts = text.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={i} className="font-semibold text-indigo-300">{part.slice(2, -2)}</strong>;
      }
      return part;
    });
  };

  return (
    <div
      className={`flex w-full gap-3 py-3 transition-all ${
        isUser ? "flex-row-reverse" : "flex-row"
      }`}
    >
      {/* Avatar */}
      <div
        className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl shadow-md border ${
          isUser
            ? "bg-gradient-to-tr from-indigo-600 to-violet-600 border-indigo-500/30 text-white"
            : "bg-zinc-900/90 border-zinc-800 text-indigo-400"
        }`}
      >
        {isUser ? <User className="h-4.5 w-4.5" /> : <Bot className="h-4.5 w-4.5" />}
      </div>

      {/* Message Bubble */}
      <div
        className={`flex max-w-[85%] flex-col md:max-w-[75%] ${
          isUser ? "items-end" : "items-start"
        }`}
      >
        <div
          className={`relative rounded-2xl px-4.5 py-3.5 text-sm leading-relaxed shadow-lg backdrop-blur-md ${
            isUser
              ? "rounded-tr-none bg-gradient-to-r from-indigo-600 to-violet-600 text-white border border-indigo-500/30"
              : "rounded-tl-none border border-zinc-800/80 bg-zinc-900/90 text-zinc-200"
          }`}
        >
          {/* Main Text */}
          <div className="whitespace-pre-wrap font-normal">{formatContent(content)}</div>

          {/* Razorpay Payment Link CTA Banner */}
          {payment_link && (
            <div className="mt-3.5 flex flex-col gap-2 rounded-xl border border-indigo-500/40 bg-gradient-to-br from-indigo-950/80 to-zinc-900/90 p-3.5 text-zinc-100 shadow-inner">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs font-bold text-indigo-300">
                  <CreditCard className="h-4 w-4 text-indigo-400" />
                  <span>Razorpay Payment Ready</span>
                </div>
                <span className="flex items-center gap-1 text-[10px] font-medium text-emerald-400 bg-emerald-950/50 px-2 py-0.5 rounded-full border border-emerald-500/30">
                  <ShieldCheck className="h-3 w-3" />
                  256-Bit Encrypted
                </span>
              </div>
              <p className="text-xs text-zinc-400">
                Click below to complete your checkout securely in Razorpay test mode.
              </p>
              <a
                href={payment_link}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-1 flex items-center justify-center gap-2 rounded-xl bg-indigo-600 py-2.5 px-4 text-xs font-bold text-white shadow-lg transition hover:bg-indigo-500 active:scale-98"
              >
                <span>Pay Now with Razorpay</span>
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            </div>
          )}

          {/* Timestamp */}
          {timestamp && (
            <div
              className={`mt-1.5 text-[10px] ${
                isUser ? "text-indigo-200" : "text-zinc-500"
              }`}
            >
              {new Date(timestamp).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </div>
          )}
        </div>

        {/* Product Recommendations Grid (if any attached) */}
        {recommendations && recommendations.length > 0 && onAddToCart && (
          <div className="mt-3.5 w-full">
            <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-zinc-400">
              <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
              <span>Recommended Add-ons & Pairings</span>
            </div>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {recommendations.map((rec) => (
                <ProductCard
                  key={rec.product_id}
                  product={rec}
                  onAddToCart={onAddToCart}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
