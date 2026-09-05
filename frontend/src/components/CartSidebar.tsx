"use client";

import React, { useState } from "react";
import Image from "next/image";
import {
  ShoppingBag,
  Trash2,
  Plus,
  Minus,
  ArrowRight,
  CreditCard,
  Loader2,
  CheckCircle2,
  ShieldCheck,
  Truck,
  Store,
  MapPin,
  Clock,
} from "lucide-react";
import Link from "next/link";
import { CartItem, resolvePaymentUrl } from "@/lib/api";

interface CartSidebarProps {
  cart: {
    items: CartItem[];
    total: number;
  };
  merchantName?: string;
  onUpdateQuantity: (productId: string, delta: number) => void;
  onRemoveItem: (productId: string) => void;
  onClearCart?: () => void;
  onCheckout?: (fulfillment: {
    mode: "delivery" | "pickup";
    address?: string;
    pickupTime?: string;
  }) => void;
  isLoading?: boolean;
  isCheckingOut?: boolean;
  activeOrderId?: string | null;
  activePaymentLink?: string | null;
  orderPaid?: boolean;
  onPayClick?: (url?: string | null) => void;
}

const QUICK_ADDRESSES = [
  "Bellandur, Bangalore",
  "Koramangala 4th Block, Bangalore",
  "Indiranagar, Bangalore",
  "HSR Layout, Bangalore",
];

const PICKUP_TIMES = [
  "⚡ Ready in 20-30 mins",
  "🕐 Today, 4:00 PM – 5:00 PM",
  "🕐 Today, 6:30 PM – 7:30 PM",
  "📅 Tomorrow, 10:00 AM",
];

