"use client";

import React from "react";
import Image from "next/image";
import { ShoppingBag, Trash2, Plus, Minus, ArrowRight, Sparkles, CreditCard, Loader2, CheckCircle2, ShieldCheck } from "lucide-react";
import { CartItem } from "@/lib/api";

interface CartSidebarProps {
  cart: {
    items: CartItem[];
    total: number;
  };
  onUpdateQuantity: (productId: string, delta: number) => void;
  onRemoveItem: (productId: string) => void;
  onClearCart?: () => void;
  onCheckout?: () => void;
  isLoading?: boolean;
  isCheckingOut?: boolean;
  activePaymentLink?: string | null;
  orderPaid?: boolean;
}

export function CartSidebar({
  cart,
  onUpdateQuantity,
  onRemoveItem,
  onClearCart,
  onCheckout,
  isLoading = false,
  isCheckingOut = false,
  activePaymentLink,
  orderPaid = false,
}: CartSidebarProps) {
  const items = cart.items || [];
  const total = cart.total || 0;
  const itemCount = items.reduce((acc, i) => acc + (i.quantity || 1), 0);

  return (
    <div className="flex h-full flex-col justify-between rounded-3xl border border-zinc-800/80 bg-zinc-900/90 p-5 shadow-xl backdrop-blur-xl">
      {/* Header */}
      <div>
        <div className="flex items-center justify-between border-b border-zinc-800 pb-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <ShoppingBag className="h-4.5 w-4.5" />
            </div>
            <div>
              <h3 className="font-semibold text-sm text-zinc-100">
                Your Shopping Cart
              </h3>
              <p className="text-xs text-zinc-400">
                {itemCount} {itemCount === 1 ? "item" : "items"}
              </p>
            </div>
          </div>

          {items.length > 0 && onClearCart && (
            <button
              onClick={onClearCart}
              className="text-xs font-medium text-zinc-400 transition-colors hover:text-red-400"
            >
              Clear
            </button>
          )}
        </div>

        {/* Item List */}
        <div className="mt-4 max-h-[calc(100vh-380px)] space-y-3 overflow-y-auto pr-1">
          {orderPaid ? (
            <div className="flex flex-col items-center justify-center py-10 text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                <CheckCircle2 className="h-8 w-8" />
              </div>
              <p className="mt-3 text-sm font-bold text-emerald-400">
                Payment Confirmed!
              </p>
              <p className="mt-1 max-w-[200px] text-xs text-zinc-400">
                Your order is confirmed and being prepared by the merchant.
              </p>
            </div>
          ) : items.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-zinc-800/80 border border-zinc-700/50 text-zinc-500">
                <ShoppingBag className="h-8 w-8" />
              </div>
              <p className="mt-3 text-sm font-medium text-zinc-300">
                Your cart is empty
              </p>
              <p className="mt-1 max-w-[220px] text-xs text-zinc-400">
                Tell the AI what you crave or your budget to add items!
              </p>
            </div>
          ) : (
            items.map((item) => (
              <div
                key={item.product_id}
                className="flex items-center justify-between gap-3 rounded-2xl border border-zinc-800 bg-zinc-950/60 p-3 transition-all hover:border-zinc-700"
              >
                {item.image_url && (
                  <div className="relative h-12 w-12 shrink-0 overflow-hidden rounded-xl bg-zinc-800">
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
                  <h5 className="truncate text-xs font-medium text-zinc-200">
                    {item.name}
                  </h5>
                  <p className="text-xs font-semibold text-indigo-400">
                    ₹{(item.price * item.quantity).toFixed(0)}
                  </p>
                </div>

                <div className="flex items-center gap-1.5 rounded-lg border border-zinc-700/80 bg-zinc-800 px-1.5 py-1">
                  <button
                    onClick={() => onUpdateQuantity(item.product_id, -1)}
                    disabled={isLoading || isCheckingOut}
                    className="flex h-5 w-5 items-center justify-center rounded text-zinc-400 transition hover:bg-zinc-700 hover:text-white"
                  >
                    <Minus className="h-3 w-3" />
                  </button>
                  <span className="w-4 text-center text-xs font-medium text-zinc-100">
                    {item.quantity}
                  </span>
                  <button
                    onClick={() => onUpdateQuantity(item.product_id, 1)}
                    disabled={isLoading || isCheckingOut}
                    className="flex h-5 w-5 items-center justify-center rounded text-zinc-400 transition hover:bg-zinc-700 hover:text-white"
                  >
                    <Plus className="h-3 w-3" />
                  </button>
                </div>

                <button
                  onClick={() => onRemoveItem(item.product_id)}
                  disabled={isCheckingOut}
                  className="p-1 text-zinc-500 transition hover:text-red-400"
                  title="Remove item"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Footer / Summary */}
      <div className="border-t border-zinc-800 pt-4">
        <div className="space-y-1.5 text-xs text-zinc-400">
          <div className="flex justify-between">
            <span>Subtotal</span>
            <span>₹{total.toFixed(0)}</span>
          </div>
          <div className="flex justify-between">
            <span>Estimated Delivery</span>
            <span className="font-medium text-emerald-400">Free</span>
          </div>
          <div className="flex justify-between border-t border-dashed border-zinc-800 pt-2 text-sm font-bold text-zinc-100">
            <span>Total</span>
            <span className="text-indigo-400">₹{total.toFixed(0)}</span>
          </div>
        </div>

        {/* Razorpay Checkout CTA */}
        {activePaymentLink ? (
          <a
            href={activePaymentLink}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-4 flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 py-3 text-xs font-bold text-white shadow-lg transition-all hover:from-emerald-500 hover:to-teal-500 active:scale-[0.98]"
          >
            <CreditCard className="h-4 w-4" />
            <span>Open Razorpay Payment Link</span>
            <ArrowRight className="h-4 w-4" />
          </a>
        ) : (
          <button
            onClick={onCheckout}
            disabled={items.length === 0 || isLoading || isCheckingOut || orderPaid}
            className="mt-4 flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-indigo-600 to-violet-600 py-3 text-xs font-bold text-white shadow-lg transition-all hover:from-indigo-500 hover:to-violet-500 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40"
          >
            {isCheckingOut ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Creating Razorpay Order...</span>
              </>
            ) : (
              <>
                <CreditCard className="h-4 w-4" />
                <span>Pay ₹{total.toFixed(0)} with Razorpay</span>
                <ArrowRight className="h-4 w-4" />
              </>
            )}
          </button>
        )}

        <div className="mt-3 flex items-center justify-center gap-1.5 text-[11px] text-zinc-500">
          <ShieldCheck className="h-3.5 w-3.5 text-indigo-400" />
          <span>Razorpay Verified Merchant Checkout</span>
        </div>
      </div>
    </div>
  );
}
