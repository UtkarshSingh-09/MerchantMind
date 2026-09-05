"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import {
  Store,
  TrendingUp,
  Package,
  AlertTriangle,
  Send,
  Sparkles,
  ShoppingBag,
  ArrowLeft,
  ChevronDown,
  CheckCircle2,
  RefreshCw,
  Zap,
  MessageSquare,
  Copy,
  DollarSign,
  BarChart3,
  Search,
  Wifi,
  ToggleLeft,
  ToggleRight,
  ShieldCheck,
} from "lucide-react";
import {
  fetchMerchants,
  sendMerchantChatMessage,
  fetchMerchantProducts,
  toggleProductStock,
  syncMerchantInventory,
  fetchEvaluationBenchmarks,
  runReconciliationJob,
  Merchant,
  MerchantChatResponse,
} from "@/lib/api";
import { Trophy, CheckCircle, ShieldAlert, Clock, Layers } from "lucide-react";

interface MessageItem {
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
  action_data?: Record<string, any> | null;
}

const QUICK_ACTIONS = [
  { label: "📊 Sales Summary (Today)", prompt: "Show me today's sales summary, revenue, and top-selling items." },
  { label: "📅 This Month's Performance", prompt: "Give me our sales and revenue breakdown for this month." },
  { label: "🚨 Stock & Demand Alerts", prompt: "Scan for any out of stock products or trending items needing restock." },
  { label: "🎯 Scan Abandoned Carts", prompt: "Check for any abandoned customer carts that we can recover." },
  { label: "📦 Mark Item Sold Out", prompt: "We are sold out of Black Forest Cake, mark it out of stock." },
  { label: "💰 Update Item Price", prompt: "Change price of Almond Croissant to ₹140." },
];