export function CartSidebar({
  cart,
  merchantName = "All Stores",
  onUpdateQuantity,
  onRemoveItem,
  onClearCart,
  onCheckout,
  isLoading = false,
  isCheckingOut = false,
  activeOrderId,
  activePaymentLink,
  orderPaid = false,
  onPayClick,
}: CartSidebarProps) {
  const [fulfillmentMode, setFulfillmentMode] = useState<"delivery" | "pickup">("delivery");
  const [deliveryAddress, setDeliveryAddress] = useState(QUICK_ADDRESSES[0]);
  const [pickupTime, setPickupTime] = useState(PICKUP_TIMES[0]);
  const [customAddress, setCustomAddress] = useState("");

  const items = cart.items || [];
  const total = cart.total || 0;
  const itemCount = items.reduce((acc, i) => acc + (i.quantity || 1), 0);

  const itemsByMerchant = React.useMemo(() => {
    const map = new Map<string, CartItem[]>();
    for (const it of items) {
      const mName = it.merchant_name || merchantName || "Bangalore Store";
      if (!map.has(mName)) {
        map.set(mName, []);
      }
      map.get(mName)!.push(it);
    }
    return map;
  }, [items, merchantName]);

  const isMultiStore = itemsByMerchant.size > 1;

  const handleCheckoutClick = () => {
    if (!items || items.length === 0) return;
    if (!onCheckout) return;
    onCheckout({
      mode: fulfillmentMode,
      address: fulfillmentMode === "delivery" ? (customAddress.trim() || deliveryAddress) : undefined,
      pickupTime: fulfillmentMode === "pickup" ? pickupTime : undefined,
    });
  };

  return (
    <div className="flex h-full flex-col justify-between rounded-3xl border border-white/[0.08] bg-[#0D0F18]/90 p-4.5 shadow-2xl backdrop-blur-2xl">
      {/* 1. Header & Cart Items Area */}
      <div>
        <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8.5 w-8.5 items-center justify-center rounded-xl bg-white/[0.04] border border-white/[0.08] text-zinc-200 shadow-sm">
              <ShoppingBag className="h-4 w-4" />
            </div>
            <div>
              <h3 className="font-semibold text-xs sm:text-sm text-zinc-100">
                Cart
              </h3>
              <p className="text-[10px] text-zinc-400">
                {itemCount} {itemCount === 1 ? "item" : "items"} • {isMultiStore ? "Dual-Store Cart" : merchantName}
              </p>
            </div>
          </div>

          {items.length > 0 && onClearCart && !orderPaid && (
            <button
              onClick={onClearCart}
              className="text-[11px] font-medium text-zinc-400 transition-colors hover:text-rose-400 cursor-pointer"
            >
              Clear
            </button>
          )}
        </div>

        {/* Item List Scroll Area */}
        <div className="mt-3 max-h-[calc(100vh-450px)] space-y-2 overflow-y-auto pr-0.5">
          {orderPaid ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                <CheckCircle2 className="h-7 w-7" />
              </div>
              <p className="mt-2.5 text-xs sm:text-sm font-bold text-emerald-400">
                Payment Confirmed
              </p>
              <p className="mt-1 max-w-[200px] text-[11px] text-zinc-400">
                {fulfillmentMode === "delivery"
                  ? "Your order will be delivered shortly."
                  : "Ready for pickup at store counter."}
              </p>
              {activeOrderId && (
                <Link
                  href={`/orders/${activeOrderId}/tracking`}
                  className="mt-3.5 inline-flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 px-4 py-2 text-xs font-semibold text-white shadow-lg shadow-emerald-900/30 transition hover:from-emerald-500 hover:to-teal-500"
                >
                  <Truck className="h-3.5 w-3.5" />
                  <span>Track Live Delivery</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              )}
            </div>
          ) : items.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-[#1E1E2E] to-[#12121E] border border-[#2A2A3E] text-zinc-500 shadow-inner">
                <ShoppingBag className="h-6 w-6 text-zinc-400" />
              </div>
              <p className="mt-3 text-xs font-semibold text-zinc-300">
                Your cart is empty
              </p>
              <p className="mt-0.5 max-w-[190px] text-[11px] text-zinc-500">
                Ask the AI agent to search Bangalore stores or add items
              </p>
            </div>
          ) : (
            <>
                <div className="flex items-center gap-1.5 rounded-xl bg-purple-500/10 border border-purple-500/20 px-2.5 py-1.5 text-[11px] font-semibold text-purple-300 mb-1">
                  <span className="flex h-1.5 w-1.5 rounded-full bg-purple-400 animate-pulse" />
                  <span>
                    {itemsByMerchant.size > 2
                      ? `Multi-Kitchen Order • ${itemsByMerchant.size} Stores (Unified Checkout)`
                      : `Dual-Kitchen Order • ${itemsByMerchant.size} Stores (Unified Checkout)`}
                  </span>
                </div>
              {Array.from(itemsByMerchant.entries()).map(([storeName, storeItems]) => (
                <div key={storeName} className="space-y-1.5 mb-2.5 last:mb-0">
                  {isMultiStore && (
                    <div className="flex items-center justify-between px-2 py-1 rounded-lg bg-white/[0.03] border border-white/[0.06] text-[11px] font-semibold text-zinc-300">
                      <span className="flex items-center gap-1.5 text-zinc-200 truncate">
                        <Store className="h-3 w-3 text-purple-400 shrink-0" />
                        <span className="truncate">{storeName}</span>
                      </span>
                      <span className="text-[10px] text-zinc-400 font-mono ml-2 shrink-0">
                        ₹{storeItems.reduce((acc, it) => acc + it.price * it.quantity, 0).toFixed(0)}
                      </span>
                    </div>
                  )}
                  {storeItems.map((item) => (
                    <div
                      key={item.product_id}
                      className="flex items-center justify-between gap-2.5 rounded-2xl border border-[#2A2A3E] bg-[#0A0A12]/60 p-2 transition-all hover:border-[#7C3AED]/30"
                    >
                      {item.image_url && (
                        <div className="relative h-10 w-10 shrink-0 overflow-hidden rounded-xl bg-[#1E1E2E]">
                          <Image
                            src={item.image_url}
                            alt={item.name}
                            fill
                            className="object-cover"
                            unoptimized
                          />
                        </div>
                      )}

                      <div className="min-w-0 flex-1">
                        <h5 className="truncate text-xs font-medium text-[#F0EEFF]">
                          {item.name}
                        </h5>
                        <p className="text-xs font-semibold text-[#0891B2]">
                          ₹{(item.price * item.quantity).toFixed(0)}
                        </p>
                      </div>

                      <div className="flex items-center gap-1 rounded-lg border border-[#2A2A3E] bg-[#1E1E2E] px-1 py-0.5">
                        <button
                          onClick={() => onUpdateQuantity(item.product_id, -1)}
                          disabled={isLoading || isCheckingOut}
                          className="flex h-4.5 w-4.5 items-center justify-center rounded text-zinc-400 transition hover:text-white"
                        >
                          <Minus className="h-2.5 w-2.5" />
                        </button>
                        <span className="w-3 text-center text-xs font-medium text-[#F0EEFF]">
                          {item.quantity}
                        </span>
                        <button
                          onClick={() => onUpdateQuantity(item.product_id, 1)}
                          disabled={isLoading || isCheckingOut}
                          className="flex h-4.5 w-4.5 items-center justify-center rounded text-zinc-400 transition hover:text-white"
                        >
                          <Plus className="h-2.5 w-2.5" />
                        </button>
                      </div>

                      <button
                        onClick={() => onRemoveItem(item.product_id)}
                        disabled={isCheckingOut}
                        className="p-1 text-zinc-500 transition hover:text-rose-400"
                        title="Remove"
                      >
                        <Trash2 className="h-3 w-3" />
                      </button>
                    </div>
                  ))}
                </div>
              ))}
            </>
          )}
        </div>
      </div>

      {/* 2. Fulfillment Mode Selector & Razorpay Checkout Footer */}
      <div className="border-t border-[#2A2A3E] pt-3 space-y-2.5">
        {/* Fulfillment Mode Toggle */}
        {!orderPaid && items.length > 0 && (
          <div className="space-y-1.5">
            <div className="grid grid-cols-2 gap-1 p-1 rounded-2xl bg-[#0A0A12] border border-[#2A2A3E]">
              {/* Option A: Delivery */}
              <button
                type="button"
                onClick={() => setFulfillmentMode("delivery")}
                className={`flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-xl text-xs font-semibold transition-all ${
                  fulfillmentMode === "delivery"
                    ? "bg-[#7C3AED] text-white shadow-sm shadow-[#7C3AED]/30"
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                <Truck className="h-3 w-3" />
                <span>Delivery</span>
              </button>

              {/* Option B: Pickup */}
              <button
                type="button"
                onClick={() => setFulfillmentMode("pickup")}
                className={`flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-xl text-xs font-semibold transition-all ${
                  fulfillmentMode === "pickup"
                    ? "bg-[#0891B2] text-white shadow-sm shadow-[#0891B2]/30"
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                <Store className="h-3 w-3" />
                <span>Pickup</span>
              </button>
            </div>

            {/* Sub-Panel: Delivery Address Input */}
            {fulfillmentMode === "delivery" && (
              <div className="rounded-xl border border-[#2A2A3E] bg-[#0A0A12]/60 p-2 space-y-1.5">
                <div className="flex items-center justify-between text-[10px] text-zinc-400">
                  <span className="flex items-center gap-1 font-medium">
                    <MapPin className="h-2.5 w-2.5 text-[#A78BFA]" />
                    Address
                  </span>
                  <span className="text-emerald-400 font-medium">Free Delivery</span>
                </div>
                <input
                  type="text"
                  value={customAddress || deliveryAddress}
                  onChange={(e) => setCustomAddress(e.target.value)}
                  placeholder="Enter delivery address..."
                  className="w-full rounded-lg bg-[#12121E] border border-[#2A2A3E] px-2 py-1 text-xs text-[#F0EEFF] placeholder-zinc-500 outline-none focus:border-[#7C3AED]"
                />
                <div className="flex items-center gap-1 overflow-x-auto text-[10px] no-scrollbar">
                  {QUICK_ADDRESSES.map((addr, idx) => (
                    <button
                      key={idx}
                      onClick={() => {
                        setDeliveryAddress(addr);
                        setCustomAddress("");
                      }}
                      className="shrink-0 rounded bg-[#1E1E2E] border border-[#2A2A3E] px-1.5 py-0.5 text-zinc-400 hover:text-zinc-200"
                    >
                      {addr.split(",")[0]}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Sub-Panel: Store Pickup Details */}
            {fulfillmentMode === "pickup" && (
              <div className="rounded-xl border border-[#0891B2]/30 bg-[#0891B2]/10 p-2 space-y-1.5">
                <div className="flex items-center justify-between text-[10px] text-[#0891B2]">
                  <span className="flex items-center gap-1 font-medium">
                    <Clock className="h-2.5 w-2.5 text-[#0891B2]" />
                    Pickup Time
                  </span>
                  <span className="text-emerald-400 font-medium">No Wait</span>
                </div>
                <select
                  value={pickupTime}
                  onChange={(e) => setPickupTime(e.target.value)}
                  className="w-full rounded-lg bg-[#12121E] border border-[#0891B2]/40 px-2 py-1 text-xs text-[#F0EEFF] outline-none focus:border-[#0891B2]"
                >
                  {PICKUP_TIMES.map((time, idx) => (
                    <option key={idx} value={time}>
                      {time}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        )}

        {/* Pricing Summary */}
        <div className="space-y-1 text-xs text-zinc-400 pt-0.5">
          <div className="flex justify-between">
            <span>Subtotal</span>
            <span className="font-mono">₹{total.toFixed(0)}</span>
          </div>
          <div className="flex justify-between border-t border-dashed border-white/[0.08] pt-1.5 text-xs sm:text-sm font-bold text-zinc-100">
            <span>Total</span>
            <span className="text-emerald-400 font-mono">₹{total.toFixed(0)}</span>
          </div>
        </div>

        {/* Razorpay Checkout CTA (21st.dev Style) */}
        {activePaymentLink ? (
          <button
            type="button"
            onClick={() => onPayClick?.(activePaymentLink)}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-emerald-500 via-emerald-600 to-teal-600 py-2.5 text-xs font-bold text-white shadow-[0_0_24px_-4px_rgba(16,185,129,0.4),inset_0_1px_0_0_rgba(255,255,255,0.25)] border border-emerald-400/30 transition-all hover:brightness-110 active:scale-[0.98] cursor-pointer"
          >
            <CreditCard className="h-3.5 w-3.5" />
            <span>Complete Payment</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        ) : (
          <button
            onClick={handleCheckoutClick}
            disabled={items.length === 0 || isLoading || isCheckingOut || orderPaid}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 via-indigo-700 to-purple-800 hover:from-indigo-500 hover:to-purple-700 py-2.5 text-xs font-bold text-white shadow-[0_0_20px_-3px_rgba(99,102,241,0.35),inset_0_1px_0_0_rgba(255,255,255,0.2)] border border-indigo-400/30 transition-all active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40 cursor-pointer"
          >
            {isCheckingOut ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                <span>Processing Order...</span>
              </>
            ) : (
              <>
                <CreditCard className="h-3.5 w-3.5" />
                <span>
                  {isMultiStore
                    ? itemsByMerchant.size > 2
                      ? `Checkout All ${itemsByMerchant.size} Orders (₹${total.toFixed(0)})`
                      : `Checkout Both Orders (₹${total.toFixed(0)})`
                    : `Pay ₹${total.toFixed(0)}`}
                </span>
                <ArrowRight className="h-3.5 w-3.5" />
              </>
            )}
          </button>
        )}

        <div className="flex items-center justify-center gap-1.5 text-[10px] text-zinc-500">
          <ShieldCheck className="h-3 w-3 text-emerald-500" />
          <span>Secured by Razorpay • 256-bit Encrypted</span>
        </div>
      </div>
    </div>
  );
}
