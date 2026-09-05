"use client";

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  User,
  Store,
  CreditCard,
  ExternalLink,
  ShieldCheck,
  Lock,
  ArrowRight,
  Truck,
  ShoppingBag,
  Tag,
} from "lucide-react";
import { ProductCard } from "./ProductCard";
import { ProductRecommendation, resolvePaymentUrl } from "@/lib/api";

export interface MessageProps {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp?: string;
  recommendations?: ProductRecommendation[];
  action?: string;
  payment_link?: string | null;
  activePaymentLink?: string | null;
  activeOrderId?: string | null;
  onAddToCart?: (product: ProductRecommendation) => void;
  onActionClick?: (actionText: string) => void;
  onPayClick?: (paymentUrl?: string | null) => void;
}

export function ChatMessage({
  role,
  content,
  timestamp,
  recommendations = [],
  payment_link,
  activePaymentLink,
  activeOrderId,
  onAddToCart,
  onActionClick,
  onPayClick,
}: MessageProps) {
  const isUser = role === "user";

  // Rich markdown parser for bold, tables, lists, interactive chips, and headings
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

      // Interactive Action Chips e.g. [🛍️ Store Pickup] [🚚 Doorstep Delivery]
      const choiceMatches = [...trimmed.matchAll(/\[([^\]]+)\](?!\()/g)];
      if (choiceMatches.length > 0 && !trimmed.includes("](")) {
        return (
          <div key={idx} className="my-3 flex flex-wrap gap-2 items-center">
            {choiceMatches.map((m, cIdx) => {
              const label = m[1].trim();
              const isPaymentBtn = label.toLowerCase().includes("pay");
              const isTrackingBtn = label.toLowerCase().includes("track");

              // If this is a payment button, it must ALWAYS open Razorpay directly via onPayClick
              if (isPaymentBtn) {
                const targetLink = payment_link || activePaymentLink;
                return (
                  <motion.button
                    key={cIdx}
                    type="button"
                    whileHover={{ scale: 1.02, y: -1 }}
                    whileTap={{ scale: 0.97 }}
                    transition={{ type: "spring", stiffness: 400, damping: 25 }}
                    onClick={() => onPayClick?.(targetLink)}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-gradient-to-r from-emerald-500 via-emerald-600 to-teal-600 text-white shadow-[0_0_22px_-3px_rgba(16,185,129,0.4),inset_0_1px_0_0_rgba(255,255,255,0.25)] border border-emerald-400/30 hover:brightness-110 transition-all cursor-pointer"
                  >
                    <CreditCard className="h-3.5 w-3.5 text-emerald-100" />
                    <span>{label}</span>
                    <ArrowRight className="h-3.5 w-3.5 text-emerald-200" />
                  </motion.button>
                );
              }

              // If this is a tracking button, open the tracking dashboard!
              if (isTrackingBtn && activeOrderId) {
                return (
                  <motion.a
                    key={cIdx}
                    href={`/orders/${activeOrderId}/tracking`}
                    whileHover={{ scale: 1.02, y: -1 }}
                    whileTap={{ scale: 0.97 }}
                    transition={{ type: "spring", stiffness: 400, damping: 25 }}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-gradient-to-r from-indigo-600 via-purple-600 to-violet-700 text-white shadow-[0_0_22px_-3px_rgba(99,102,241,0.4),inset_0_1px_0_0_rgba(255,255,255,0.25)] border border-indigo-400/30 hover:brightness-110 transition-all cursor-pointer no-underline"
                  >
                    <Truck className="h-3.5 w-3.5 text-indigo-100" />
                    <span>{label}</span>
                    <ArrowRight className="h-3.5 w-3.5 text-indigo-200" />
                  </motion.a>
                );
              }

              return (
                <motion.button
                  key={cIdx}
                  type="button"
                  whileHover={{ scale: 1.03, y: -1 }}
                  whileTap={{ scale: 0.96 }}
                  transition={{ type: "spring", stiffness: 400, damping: 25 }}
                  onClick={() => onActionClick?.(label)}
                  className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-medium bg-white/[0.04] hover:bg-white/[0.09] border border-white/[0.1] hover:border-white/[0.25] text-zinc-200 hover:text-white backdrop-blur-md transition-all shadow-sm cursor-pointer active:scale-95"
                >
                  <span>{label}</span>
                </motion.button>
              );
            })}
          </div>
        );
      }

      if (trimmed.startsWith("### ")) {
        return (
          <h4 key={idx} className="mt-3.5 mb-1.5 text-xs font-bold uppercase tracking-wider text-zinc-200 flex items-center gap-2">
            <span className="h-3 w-1 rounded-full bg-indigo-500 shrink-0" />
            {formatInlineMarkdown(trimmed.replace("### ", ""))}
          </h4>
        );
      }

      if (trimmed.startsWith("- ") || trimmed.startsWith("• ")) {
        return (
          <div key={idx} className="my-1 flex items-start gap-2 text-xs">
            <span className="text-indigo-400 font-bold mt-0.5">•</span>
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
      <div key={key} className="my-3 overflow-x-auto rounded-2xl border border-white/[0.08] bg-[#0A0C14]/90 shadow-xl backdrop-blur-md">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-white/[0.08] bg-white/[0.03] text-zinc-300 font-semibold">
              {header.map((col, i) => (
                <th key={i} className="py-2.5 px-3.5 text-[11px] uppercase tracking-wider">
                  {formatInlineMarkdown(col)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04] font-mono text-[11px]">
            {dataRows.map((row, rIdx) => (
              <tr key={rIdx} className="hover:bg-white/[0.02] transition-colors">
                {row.map((cell, cIdx) => (
                  <td key={cIdx} className="py-2.5 px-3.5 text-zinc-200 font-normal">
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
    // Split by bold, italic, inline code, and markdown links [text](url)
    const parts = text.split(/(\*\*.*?\*\*|\*.*?\*|`.*?`|\[[^\]]+\]\([^)]+\))/g);
    return parts.map((part, i) => {
      if (part.startsWith("[") && part.includes("](") && part.endsWith(")")) {
        const match = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
        if (match) {
          const [, linkText, url] = match;
          const isPay = linkText.toLowerCase().includes("pay");
          if (isPay) {
            return (
              <motion.button
                key={i}
                type="button"
                onClick={() => onPayClick?.(url)}
                whileHover={{ scale: 1.02, y: -1 }}
                whileTap={{ scale: 0.97 }}
                transition={{ type: "spring", stiffness: 400, damping: 25 }}
                className="my-1 inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-bold bg-gradient-to-r from-emerald-500 via-emerald-600 to-teal-600 text-white shadow-[0_0_20px_-3px_rgba(16,185,129,0.4),inset_0_1px_0_0_rgba(255,255,255,0.25)] border border-emerald-400/30 hover:brightness-110 transition-all cursor-pointer"
              >
                <CreditCard className="h-3 w-3 text-emerald-100" />
                <span>{linkText}</span>
                <ArrowRight className="h-3.5 w-3.5 text-emerald-200" />
              </motion.button>
            );
          }
          const isTrack = linkText.toLowerCase().includes("track") || url.includes("/tracking");
          if (isTrack) {
            const finalUrl = (url && url !== "#")
              ? url
              : (activeOrderId ? `/orders/${activeOrderId}/tracking` : "/orders");
            return (
              <motion.a
                key={i}
                href={finalUrl}
                target={finalUrl.startsWith("http") ? "_blank" : undefined}
                rel={finalUrl.startsWith("http") ? "noopener noreferrer" : undefined}
                whileHover={{ scale: 1.02, y: -1 }}
                whileTap={{ scale: 0.97 }}
                transition={{ type: "spring", stiffness: 400, damping: 25 }}
                className="my-1.5 inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-gradient-to-r from-indigo-600 via-purple-600 to-violet-700 text-white shadow-[0_0_20px_-3px_rgba(99,102,241,0.4),inset_0_1px_0_0_rgba(255,255,255,0.25)] border border-indigo-400/30 hover:brightness-110 transition-all cursor-pointer no-underline"
              >
                <Truck className="h-3.5 w-3.5 text-indigo-100" />
                <span>{linkText}</span>
                <ArrowRight className="h-3.5 w-3.5 text-indigo-200" />
              </motion.a>
            );
          }
          return (
            <a
              key={i}
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-indigo-400 hover:text-indigo-300 underline underline-offset-2 transition-colors font-medium"
            >
              {linkText}
            </a>
          );
        }
      }
      if (part.startsWith("**") && part.endsWith("**")) {
        return (
          <strong key={i} className="font-semibold text-zinc-100">
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
          <code key={i} className="rounded-md bg-white/[0.05] border border-white/[0.08] px-1.5 py-0.5 text-[11px] font-mono text-indigo-300">
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
      {/* Avatar: Sleek Monogram & Store Mark (NO ROBOT, NO AI ICONS) */}
      <motion.div
        whileHover={{ scale: 1.05 }}
        className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl shadow-lg border relative ${
          isUser
            ? "bg-gradient-to-br from-indigo-500 via-indigo-600 to-violet-700 border-indigo-400/40 text-white shadow-indigo-500/20"
            : "bg-gradient-to-b from-zinc-800 to-zinc-950 border-white/10 text-zinc-200 shadow-black/60"
        }`}
      >
        {!isUser && (
          <span className="absolute -top-0.5 -right-0.5 flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500 ring-2 ring-[#08090E]" />
          </span>
        )}
        {isUser ? (
          <User className="h-4 w-4" />
        ) : (
          <Store className="h-4 w-4 text-zinc-200" />
        )}
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
              ? "rounded-tr-none bg-gradient-to-r from-indigo-600 via-indigo-700 to-purple-800 text-white border border-indigo-400/25 shadow-[0_4px_20px_-2px_rgba(99,102,241,0.25)]"
              : "rounded-tl-none border border-white/[0.08] bg-[#11131E]/95 text-zinc-100 shadow-[0_10px_30px_rgba(0,0,0,0.5)] [box-shadow:inset_0_1px_0_0_rgba(255,255,255,0.06)]"
          }`}
        >
          {/* Formatted Content */}
          <div className="font-normal">{renderFormattedText(content)}</div>

          {/* Razorpay Payment Link CTA Banner (Only for assistant messages, and not duplicated if already rendered inline) */}
          {!isUser && payment_link && !content.includes("/pay/") && !(content.includes("[") && content.toLowerCase().includes("pay") && content.includes("]")) && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15, duration: 0.3 }}
              className="mt-3.5 flex flex-col gap-2.5 rounded-2xl border border-emerald-500/30 bg-gradient-to-br from-[#091A14] to-[#07130F] p-3.5 text-zinc-100 shadow-xl"
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
              <motion.button
                type="button"
                onClick={() => onPayClick?.(payment_link)}
                whileHover={{ scale: 1.02, y: -1 }}
                whileTap={{ scale: 0.98 }}
                transition={{ type: "spring", stiffness: 400, damping: 25 }}
                className="mt-1 flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-emerald-500 via-emerald-600 to-teal-600 py-2.5 px-4 text-xs font-bold text-white shadow-[0_0_24px_-4px_rgba(16,185,129,0.4),inset_0_1px_0_0_rgba(255,255,255,0.25)] transition hover:brightness-110 cursor-pointer"
              >
                <span>Pay via Razorpay Secure</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </motion.button>
            </motion.div>
          )}

          {/* Timestamp */}
          {timestamp && (
            <div
              className={`mt-1.5 text-[10px] ${
                isUser ? "text-indigo-200/70" : "text-zinc-500"
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
                <ShoppingBag className="h-3.5 w-3.5 text-indigo-400" />
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
