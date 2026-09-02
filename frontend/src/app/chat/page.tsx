"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  Store,
  ShoppingBag,
  Sparkles,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  ArrowLeft,
  ChevronDown,
  Zap,
  Globe2,
  Brain,
  Cake,
  Salad,
  Shirt,
  UtensilsCrossed,
  Coffee,
  Terminal,
  ArrowRightLeft,
  ShieldCheck,
  Cpu,
  Compass,
  RotateCcw,
} from "lucide-react";
import {
  fetchMerchants,
  sendChatMessage,
  sendChatMessageStreaming,
  updateCartDirectly,
  createOrder,
  fetchOrderStatus,
  Merchant,
  CartItem,
  ProductRecommendation,
  ReasoningEvent,
} from "@/lib/api";
import { ChatMessage, MessageProps } from "@/components/ChatMessage";
import { CartSidebar } from "@/components/CartSidebar";
import { ChatInput } from "@/components/ChatInput";
import { AgentReasoningPanel, ReasoningLog } from "@/components/AgentReasoningPanel";

// Real-Time ReAct Reasoning Stream Indicator with Professional Lucide Icons
function LiveReActStream({ events }: { events: ReasoningEvent[] }) {
  if (events.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8, scale: 0.96 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 4, scale: 0.96 }}
        transition={{ duration: 0.25, ease: "easeOut" }}
        className="flex items-center gap-2.5 py-1.5"
      >
        <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-tr from-[#1E1E2E] to-[#12121E] border border-[#7C3AED]/30 text-[#A78BFA] shadow-md">
          <Sparkles className="h-4 w-4 animate-spin text-[#7C3AED]" />
        </div>
        <div className="inline-flex items-center gap-2 rounded-2xl rounded-tl-none border border-[#2A2A3E] bg-[#12121E]/95 px-3.5 py-2.5 backdrop-blur-md shadow-lg shadow-black/20">
          <div className="flex gap-1 items-center">
            {[0, 1, 2].map((i) => (
              <motion.span
                key={i}
                className="h-2 w-2 rounded-full bg-gradient-to-tr from-[#7C3AED] to-[#0891B2]"
                animate={{ opacity: [0.35, 1, 0.35], y: [0, -3.5, 0] }}
                transition={{
                  duration: 0.85,
                  repeat: Infinity,
                  delay: i * 0.16,
                  ease: "easeInOut",
                }}
              />
            ))}
          </div>
          <span className="text-xs font-medium text-zinc-300">Agent reasoning & catalog scanning...</span>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 4 }}
      className="my-3 space-y-2.5 rounded-2xl border border-[#7C3AED]/35 bg-[#12121E]/95 p-3.5 shadow-2xl backdrop-blur-xl max-w-2xl"
    >
      <div className="flex items-center justify-between border-b border-[#2A2A3E] pb-2">
        <div className="flex items-center gap-2">
          <div className="flex h-5 w-5 items-center justify-center rounded-lg bg-[#7C3AED]/20 text-[#A78BFA]">
            <Brain className="h-3 w-3 animate-pulse text-[#7C3AED]" />
          </div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-[#A78BFA]">
            Live ReAct Reasoning Stream
          </span>
        </div>
        <span className="inline-flex items-center gap-1.5 text-[10px] font-semibold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded-full border border-emerald-500/30">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-ping" />
          Autonomous Multi-Agent Loop
        </span>
      </div>

      <div className="space-y-1.5 text-xs font-mono max-h-48 overflow-y-auto pr-1">
        {events.map((ev, idx) => {
          const isLatest = idx === events.length - 1;
          let Icon = Brain;
          let badgeColor = "text-indigo-300 bg-indigo-950/70 border-indigo-500/35";
          let label = "Thought";

          if (ev.type === "budget_check") {
            Icon = ShieldCheck;
            badgeColor = "text-amber-300 bg-amber-950/70 border-amber-500/35";
            label = "Budget Guardrail";
          } else if (ev.type === "tool_call") {
            Icon = Terminal;
            badgeColor = "text-cyan-300 bg-cyan-950/70 border-cyan-500/35";
            label = `Action: ${ev.tool_display || ev.tool}`;
          } else if (ev.type === "tool_result") {
            Icon = CheckCircle2;
            badgeColor = "text-emerald-300 bg-emerald-950/70 border-emerald-500/35";
            label = "Observation";
          } else if (ev.type === "handoff" || ev.type === "handoff_context_applied") {
            Icon = ArrowRightLeft;
            badgeColor = "text-purple-300 bg-purple-950/70 border-purple-500/35";
            label = "Agent Handoff";
          }

          return (
            <motion.div
              key={idx}
              initial={{ opacity: 0, x: -6 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.2 }}
              className={`flex items-start gap-2.5 rounded-xl border p-2 ${badgeColor} ${
                isLatest ? "ring-1 ring-[#7C3AED]/50 shadow-md" : "opacity-85"
              }`}
            >
              <div className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-md bg-black/40">
                <Icon className="h-3 w-3" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[10px] uppercase font-bold tracking-wider opacity-90">{label}</span>
                  {ev.agent && (
                    <span className="text-[9px] font-sans px-1.5 py-0.2 rounded bg-black/50 text-zinc-300 border border-white/5">
                      {ev.agent}
                    </span>
                  )}
                </div>
                <div className="text-[11px] font-sans text-zinc-200 mt-0.5 break-words">
                  {ev.summary || ev.content}
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </motion.div>
  );
}

const DISCOVERY_SUGGESTIONS = [
  "🎂 Birthday cake under ₹700",
  "🥬 Weekly grocery basket under ₹1000",
  "👗 Linen shirt or festive gift under ₹2000",
  "🏪 Available stores in city",
  "🥐 Fresh croissants & coffee under ₹400",
];

const DISCOVERY_PLACEHOLDER =
  "Ask for any item or budget across all stores (e.g. 'Chocolate cake under ₹700')...";

const MERCHANT_SUGGESTIONS: Record<string, string[]> = {
  bakery: [
    "🎂 Chocolate cake under ₹800",
    "🥐 Fresh pastries & almond croissants",
    "🍓 Fruit gateau & tiramisu",
    "🎉 Birthday cake combo",
    "☕ Cold coffee & sourdough",
  ],
  grocery: [
    "🥬 Weekly grocery basket under ₹1000",
    "🍎 Himachal apples & avocado",
    "🥛 Organic milk & eggs",
    "🥑 Salad greens & mushrooms",
    "🥥 Cold-pressed oil & granola",
  ],
  boutique: [
    "👕 Pure linen shirt under ₹1500",
    "👗 Silk anarkali for wedding",
    "🎁 Festive gift hamper",
    "⌚ Minimalist watch",
    "👖 Cotton kurta in olive",
  ],
};

const MERCHANT_PLACEHOLDERS: Record<string, string> = {
  bakery: "Ask for cakes, pastries, sourdough, or budget (e.g. under ₹800)...",
  grocery: "Ask for fresh produce, dairy, snacks, or groceries...",
  boutique: "Ask for shirts, dresses, ethnic wear, or gifts...",
};

function getMerchantType(name: string): "bakery" | "grocery" | "boutique" {
  const lower = name.toLowerCase();
  if (lower.includes("fresh") || lower.includes("grocery") || lower.includes("market")) return "grocery";
  if (lower.includes("style") || lower.includes("boutique") || lower.includes("fashion") || lower.includes("wear")) return "boutique";
  return "bakery";
}

export default function ChatPage() {
  const [merchants, setMerchants] = useState<Merchant[]>([]);
  const [selectedMerchant, setSelectedMerchant] = useState<Merchant | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<MessageProps[]>([]);
  const [cart, setCart] = useState<{ items: CartItem[]; total: number }>({
    items: [],
    total: 0,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isCheckingOut, setIsCheckingOut] = useState(false);
  const [activeOrderId, setActiveOrderId] = useState<string | null>(null);
  const [activePaymentLink, setActivePaymentLink] = useState<string | null>(null);
  const [orderPaid, setOrderPaid] = useState(false);
  const [showMobileCart, setShowMobileCart] = useState(false);
  const [showMerchantPicker, setShowMerchantPicker] = useState(false);
  const [storeSearchQuery, setStoreSearchQuery] = useState("");
  const [showReasoningPanel, setShowReasoningPanel] = useState(false);
  const [reasoningLogs, setReasoningLogs] = useState<ReasoningLog[]>([]);
  const [liveStreamingEvents, setLiveStreamingEvents] = useState<ReasoningEvent[]>([]);
  const [notification, setNotification] = useState<{ msg: string; type?: "success" | "error" } | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading, activePaymentLink, liveStreamingEvents]);

  // Load merchants on initial render
  useEffect(() => {
    async function loadData() {
      try {
        const data = await fetchMerchants();
        setMerchants(data);
      } catch (err) {
        console.error("Failed to load merchants:", err);
      }
    }
    loadData();
  }, []);

  // Initial welcome message on mount (Discovery Mode)
  useEffect(() => {
    setMessages([
      {
        role: "assistant",
        content: `Welcome to **MerchantMind**!\n\nTell me what you're looking for and your budget (e.g. *"Birthday cake under ₹700"* or *"Weekly groceries"*). I'll scan live catalogs across all stores and guide you to seamless checkout with Razorpay.`,
        timestamp: new Date().toISOString(),
      },
    ]);
  }, []);

  const handleManualStoreSelect = (m: Merchant | null) => {
    setSelectedMerchant(m);
    setShowMerchantPicker(false);
    setConversationId(null);
    setCart({ items: [], total: 0 });
    setActivePaymentLink(null);
    setActiveOrderId(null);
    setOrderPaid(false);

    if (m) {
      setMessages([
        {
          role: "assistant",
          content: `Welcome to **${m.name}**!\n\nTell me what you'd like to order or your budget constraint, and I'll find the best options in stock.`,
          timestamp: new Date().toISOString(),
        },
      ]);
      showToast(`Switched to ${m.name}`);
    } else {
      setMessages([
        {
          role: "assistant",
          content: `Welcome to **MerchantMind**!\n\nTell me what you're looking for and your budget (e.g. *"Birthday cake under ₹700"* or *"Weekly groceries"*). I'll scan live catalogs across all stores and guide you to seamless checkout with Razorpay.`,
          timestamp: new Date().toISOString(),
        },
      ]);
      showToast("All Stores Mode");
    }
  };

  // Poll order status if active order is pending
  useEffect(() => {
    if (!activeOrderId || orderPaid) return;

    const interval = setInterval(async () => {
      try {
        const statusRes = await fetchOrderStatus(activeOrderId);
        if (statusRes && statusRes.status === "paid") {
          setOrderPaid(true);
          setActivePaymentLink(null);
          showToast("Payment confirmed!", "success");
          setMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              content: `🎉 **Payment Confirmed!** (₹${statusRes.total.toFixed(0)})\n\nPayment captured via Razorpay (\`${statusRes.rzp_payment_id || "captured"}\`). **${selectedMerchant?.name || "The merchant"}** has confirmed your order.\n\n🛵 **[Track Order Live 🚀](/orders/${activeOrderId}/tracking)**`,
              timestamp: new Date().toISOString(),
            },
          ]);
          setCart({ items: [], total: 0 });
          clearInterval(interval);
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [activeOrderId, orderPaid, selectedMerchant]);

  const showToast = (msg: string, type: "success" | "error" = "success") => {
    setNotification({ msg, type });
    setTimeout(() => setNotification(null), 3500);
  };

  // Handle sending chat message with real-time ReAct SSE streaming
  const handleSendMessage = async (text: string) => {
    if (isLoading) return;

    const userMsg: MessageProps = {
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);
    setLiveStreamingEvents([]);

    try {
      const response = await sendChatMessageStreaming(
        {
          merchant_id: selectedMerchant ? selectedMerchant.id : null,
          conversation_id: conversationId,
          message: text,
        },
        (event: ReasoningEvent) => {
          setLiveStreamingEvents((prev) => [...prev, event]);
        }
      );

      if (!response) {
        throw new Error("No response received from streaming chat agent");
      }

      if (response.conversation_id) {
        setConversationId(response.conversation_id);
      }

      // Auto-lock merchant if agent selected/resolved one
      if (response.merchant_id) {
        const matched = merchants.find((m) => m.id === response.merchant_id);
        if (matched && (!selectedMerchant || selectedMerchant.id !== matched.id)) {
          setSelectedMerchant(matched);
          showToast(`Store: ${matched.name}`, "success");
        }
      }

      if (response.payment_link) {
        setActivePaymentLink(response.payment_link);
      }

      const assistantMsg: MessageProps = {
        role: "assistant",
        content: response.message,
        timestamp: new Date().toISOString(),
        recommendations: response.recommendations || [],
        action: response.action || "chat",
        payment_link: response.payment_link,
      };
      setMessages((prev) => [...prev, assistantMsg]);

      if (response.cart) {
        setCart({
          items: response.cart,
          total: response.cart_total || 0,
        });
      }

      if (response.agent_reasoning && response.agent_reasoning.length > 0) {
        setReasoningLogs(response.agent_reasoning);
      }
    } catch (err: any) {
      console.error("Chat error:", err);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "⚠️ Connection issue. Please try again.",
          timestamp: new Date().toISOString(),
        },
      ]);
      showToast("Failed to reach AI agent", "error");
    } finally {
      setIsLoading(false);
      setLiveStreamingEvents([]);
    }
  };

  // Handle Add to Cart from product cards
  const handleAddToCart = async (product: ProductRecommendation) => {
    await handleSendMessage(`Add 1 ${product.name} to my cart`);
    showToast(`Added ${product.name}`);
  };

  // Handle Direct Checkout Initiation from Sidebar
  const handleCheckout = async (fulfillment?: {
    mode: "delivery" | "pickup";
    address?: string;
    pickupTime?: string;
  }) => {
    if (!cart || !cart.items || cart.items.length === 0) {
      showToast("Your cart is empty. Please add items to your cart first.", "error");
      return;
    }

    // If no specific merchant selected in Discovery Mode, resolve from first item or default merchant
    let merchantToUse = selectedMerchant;
    if (!merchantToUse && merchants.length > 0) {
      merchantToUse = merchants[0];
      setSelectedMerchant(merchantToUse);
    }

    if (!merchantToUse) {
      showToast("Please select a merchant store to proceed with checkout.", "error");
      return;
    }

    setIsCheckingOut(true);
    try {
      const mode = fulfillment?.mode || "delivery";
      const address = fulfillment?.address;
      const pickupTime = fulfillment?.pickupTime;

      const order = await createOrder({
        conversation_id: conversationId || "00000000-0000-0000-0000-000000000000",
        merchant_id: merchantToUse.id,
        fulfillment_mode: mode,
        delivery_address: address,
        pickup_time: pickupTime,
        items: cart.items,
      });

      setActiveOrderId(order.id);
      if (order.payment_link) {
        setActivePaymentLink(order.payment_link);
      }

      const fulfillmentSummary =
        mode === "delivery"
          ? `🚚 Delivery${address ? ` to *${address}*` : ""}`
          : `🏪 Pickup${pickupTime ? ` (*${pickupTime}*)` : ""}`;

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `💳 Order created for **₹${order.total.toFixed(0)}** (${fulfillmentSummary}). Click below to pay with Razorpay:`,
          timestamp: new Date().toISOString(),
          payment_link: order.payment_link,
          action: "checkout",
        },
      ]);
      showToast("Razorpay link created", "success");
    } catch (err: any) {
      console.error("Checkout error:", err);
      const errMsg = err.message || "Checkout blocked by guardrail.";
      showToast(errMsg, "error");
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `🛡️ **Budget Guardrail Alert**:\n\n${errMsg}`,
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsCheckingOut(false);
    }
  };

  const handleUpdateQuantity = async (productId: string, delta: number) => {
    if (!conversationId) return;
    const currentItems = [...cart.items];
    const itemIndex = currentItems.findIndex((i) => i.product_id === productId);
    if (itemIndex === -1) return;

    const newQty = currentItems[itemIndex].quantity + delta;
    if (newQty <= 0) {
      currentItems.splice(itemIndex, 1);
    } else {
      currentItems[itemIndex].quantity = newQty;
    }

    try {
      const updated = await updateCartDirectly(conversationId, currentItems);
      setCart(updated);
    } catch (err) {
      console.error("Cart update error:", err);
    }
  };

  const handleRemoveItem = async (productId: string) => {
    if (!conversationId) return;
    const filtered = cart.items.filter((i) => i.product_id !== productId);
    try {
      const updated = await updateCartDirectly(conversationId, filtered);
      setCart(updated);
      showToast("Item removed");
    } catch (err) {
      console.error("Remove item error:", err);
    }
  };

  const handleClearCart = async () => {
    if (!conversationId) return;
    try {
      const updated = await updateCartDirectly(conversationId, []);
      setCart(updated);
      showToast("Cart cleared");
    } catch (err) {
      console.error("Clear cart error:", err);
    }
  };

  const handleNewSession = () => {
    setConversationId(null);
    setCart({ items: [], total: 0 });
    setActiveOrderId(null);
    setActivePaymentLink(null);
    setOrderPaid(false);
    if (selectedMerchant) {
      setMessages([
        {
          role: "assistant",
          content: `New session for **${selectedMerchant.name}**. What can I get for you?`,
          timestamp: new Date().toISOString(),
        },
      ]);
    } else {
      setMessages([
        {
          role: "assistant",
          content: `New session started. Ask for any item or budget constraint across all stores.`,
          timestamp: new Date().toISOString(),
        },
      ]);
    }
    showToast("New chat started");
  };

  const activeType = selectedMerchant ? getMerchantType(selectedMerchant.name) : null;
  const activeSuggestions = selectedMerchant && activeType
    ? MERCHANT_SUGGESTIONS[activeType] || MERCHANT_SUGGESTIONS.bakery
    : DISCOVERY_SUGGESTIONS;
  const activePlaceholder = selectedMerchant && activeType
    ? MERCHANT_PLACEHOLDERS[activeType] || MERCHANT_PLACEHOLDERS.bakery
    : DISCOVERY_PLACEHOLDER;

  return (
    <div className="flex min-h-screen flex-col bg-[#0A0A12] text-[#F0EEFF] font-sans selection:bg-[#7C3AED] selection:text-white">
      {/* Dynamic ambient floating gradient orbs */}
      <motion.div
        animate={{
          scale: [1, 1.1, 1],
          opacity: [0.15, 0.22, 0.15],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: "easeInOut",
        }}
        className="fixed top-0 left-1/2 -translate-x-1/2 h-[350px] w-[700px] bg-gradient-to-tr from-[#7C3AED]/20 via-[#0891B2]/15 to-[#A78BFA]/10 blur-[140px] pointer-events-none rounded-full"
      />

      {/* Toast Notification */}
      <AnimatePresence>
        {notification && (
          <motion.div
            initial={{ opacity: 0, y: -12, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -12, scale: 0.95 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            className={`fixed top-4 right-4 z-50 flex items-center gap-2 rounded-2xl px-4 py-2.5 text-xs font-semibold shadow-2xl backdrop-blur-xl border ${
              notification.type === "error"
                ? "bg-rose-950/90 text-rose-200 border-rose-500/40"
                : "bg-[#12121E]/95 text-white border-[#2A2A3E]"
            }`}
          >
            {notification.type === "error" ? (
              <AlertCircle className="h-4 w-4 text-rose-400" />
            ) : (
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            )}
            <span>{notification.msg}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Top Header */}
      <header className="sticky top-0 z-30 border-b border-[#2A2A3E]/80 bg-[#0A0A12]/85 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-2.5 sm:px-6">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="flex h-8.5 w-8.5 items-center justify-center rounded-xl bg-[#12121E] border border-[#2A2A3E] text-zinc-400 hover:text-white hover:border-[#7C3AED]/40 transition"
              title="Home"
            >
              <ArrowLeft className="h-4 w-4" />
            </Link>

            <div className="flex h-8.5 w-8.5 items-center justify-center rounded-xl bg-gradient-to-tr from-[#7C3AED] to-[#A78BFA] text-white shadow-md shadow-[#7C3AED]/20">
              <Sparkles className="h-4 w-4" />
            </div>

            <div className="flex items-center gap-2">
              <h1 className="text-sm font-bold tracking-tight text-[#F0EEFF]">
                MerchantMind
              </h1>
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-950/60 border border-emerald-500/30 px-2 py-0.5 text-[10px] font-semibold text-emerald-400">
                <Zap className="h-2.5 w-2.5" />
                Live Agent
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Multi-Tenant Merchant Selector Dropdown */}
            <div className="relative">
              <button
                onClick={() => setShowMerchantPicker(!showMerchantPicker)}
                className={`flex items-center gap-2 rounded-xl border px-3 py-1.5 text-xs font-medium transition shadow-sm ${
                  selectedMerchant
                    ? "border-[#2A2A3E] bg-[#12121E] text-zinc-200 hover:border-[#7C3AED]/40"
                    : "border-[#7C3AED]/40 bg-[#7C3AED]/10 text-[#A78BFA] hover:border-[#7C3AED]/60"
                }`}
              >
                {selectedMerchant ? (
                  <>
                    <Store className="h-3.5 w-3.5 text-[#A78BFA]" />
                    <span className="max-w-[130px] sm:max-w-none truncate">{selectedMerchant.name}</span>
                  </>
                ) : (
                  <>
                    <Globe2 className="h-3.5 w-3.5 text-[#0891B2]" />
                    <span>All Stores</span>
                  </>
                )}
                <ChevronDown className="h-3 w-3 text-zinc-400" />
              </button>

              <AnimatePresence>
                {showMerchantPicker && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95, y: -4 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: -4 }}
                    transition={{ duration: 0.15 }}
                    className="absolute right-0 mt-2 w-80 max-h-[80vh] sm:max-h-[490px] flex flex-col rounded-2xl border border-[#2A2A3E] bg-[#12121E]/98 shadow-2xl backdrop-blur-2xl z-50 overflow-hidden"
                  >
                    <div className="p-2.5 border-b border-[#2A2A3E] bg-[#0E0E18]">
                      <div className="flex items-center justify-between mb-2 px-1">
                        <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider">
                          Select Store ({merchants.length} Stores)
                        </span>
                        <span className="text-[9px] font-medium text-[#A78BFA] bg-[#7C3AED]/20 px-1.5 py-0.5 rounded">
                          Bangalore
                        </span>
                      </div>

                      {/* Discovery Mode Option */}
                      <button
                        onClick={() => handleManualStoreSelect(null)}
                        className={`flex w-full items-center gap-2.5 rounded-xl px-2.5 py-2 text-left text-xs transition mb-2 ${
                          selectedMerchant === null
                            ? "bg-[#7C3AED]/20 text-[#A78BFA] border border-[#7C3AED]/40 shadow-sm"
                            : "text-zinc-300 hover:bg-[#1E1E2E] border border-transparent"
                        }`}
                      >
                        <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-cyan-500/15 border border-cyan-500/30 text-[#0891B2]">
                          <Globe2 className="h-3.5 w-3.5" />
                        </div>
                        <div className="flex-1 min-w-0 font-medium">All Stores (Discovery Mode)</div>
                        {selectedMerchant === null && (
                          <CheckCircle2 className="h-3.5 w-3.5 text-[#7C3AED] shrink-0" />
                        )}
                      </button>

                      {/* Instant Search Bar */}
                      <input
                        type="text"
                        placeholder="Search store name or area..."
                        value={storeSearchQuery}
                        onChange={(e) => setStoreSearchQuery(e.target.value)}
                        className="w-full rounded-xl border border-[#2A2A3E] bg-[#12121E] px-2.5 py-1.5 text-xs text-zinc-200 placeholder-zinc-500 focus:border-[#7C3AED] focus:outline-none"
                      />
                    </div>

                    {/* Scrollable list of Bangalore stores */}
                    <div className="flex-1 overflow-y-auto p-1.5 space-y-0.5 max-h-[320px] divide-y divide-zinc-800/30">
                      {merchants
                        .filter((m) => {
                          if (!storeSearchQuery.trim()) return true;
                          const q = storeSearchQuery.toLowerCase();
                          return (
                            m.name.toLowerCase().includes(q) ||
                            (m.store_address && m.store_address.toLowerCase().includes(q))
                          );
                        })
                        .map((m) => {
                          const type = getMerchantType(m.name);
                          let Icon = Cake;
                          let iconBadge = "bg-purple-500/15 border-purple-500/30 text-purple-400";
                          let tag = "Bakery";
                          
                          if (type === "grocery") {
                            Icon = Salad;
                            iconBadge = "bg-emerald-500/15 border-emerald-500/30 text-emerald-400";
                            tag = "Groceries";
                          } else if (type === "boutique") {
                            Icon = Shirt;
                            iconBadge = "bg-pink-500/15 border-pink-500/30 text-pink-400";
                            tag = "Fashion";
                          } else if (
                            m.name.toLowerCase().includes("biryani") ||
                            m.name.toLowerCase().includes("foods") ||
                            m.name.toLowerCase().includes("bhavan") ||
                            m.name.toLowerCase().includes("restaurant")
                          ) {
                            Icon = UtensilsCrossed;
                            iconBadge = "bg-amber-500/15 border-amber-500/30 text-amber-400";
                            tag = "Restaurant";
                          } else if (m.name.toLowerCase().includes("coffee") || m.name.toLowerCase().includes("tea") || m.name.toLowerCase().includes("bar")) {
                            Icon = Coffee;
                            iconBadge = "bg-amber-500/15 border-amber-500/30 text-amber-300";
                            tag = "Beverages";
                          }

                          return (
                            <button
                              key={m.id}
                              onClick={() => {
                                handleManualStoreSelect(m);
                                setStoreSearchQuery("");
                              }}
                              className={`flex w-full items-center gap-2.5 rounded-xl px-2.5 py-1.5 text-left text-xs transition ${
                                selectedMerchant?.id === m.id
                                  ? "bg-[#7C3AED]/20 text-[#A78BFA] border border-[#7C3AED]/30"
                                  : "text-zinc-300 hover:bg-[#1E1E2E] border border-transparent"
                              }`}
                            >
                              <div className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-lg border ${iconBadge}`}>
                                <Icon className="h-3.5 w-3.5" />
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="font-medium truncate text-zinc-200">{m.name}</div>
                                <div className="text-[10px] text-zinc-500 truncate">
                                  {tag} • {m.store_address ? m.store_address.split(",")[0] : "Bangalore"}
                                </div>
                              </div>
                              {selectedMerchant?.id === m.id && (
                                <CheckCircle2 className="h-3.5 w-3.5 text-[#7C3AED] shrink-0" />
                              )}
                            </button>
                          );
                        })}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Agent Decisions Reasoning Panel Toggle */}
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => setShowReasoningPanel(true)}
              className="flex items-center gap-1.5 rounded-xl bg-[#7C3AED]/10 border border-[#7C3AED]/30 px-2.5 py-1.5 text-xs font-medium text-[#A78BFA] hover:bg-[#7C3AED]/20 hover:text-white transition shadow-sm"
              title="Agent Decision Log"
            >
              <Brain className="h-3.5 w-3.5 text-[#7C3AED]" />
              <span className="hidden md:inline">Decisions</span>
              {reasoningLogs.length > 0 && (
                <span className="flex h-4 w-4 items-center justify-center rounded-full bg-[#7C3AED] text-[10px] font-bold text-white">
                  {reasoningLogs.length}
                </span>
              )}
            </motion.button>

            {/* Merchant Console Link */}
            <Link
              href="/merchant"
              className="hidden sm:flex items-center gap-1.5 rounded-xl bg-[#12121E] border border-[#2A2A3E] px-2.5 py-1.5 text-xs font-medium text-zinc-300 hover:border-[#7C3AED]/40 hover:text-white transition shadow-sm"
              title="Merchant Portal"
            >
              <Store className="h-3.5 w-3.5 text-zinc-400" />
              <span>Merchant</span>
            </Link>

            <motion.button
              whileHover={{ scale: 1.05, rotate: 180 }}
              whileTap={{ scale: 0.95 }}
              transition={{ duration: 0.3 }}
              onClick={handleNewSession}
              title="New Chat"
              className="flex h-8.5 w-8.5 items-center justify-center rounded-xl border border-[#2A2A3E] bg-[#12121E] text-zinc-400 transition hover:border-[#7C3AED]/40 hover:text-white"
            >
              <RefreshCw className="h-3.5 w-3.5" />
            </motion.button>

            {/* Mobile Cart Button */}
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={() => setShowMobileCart(!showMobileCart)}
              className="relative flex items-center gap-1.5 rounded-xl bg-[#7C3AED] px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-[#6D28D9] lg:hidden"
            >
              <ShoppingBag className="h-3.5 w-3.5" />
              <span>₹{cart.total.toFixed(0)}</span>
              {cart.items.length > 0 && (
                <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-rose-500 text-[10px] font-bold text-white">
                  {cart.items.reduce((a, b) => a + b.quantity, 0)}
                </span>
              )}
            </motion.button>
          </div>
        </div>
      </header>

      {/* Main Content Layout */}
      <main className="mx-auto flex w-full max-w-7xl flex-1 gap-5 p-4 sm:p-5">
        {/* Left Column: Chat Conversation Stream */}
        <section className="flex flex-1 flex-col justify-between overflow-hidden rounded-3xl border border-[#2A2A3E] bg-[#12121E]/70 shadow-xl backdrop-blur-xl">
          {/* Chat Messages Feed */}
          <div className="flex-1 space-y-1 overflow-y-auto p-4 sm:p-5">
            {messages.map((msg, i) => (
              <ChatMessage
                key={i}
                role={msg.role}
                content={msg.content}
                timestamp={msg.timestamp}
                recommendations={msg.recommendations}
                action={msg.action}
                payment_link={msg.payment_link}
                onAddToCart={handleAddToCart}
              />
            ))}

            {/* Real-Time Live ReAct Reasoning Stream & Animation */}
            <AnimatePresence>
              {isLoading && <LiveReActStream events={liveStreamingEvents} />}
            </AnimatePresence>
            <div ref={messagesEndRef} />
          </div>

          {/* Chat Input Bar */}
          <div className="border-t border-[#2A2A3E] bg-[#0A0A12]/70 p-3.5">
            <ChatInput
              onSendMessage={handleSendMessage}
              isLoading={isLoading}
              suggestions={activeSuggestions}
              placeholder={activePlaceholder}
              onSuggestionClick={(s) => handleSendMessage(s.replace(/^[^\s]+ /, ""))}
            />
          </div>
        </section>

        {/* Right Column: Sticky Cart Sidebar (Desktop) */}
        <aside className="hidden w-80 shrink-0 lg:block xl:w-92">
          <div className="sticky top-18 h-[calc(100vh-95px)]">
            <CartSidebar
              cart={cart}
              merchantName={selectedMerchant ? selectedMerchant.name : "All Stores"}
              onUpdateQuantity={handleUpdateQuantity}
              onRemoveItem={handleRemoveItem}
              onClearCart={handleClearCart}
              onCheckout={handleCheckout}
              isLoading={isLoading}
              isCheckingOut={isCheckingOut}
              activeOrderId={activeOrderId}
              activePaymentLink={activePaymentLink}
              orderPaid={orderPaid}
            />
          </div>
        </aside>
      </main>

      {/* Mobile Cart Drawer */}
      <AnimatePresence>
        {showMobileCart && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-end bg-black/70 backdrop-blur-sm lg:hidden"
          >
            <motion.div
              initial={{ y: "100%" }}
              animate={{ y: 0 }}
              exit={{ y: "100%" }}
              transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
              className="h-[85vh] w-full rounded-t-3xl bg-[#12121E] border-t border-[#2A2A3E] p-4 shadow-2xl overflow-y-auto"
            >
              <div className="mb-3 flex justify-between items-center pb-2 border-b border-[#2A2A3E]">
                <span className="text-sm font-bold text-[#F0EEFF]">Cart</span>
                <button
                  onClick={() => setShowMobileCart(false)}
                  className="text-xs font-medium text-zinc-400 hover:text-white"
                >
                  Close ✕
                </button>
              </div>
              <CartSidebar
                cart={cart}
                merchantName={selectedMerchant ? selectedMerchant.name : "All Stores"}
                onUpdateQuantity={handleUpdateQuantity}
                onRemoveItem={handleRemoveItem}
                onClearCart={handleClearCart}
                onCheckout={handleCheckout}
                isLoading={isLoading}
                isCheckingOut={isCheckingOut}
                activeOrderId={activeOrderId}
                activePaymentLink={activePaymentLink}
                orderPaid={orderPaid}
              />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Real-Time Agent Reasoning & Decision Drawer */}
      <AgentReasoningPanel
        logs={reasoningLogs}
        isOpen={showReasoningPanel}
        onClose={() => setShowReasoningPanel(false)}
      />
    </div>
  );
}
