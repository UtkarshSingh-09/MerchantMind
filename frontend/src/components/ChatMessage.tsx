"use client";

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bot,
  User,
  Sparkles,
  CreditCard,
  ExternalLink,
  ShieldCheck,
  Zap,
  Lock,
  ArrowRight,
} from "lucide-react";
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

  // Rich markdown parser for bold, tables, lists, and headings
  const renderFormattedText = (rawText: string) => {
    if (rawText.includes("|") && rawText.includes("---")) {
      const lines = rawText.split("\n");
      const elements: React.ReactNode[] = [];
      let tableRows: string[] = [];
      let inTable = false;

      lines.forEach((line, idx) => {
        const trimmed = line.trim();
        if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
          inTable = true;
          tableRows.push(trimmed);
        } else {
          if (inTable && tableRows.length > 0) {
            elements.push(renderTable(tableRows, `table-${idx}`));
            tableRows = [];
            inTable = false;
          }
          if (trimmed) {
            elements.push(
              <div key={`line-${idx}`} className="my-1.5 leading-relaxed">
                {formatInlineMarkdown(trimmed)}
              </div>
            );
          } else {
            elements.push(<div key={`br-${idx}`} className="h-2" />);
          }
        }
      });

      if (inTable && tableRows.length > 0) {
        elements.push(renderTable(tableRows, "table-last"));
      }

      return elements;
    }

    return rawText.split("\n").map((line, idx) => {
      const trimmed = line.trim();
      if (!trimmed) return <div key={idx} className="h-1.5" />;

      if (trimmed.startsWith("### ")) {
        return (
          <h4 key={idx} className="mt-3 mb-1.5 text-xs font-bold uppercase tracking-wider text-[#A78BFA] flex items-center gap-1.5">
            <Zap className="h-3 w-3 text-[#7C3AED]" />
            {formatInlineMarkdown(trimmed.replace("### ", ""))}
          </h4>
        );
      }

      if (trimmed.startsWith("- ") || trimmed.startsWith("• ")) {
        return (
          <div key={idx} className="my-1 flex items-start gap-2 text-xs">
            <span className="text-[#7C3AED] font-bold mt-0.5">•</span>
            <span>{formatInlineMarkdown(trimmed.replace(/^[-•]\s*/, ""))}</span>
          </div>
        );
      }

      return (
        <div key={idx} className="my-1 leading-relaxed">
          {formatInlineMarkdown(trimmed)}
        </div>
      );
    });
  };

  const renderTable = (rows: string[], key: string) => {
    const parsedRows = rows
      .filter((r) => !r.includes("---"))
      .map((r) =>
        r
          .split("|")
          .map((c) => c.trim())
          .filter((c, i, arr) => i !== 0 && i !== arr.length - 1)
      );

    if (parsedRows.length === 0) return null;
    const header = parsedRows[0];
    const dataRows = parsedRows.slice(1);

    return (
      <div key={key} className="my-3 overflow-x-auto rounded-2xl border border-[#2A2A3E] bg-[#0A0A12]/90 shadow-xl">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-[#2A2A3E] bg-gradient-to-r from-[#1A1A2C] to-[#12121E] text-[#A78BFA] font-semibold">
              {header.map((col, i) => (
                <th key={i} className="py-2.5 px-3.5 text-[11px] uppercase tracking-wider">
                  {formatInlineMarkdown(col)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-[#2A2A3E]/60 font-mono text-[11px]">
            {dataRows.map((row, rIdx) => (
              <tr key={rIdx} className="hover:bg-[#1E1E2E]/50 transition-colors">
                {row.map((cell, cIdx) => (
                  <td key={cIdx} className="py-2.5 px-3.5 text-[#F0EEFF] font-normal">
                    {formatInlineMarkdown(cell)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const formatInlineMarkdown = (text: string) => {
    const parts = text.split(/(\*\*.*?\*\*|\*.*?\*|`.*?`)/g);
    return parts.map((part, i) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return (
          <strong key={i} className="font-semibold text-[#A78BFA]">
            {part.slice(2, -2)}
          </strong>
        );
      }
      if (part.startsWith("*") && part.endsWith("*")) {
        return (
          <em key={i} className="italic text-zinc-300">
            {part.slice(1, -1)}
          </em>
        );
      }
      if (part.startsWith("`") && part.endsWith("`")) {
        return (
          <code key={i} className="rounded-md bg-[#1E1E2E] border border-[#2A2A3E] px-1.5 py-0.5 text-[11px] font-mono text-[#0891B2]">
            {part.slice(1, -1)}
          </code>
        );
      }
      return part;
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12, scale: 0.98, x: isUser ? 12 : -12 }}
      animate={{ opacity: 1, y: 0, scale: 1, x: 0 }}
      transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
      className={`flex w-full gap-3 py-2 transition-all ${
        isUser ? "flex-row-reverse" : "flex-row"
      }`}
    >
      {/* Avatar */}
      <motion.div
        whileHover={{ scale: 1.06 }}
        className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl shadow-lg border relative ${
          isUser
            ? "bg-gradient-to-tr from-[#7C3AED] to-[#9333EA] border-[#7C3AED]/50 text-white shadow-[#7C3AED]/25"
            : "bg-gradient-to-tr from-[#12121E] via-[#1A1A2E] to-[#161626] border-[#7C3AED]/30 text-[#A78BFA] shadow-black/40"
        }`}
      >
        {!isUser && (
          <span className="absolute -top-0.5 -right-0.5 flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#7C3AED] opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-[#7C3AED]" />
          </span>
        )}
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4 text-[#A78BFA]" />}
      </motion.div>

      {/* Message Bubble Container */}
      <div
        className={`flex max-w-[92%] flex-col md:max-w-[82%] ${
          isUser ? "items-end" : "items-start"
        }`}
      >
        <motion.div
          whileHover={{ y: -1 }}
          transition={{ duration: 0.15 }}
          className={`relative rounded-3xl px-4.5 py-3.5 text-xs sm:text-sm leading-relaxed shadow-xl backdrop-blur-xl ${
            isUser
              ? "rounded-tr-none bg-gradient-to-r from-[#7C3AED] via-[#6D28D9] to-[#5B21B6] text-white border border-[#7C3AED]/40 shadow-[#7C3AED]/20"
              : "rounded-tl-none border border-[#2A2A3E] bg-[#12121E]/95 text-[#F0EEFF] shadow-black/30"
          }`}
        >
          {/* Formatted Content */}
          <div className="font-normal">{renderFormattedText(content)}</div>

          {/* Razorpay Payment Link CTA Banner */}
          {payment_link && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15, duration: 0.3 }}
              className="mt-3.5 flex flex-col gap-2.5 rounded-2xl border border-emerald-500/30 bg-gradient-to-br from-[#0B1E17] to-[#0A1612] p-3.5 text-[#F0EEFF] shadow-xl"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs font-semibold text-emerald-300">
                  <CreditCard className="h-4 w-4 text-emerald-400" />
                  <span>Razorpay Payment Ready</span>
                </div>
                <span className="flex items-center gap-1 text-[10px] font-semibold text-emerald-300 bg-emerald-950/70 px-2 py-0.5 rounded-full border border-emerald-500/40 shadow-sm">
                  <Lock className="h-3 w-3" />
                  256-Bit Encrypted
                </span>
              </div>
              <motion.a
                href={payment_link}
                target="_blank"
                rel="noopener noreferrer"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="mt-1 flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-emerald-600 via-emerald-500 to-teal-600 py-2.5 px-4 text-xs font-bold text-white shadow-lg shadow-emerald-900/40 transition hover:from-emerald-500 hover:to-teal-500 cursor-pointer"
              >
                <span>Pay via Razorpay Secure</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </motion.a>
            </motion.div>
          )}

          {/* Timestamp */}
          {timestamp && (
            <div
              className={`mt-1.5 text-[10px] ${
                isUser ? "text-[#A78BFA]/80" : "text-zinc-500"
              }`}
            >
              {new Date(timestamp).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </div>
          )}
        </motion.div>

        {/* Product Recommendations Grid */}
        <AnimatePresence>
          {recommendations && recommendations.length > 0 && onAddToCart && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1, duration: 0.3 }}
              className="mt-3 w-full"
            >
              <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-zinc-300">
                <Sparkles className="h-3.5 w-3.5 text-[#A78BFA]" />
                <span>Recommended Items for You</span>
              </div>
              <div className="grid grid-cols-1 gap-3.5 sm:grid-cols-2 items-stretch">
                {recommendations.map((rec) => (
                  <div key={rec.product_id} className="h-full">
                    <ProductCard
                      product={rec}
                      onAddToCart={onAddToCart}
                    />
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
