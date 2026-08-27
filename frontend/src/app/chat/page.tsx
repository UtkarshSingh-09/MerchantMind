"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import {
  Store,
  ShoppingBag,
  Sparkles,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  CreditCard,
  ArrowLeft,
  ChevronDown,
  ShieldCheck,
  Zap,
} from "lucide-react";
import {
  fetchMerchants,
  sendChatMessage,
  updateCartDirectly,
  createOrder,
  fetchOrderStatus,
  Merchant,
  CartItem,
  ProductRecommendation,
} from "@/lib/api";
import { ChatMessage, MessageProps } from "@/components/ChatMessage";
import { CartSidebar } from "@/components/CartSidebar";
import { ChatInput } from "@/components/ChatInput";

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
  const [notification, setNotification] = useState<{ msg: string; type?: "success" | "error" } | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading, activePaymentLink]);

  // Load merchants on initial render
  useEffect(() => {
    async function loadData() {
      try {
        const data = await fetchMerchants();
        setMerchants(data);
        if (data.length > 0) {
          const sweetBakes = data.find((m) => m.name.includes("Sweet Bakes")) || data[0];
          setSelectedMerchant(sweetBakes);
        }
      } catch (err) {
        console.error("Failed to load merchants:", err);
      }
    }
    loadData();
  }, []);

  // Initial welcome message when merchant selected or changed
  useEffect(() => {
    if (selectedMerchant) {
      setMessages([
        {
          role: "assistant",
          content: `👋 Welcome to **${selectedMerchant.name}**! I'm your AI shopping and growth agent.\n\nTell me what you're craving, your occasion, or a budget constraint (e.g. *"I want a chocolate cake under ₹800"*), and I'll find the best options with personalized reasoning!`,
          timestamp: new Date().toISOString(),
        },
      ]);
      setConversationId(null);
      setCart({ items: [], total: 0 });
      setActivePaymentLink(null);
      setOrderPaid(false);
    }
  }, [selectedMerchant]);

  // Poll order status if active order is pending
  useEffect(() => {
    if (!activeOrderId || orderPaid) return;

    const interval = setInterval(async () => {
      try {
        const statusRes = await fetchOrderStatus(activeOrderId);
        if (statusRes && statusRes.status === "paid") {
          setOrderPaid(true);
          setActivePaymentLink(null);
          showToast("🎉 Payment confirmed by Razorpay!", "success");
          setMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              content: `🎉 **Payment Confirmed!**\n\nYour payment of **₹${statusRes.total.toFixed(0)}** has been received successfully via Razorpay (Payment ID: \`${statusRes.rzp_payment_id || "captured"}\`).\n\n${selectedMerchant?.name} is now preparing your items! An audit trail of this transaction has been logged in compliance with our guardrails.`,
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

  // Toast notification helper
  const showToast = (msg: string, type: "success" | "error" = "success") => {
    setNotification({ msg, type });
    setTimeout(() => setNotification(null), 4000);
  };

  // Handle sending a chat message
  const handleSendMessage = async (text: string) => {
    if (!selectedMerchant || isLoading) return;

    const userMsg: MessageProps = {
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const response = await sendChatMessage({
        merchant_id: selectedMerchant.id,
        conversation_id: conversationId,
        message: text,
      });

      if (response.conversation_id) {
        setConversationId(response.conversation_id);
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
    } catch (err) {
      console.error("Chat error:", err);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "⚠️ I encountered a temporary connection issue. Please retry in a moment!",
          timestamp: new Date().toISOString(),
        },
      ]);
      showToast("Failed to reach agent", "error");
    } finally {
      setIsLoading(false);
    }
  };

  // Handle Add to Cart from product cards
  const handleAddToCart = async (product: ProductRecommendation) => {
    await handleSendMessage(`Add 1 ${product.name} to my cart`);
    showToast(`Added ${product.name} to cart!`);
  };

  // Handle Direct Checkout Initiation from Sidebar
  const handleCheckout = async () => {
    if (!selectedMerchant || !conversationId || cart.items.length === 0) {
      showToast("Please add items to cart before checking out.", "error");
      return;
    }

    setIsCheckingOut(true);
    try {
      const order = await createOrder({
        conversation_id: conversationId,
        merchant_id: selectedMerchant.id,
      });

      setActiveOrderId(order.id);
      if (order.payment_link) {
        setActivePaymentLink(order.payment_link);
      }

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `💳 I've created your Razorpay order for **₹${order.total.toFixed(0)}**.\n\nPlease click the button below to complete your payment securely with test card:`,
          timestamp: new Date().toISOString(),
          payment_link: order.payment_link,
          action: "checkout",
        },
      ]);
      showToast("Razorpay order & payment link created!", "success");
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

  // Handle direct cart quantity changes
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

  // Remove single item
  const handleRemoveItem = async (productId: string) => {
    if (!conversationId) return;
    const filtered = cart.items.filter((i) => i.product_id !== productId);
    try {
      const updated = await updateCartDirectly(conversationId, filtered);
      setCart(updated);
      showToast("Item removed from cart");
    } catch (err) {
      console.error("Remove item error:", err);
    }
  };

  // Clear all cart items
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

  // Reset conversation session
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
          content: `👋 New session started for **${selectedMerchant.name}**! What can I help you find today?`,
          timestamp: new Date().toISOString(),
        },
      ]);
    }
    showToast("Started a new conversation session");
  };

  return (
    <div className="flex min-h-screen flex-col bg-zinc-950 text-zinc-100 font-sans selection:bg-indigo-500 selection:text-white">
      {/* Background glow gradient */}
      <div className="fixed top-0 left-1/2 -translate-x-1/2 h-[350px] w-[700px] bg-gradient-to-tr from-indigo-600/15 via-violet-600/15 to-purple-600/10 blur-[140px] pointer-events-none rounded-full" />

      {/* Toast Notification */}
      {notification && (
        <div className={`fixed top-4 right-4 z-50 flex items-center gap-2 rounded-2xl px-4.5 py-3 text-xs font-semibold shadow-2xl backdrop-blur-xl border ${
          notification.type === "error"
            ? "bg-rose-950/90 text-rose-200 border-rose-500/40"
            : "bg-zinc-900/95 text-white border-zinc-700/80"
        }`}>
          {notification.type === "error" ? (
            <AlertCircle className="h-4 w-4 text-rose-400" />
          ) : (
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          )}
          <span>{notification.msg}</span>
        </div>
      )}

      {/* Top Header */}
      <header className="sticky top-0 z-30 border-b border-zinc-800/80 bg-zinc-950/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="flex h-9 w-9 items-center justify-center rounded-xl bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white hover:border-zinc-700 transition"
              title="Back to Home"
            >
              <ArrowLeft className="h-4 w-4" />
            </Link>

            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-500 to-violet-600 text-white shadow-md">
              <Sparkles className="h-4.5 w-4.5" />
            </div>

            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-sm font-bold tracking-tight text-zinc-100">
                  MerchantMind
                </h1>
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-950/60 border border-emerald-500/30 px-2 py-0.5 text-[10px] font-semibold text-emerald-400">
                  <Zap className="h-2.5 w-2.5" />
                  Live AI Agent
                </span>
              </div>
              <p className="text-[11px] text-zinc-400">
                Agentic Commerce with Razorpay Checkout
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            {/* Merchant Switcher Dropdown */}
            {selectedMerchant && (
              <div className="relative">
                <button
                  onClick={() => setShowMerchantPicker(!showMerchantPicker)}
                  className="flex items-center gap-2 rounded-xl border border-zinc-800 bg-zinc-900/90 px-3 py-1.5 text-xs font-medium text-zinc-200 hover:border-zinc-700 transition"
                >
                  <Store className="h-3.5 w-3.5 text-indigo-400" />
                  <span>{selectedMerchant.name}</span>
                  <ChevronDown className="h-3 w-3 text-zinc-400" />
                </button>

                {showMerchantPicker && (
                  <div className="absolute right-0 mt-2 w-56 rounded-2xl border border-zinc-800 bg-zinc-900/95 p-2 shadow-2xl backdrop-blur-xl z-50">
                    <p className="px-2 py-1 text-[10px] font-bold text-zinc-400 uppercase tracking-wider">
                      Switch Store (Multi-Tenant)
                    </p>
                    {merchants.map((m) => (
                      <button
                        key={m.id}
                        onClick={() => {
                          setSelectedMerchant(m);
                          setShowMerchantPicker(false);
                        }}
                        className={`flex w-full items-center justify-between rounded-xl px-2.5 py-2 text-xs font-medium transition ${
                          selectedMerchant.id === m.id
                            ? "bg-indigo-600/20 text-indigo-300 border border-indigo-500/30"
                            : "text-zinc-300 hover:bg-zinc-800"
                        }`}
                      >
                        <span>{m.name}</span>
                        {selectedMerchant.id === m.id && (
                          <CheckCircle2 className="h-3.5 w-3.5 text-indigo-400" />
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            <button
              onClick={handleNewSession}
              title="Reset Chat Session"
              className="flex h-9 w-9 items-center justify-center rounded-xl border border-zinc-800 bg-zinc-900 text-zinc-400 transition hover:bg-zinc-800 hover:text-white"
            >
              <RefreshCw className="h-4 w-4" />
            </button>

            {/* Mobile Cart Button */}
            <button
              onClick={() => setShowMobileCart(!showMobileCart)}
              className="relative flex items-center gap-2 rounded-xl bg-indigo-600 px-3 py-2 text-xs font-semibold text-white transition hover:bg-indigo-500 lg:hidden"
            >
              <ShoppingBag className="h-4 w-4" />
              <span>₹{cart.total.toFixed(0)}</span>
              {cart.items.length > 0 && (
                <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-rose-500 text-[10px] font-bold text-white">
                  {cart.items.reduce((a, b) => a + b.quantity, 0)}
                </span>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Layout */}
      <main className="mx-auto flex w-full max-w-7xl flex-1 gap-6 p-4 sm:p-6">
        {/* Left Column: Chat Conversation Stream */}
        <section className="flex flex-1 flex-col justify-between overflow-hidden rounded-3xl border border-zinc-800/80 bg-zinc-900/60 shadow-xl backdrop-blur-xl">
          {/* Chat Messages Feed */}
          <div className="flex-1 space-y-2 overflow-y-auto p-4 sm:p-6">
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

            {/* Typing indicator */}
            {isLoading && (
              <div className="flex items-center gap-3 py-3 text-xs text-zinc-400">
                <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-zinc-900 border border-zinc-800 text-indigo-400">
                  <Sparkles className="h-4 w-4 animate-spin text-indigo-400" />
                </div>
                <div className="flex items-center gap-1.5 rounded-2xl bg-zinc-900/80 border border-zinc-800 px-3 py-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-indigo-400 dot-1"></span>
                  <span className="h-1.5 w-1.5 rounded-full bg-indigo-400 dot-2"></span>
                  <span className="h-1.5 w-1.5 rounded-full bg-indigo-400 dot-3"></span>
                  <span className="ml-2 font-medium text-xs text-zinc-400">
                    AI agent is searching catalog & evaluating budget...
                  </span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Chat Input Bar */}
          <div className="border-t border-zinc-800/80 bg-zinc-950/60 p-4">
            <ChatInput
              onSendMessage={handleSendMessage}
              isLoading={isLoading}
              onSuggestionClick={(s) => handleSendMessage(s.replace(/^[^\s]+ /, ""))}
            />
          </div>
        </section>

        {/* Right Column: Sticky Cart Sidebar (Desktop) */}
        <aside className="hidden w-80 shrink-0 lg:block xl:w-96">
          <div className="sticky top-20 h-[calc(100vh-110px)]">
            <CartSidebar
              cart={cart}
              onUpdateQuantity={handleUpdateQuantity}
              onRemoveItem={handleRemoveItem}
              onClearCart={handleClearCart}
              onCheckout={handleCheckout}
              isLoading={isLoading}
              isCheckingOut={isCheckingOut}
              activePaymentLink={activePaymentLink}
              orderPaid={orderPaid}
            />
          </div>
        </aside>
      </main>

      {/* Mobile Cart Drawer */}
      {showMobileCart && (
        <div className="fixed inset-0 z-50 flex items-end bg-black/70 backdrop-blur-sm lg:hidden">
          <div className="h-[80vh] w-full rounded-t-3xl bg-zinc-900 border-t border-zinc-800 p-4 shadow-2xl">
            <div className="mb-3 flex justify-between items-center pb-2 border-b border-zinc-800">
              <span className="text-sm font-bold text-zinc-100">Shopping Cart</span>
              <button
                onClick={() => setShowMobileCart(false)}
                className="text-xs font-semibold text-zinc-400 hover:text-white"
              >
                Close ✕
              </button>
            </div>
            <CartSidebar
              cart={cart}
              onUpdateQuantity={handleUpdateQuantity}
              onRemoveItem={handleRemoveItem}
              onClearCart={handleClearCart}
              onCheckout={handleCheckout}
              isLoading={isLoading}
              isCheckingOut={isCheckingOut}
              activePaymentLink={activePaymentLink}
              orderPaid={orderPaid}
            />
          </div>
        </div>
      )}
    </div>
  );
}