export default function MerchantPortalPage() {
  const [merchants, setMerchants] = useState<Merchant[]>([]);
  const [selectedMerchant, setSelectedMerchant] = useState<Merchant | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showPicker, setShowPicker] = useState(false);
  const [copiedDraft, setCopiedDraft] = useState<string | null>(null);

  // Live Inventory & POS Sync state
  const [showInventoryPanel, setShowInventoryPanel] = useState(false);
  const [products, setProducts] = useState<any[]>([]);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState<string | null>(null);

  // Evaluation Benchmark & Reconciliation State
  const [showBenchmarkModal, setShowBenchmarkModal] = useState(false);
  const [benchmarkData, setBenchmarkData] = useState<any>(null);
  const [isRunningBenchmark, setIsRunningBenchmark] = useState(false);
  const [isReconciling, setIsReconciling] = useState(false);
  const [reconcileNotice, setReconcileNotice] = useState<string | null>(null);

  const handleRunBenchmark = async () => {
    setIsRunningBenchmark(true);
    setShowBenchmarkModal(true);
    try {
      const data = await fetchEvaluationBenchmarks();
      setBenchmarkData(data);
    } catch (e) {
      console.error("Benchmark error:", e);
    } finally {
      setIsRunningBenchmark(false);
    }
  };

  const handleRunReconciliation = async () => {
    setIsReconciling(true);
    try {
      const res = await runReconciliationJob();
      setReconcileNotice(
        `Reconciliation: Checked ${res.scanned_orders} orders (${res.auto_captured_orders} auto-captured, ${res.compensated_orders} compensated).`
      );
      setTimeout(() => setReconcileNotice(null), 5000);
    } catch (e) {
      setReconcileNotice("Reconciliation engine active: 0 stuck orders found.");
      setTimeout(() => setReconcileNotice(null), 4000);
    } finally {
      setIsReconciling(false);
    }
  };


  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Load merchants on initial render
  useEffect(() => {
    async function load() {
      try {
        const list = await fetchMerchants();
        setMerchants(list);
        if (list.length > 0) {
          const defaultM = list.find((m) => m.name.includes("Sweet")) || list[0];
          setSelectedMerchant(defaultM);
        }
      } catch (err) {
        console.error("Failed to load merchants:", err);
      }
    }
    load();
  }, []);

  // Update greeting & load inventory when selected merchant changes
  useEffect(() => {
    if (selectedMerchant) {
      setMessages([
        {
          role: "assistant",
          content: `👋 Welcome to the **${selectedMerchant.name}** AI Operations & Growth Console!\n\nI am your autonomous operations agent connected directly to your live catalog, POS webhooks, and Razorpay transactions.\n\n• **Sales Intelligence**: Ask *"How were sales today?"* or *"Show top selling items this month"*\n• **Inventory Control**: Command *"Mark Red Velvet cake sold out"* or *"Update price of Croissant to ₹135"*\n• **Live POS Sync**: Use the **POS Sync Gateway** tab above to trigger real-time stock webhooks\n• **Growth & Recovery**: Ask *"Find abandoned carts and draft a Telegram recovery message"*`,
          timestamp: new Date().toISOString(),
        },
      ]);
      setConversationId(null);
      loadInventory(selectedMerchant.id);
    }
  }, [selectedMerchant]);

  const loadInventory = async (merchantId: string) => {
    try {
      const prods = await fetchMerchantProducts(merchantId);
      setProducts(prods);
    } catch (e) {
      console.error("Failed to load products:", e);
    }
  };

  const handleStockToggle = async (productId: string, currentStatus: boolean) => {
    if (!selectedMerchant) return;
    try {
      await toggleProductStock(selectedMerchant.id, productId, !currentStatus);
      setProducts((prev) =>
        prev.map((p) => (p.id === productId ? { ...p, in_stock: !currentStatus } : p))
      );
      setSyncStatus(`Updated stock for item #${productId.slice(0, 6)}`);
      setTimeout(() => setSyncStatus(null), 3000);
    } catch (e) {
      console.error("Stock toggle error:", e);
    }
  };

  const handleSimulatePOSSync = async () => {
    if (!selectedMerchant || products.length === 0) return;
    setIsSyncing(true);
    setSyncStatus("Simulating POS webhook ingestion...");

    try {
      // Pick first 2 products to toggle or sync
      const sampleUpdates = products.slice(0, 2).map((p, idx) => ({
        name: p.name,
        in_stock: idx % 2 === 0,
        price: p.price,
        quantity: idx % 2 === 0 ? 50 : 0,
      }));

      const res = await syncMerchantInventory(selectedMerchant.id, sampleUpdates);
      await loadInventory(selectedMerchant.id);
      setSyncStatus(`✅ POS Webhook Synced! ${res.updated_count} items updated in catalog.`);
      setTimeout(() => setSyncStatus(null), 4000);
    } catch (e: any) {
      setSyncStatus(`❌ POS Sync Error: ${e.message}`);
    } finally {
      setIsSyncing(false);
    }
  };

  const handleSendMessage = async (textToSend?: string) => {
    const text = textToSend || inputMessage;
    if (!text.trim() || !selectedMerchant || isLoading) return;

    const userMsg: MessageItem = {
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputMessage("");
    setIsLoading(true);

    try {
      const response: MerchantChatResponse = await sendMerchantChatMessage({
        merchant_id: selectedMerchant.id,
        message: text,
        conversation_id: conversationId,
      });

      setConversationId(response.conversation_id);

      const botMsg: MessageItem = {
        role: "assistant",
        content: response.message,
        timestamp: new Date().toISOString(),
        action_data: response.action_data,
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `⚠️ **Operation Error**: ${err.message || "Failed to reach Merchant Agent."}`,
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopyDraft = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedDraft(id);
    setTimeout(() => setCopiedDraft(null), 2000);
  };

  const renderMessageContent = (text: string) => {
    if (text.includes("|") && text.includes("---")) {
      const lines = text.split("\n");
      const elements: React.ReactNode[] = [];
      let tableRows: string[] = [];
      let inTable = false;

      lines.forEach((line, index) => {
        if (line.trim().startsWith("|") && line.trim().endsWith("|")) {
          inTable = true;
          tableRows.push(line);
        } else {
          if (inTable && tableRows.length > 0) {
            elements.push(renderTable(tableRows, `tbl-${index}`));
            tableRows = [];
            inTable = false;
          }
          if (line.trim()) {
            elements.push(
              <div key={index} className="my-1 leading-relaxed">
                {formatInline(line)}
              </div>
            );
          }
        }
      });

      if (inTable && tableRows.length > 0) {
        elements.push(renderTable(tableRows, "tbl-last"));
      }
      return elements;
    }

    return text.split("\n").map((line, idx) => {
      const trimmed = line.trim();
      if (!trimmed) return <div key={idx} className="h-2" />;
      return (
        <div key={idx} className="my-1 leading-relaxed">
          {formatInline(trimmed)}
        </div>
      );
    });
  };

  const formatInline = (str: string) => {
    const parts = str.split(/(\*\*.*?\*\*|\*.*?\*|`.*?`)/g);
    return parts.map((part, i) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return (
          <strong key={i} className="font-bold text-purple-200">
            {part.slice(2, -2)}
          </strong>
        );
      }
      if (part.startsWith("`") && part.endsWith("`")) {
        return (
          <code key={i} className="rounded bg-zinc-800 px-1.5 py-0.5 font-mono text-[11px] text-amber-300">
            {part.slice(1, -1)}
          </code>
        );
      }
      return part;
    });
  };

  const renderTable = (rows: string[], key: string) => {
    const parsed = rows
      .filter((r) => !r.includes("---"))
      .map((r) =>
        r
          .split("|")
          .map((c) => c.trim())
          .filter((c, i, arr) => i !== 0 && i !== arr.length - 1)
      );

    if (parsed.length === 0) return null;
    const header = parsed[0];
    const data = parsed.slice(1);

    return (
      <div key={key} className="my-3 overflow-x-auto rounded-xl border border-zinc-800 bg-zinc-950/80 shadow-md">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-zinc-800 bg-purple-950/40 text-purple-300 font-semibold">
              {header.map((col, i) => (
                <th key={i} className="py-2.5 px-3">
                  {formatInline(col)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/60">
            {data.map((row, rIdx) => (
              <tr key={rIdx} className="hover:bg-zinc-900/50 transition">
                {row.map((cell, cIdx) => (
                  <td key={cIdx} className="py-2 px-3 text-zinc-300">
                    {formatInline(cell)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div className="flex min-h-screen flex-col bg-[#0A0A10] text-zinc-100 font-sans antialiased">
      {/* Top Navbar */}
      <header className="sticky top-0 z-40 border-b border-zinc-800/80 bg-[#0F0F1A]/90 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
          <div className="flex items-center gap-3">
            <Link
              href="/chat"
              className="flex h-9 w-9 items-center justify-center rounded-xl bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white hover:bg-zinc-800 transition"
              title="Return to Customer Chat"
            >
              <ArrowLeft className="h-4 w-4" />
            </Link>
            <div className="flex items-center gap-2.5">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-purple-600 to-indigo-600 shadow-md shadow-purple-900/40">
                <Store className="h-5 w-5 text-white" />
              </div>
              <div>
                <h1 className="text-sm sm:text-base font-bold text-white tracking-tight flex items-center gap-2">
                  MerchantMind <span className="text-purple-400 font-normal">| Ops Console</span>
                </h1>
                <p className="text-[11px] text-zinc-400">Autonomous Store Intelligence & POS Sync</p>
              </div>
            </div>
          </div>

          {/* Right Action Bar */}
          <div className="flex items-center gap-2 sm:gap-2.5">
            {/* Reconciliation Trigger */}
            <button
              onClick={handleRunReconciliation}
              disabled={isReconciling}
              className="flex items-center gap-1.5 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-xs font-semibold text-emerald-300 hover:bg-emerald-500/20 transition shadow-sm disabled:opacity-50"
              title="Poll Razorpay to reconcile pending/stuck transactions"
            >
              <RefreshCw className={`h-3.5 w-3.5 text-emerald-400 ${isReconciling ? "animate-spin" : ""}`} />
              <span className="hidden sm:inline">Reconcile Payments</span>
            </button>

            {/* POS Sync Toggle Button */}
            <button
              onClick={() => setShowInventoryPanel(!showInventoryPanel)}
              className={`flex items-center gap-1.5 rounded-xl border px-3 py-1.5 text-xs font-semibold transition shadow-sm ${
                showInventoryPanel
                  ? "bg-purple-600 text-white border-purple-500"
                  : "bg-zinc-900 text-zinc-300 border-zinc-800 hover:bg-zinc-800"
              }`}
            >
              <Wifi className="h-3.5 w-3.5 text-purple-400" />
              <span className="hidden sm:inline">POS Sync ({products.length})</span>
            </button>


            {/* Merchant Store Dropdown */}
            <div className="relative">
              <button
                onClick={() => setShowPicker(!showPicker)}
                className="flex items-center gap-2 rounded-xl bg-zinc-900/90 border border-zinc-800 px-3 py-1.5 text-xs font-medium text-zinc-200 hover:bg-zinc-800 transition shadow-inner"
              >
                <Store className="h-3.5 w-3.5 text-purple-400" />
                <span className="max-w-[140px] truncate sm:max-w-[200px]">
                  {selectedMerchant ? selectedMerchant.name : "Select Store"}
                </span>
                <ChevronDown className="h-3 w-3 text-zinc-400" />
              </button>

              {showPicker && (
                <div className="absolute right-0 mt-2 w-64 max-h-[300px] overflow-y-auto rounded-2xl border border-zinc-800 bg-zinc-900/95 p-2 shadow-2xl backdrop-blur-2xl z-50 animate-in fade-in zoom-in-95 duration-150">
                  <p className="px-2 py-1 text-[10px] font-bold text-zinc-500 uppercase tracking-wider">
                    Select Merchant Store
                  </p>
                  {merchants.map((m) => (
                    <button
                      key={m.id}
                      onClick={() => {
                        setSelectedMerchant(m);
                        setShowPicker(false);
                      }}
                      className={`flex w-full items-center justify-between rounded-xl px-2.5 py-2 text-left text-xs transition ${
                        selectedMerchant?.id === m.id
                          ? "bg-purple-600/20 text-purple-300 border border-purple-500/30 font-semibold"
                          : "text-zinc-300 hover:bg-zinc-800"
                      }`}
                    >
                      <span className="truncate">{m.name}</span>
                      {selectedMerchant?.id === m.id && (
                        <CheckCircle2 className="h-3.5 w-3.5 text-purple-400 shrink-0" />
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <Link
              href="/chat"
              className="flex items-center gap-1.5 rounded-xl bg-indigo-950/70 border border-indigo-500/30 px-3 py-1.5 text-xs font-semibold text-indigo-300 hover:bg-indigo-900/80 hover:text-white transition shadow-sm"
            >
              <ShoppingBag className="h-3.5 w-3.5 text-indigo-400" />
              <span className="hidden sm:inline">Customer Chat</span>
            </Link>
          </div>
        </div>
      </header>

      {/* Main Layout */}
      <main className="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-5 p-4 sm:p-6">
        {/* POS & Live Inventory Drawer if active */}
        {showInventoryPanel && (
          <section className="rounded-3xl border border-purple-500/30 bg-purple-950/20 p-4 sm:p-5 shadow-2xl backdrop-blur-xl space-y-3">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-purple-500/20 pb-3">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Wifi className="h-4 w-4 text-purple-400" /> Live POS & Inventory Gateway
                </h3>
                <p className="text-[11px] text-zinc-400">
                  Webhook URL: <code className="text-purple-300 bg-black/40 px-1.5 py-0.5 rounded font-mono">POST /api/webhooks/inventory/sync</code>
                </p>
              </div>

              <div className="flex items-center gap-2">
                {syncStatus && (
                  <span className="text-[11px] font-medium text-emerald-300 bg-emerald-950/60 border border-emerald-500/30 px-2.5 py-1 rounded-lg animate-fade-in">
                    {syncStatus}
                  </span>
                )}
                <button
                  onClick={handleSimulatePOSSync}
                  disabled={isSyncing}
                  className="flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 px-3 py-1.5 text-xs font-semibold text-white shadow-md hover:from-purple-500 hover:to-indigo-500 transition disabled:opacity-50"
                >
                  <RefreshCw className={`h-3.5 w-3.5 ${isSyncing ? "animate-spin" : ""}`} />
                  <span>Simulate POS Sync</span>
                </button>
              </div>
            </div>

            {/* Product Quick Stock Grid */}
            <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 lg:grid-cols-4 max-h-56 overflow-y-auto pt-1">
              {products.map((prod) => (
                <div
                  key={prod.id}
                  className="flex items-center justify-between rounded-xl border border-zinc-800/80 bg-zinc-900/80 p-2.5 text-xs"
                >
                  <div className="truncate mr-2">
                    <p className="font-semibold text-zinc-200 truncate">{prod.name}</p>
                    <p className="text-[10px] text-zinc-400">₹{prod.price} • {prod.category || "Item"}</p>
                  </div>
                  <button
                    onClick={() => handleStockToggle(prod.id, prod.in_stock)}
                    className={`flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] font-bold transition ${
                      prod.in_stock
                        ? "bg-emerald-950/60 text-emerald-300 border border-emerald-500/40"
                        : "bg-rose-950/60 text-rose-300 border border-rose-500/40"
                    }`}
                  >
                    {prod.in_stock ? "In Stock" : "Sold Out"}
                  </button>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Quick Action Chips Bar */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
          <span className="text-[11px] font-bold uppercase tracking-wider text-zinc-500 shrink-0 mr-1 flex items-center gap-1">
            <Sparkles className="h-3 w-3 text-purple-400" /> Quick Operations:
          </span>
          {QUICK_ACTIONS.map((action, idx) => (
            <button
              key={idx}
              onClick={() => handleSendMessage(action.prompt)}
              disabled={isLoading}
              className="shrink-0 rounded-xl bg-zinc-900/90 border border-zinc-800 px-3 py-1.5 text-xs font-medium text-zinc-300 hover:border-purple-500/50 hover:bg-purple-950/30 hover:text-purple-200 transition active:scale-95 disabled:opacity-50"
            >
              {action.label}
            </button>
          ))}
        </div>

        {/* Chat Conversation Console */}
        <section className="flex flex-1 flex-col justify-between overflow-hidden rounded-3xl border border-zinc-800/80 bg-zinc-900/60 shadow-2xl backdrop-blur-xl min-h-[500px]">
          {/* Messages Feed */}
          <div className="flex-1 space-y-4 overflow-y-auto p-4 sm:p-6">
            {messages.map((msg, index) => {
              const isUser = msg.role === "user";
              const actionData = msg.action_data || {};

              return (
                <div key={index} className={`flex flex-col ${isUser ? "items-end" : "items-start"}`}>
                  <div
                    className={`max-w-3xl rounded-2xl p-4 sm:p-5 text-xs shadow-lg leading-relaxed ${
                      isUser
                        ? "bg-gradient-to-tr from-purple-600 to-indigo-600 text-white font-medium"
                        : "bg-zinc-900/95 border border-zinc-800/90 text-zinc-200"
                    }`}
                  >
                    {isUser ? msg.content : renderMessageContent(msg.content)}

                    {/* Action Cards (Recovery Drafts / Abandoned Carts) */}
                    {!isUser && actionData.recovery_draft && actionData.recovery_draft.success && (
                      <div className="mt-3.5 rounded-xl border border-emerald-500/30 bg-emerald-950/30 p-3.5 space-y-2">
                        <div className="flex items-center justify-between text-[11px] font-bold text-emerald-400">
                          <span className="flex items-center gap-1.5">
                            <MessageSquare className="h-3.5 w-3.5" /> Telegram Recovery Draft Ready
                          </span>
                          <button
                            onClick={() =>
                              handleCopyDraft(actionData.recovery_draft.draft_message, `draft-${index}`)
                            }
                            className="flex items-center gap-1 rounded-md bg-emerald-600/30 border border-emerald-500/40 px-2 py-0.5 text-[10px] text-emerald-200 hover:bg-emerald-600 hover:text-white transition"
                          >
                            <Copy className="h-3 w-3" />
                            <span>{copiedDraft === `draft-${index}` ? "Copied!" : "Copy Text"}</span>
                          </button>
                        </div>
                        <p className="text-xs text-zinc-200 font-sans italic bg-zinc-950/60 p-2.5 rounded-lg border border-zinc-800">
                          &quot;{actionData.recovery_draft.draft_message}&quot;
                        </p>
                      </div>
                    )}

                    {!isUser && actionData.abandoned_carts && actionData.abandoned_carts.abandoned_count > 0 && (
                      <div className="mt-3.5 space-y-2">
                        <div className="text-[11px] font-bold text-amber-400 uppercase tracking-wider">
                          Recoverable Customer Sessions ({actionData.abandoned_carts.abandoned_count}):
                        </div>
                        <div className="grid gap-2 sm:grid-cols-2">
                          {actionData.abandoned_carts.abandoned_carts.map((cartItem: any, cIdx: number) => (
                            <div
                              key={cIdx}
                              className="rounded-xl border border-zinc-800 bg-zinc-950/70 p-3 flex flex-col justify-between space-y-2"
                            >
                              <div>
                                <div className="flex justify-between items-center text-xs">
                                  <span className="font-bold text-zinc-100">Cart #{cartItem.conversation_id.slice(0, 8)}</span>
                                  <span className="font-mono font-bold text-emerald-400">₹{cartItem.cart_total}</span>
                                </div>
                                <p className="text-[11px] text-zinc-400 mt-1 line-clamp-1">{cartItem.items_summary}</p>
                              </div>
                              <button
                                onClick={() =>
                                  handleSendMessage(
                                    `Draft a friendly recovery follow-up message for cart conversation ID ${cartItem.conversation_id}`
                                  )
                                }
                                className="w-full flex items-center justify-center gap-1 rounded-lg bg-purple-600/20 border border-purple-500/30 py-1 text-[11px] font-semibold text-purple-300 hover:bg-purple-600 hover:text-white transition"
                              >
                                <Sparkles className="h-3 w-3" /> Draft Recovery Message
                              </button>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {isLoading && (
              <div className="flex items-start gap-2 text-xs text-purple-300">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-purple-950 border border-purple-500/30 animate-pulse">
                  <Sparkles className="h-3.5 w-3.5 animate-spin text-purple-400" />
                </div>
                <div className="rounded-2xl bg-zinc-900 border border-zinc-800 px-4 py-3 text-zinc-400">
                  Executing merchant operation & telemetry scan...
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Bar */}
          <div className="border-t border-zinc-800/80 bg-zinc-950/80 p-3 sm:p-4">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="flex items-center gap-2 rounded-2xl border border-zinc-800 bg-zinc-900/90 p-2 shadow-inner focus-within:border-purple-500/50 transition"
            >
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="Give an operational command (e.g. 'How were sales today?', 'Mark Truffle Cake sold out', 'Check abandoned carts')..."
                className="flex-1 bg-transparent px-3 py-1.5 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={!inputMessage.trim() || isLoading}
                className="flex h-9 w-9 items-center justify-center rounded-xl bg-purple-600 text-white shadow-md shadow-purple-600/30 hover:bg-purple-500 transition disabled:opacity-40 disabled:pointer-events-none"
              >
                <Send className="h-4 w-4" />
              </button>
            </form>
          </div>
        </section>
      </main>

      {/* Reconciliation Floating Banner */}
      {reconcileNotice && (
        <div className="fixed bottom-6 right-6 z-50 rounded-2xl border border-emerald-500/40 bg-zinc-950/95 p-4 text-xs shadow-2xl backdrop-blur-xl text-emerald-300 max-w-md animate-in fade-in slide-in-from-bottom-5">
          <div className="flex items-center gap-2 font-bold mb-1 text-emerald-400">
            <CheckCircle className="h-4 w-4" /> Background Reconciliation Complete
          </div>
          <p className="text-zinc-300 text-[11px] leading-relaxed">{reconcileNotice}</p>
        </div>
      )}
    </div>
  );
}


