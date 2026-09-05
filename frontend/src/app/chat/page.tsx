"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Store,
  ShoppingBag,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  ArrowLeft,
  ChevronDown,
  Globe2,
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
  Volume2,
  Mic,
  MicOff,
  Layers,
  SlidersHorizontal,
  UserCheck,
  Search,
} from "lucide-react";
import {
  fetchMerchants,
  sendChatMessage,
  sendChatMessageStreaming,
  updateCartDirectly,
  createOrder,
  createMultiOrder,
  fetchOrderStatus,
  fetchLatestConversationOrder,
  verifyOrderPayment,
  fetchDemoCustomer,
  Merchant,
  CartItem,
  ProductRecommendation,
  ReasoningEvent,
  CustomerProfile,
  resolvePaymentUrl,
} from "@/lib/api";
import { ChatMessage, MessageProps } from "@/components/ChatMessage";
import { CartSidebar } from "@/components/CartSidebar";
import { ChatInput } from "@/components/ChatInput";
import { AgentReasoningPanel, ReasoningLog } from "@/components/AgentReasoningPanel";
import { VoiceOrb } from "@/components/VoiceOrb";
import { voiceManager, VoiceState } from "@/lib/voice-manager";

// Real-Time Live Catalog & Sourcing Pipeline (21st.dev Style, Clean Concierge)
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
        <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-white/[0.04] border border-white/[0.08] text-zinc-300 shadow-md">
          <Layers className="h-4 w-4 text-indigo-400" />
        </div>
        <div className="inline-flex items-center gap-2.5 rounded-2xl rounded-tl-none border border-white/[0.08] bg-[#0E1019]/95 px-3.5 py-2.5 backdrop-blur-md shadow-lg shadow-black/40">
          <div className="flex gap-1 items-center">
            {[0, 1, 2].map((i) => (
              <motion.span
                key={i}
                className="h-1.5 w-1.5 rounded-full bg-gradient-to-tr from-indigo-400 to-cyan-400"
                animate={{ opacity: [0.35, 1, 0.35], y: [0, -3, 0] }}
                transition={{
                  duration: 0.8,
                  repeat: Infinity,
                  delay: i * 0.15,
                  ease: "easeInOut",
                }}
              />
            ))}
          </div>
          <span className="text-xs font-medium text-zinc-300">Searching store catalog & verifying stock...</span>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 4 }}
      className="my-3 space-y-2.5 rounded-2xl border border-white/[0.08] bg-[#0E1019]/95 p-3.5 shadow-2xl backdrop-blur-xl max-w-2xl"
    >
      <div className="flex items-center justify-between border-b border-white/[0.08] pb-2">
        <div className="flex items-center gap-2">
          <div className="flex h-5 w-5 items-center justify-center rounded-lg bg-white/[0.05] text-indigo-400">
            <Layers className="h-3 w-3" />
          </div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-zinc-300">
            Live Catalog & Sourcing Stream
          </span>
        </div>
        <span className="inline-flex items-center gap-1.5 text-[10px] font-semibold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded-full border border-emerald-500/30">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-ping" />
          Autonomous Pipeline
        </span>
      </div>

      <div className="space-y-1.5 text-xs font-mono max-h-48 overflow-y-auto pr-1">
        {events.map((ev, idx) => {
          const isLatest = idx === events.length - 1;
          let Icon = Layers;
          let badgeColor = "text-indigo-300 bg-indigo-950/70 border-indigo-500/35";
          let label = "Analysis";

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
            label = "Specialist Dispatch";
          }

          return (
            <motion.div
              key={idx}
              initial={{ opacity: 0, x: -6 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.2 }}
              className={`flex items-start gap-2.5 rounded-xl border p-2 ${badgeColor} ${
                isLatest ? "ring-1 ring-indigo-500/50 shadow-md" : "opacity-85"
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
  "🎙️ Hey MerchantMind",
  "🎂 Birthday cake under ₹700",
  "🥞 2 dosas, 1 pizza, and burger",
  "🥬 Weekly grocery basket under ₹1000",
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
  const router = useRouter();
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
  
  // Ambient Voice & Customer Memory States
  const [customerProfile, setCustomerProfile] = useState<CustomerProfile | null>(null);
  const [showMemoryModal, setShowMemoryModal] = useState(false);
  const [isVoiceMode, setIsVoiceMode] = useState(false);
  const [voiceState, setVoiceState] = useState<VoiceState>("idle");
  const [liveTranscript, setLiveTranscript] = useState("");
  const lastMessageRef = useRef<{ text: string; time: number }>({ text: "", time: 0 });

  const cartRef = useRef(cart);
  useEffect(() => {
    cartRef.current = cart;
  }, [cart]);

  const conversationIdRef = useRef(conversationId);
  useEffect(() => {
    conversationIdRef.current = conversationId;
  }, [conversationId]);

  const selectedMerchantRef = useRef(selectedMerchant);
  useEffect(() => {
    selectedMerchantRef.current = selectedMerchant;
  }, [selectedMerchant]);

  const customerProfileRef = useRef(customerProfile);
  useEffect(() => {
    customerProfileRef.current = customerProfile;
  }, [customerProfile]);

  const activeOrderIdRef = useRef(activeOrderId);
  useEffect(() => {
    activeOrderIdRef.current = activeOrderId;
  }, [activeOrderId]);

  const activePaymentLinkRef = useRef(activePaymentLink);
  useEffect(() => {
    activePaymentLinkRef.current = activePaymentLink;
  }, [activePaymentLink]);

  const isVoiceModeRef = useRef(isVoiceMode);
  useEffect(() => {
    isVoiceModeRef.current = isVoiceMode;
  }, [isVoiceMode]);

  const messagesRef = useRef(messages);
  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  // Persistent & robust order ID resolver across state, localStorage, and message history
  const resolveCurrentOrderId = (): string | null => {
    if (activeOrderIdRef.current) return activeOrderIdRef.current;
    if (activeOrderId) return activeOrderId;

    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("merchantmind_active_order_id");
      if (stored) return stored;
    }

    const currentMsgs = messagesRef.current.length > 0 ? messagesRef.current : messages;
    for (let i = currentMsgs.length - 1; i >= 0; i--) {
      const content = currentMsgs[i]?.content || "";
      const match = content.match(/\/orders\/([0-9a-fA-F-]{36})\/tracking/) || content.match(/([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})/);
      if (match) {
        return match[1];
      }
    }

    const link = activePaymentLinkRef.current || activePaymentLink;
    if (link) {
      const match = link.match(/([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})/);
      if (match) return match[1];
    }

    return null;
  };

  // Restore persisted active order from localStorage on mount
  useEffect(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("merchantmind_active_order_id");
      if (saved && !activeOrderId) {
        setActiveOrderId(saved);
        activeOrderIdRef.current = saved;
      }
    }
  }, []);

  const handleSendMessageRef = useRef<(text: string) => Promise<void>>(async () => {});

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading, activePaymentLink, liveStreamingEvents]);

  // Load merchants & Demo Customer Memory on initial render
  useEffect(() => {
    async function loadData() {
      try {
        const [mList, demoCust] = await Promise.all([
          fetchMerchants(),
          fetchDemoCustomer(),
        ]);
        setMerchants(mList);
        if (demoCust) {
          setCustomerProfile(demoCust);
        }
      } catch (err) {
        console.error("Failed to load initial data:", err);
      }
    }
    loadData();

    // Auto-enable hands-free wake word if microphone permission already granted
    if (typeof window !== "undefined" && navigator.permissions && navigator.permissions.query) {
      navigator.permissions
        .query({ name: "microphone" as PermissionName })
        .then((permissionStatus) => {
          if (permissionStatus.state === "granted") {
            voiceManager.toggleVoiceMode(true);
            setIsVoiceMode(true);
          }
        })
        .catch(() => {});
    }
  }, []);
  const showToast = (msg: string, type: "success" | "error" = "success") => {
    setNotification({ msg, type });
    setTimeout(() => setNotification(null), 3500);
  };

  const toggleVoiceMode = () => {
    voiceManager.unlockAudio();
    const newState = voiceManager.toggleVoiceMode();
    setIsVoiceMode(newState);
    if (newState) {
      showToast("Voice Mode Activated 🎙️", "success");
      voiceManager.speak("MerchantMind voice assistant activated. You can order using voice.");
    } else {
      voiceManager.stopSpeaking();
      showToast("Voice Mode Deactivated", "success");
    }
  };

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

  // Poll order status if active order is pending
  useEffect(() => {
    if (!activeOrderId || orderPaid) return;

    const interval = setInterval(async () => {
      try {
        const statusRes = await fetchOrderStatus(activeOrderId);
        if (statusRes && statusRes.status === "paid") {
          setOrderPaid(true);
          setActivePaymentLink(null);
          setActiveOrderId(activeOrderId);
          activeOrderIdRef.current = activeOrderId;
          if (typeof window !== "undefined" && activeOrderId) {
            localStorage.setItem("merchantmind_active_order_id", activeOrderId);
          }
          const targetOrdId = activeOrderId;
          showToast("Payment confirmed! Taking you to Live Tracking... 🚀", "success");
          
          if (voiceManager.isVoiceMode() || isVoiceMode) {
            voiceManager.speak(`Payment confirmed! ${selectedMerchant?.name || "The store"} has confirmed your order. Taking you to live order tracking now.`);
          }

          setMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              content: `🎉 **Payment Confirmed!** (₹${statusRes.total.toFixed(0)})\n\nPayment captured via Razorpay (\`${statusRes.rzp_payment_id || "captured"}\`). **${selectedMerchant?.name || "The merchant"}** has confirmed your order.\n\n🛵 **[Track Order Live 🚀](/orders/${targetOrdId}/tracking)**`,
              timestamp: new Date().toISOString(),
            },
          ]);
          setCart({ items: [], total: 0 });
          clearInterval(interval);

          setTimeout(() => {
            if (targetOrdId) {
              router.push(`/orders/${targetOrdId}/tracking`);
            }
          }, 2500);
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [activeOrderId, orderPaid, selectedMerchant, isVoiceMode]);

  // Dynamically load Razorpay standard checkout script
  const loadRazorpayScript = (): Promise<boolean> => {
    return new Promise((resolve) => {
      if (typeof window === "undefined") return resolve(false);
      if ((window as any).Razorpay) return resolve(true);
      const existing = document.querySelector('script[src="https://checkout.razorpay.com/v1/checkout.js"]');
      if (existing) {
        existing.addEventListener("load", () => resolve(true));
        existing.addEventListener("error", () => resolve(false));
        return;
      }
      const script = document.createElement("script");
      script.src = "https://checkout.razorpay.com/v1/checkout.js";
      script.async = true;
      script.onload = () => resolve(true);
      script.onerror = () => resolve(false);
      document.body.appendChild(script);
    });
  };

  // Directly launch native Razorpay Checkout modal right on top of the chat
  const openRazorpayCheckout = async (targetUrlOrOrderId?: string | null) => {
    let targetOrderId = activeOrderId || activeOrderIdRef.current;
    if (targetUrlOrOrderId) {
      const match = targetUrlOrOrderId.match(/([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})/);
      if (match) {
        targetOrderId = match[1];
      }
    }

    const currConvId = conversationIdRef.current || conversationId;
    if (!targetOrderId && currConvId) {
      try {
        const latestOrder = await fetchLatestConversationOrder(currConvId);
        if (latestOrder?.id) {
          targetOrderId = latestOrder.id;
          setActiveOrderId(latestOrder.id);
          activeOrderIdRef.current = latestOrder.id;
          if (latestOrder.payment_link) {
            setActivePaymentLink(latestOrder.payment_link);
            activePaymentLinkRef.current = latestOrder.payment_link;
          }
        }
      } catch (err) {
        console.warn("Could not fetch latest conversation order:", err);
      }
    }

    if (!targetOrderId) {
      const currentCart = (cartRef.current?.items?.length ?? 0) > 0 ? cartRef.current : cart;
      if (currentCart.items.length > 0) {
        await handleCheckout();
        return;
      }
      const fallbackUrl = resolvePaymentUrl(targetUrlOrOrderId || activePaymentLinkRef.current || activePaymentLink);
      if (fallbackUrl) {
        showToast("Opening Razorpay payment window...", "success");
        window.open(fallbackUrl, "_blank");
        return;
      }
      showToast("No active order found. Please add items to cart first.", "error");
      return;
    }

    showToast("Launching Razorpay Checkout...", "success");

    let orderStatus = await fetchOrderStatus(targetOrderId);
    const amount = orderStatus?.total || cart.total || 0;
    const amountPaise = Math.round(amount * 100);
    const rzpOrderId = orderStatus?.rzp_order_id || undefined;
    const rzpKeyId = orderStatus?.rzp_key_id || process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID || "rzp_test_TTBzVCxzHMSaip";
    const merchantTitle = selectedMerchant?.name || "MerchantMind Bangalore";

    if (voiceManager.isVoiceMode() || isVoiceMode) {
      voiceManager.speak(`Opening secure Razorpay payment for ₹${amount.toFixed(0)}. Please complete your transaction.`);
    }

    const scriptLoaded = await loadRazorpayScript();
    if (!scriptLoaded || typeof (window as any).Razorpay === "undefined") {
      console.warn("Razorpay script not loaded, falling back to payment URL:", targetUrlOrOrderId);
      const fallbackUrl = resolvePaymentUrl(targetUrlOrOrderId || activePaymentLink);
      if (fallbackUrl) {
        window.open(fallbackUrl, "_blank");
      }
      return;
    }

    const options: any = {
      key: rzpKeyId,
      amount: amountPaise,
      currency: "INR",
      name: merchantTitle,
      description: `Order #${targetOrderId.slice(0, 8)}`,
      order_id: rzpOrderId,
      prefill: {
        name: customerProfile?.name || "Utkarsh Singh",
        contact: customerProfile?.phone || "+919876543210",
        email: customerProfile?.email || "utkarsh@merchantmind.ai",
      },
      theme: {
        color: "#059669",
      },
      modal: {
        ondismiss: () => {
          showToast("Payment window closed. Tap Pay when ready.");
        },
      },
      handler: async (response: any) => {
        showToast("Payment captured! Verifying...", "success");
        try {
          await verifyOrderPayment(
            targetOrderId!,
            response.razorpay_payment_id,
            response.razorpay_order_id,
            response.razorpay_signature
          );
          setOrderPaid(true);
          setActivePaymentLink(null);
          setActiveOrderId(targetOrderId);
          activeOrderIdRef.current = targetOrderId;
          if (typeof window !== "undefined" && targetOrderId) {
            localStorage.setItem("merchantmind_active_order_id", targetOrderId);
          }
          setCart({ items: [], total: 0 });
          showToast("Payment confirmed! Taking you to Live Tracking... 🚀", "success");

          const confMsg = `🎉 **Payment Confirmed!** (₹${amount.toFixed(0)})\n\nPayment captured via Razorpay (\`${response.razorpay_payment_id || "captured"}\`). **${merchantTitle}** has confirmed your order.\n\n🛵 **[Track Order Live 🚀](/orders/${targetOrderId}/tracking)**`;
          setMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              content: confMsg,
              timestamp: new Date().toISOString(),
            },
          ]);

          if (voiceManager.isVoiceMode() || isVoiceMode) {
            voiceManager.speak(`Payment confirmed via Razorpay for ₹${amount.toFixed(0)}! Taking you to live delivery tracking now.`);
          }

          setTimeout(() => {
            if (targetOrderId) {
              router.push(`/orders/${targetOrderId}/tracking`);
            }
          }, 2500);
        } catch (verErr) {
          console.error("Payment verification error:", verErr);
          showToast("Payment verification error. Retrying...", "error");
        }
      },
    };

    try {
      const rzp = new (window as any).Razorpay(options);
      rzp.open();
    } catch (openErr) {
      console.error("Razorpay open error:", openErr);
      const fallbackUrl = resolvePaymentUrl(targetUrlOrOrderId || activePaymentLink);
      if (fallbackUrl) window.open(fallbackUrl, "_blank");
    }
  };

  // Handle sending chat message with real-time ReAct SSE streaming
  async function handleSendMessage(text: string) {
    handleSendMessageRef.current = handleSendMessage;
    if (isLoading) return;

    const cleanLower = text.toLowerCase().trim();
    if (!cleanLower) return;

    // Prevent duplicate triggers within 2 seconds
    const now = Date.now();
    if (
      lastMessageRef.current.text === cleanLower &&
      now - lastMessageRef.current.time < 2000
    ) {
      return;
    }
    lastMessageRef.current = { text: cleanLower, time: now };

    // Robust Wake Word Detection (Alexa / Siri style)
    // Matches "hi merchantmind", "merchantmind", "hey merchantmind", "mercanhtmind", "merchant mind", etc.
    const WAKE_WORD_REGEX =
      /^(?:(?:hey|hi|hello|ok|okay)\s+)?(?:merchant\s*mind|merchantmind|merchants\s*mind|mercanhtmind|mercanht\s*mind|merchant\s*mine|merchant\s*man|merchant)\b[,\s]*/i;
    const isWakeWordPresent =
      WAKE_WORD_REGEX.test(cleanLower) ||
      cleanLower.includes("merchantmind") ||
      cleanLower.includes("merchant mind") ||
      cleanLower.includes("mercanhtmind");

    // Strip wake word prefix if present to extract user intent
    const textWithoutWake = cleanLower
      .replace(WAKE_WORD_REGEX, "")
      .replace(/^(?:merchant\s*mind|merchantmind|mercanhtmind|merchant)[,\s]*/i, "")
      .replace(/^[,\s.!?]+/, "")
      .trim();

    // Standalone Wake Word (e.g. "hi merchantmind", "hey merchant mind", "merchantmind", "hello merchantmind")
    if (isWakeWordPresent && !textWithoutWake) {
      const userName = customerProfile?.name ? customerProfile.name.split(" ")[0] : "Utkarsh";
      const userMsg: MessageProps = {
        role: "user",
        content: text,
        timestamp: new Date().toISOString(),
      };
      const assistantGreeting: MessageProps = {
        role: "assistant",
        content: `Hey ${userName}! 👋 I'm right here and listening.\n\nWhat would you like to explore or order today across Bangalore stores? (e.g. *"Truffle cake under ₹600"* or *"2 dosas, 1 pizza, and a burger"*).`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg, assistantGreeting]);
      const speechGreeting = `Hey ${userName}! I'm here. What would you like to explore or order today?`;
      voiceManager.speak(speechGreeting);
      return;
    }

    const queryText = textWithoutWake || cleanLower;

    const currentCart = (cartRef.current?.items?.length ?? 0) > 0 ? cartRef.current : cart;
    const currentConvId = conversationIdRef.current || conversationId;
    const currentMerchant = selectedMerchantRef.current || selectedMerchant;
    const currentProfile = customerProfileRef.current || customerProfile;

    const hasActiveOrderOrCart = Boolean(
      activePaymentLink ||
      activePaymentLinkRef.current ||
      activeOrderId ||
      activeOrderIdRef.current ||
      currentCart.items.length > 0
    );

    // Voice or typed payment commands (e.g. "to a payment for me", "pay", "pay now", "make payment", "pay with razorpay")
    const isDirectPayClick =
      [
        "pay",
        "payment",
        "to a payment",
        "to payment",
        "do a payment",
        "do payment",
        "pay for me",
        "make payment",
        "make a payment",
        "pay now",
        "pay with razorpay",
        "pay via razorpay",
        "pay 860",
        "complete payment",
        "pay the bill",
        "pay bill",
        "proceed to pay",
        "proceed with payment",
        "process payment",
        "pay for order",
        "open razorpay",
        "open payment",
        "pay please",
        "pay it",
        "pay this",
      ].some((k) => queryText === k || queryText.includes(k)) ||
      (queryText.includes("pay") &&
        (queryText.includes("now") ||
          queryText.includes("₹") ||
          queryText.startsWith("💳") ||
          queryText.includes("razorpay") ||
          queryText.includes("for me") ||
          queryText.includes("me") ||
          queryText.includes("order") ||
          queryText.includes("bill") ||
          queryText.includes("done"))) ||
      (hasActiveOrderOrCart &&
        (queryText.includes("payment") ||
          queryText.includes("razorpay") ||
          queryText === "pay" ||
          queryText.startsWith("pay ") ||
          queryText.endsWith(" pay") ||
          queryText.includes(" pay ")));

    if (isDirectPayClick) {
      const link = activePaymentLinkRef.current || activePaymentLink;
      const ordId = activeOrderIdRef.current || activeOrderId;
      openRazorpayCheckout(ordId || link);
      return;
    }

    const isAlarmQuery =
      [
        "set alarm",
        "set a alarm",
        "set an alarm",
        "alarm when",
        "alarm on arrival",
        "wake me",
        "alert me when",
        "ring alarm",
        "arrival alarm",
      ].some((k) => queryText.includes(k)) ||
      (queryText.includes("alarm") &&
        (queryText.includes("order") ||
          queryText.includes("food") ||
          queryText.includes("arrive") ||
          queryText.includes("comes")));

    if (isAlarmQuery) {
      const userMsg: MessageProps = {
        role: "user",
        content: text,
        timestamp: new Date().toISOString(),
      };
      if (activeOrderId) {
        const trackingUrl = `/orders/${activeOrderId}/tracking?alarm=true`;
        const assistantAlarm: MessageProps = {
          role: "assistant",
          content: `⏰ **Arrival Alarm Armed!**\n\nI have set an arrival alarm for **Order #${activeOrderId.slice(0, 8)}**! The moment your delivery arrives, a loud audio chime will ring to alert you.\n\n[🔔 Open Live Tracking & Armed Alarm](${trackingUrl})\n\nYou can also test or manage the alarm directly on your live tracking dashboard.`,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, userMsg, assistantAlarm]);
        if (voiceManager.isVoiceMode() || isVoiceMode) {
          voiceManager.speak(
            "Arrival alarm is armed! A loud chime will sound the moment your delivery arrives. Tap the button to view your live tracking."
          );
        }
      } else {
        const assistantAlarm: MessageProps = {
          role: "assistant",
          content: `You don't have an active order yet! Once you place your order, you can tell me to set an alarm, and I'll sound a loud chime when your delivery arrives.`,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, userMsg, assistantAlarm]);
        if (voiceManager.isVoiceMode() || isVoiceMode) {
          voiceManager.speak(
            "You don't have an active order yet. Once you place an order, I can set an arrival alarm for you!"
          );
        }
      }
      return;
    }

    const isTrackingQuery =
      [
        "tracking page",
        "tracking pagre",
        "tracking",
        "track page",
        "show me tracking",
        "show tracking",
        "open tracking",
        "go to tracking",
        "take me to tracking",
        "bring me to tracking",
        "view tracking",
        "check tracking",
        "track order",
        "track my order",
        "track my food",
        "track food",
        "live tracking",
        "where is my order",
        "where is my food",
        "where's my food",
        "where's my order",
        "order status",
        "delivery status",
        "driver status",
      ].some((k) => queryText === k || queryText.includes(k)) ||
      (/\b(go to|take me to|open|show|view|check|bring me to|switch to|navigate to)\b.*\btrack/i.test(queryText)) ||
      (/\b(tracking|tracker)\b/i.test(queryText));

    if (isTrackingQuery) {
      let targetOrdId = resolveCurrentOrderId();

      if (!targetOrdId && currentConvId) {
        try {
          const latestOrder = await fetchLatestConversationOrder(currentConvId);
          if (latestOrder?.id) {
            targetOrdId = latestOrder.id;
          }
        } catch (err) {
          console.warn("Could not fetch latest conversation order for tracking redirect:", err);
        }
      }

      if (targetOrdId) {
        setActiveOrderId(targetOrdId);
        activeOrderIdRef.current = targetOrdId;
        if (typeof window !== "undefined") {
          localStorage.setItem("merchantmind_active_order_id", targetOrdId);
        }

        const userMsg: MessageProps = {
          role: "user",
          content: text,
          timestamp: new Date().toISOString(),
        };
        const assistantMsg: MessageProps = {
          role: "assistant",
          content: `Okay! Taking you to your live tracking page now... 🚀\n\n[🚚 View Live Order Tracking](/orders/${targetOrdId}/tracking)`,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, userMsg, assistantMsg]);

        if (voiceManager.isVoiceMode() || isVoiceMode) {
          voiceManager.speak("Okay! Taking you to your live tracking page now.");
        }

        showToast("Redirecting to Live Order Tracking...", "success");

        setTimeout(() => {
          router.push(`/orders/${targetOrdId}/tracking`);
        }, 600);
        return;
      } else {
        const userMsg: MessageProps = {
          role: "user",
          content: text,
          timestamp: new Date().toISOString(),
        };
        const assistantMsg: MessageProps = {
          role: "assistant",
          content: `You don't have an active order yet! Once you place an order with any Bangalore store, I'll take you straight to your live delivery tracking dashboard.`,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, userMsg, assistantMsg]);
        if (voiceManager.isVoiceMode() || isVoiceMode) {
          voiceManager.speak("You don't have an active order yet. Place an order first, and I'll take you straight to live tracking!");
        }
        return;
      }
    }

    const userMsg: MessageProps = {
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);
    setLiveStreamingEvents([]);
    voiceManager.notifyThinking();

    try {
      const response = await sendChatMessageStreaming(
        {
          merchant_id: currentMerchant ? currentMerchant.id : null,
          conversation_id: currentConvId,
          customer_id: currentProfile ? (currentProfile.id as any) : undefined,
          message: textWithoutWake || text,
          cart_items: currentCart.items,
        },
        (event: ReasoningEvent) => {
          setLiveStreamingEvents((prev) => [...prev, event]);
          if ((event as any).data?.order_id) {
            setActiveOrderId((event as any).data.order_id);
            activeOrderIdRef.current = (event as any).data.order_id;
          }
          if ((event as any).data?.payment_link) {
            setActivePaymentLink((event as any).data.payment_link);
            activePaymentLinkRef.current = (event as any).data.payment_link;
          }
        }
      );

      if (!response) {
        throw new Error("No response received from streaming chat agent");
      }

      if (response.conversation_id) {
        setConversationId(response.conversation_id);
        conversationIdRef.current = response.conversation_id;
      }

      // Auto-lock merchant if agent selected/resolved one
      if (response.merchant_id) {
        const matched = merchants.find((m) => m.id === response.merchant_id);
        if (matched && (!selectedMerchant || selectedMerchant.id !== matched.id)) {
          setSelectedMerchant(matched);
          selectedMerchantRef.current = matched;
          showToast(`Store: ${matched.name}`, "success");
        }
      }

      if (response.order_id) {
        setActiveOrderId(response.order_id);
        activeOrderIdRef.current = response.order_id;
      }

      if (response.payment_link) {
        setActivePaymentLink(response.payment_link);
        activePaymentLinkRef.current = response.payment_link;
        const uuidMatch = response.payment_link.match(/([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})/);
        if (uuidMatch && !activeOrderIdRef.current) {
          setActiveOrderId(uuidMatch[1]);
          activeOrderIdRef.current = uuidMatch[1];
        }
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

      // Speak response aloud if Voice Mode is active (STRICTLY speak only items & amount on checkout)
      if (voiceManager.isVoiceMode() || isVoiceMode) {
        if (response.payment_link || response.action === "checkout") {
          const itemsSummary =
            response.cart && response.cart.length > 0
              ? response.cart.map((i) => `${i.quantity}x ${i.name}`).join(", ")
              : currentCart.items.map((i) => `${i.quantity}x ${i.name}`).join(", ") || "your items";
          const totalStr = (response.cart_total || currentCart.total)
            ? `${(response.cart_total || currentCart.total).toFixed(0)} rupees`
            : "";
          const isPickup = response.message.toLowerCase().includes("pickup");
          voiceManager.speak(
            `Your ${isPickup ? "pickup " : ""}order for ${itemsSummary} is ${totalStr}. Say 'Pay' or tap below to open Razorpay payment.`
          );
        } else {
          voiceManager.speak(response.message);
        }
      }

      // If backend returned checkout or payment trigger in response to user's payment intent, auto-open Razorpay
      const queryLower = (textWithoutWake || text).toLowerCase();
      const userAskedPay = ["pay", "payment", "to a payment", "do payment", "pay for me", "make payment", "proceed to pay"].some((k) => queryLower.includes(k));
      if (
        (response.payment_link || response.action === "checkout") &&
        (userAskedPay || response.message.toLowerCase().includes("opening secure razorpay checkout"))
      ) {
        setTimeout(() => {
          openRazorpayCheckout(response.order_id || activeOrderIdRef.current || response.payment_link);
        }, 350);
      }

      // If user asked to track or backend returned tracking action, auto-redirect to live tracking page!
      let detectedTrackingOrderId: string | null = response.order_id || null;
      if (!detectedTrackingOrderId && response.message) {
        const match = response.message.match(/\/orders\/([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\/tracking/);
        if (match) detectedTrackingOrderId = match[1];
      }
      if (!detectedTrackingOrderId) {
        detectedTrackingOrderId = resolveCurrentOrderId();
      }

      const userAskedTracking =
        isTrackingQuery ||
        queryLower.includes("track") ||
        queryLower.includes("where is my") ||
        queryLower.includes("where is the");

      if (
        detectedTrackingOrderId &&
        (response.action === "tracking" || response.action === "redirect_tracking" || userAskedTracking || response.message.includes("/tracking"))
      ) {
        setActiveOrderId(detectedTrackingOrderId);
        activeOrderIdRef.current = detectedTrackingOrderId;
        if (typeof window !== "undefined") {
          localStorage.setItem("merchantmind_active_order_id", detectedTrackingOrderId);
        }
        if (userAskedTracking) {
          if (voiceManager.isVoiceMode() || isVoiceMode) {
            voiceManager.speak("Taking you to your live tracking page now.");
          }
          showToast("Redirecting to Live Order Tracking...", "success");
          setTimeout(() => {
            router.push(`/orders/${detectedTrackingOrderId}/tracking`);
          }, 700);
        }
      }

      if (response.payment_link) {
        // Clear active cart only when order and payment link are created
        const emptyCart = { items: [], total: 0 };
        setCart(emptyCart);
        cartRef.current = emptyCart;
      } else if (response.cart && response.cart.length > 0) {
        const updatedCart = {
          items: response.cart,
          total: response.cart_total || 0,
        };
        setCart(updatedCart);
        cartRef.current = updatedCart;
      } else {
        // Never wipe client cart when checkout or clarification is in progress
        const lowerTxt = (textWithoutWake || text).toLowerCase().trim();
        const isClearIntent = ["clear cart", "empty cart", "clear my cart", "empty my cart", "reset cart"].some((k) => lowerTxt.includes(k));
        if (isClearIntent) {
          const emptyCart = { items: [], total: 0 };
          setCart(emptyCart);
          cartRef.current = emptyCart;
        }
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
  }

  // Keep handleSendMessageRef always synchronized so first voice command triggers immediately
  handleSendMessageRef.current = handleSendMessage;

  // Initialize Voice Manager callbacks
  useEffect(() => {
    handleSendMessageRef.current = handleSendMessage;
    voiceManager.init({
      onTranscript: (transcript: string, isFinal: boolean) => {
        setLiveTranscript(transcript);
        if (isFinal && transcript.trim()) {
          const t = transcript.toLowerCase().trim();
          const WAKE_WORD_REGEX =
            /^(?:(?:hey|hi|hello|ok|okay)\s+)?(?:merchant\s*mind|merchantmind|merchants\s*mind|mercanhtmind|mercanht\s*mind|merchant\s*mine|merchant)\b[,\s]*/i;
          if (WAKE_WORD_REGEX.test(t) || isVoiceModeRef.current || voiceManager.isVoiceMode()) {
            setLiveTranscript("");
            handleSendMessageRef.current(transcript);
          }
        }
      },
      onAutoSubmit: (transcript: string) => {
        setLiveTranscript("");
        handleSendMessageRef.current(transcript);
      },
      onStateChange: (state: VoiceState) => {
        setVoiceState(state);
      },
      onError: (err: string) => {
        showToast(err, "error");
      },
    });
  }, []);

  // Handle Add to Cart from product cards
  const handleAddToCart = async (product: ProductRecommendation) => {
    // 1. Immediately update local cart state with zero latency
    const currentItems = [...cart.items];
    const existingIdx = currentItems.findIndex((i) => String(i.product_id) === String(product.product_id));
    if (existingIdx >= 0) {
      currentItems[existingIdx] = {
        ...currentItems[existingIdx],
        quantity: currentItems[existingIdx].quantity + 1,
      };
    } else {
      currentItems.push({
        product_id: product.product_id as any,
        name: product.name,
        price: product.price,
        quantity: 1,
        merchant_id: (product as any).merchant_id,
        merchant_name: product.merchant_name,
      } as any);
    }
    const newTotal = currentItems.reduce((acc, i) => acc + i.price * i.quantity, 0);
    setCart({ items: currentItems, total: newTotal });
    showToast(`Added 1x ${product.name} to cart! 🛒`, "success");

    // Auto-select merchant if in All-Stores mode
    if ((product as any).merchant_id) {
      const matchM = merchants.find((m) => m.id === (product as any).merchant_id);
      if (matchM && (!selectedMerchant || selectedMerchant.id !== matchM.id)) {
        setSelectedMerchant(matchM);
      }
    }

    // 2. Persist directly to backend if conversation exists
    if (conversationId) {
      updateCartDirectly(conversationId, currentItems).catch((err) => {
        console.error("Direct cart sync error:", err);
      });
    }

    // 3. Notify assistant in chat
    handleSendMessage(`Add 1 ${product.name} to my cart`);
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

    // Detect multi-store cart
    const distinctStores = new Set(
      cart.items.map((i: any) => i.merchant_id || i.merchant_name).filter(Boolean)
    );
    const isMultiStoreCart = distinctStores.size > 1;

    if (isMultiStoreCart) {
      setIsCheckingOut(true);
      try {
        const mode = fulfillment?.mode || "delivery";
        const address = fulfillment?.address;
        const pickupTime = fulfillment?.pickupTime;

        const multiRes = await createMultiOrder({
          conversation_id: conversationId || "00000000-0000-0000-0000-000000000000",
          fulfillment_mode: mode,
          delivery_address: address,
          pickup_time: pickupTime,
          items: cart.items,
        });

        setActiveOrderId(multiRes.primary_order_id);
        if (multiRes.payment_link) {
          setActivePaymentLink(multiRes.payment_link);
        }
        setCart({ items: [], total: 0 });

        const fulfillmentSummary =
          mode === "delivery"
            ? `🚚 Delivery${address ? ` to *${address}*` : ""}`
            : `🏪 Pickup${pickupTime ? ` (*${pickupTime}*)` : ""}`;

        const siblingParam =
          multiRes.sibling_order_ids && multiRes.sibling_order_ids.length > 0
            ? `?sibling=${multiRes.sibling_order_ids[0]}`
            : "";

        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `🎉 **Dual-Store Orders Created (${multiRes.orders.length} Kitchens)** for a total of **₹${multiRes.total.toFixed(0)}** (${fulfillmentSummary}).\n\nPay once with your unified Razorpay link below:\n\n[🚚 Open Live Dual-Tracking Dashboard](/orders/${multiRes.primary_order_id}/tracking${siblingParam})`,
            timestamp: new Date().toISOString(),
            payment_link: multiRes.payment_link,
            action: "checkout",
          },
        ]);
        showToast("Unified Dual-Store link created", "success");
        setTimeout(() => {
          openRazorpayCheckout(multiRes.primary_order_id);
        }, 400);
        if (voiceManager.isVoiceMode() || isVoiceMode) {
          voiceManager.speak(
            `Dual-store order created for ₹${multiRes.total.toFixed(0)}. Please complete payment in the Razorpay checkout.`
          );
        }
        return;
      } catch (err: any) {
        console.error("Multi-checkout error:", err);
        const errMsg = err.message || "Dual-store checkout failed.";
        showToast(errMsg, "error");
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `⚠️ **Dual-Store Checkout Blocked**: ${errMsg}`,
            timestamp: new Date().toISOString(),
          },
        ]);
        return;
      } finally {
        setIsCheckingOut(false);
      }
    }

    // If no specific merchant selected in Discovery Mode, resolve from first item's store
    let merchantToUse = selectedMerchant;
    if (!merchantToUse && cart.items.length > 0) {
      const firstItem = cart.items[0] as any;
      if (firstItem.merchant_id) {
        merchantToUse = merchants.find((m) => m.id === firstItem.merchant_id) || null;
      }
      if (!merchantToUse && firstItem.merchant_name) {
        merchantToUse = merchants.find((m) => m.name.toLowerCase().includes(firstItem.merchant_name.toLowerCase())) || null;
      }
    }
    if (!merchantToUse && merchants.length > 0) {
      merchantToUse = merchants[0];
    }
    if (merchantToUse && (!selectedMerchant || selectedMerchant.id !== merchantToUse.id)) {
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
      const emptyCart = { items: [], total: 0 };
      setCart(emptyCart);
      cartRef.current = emptyCart;

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
      setTimeout(() => {
        openRazorpayCheckout(order.id);
      }, 400);
      if (voiceManager.isVoiceMode() || isVoiceMode) {
        voiceManager.speak(`Order created for ₹${order.total.toFixed(0)}. Please complete payment in the Razorpay checkout.`);
      }
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
      cartRef.current = updated;
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
      cartRef.current = updated;
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
      cartRef.current = updated;
      showToast("Cart cleared");
    } catch (err) {
      console.error("Clear cart error:", err);
    }
  };

  const handleNewSession = () => {
    setConversationId(null);
    conversationIdRef.current = null;
    const emptyCart = { items: [], total: 0 };
    setCart(emptyCart);
    cartRef.current = emptyCart;
    setActiveOrderId(null);
    activeOrderIdRef.current = null;
    setActivePaymentLink(null);
    activePaymentLinkRef.current = null;
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

  const validMerchants = merchants.filter(
    (m) => !m.name.toLowerCase().includes("test") && !m.email?.endsWith("@test.com")
  );

  return (
    <div className="flex min-h-screen flex-col bg-[#08090E] text-zinc-100 font-sans selection:bg-indigo-600 selection:text-white relative">
      {/* 21st.dev Atmospheric Lighting & Mesh Backdrop */}
      <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
        <div className="absolute -top-32 left-1/2 -translate-x-1/2 h-[450px] w-[750px] rounded-full bg-gradient-to-b from-indigo-500/12 via-violet-500/5 to-transparent blur-[120px]" />
        <div className="absolute -bottom-32 right-[-5%] h-[400px] w-[500px] rounded-full bg-emerald-500/[0.03] blur-[140px]" />
        <div className="absolute inset-0 bg-[radial-gradient(rgba(255,255,255,0.06)_1px,transparent_1px)] [background-size:24px_24px] opacity-25" />
      </div>

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
                : "bg-[#0E1019]/95 text-white border-white/10"
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

      {/* Top Header (21st.dev Frosted Glass) */}
      <header className="sticky top-0 z-30 border-b border-white/[0.07] bg-[#08090E]/85 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-2.5 sm:px-6">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="flex h-8.5 w-8.5 items-center justify-center rounded-xl bg-white/[0.03] border border-white/[0.08] text-zinc-400 hover:text-white hover:border-white/[0.2] transition"
              title="Home"
            >
              <ArrowLeft className="h-4 w-4" />
            </Link>

            <div className="flex h-8.5 w-8.5 items-center justify-center rounded-xl bg-gradient-to-b from-zinc-800 to-zinc-950 border border-white/10 text-white shadow-md">
              <Store className="h-4 w-4 text-zinc-100" />
            </div>

            <div className="flex items-center gap-2.5">
              <h1 className="text-sm font-bold tracking-tight text-zinc-100">
                MerchantMind
              </h1>
              <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-950/60 border border-emerald-500/30 px-2.5 py-0.5 text-[10px] font-semibold text-emerald-400 shadow-sm">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-ping" />
                Live Concierge
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Multi-Tenant Merchant Selector Dropdown */}
            <div className="relative">
              <button
                onClick={() => setShowMerchantPicker(!showMerchantPicker)}
                className={`flex items-center gap-2 rounded-xl border px-3 py-1.5 text-xs font-medium transition shadow-sm cursor-pointer ${
                  selectedMerchant
                    ? "border-white/[0.08] bg-white/[0.04] text-zinc-200 hover:border-white/[0.2]"
                    : "border-indigo-500/30 bg-indigo-500/10 text-indigo-300 hover:border-indigo-500/50"
                }`}
              >
                {selectedMerchant ? (
                  <>
                    <Store className="h-3.5 w-3.5 text-indigo-300" />
                    <span className="max-w-[130px] sm:max-w-none truncate">{selectedMerchant.name}</span>
                  </>
                ) : (
                  <>
                    <Globe2 className="h-3.5 w-3.5 text-cyan-400" />
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
                    className="absolute right-0 mt-2 w-80 max-h-[80vh] sm:max-h-[490px] flex flex-col rounded-2xl border border-white/[0.08] bg-[#0E1019]/98 shadow-2xl backdrop-blur-2xl z-50 overflow-hidden"
                  >
                    <div className="p-2.5 border-b border-white/[0.08] bg-white/[0.02]">
                      <div className="flex items-center justify-between mb-2 px-1">
                        <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider">
                          Select Store ({validMerchants.length} Stores)
                        </span>
                        <span className="text-[9px] font-medium text-indigo-300 bg-indigo-500/20 px-1.5 py-0.5 rounded border border-indigo-500/30">
                          Bangalore
                        </span>
                      </div>

                      {/* Discovery Mode Option */}
                      <button
                        onClick={() => handleManualStoreSelect(null)}
                        className={`flex w-full items-center gap-2.5 rounded-xl px-2.5 py-2 text-left text-xs transition mb-2 cursor-pointer ${
                          selectedMerchant === null
                            ? "bg-indigo-500/20 text-indigo-200 border border-indigo-500/40 shadow-sm"
                            : "text-zinc-300 hover:bg-white/[0.04] border border-transparent"
                        }`}
                      >
                        <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-cyan-500/15 border border-cyan-500/30 text-cyan-400">
                          <Globe2 className="h-3.5 w-3.5" />
                        </div>
                        <div className="flex-1 min-w-0 font-medium">All Stores (Discovery Mode)</div>
                        {selectedMerchant === null && (
                          <CheckCircle2 className="h-3.5 w-3.5 text-indigo-400 shrink-0" />
                        )}
                      </button>

                      {/* Instant Search Bar */}
                      <input
                        type="text"
                        placeholder="Search store name or area..."
                        value={storeSearchQuery}
                        onChange={(e) => setStoreSearchQuery(e.target.value)}
                        className="w-full rounded-xl border border-white/[0.08] bg-black/40 px-2.5 py-1.5 text-xs text-zinc-200 placeholder-zinc-500 focus:border-indigo-500 focus:outline-none"
                      />
                    </div>

                    {/* Scrollable list of Bangalore stores */}
                    <div className="flex-1 overflow-y-auto p-1.5 space-y-0.5 max-h-[320px] divide-y divide-white/[0.04]">
                      {validMerchants
                        .filter((m) => {
                          // Exclude automated test fixture stores (Telegram Test Bakery, WhatsApp Test Bakery, etc.)
                          if (m.name.toLowerCase().includes("test") || m.email?.endsWith("@test.com")) {
                            return false;
                          }
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
                              className={`flex w-full items-center gap-2.5 rounded-xl px-2.5 py-1.5 text-left text-xs transition cursor-pointer ${
                                selectedMerchant?.id === m.id
                                  ? "bg-indigo-500/20 text-indigo-200 border border-indigo-500/30"
                                  : "text-zinc-300 hover:bg-white/[0.04] border border-transparent"
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
                                <CheckCircle2 className="h-3.5 w-3.5 text-indigo-400 shrink-0" />
                              )}
                            </button>
                          );
                        })}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Customer Memory Profile Badge (NO SPARKLES) */}
            {customerProfile && (
              <motion.button
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => setShowMemoryModal(true)}
                className="flex items-center gap-1.5 rounded-xl bg-cyan-950/60 border border-cyan-500/40 px-2.5 py-1.5 text-xs font-medium text-cyan-300 hover:bg-cyan-900/50 transition shadow-sm cursor-pointer"
                title="Customer Memory Profile"
              >
                <UserCheck className="h-3.5 w-3.5 text-cyan-400" />
                <span className="hidden sm:inline font-semibold">{customerProfile.name.split(" ")[0]}</span>
                <span className="text-[10px] text-cyan-300 bg-cyan-500/20 px-1.5 py-0.5 rounded font-mono">Memory</span>
              </motion.button>
            )}

            {/* Ambient Voice Mode Toggle */}
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={toggleVoiceMode}
              className={`flex items-center gap-1.5 rounded-xl border px-2.5 py-1.5 text-xs font-medium transition shadow-sm cursor-pointer ${
                isVoiceMode
                  ? "bg-gradient-to-tr from-cyan-500/20 to-emerald-500/20 border-cyan-500 text-cyan-300 shadow-cyan-500/20 shadow-lg"
                  : "bg-white/[0.04] border-white/[0.08] text-zinc-300 hover:border-white/[0.2] hover:text-white"
              }`}
              title="Toggle Ambient Voice Assistant"
            >
              {isVoiceMode ? (
                <Volume2 className="h-3.5 w-3.5 text-cyan-400 animate-pulse" />
              ) : (
                <Mic className="h-3.5 w-3.5 text-zinc-400" />
              )}
              <span className="hidden md:inline">{isVoiceMode ? "Voice ON" : "Voice"}</span>
            </motion.button>

            {/* Pipeline Activity Panel Toggle (NO BRAIN) */}
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => setShowReasoningPanel(true)}
              className="flex items-center gap-1.5 rounded-xl bg-white/[0.04] border border-white/[0.08] px-2.5 py-1.5 text-xs font-medium text-zinc-300 hover:border-white/[0.2] hover:text-white transition shadow-sm cursor-pointer"
              title="Activity Log"
            >
              <SlidersHorizontal className="h-3.5 w-3.5 text-indigo-400" />
              <span className="hidden md:inline">Activity</span>
              {reasoningLogs.length > 0 && (
                <span className="flex h-4 w-4 items-center justify-center rounded-full bg-indigo-600 text-[10px] font-bold text-white">
                  {reasoningLogs.length}
                </span>
              )}
            </motion.button>

            {/* Merchant Console Link */}
            <Link
              href="/merchant"
              className="hidden sm:flex items-center gap-1.5 rounded-xl bg-white/[0.03] border border-white/[0.08] px-2.5 py-1.5 text-xs font-medium text-zinc-300 hover:border-white/[0.2] hover:text-white transition shadow-sm"
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
              className="flex h-8.5 w-8.5 items-center justify-center rounded-xl border border-white/[0.08] bg-white/[0.03] text-zinc-400 transition hover:border-white/[0.2] hover:text-white cursor-pointer"
            >
              <RefreshCw className="h-3.5 w-3.5" />
            </motion.button>

            {/* Mobile Cart Button */}
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={() => setShowMobileCart(!showMobileCart)}
              className="relative flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-700 hover:from-indigo-500 hover:to-violet-600 px-3 py-1.5 text-xs font-semibold text-white transition lg:hidden cursor-pointer"
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
        {/* Left Column: Chat Conversation Stream (21st.dev Card) */}
        <section className="flex flex-1 flex-col justify-between overflow-hidden rounded-3xl border border-white/[0.08] bg-[#0D0F18]/85 shadow-[0_20px_50px_rgba(0,0,0,0.6)] backdrop-blur-2xl">
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
                payment_link={msg.role === "assistant" ? msg.payment_link : null}
                activePaymentLink={activePaymentLink}
                activeOrderId={activeOrderId}
                onAddToCart={handleAddToCart}
                onActionClick={(choice) => handleSendMessage(choice)}
                onPayClick={(url) => {
                  openRazorpayCheckout(url || activePaymentLink);
                }}
              />
            ))}

            {/* Real-Time Live Catalog & Sourcing Stream */}
            <AnimatePresence>
              {isLoading && <LiveReActStream events={liveStreamingEvents} />}
            </AnimatePresence>
            <div ref={messagesEndRef} />
          </div>

          {/* Chat Input Bar with Embedded Voice Controls */}
          <div className="border-t border-white/[0.08] bg-[#08090E]/80 p-3.5">
            <ChatInput
              onSendMessage={handleSendMessage}
              isLoading={isLoading}
              suggestions={activeSuggestions}
              placeholder={activePlaceholder}
              onSuggestionClick={(s) => handleSendMessage(s.replace(/^[^\s]+ /, ""))}
              isVoiceMode={isVoiceMode}
              voiceState={voiceState}
              onToggleVoice={toggleVoiceMode}
              liveTranscript={liveTranscript}
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
              onPayClick={(url) => openRazorpayCheckout(url || activePaymentLink)}
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
                onPayClick={(url) => openRazorpayCheckout(url || activePaymentLink)}
              />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Customer Ambient Memory Profile Modal */}
      <AnimatePresence>
        {showMemoryModal && customerProfile && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4"
            onClick={() => setShowMemoryModal(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0, y: 10 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.95, opacity: 0, y: 10 }}
              onClick={(e) => e.stopPropagation()}
              className="w-full max-w-lg rounded-3xl border border-cyan-500/30 bg-[#0E1019] p-6 shadow-2xl backdrop-blur-2xl text-zinc-100 space-y-4"
            >
              <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
                <div className="flex items-center gap-2.5">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-cyan-500/20 text-cyan-400 border border-cyan-500/40">
                    <UserCheck className="h-5 w-5 text-cyan-400" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      {customerProfile.name}
                      <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950/80 px-2 py-0.5 rounded-full border border-cyan-500/40">
                        Memory Active
                      </span>
                    </h3>
                    <p className="text-xs text-zinc-400">{customerProfile.phone} • {customerProfile.order_count} Orders (₹{customerProfile.total_spent.toFixed(0)})</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowMemoryModal(false)}
                  className="rounded-lg p-1.5 text-zinc-400 hover:text-white hover:bg-[#1E1E2E] transition cursor-pointer"
                >
                  ✕
                </button>
              </div>

              {/* Saved Delivery Addresses */}
              <div className="space-y-2">
                <span className="text-xs font-semibold text-cyan-400 uppercase tracking-wider flex items-center gap-1.5">
                  📍 Saved Delivery Locations
                </span>
                <div className="space-y-1.5">
                  {customerProfile.saved_addresses.map((addr, idx) => (
                    <div
                      key={idx}
                      className={`flex items-start justify-between rounded-xl p-2.5 text-xs border ${
                        addr.is_default
                          ? "bg-cyan-950/30 border-cyan-500/40 text-cyan-100"
                          : "bg-[#1E1E2E]/60 border-[#2A2A3E] text-zinc-300"
                      }`}
                    >
                      <div>
                        <div className="font-semibold flex items-center gap-1.5">
                          {addr.label}
                          {addr.is_default && (
                            <span className="text-[9px] font-mono bg-cyan-500/20 text-cyan-300 px-1.5 py-0.2 rounded">
                              DEFAULT
                            </span>
                          )}
                        </div>
                        <div className="text-[11px] text-zinc-400 mt-0.5">{addr.address}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Past Ratings & Favorite Merchants */}
              {customerProfile.favorite_merchants && customerProfile.favorite_merchants.length > 0 && (
                <div className="space-y-2">
                  <span className="text-xs font-semibold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                    ⭐ Past Favorites & Ratings
                  </span>
                  <div className="space-y-1.5">
                    {customerProfile.favorite_merchants.map((fav, i) => (
                      <div
                        key={i}
                        className="flex items-center justify-between rounded-xl bg-[#1E1E2E]/60 border border-[#2A2A3E] p-2.5 text-xs"
                      >
                        <div>
                          <div className="font-semibold text-white">{fav.name}</div>
                          <div className="text-[11px] text-zinc-400">Loved: {fav.last_item}</div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-amber-400 font-mono font-bold">⭐ {fav.rating || 5}/5</span>
                          <button
                            onClick={() => {
                              setShowMemoryModal(false);
                              handleSendMessage(`Reorder my favorite ${fav.last_item} from ${fav.name}`);
                            }}
                            className="px-2 py-1 rounded-lg bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 text-[10px] font-semibold hover:bg-cyan-500/30 transition cursor-pointer"
                          >
                            Reorder
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Voice Quick Action Prompt */}
              <div className="pt-2 border-t border-[#2A2A3E]">
                <button
                  onClick={() => {
                    setShowMemoryModal(false);
                    toggleVoiceMode();
                  }}
                  className="w-full flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-cyan-500 to-emerald-500 px-4 py-2.5 text-xs font-bold text-white shadow-lg shadow-cyan-500/20 hover:opacity-95 transition cursor-pointer"
                >
                  <Volume2 className="h-4 w-4" />
                  <span>Start Ambient Voice Assistant</span>
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Floating Ambient Voice Orb Widget (Desktop bottom-right) */}
      <div className="fixed bottom-6 right-6 z-40 hidden xl:flex flex-col items-center">
        <VoiceOrb
          state={voiceState}
          isActive={isVoiceMode}
          onToggle={toggleVoiceMode}
          size={72}
        />
      </div>

      {/* Real-Time Agent Reasoning & Decision Drawer */}
      <AgentReasoningPanel
        logs={reasoningLogs}
        isOpen={showReasoningPanel}
        onClose={() => setShowReasoningPanel(false)}
      />
    </div>
  );
}

