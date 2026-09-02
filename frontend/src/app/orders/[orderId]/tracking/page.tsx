"use client";

import React, { useState, useEffect, use } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  CheckCircle2,
  Clock,
  MapPin,
  Phone,
  MessageSquare,
  Navigation,
  ArrowLeft,
  ShoppingBag,
  Sparkles,
  ShieldCheck,
  Truck,
  Store,
  ChevronRight,
  QrCode,
  Copy,
  Receipt,
  Download,
  AlertCircle,
  ChefHat,
  Timer,
  Package,
} from "lucide-react";
import {
  fetchOrder,
  verifyOrderPayment,
  fetchMerchants,
  fetchTrackingData,
  OrderResponse,
  Merchant,
  TrackingData,
} from "@/lib/api";

interface TrackingPageProps {
  params: Promise<{ orderId: string }>;
}

export default function OrderTrackingPage({ params }: TrackingPageProps) {
  const { orderId } = use(params);
  const searchParams = useSearchParams();

  const [order, setOrder] = useState<OrderResponse | null>(null);
  const [merchant, setMerchant] = useState<Merchant | null>(null);
  const [trackingData, setTrackingData] = useState<TrackingData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [showQrModal, setShowQrModal] = useState(false);
  const [showCallModal, setShowCallModal] = useState(false);

  // Derived from tracking data
  const etaMinutes = trackingData?.remaining_eta_minutes ?? 15;
  const simulatedProgress = trackingData?.live_progress_percentage ?? 10;
  const currentStage = trackingData?.current_stage ?? "preparing";
  const driverName = trackingData?.driver_name ?? "Delivery Partner";
  const driverVehicle = trackingData?.driver_vehicle ?? "Electric Scooter";
  const pickupOtp = trackingData?.pickup_otp ?? "0000";
  const prepTime = trackingData?.prep_time_minutes ?? 10;

  // 1. Fetch Order and verify payment if callback params exist
  useEffect(() => {
    async function loadOrderData() {
      try {
        setLoading(true);
        const rzpPaymentId = searchParams.get("razorpay_payment_id");

        let orderData: OrderResponse | null = null;
        if (rzpPaymentId) {
          orderData = await verifyOrderPayment(orderId, rzpPaymentId);
        }

        if (!orderData) {
          orderData = await fetchOrder(orderId);
        }

        if (orderData) {
          setOrder(orderData);
          // Fetch real Haversine telemetry
          const telemetry = await fetchTrackingData(orderId);
          if (telemetry) {
            setTrackingData(telemetry);
          }

          // Fetch merchant info
          const merchants = await fetchMerchants();
          const match = merchants.find((m) => m.id === orderData?.merchant_id);
          if (match) setMerchant(match);
        } else {
          setError("Order not found or still processing.");
        }
      } catch (err: any) {
        console.error("Tracking load error:", err);
        setError("Could not load order tracking details.");
      } finally {
        setLoading(false);
      }
    }

    if (orderId) {
      loadOrderData();
    }
  }, [orderId, searchParams]);

  // 2. Real-time polling every 30 seconds — re-fetch from backend
  useEffect(() => {
    const poll = setInterval(async () => {
      try {
        const telemetry = await fetchTrackingData(orderId);
        if (telemetry) {
          setTrackingData(telemetry);
        }
      } catch (e) {
        // Silently fail on poll errors
      }
    }, 30000);
    return () => clearInterval(poll);
  }, [orderId]);

  const handleCopyOrderId = () => {
    navigator.clipboard.writeText(orderId);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  if (loading) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-zinc-950 text-white p-4 font-sans">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 shadow-xl shadow-indigo-500/10 animate-pulse">
          <Sparkles className="h-8 w-8 animate-spin text-indigo-400" />
        </div>
        <h2 className="mt-5 text-lg font-bold tracking-tight">Locating Your Order...</h2>
        <p className="mt-1 text-xs text-zinc-400">Connecting to store dispatch and fulfillment system</p>
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-zinc-950 text-white p-4 font-sans text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-400">
          <AlertCircle className="h-8 w-8 text-rose-400" />
        </div>
        <h2 className="mt-4 text-xl font-bold">Order Details Unavailable</h2>
        <p className="mt-2 text-sm text-zinc-400 max-w-md">
          {error || "We couldn't locate this order. It might still be processing."}
        </p>
        <Link
          href="/chat"
          className="mt-6 inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-xs font-semibold text-white shadow-lg shadow-indigo-600/30 hover:bg-indigo-500 transition"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Shopping Chat
        </Link>
      </div>
    );
  }

  const isPickup = order.fulfillment_mode === "pickup";
  const items = order.items || [];
  const merchantName = merchant?.name || trackingData?.store_name || "Store";
  const storeAddress = trackingData?.store_address || "Bangalore";
  const distanceKm = trackingData?.haversine_distance_km ?? 0;
  const formattedDate = new Date(order.created_at || Date.now()).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  // ═══════════════════════════════════════════════════════════════
  // PICKUP ORDER VIEW
  // ═══════════════════════════════════════════════════════════════
  if (isPickup) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100 font-sans selection:bg-indigo-500 selection:text-white pb-16">
        {/* Background glow */}
        <div className="fixed top-0 left-1/2 -translate-x-1/2 h-[380px] w-[800px] bg-gradient-to-tr from-amber-600/15 via-indigo-600/15 to-violet-600/10 blur-[150px] pointer-events-none rounded-full" />

        {/* Navbar */}
        <header className="sticky top-0 z-30 border-b border-zinc-800/80 bg-zinc-950/80 backdrop-blur-md">
          <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3 sm:px-6">
            <div className="flex items-center gap-3">
              <Link href="/chat" className="flex h-9 w-9 items-center justify-center rounded-xl bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white hover:border-zinc-700 transition" title="Back">
                <ArrowLeft className="h-4 w-4" />
              </Link>
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-amber-500 to-orange-600 text-white shadow-md">
                <Store className="h-4.5 w-4.5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-sm font-bold tracking-tight text-zinc-100">Store Pickup</h1>
                  <span className="inline-flex items-center gap-1 rounded-full bg-amber-950/80 border border-amber-500/40 px-2 py-0.5 text-[10px] font-semibold text-amber-400">
                    <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-ping"></span>
                    {currentStage === "ready_for_pickup" ? "Ready!" : "Preparing"}
                  </span>
                </div>
                <p className="text-[11px] text-zinc-400">
                  Order <span className="font-mono text-zinc-300 font-medium">#{order.id.slice(0, 8)}</span> • {merchantName}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button onClick={handleCopyOrderId} className="flex items-center gap-1.5 rounded-xl border border-zinc-800 bg-zinc-900/90 px-3 py-1.5 text-xs font-semibold text-zinc-300 hover:border-zinc-700 transition" title="Copy Order ID">
                {copied ? <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5 text-zinc-400" />}
                <span>{copied ? "Copied" : "Order ID"}</span>
              </button>
            </div>
          </div>
        </header>

        <main className="mx-auto max-w-5xl px-4 py-6 sm:px-6 space-y-6">
          {/* HERO — Pickup Status */}
          <section className="relative overflow-hidden rounded-3xl border border-zinc-800 bg-gradient-to-b from-zinc-900/90 to-zinc-900/50 p-6 shadow-2xl backdrop-blur-2xl">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
              <div className="space-y-2">
                <div className="inline-flex items-center gap-2 rounded-full bg-emerald-500/10 border border-emerald-500/30 px-3 py-1 text-xs font-semibold text-emerald-400">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  <span>Payment Confirmed via Razorpay ({order.rzp_payment_id || "Verified"})</span>
                </div>

                <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
                  {currentStage === "ready_for_pickup"
                    ? "Your order is Ready! 🎉"
                    : currentStage === "almost_ready"
                    ? `Almost Ready — ~${etaMinutes} min left ⏳`
                    : `Preparing — Ready in ~${etaMinutes} mins 🔥`}
                </h2>
                <p className="text-sm text-zinc-400 mt-1">
                  {currentStage === "ready_for_pickup"
                    ? `Head to ${merchantName} counter and show your OTP to collect.`
                    : `Your items are being freshly prepared at ${merchantName} (${storeAddress}).`}
                </p>
              </div>

              {/* OTP Badge */}
              <div className="flex items-center gap-3 rounded-2xl bg-zinc-950/80 border border-amber-500/40 px-5 py-4 shadow-inner">
                <div>
                  <div className="text-[10px] uppercase font-bold tracking-wider text-amber-400">Counter Pickup OTP</div>
                  <div className="text-3xl font-mono font-black text-white tracking-widest">{pickupOtp}</div>
                </div>
                <button onClick={() => setShowQrModal(true)} className="flex h-12 w-12 items-center justify-center rounded-xl bg-amber-600/30 border border-amber-500/50 text-amber-300 hover:bg-amber-600 hover:text-white transition" title="Show Pickup QR">
                  <QrCode className="h-6 w-6" />
                </button>
              </div>
            </div>

            {/* Pickup Progress Steps */}
            <div className="mt-6 pt-6 border-t border-zinc-800/80">
              <div className="relative h-2 w-full rounded-full bg-zinc-800 overflow-hidden">
                <div
                  className="absolute top-0 left-0 h-full bg-gradient-to-r from-amber-500 via-orange-500 to-emerald-500 transition-all duration-1000 ease-out"
                  style={{ width: `${currentStage === "ready_for_pickup" ? 100 : currentStage === "almost_ready" ? 70 : 35}%` }}
                />
              </div>

              <div className="mt-4 grid grid-cols-4 text-center text-xs font-semibold">
                {/* Step 1: Order Placed */}
                <div className="space-y-1 text-emerald-400">
                  <div className="mx-auto flex h-6 w-6 items-center justify-center rounded-full bg-emerald-500/20 border border-emerald-500 text-[10px]">✓</div>
                  <div className="text-[11px]">Order Placed</div>
                  <div className="text-[10px] text-zinc-500 font-normal">{formattedDate}</div>
                </div>

                {/* Step 2: Preparing */}
                <div className={`space-y-1 ${currentStage === "preparing" ? "text-amber-400 font-bold" : "text-emerald-400"}`}>
                  <div className={`mx-auto flex h-6 w-6 items-center justify-center rounded-full ${currentStage === "preparing" ? "bg-amber-500/20 border border-amber-500 animate-pulse" : "bg-emerald-500/20 border border-emerald-500"} text-[10px]`}>
                    {currentStage === "preparing" ? "🔥" : "✓"}
                  </div>
                  <div className="text-[11px]">Preparation</div>
                  <div className="text-[10px] text-zinc-500 font-normal">~{prepTime} min</div>
                </div>

                {/* Step 3: Almost Ready */}
                <div className={`space-y-1 ${currentStage === "almost_ready" ? "text-orange-400 font-bold" : currentStage === "ready_for_pickup" ? "text-emerald-400" : "text-zinc-500"}`}>
                  <div className={`mx-auto flex h-6 w-6 items-center justify-center rounded-full ${currentStage === "almost_ready" ? "bg-orange-500/20 border border-orange-500 animate-pulse" : currentStage === "ready_for_pickup" ? "bg-emerald-500/20 border border-emerald-500" : "bg-zinc-800 border border-zinc-700"} text-[10px]`}>
                    {currentStage === "almost_ready" ? "⏳" : currentStage === "ready_for_pickup" ? "✓" : "3"}
                  </div>
                  <div className="text-[11px]">Almost Ready</div>
                  <div className="text-[10px] text-zinc-500 font-normal">Final packing</div>
                </div>

                {/* Step 4: Ready for Pickup */}
                <div className={`space-y-1 ${currentStage === "ready_for_pickup" ? "text-emerald-400 font-bold" : "text-zinc-500"}`}>
                  <div className={`mx-auto flex h-6 w-6 items-center justify-center rounded-full ${currentStage === "ready_for_pickup" ? "bg-emerald-500/20 border border-emerald-500 animate-pulse" : "bg-zinc-800 border border-zinc-700"} text-[10px]`}>
                    {currentStage === "ready_for_pickup" ? "✅" : "🏪"}
                  </div>
                  <div className="text-[11px]">Ready!</div>
                  <div className="text-[10px] text-zinc-500 font-normal">Collect at counter</div>
                </div>
              </div>
            </div>
          </section>

          {/* Store Info Card */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="rounded-3xl border border-zinc-800 bg-zinc-900/90 p-5 shadow-xl space-y-4">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-400">
                  <Store className="h-6 w-6" />
                </div>
                <div>
                  <h4 className="font-bold text-sm text-zinc-100">{merchantName}</h4>
                  <p className="text-[11px] text-zinc-400">{storeAddress}</p>
                </div>
              </div>

              <div className="space-y-2 text-xs text-zinc-300 border-t border-zinc-800 pt-3">
                <div className="flex justify-between">
                  <span className="text-zinc-500">Prep Time:</span>
                  <span className="font-semibold text-white">~{prepTime} mins ({items.length} item{items.length !== 1 ? "s" : ""})</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Pickup OTP:</span>
                  <span className="font-semibold text-amber-400 font-mono">{pickupOtp}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Instructions:</span>
                  <span className="text-zinc-300">Show OTP at billing counter</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <button onClick={() => setShowQrModal(true)} className="flex items-center justify-center gap-2 rounded-xl bg-amber-600 hover:bg-amber-500 py-2.5 text-xs font-semibold text-white shadow-md transition">
                  <QrCode className="h-4 w-4" />
                  <span>Show QR Code</span>
                </button>
                <a
                  href={`https://maps.google.com/?q=${encodeURIComponent(`${merchantName} ${storeAddress}`)}`}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center justify-center gap-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 py-2.5 text-xs font-semibold text-zinc-200 border border-zinc-700 transition"
                >
                  <MapPin className="h-4 w-4 text-indigo-400" />
                  <span>Get Directions</span>
                </a>
              </div>
            </div>

            {/* Razorpay Proof Card */}
            <div className="rounded-3xl border border-zinc-800 bg-zinc-900/60 p-5 space-y-4">
              <div className="flex items-center justify-between text-xs font-semibold">
                <span className="text-zinc-400 flex items-center gap-1.5">
                  <ShieldCheck className="h-4 w-4 text-indigo-400" />
                  Razorpay Verified Payment
                </span>
                <span className="text-emerald-400 font-mono">Captured</span>
              </div>
              <div className="text-[11px] text-zinc-400 space-y-1 font-mono">
                <div>Payment ID: <span className="text-zinc-200">{order.rzp_payment_id || "Verified"}</span></div>
                <div>Amount Paid: <span className="text-white font-bold">₹{order.total.toFixed(2)}</span></div>
              </div>

              {/* What to bring */}
              <div className="rounded-2xl bg-amber-950/40 border border-amber-500/20 p-3 space-y-2">
                <div className="text-xs font-bold text-amber-400">📋 What to bring:</div>
                <ul className="text-[11px] text-zinc-300 space-y-1 list-disc list-inside">
                  <li>Your <strong className="text-white">OTP: {pickupOtp}</strong> or QR code</li>
                  <li>Photo ID (optional, for high-value orders)</li>
                  <li>A bag for your items</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Order Items */}
          <OrderItemsSection items={items} order={order} />

          {/* Bottom Actions */}
          <BottomActions />
        </main>

        {/* QR Modal */}
        {showQrModal && (
          <QrModal
            orderId={order.id}
            pickupOtp={pickupOtp}
            merchantName={merchantName}
            onClose={() => setShowQrModal(false)}
          />
        )}
      </div>
    );
  }

  // ═══════════════════════════════════════════════════════════════
  // DELIVERY ORDER VIEW
  // ═══════════════════════════════════════════════════════════════
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 font-sans selection:bg-indigo-500 selection:text-white pb-16">
      {/* Background glow gradient */}
      <div className="fixed top-0 left-1/2 -translate-x-1/2 h-[380px] w-[800px] bg-gradient-to-tr from-emerald-600/15 via-indigo-600/15 to-violet-600/10 blur-[150px] pointer-events-none rounded-full" />

      {/* Top Navbar */}
      <header className="sticky top-0 z-30 border-b border-zinc-800/80 bg-zinc-950/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3 sm:px-6">
          <div className="flex items-center gap-3">
            <Link href="/chat" className="flex h-9 w-9 items-center justify-center rounded-xl bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white hover:border-zinc-700 transition" title="Back to Chat">
              <ArrowLeft className="h-4 w-4" />
            </Link>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-emerald-500 to-indigo-600 text-white shadow-md">
              <Sparkles className="h-4.5 w-4.5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-sm font-bold tracking-tight text-zinc-100">Live Delivery Tracking</h1>
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-950/80 border border-emerald-500/40 px-2 py-0.5 text-[10px] font-semibold text-emerald-400">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-ping"></span>
                  {currentStage === "preparing" ? "Preparing" : currentStage === "arriving" ? "Arriving!" : "En Route"}
                </span>
              </div>
              <p className="text-[11px] text-zinc-400">
                Order <span className="font-mono text-zinc-300 font-medium">#{order.id.slice(0, 8)}</span> • {merchantName}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button onClick={handleCopyOrderId} className="flex items-center gap-1.5 rounded-xl border border-zinc-800 bg-zinc-900/90 px-3 py-1.5 text-xs font-semibold text-zinc-300 hover:border-zinc-700 transition" title="Copy Order ID">
              {copied ? <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5 text-zinc-400" />}
              <span>{copied ? "Copied" : "Order ID"}</span>
            </button>
            <Link href="/chat" className="hidden sm:flex items-center gap-1.5 rounded-xl bg-indigo-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-indigo-500 transition shadow-sm">
              <ShoppingBag className="h-3.5 w-3.5" />
              <span>New Order</span>
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-6 sm:px-6 space-y-6">
        {/* HERO STATUS CARD */}
        <section className="relative overflow-hidden rounded-3xl border border-zinc-800 bg-gradient-to-b from-zinc-900/90 to-zinc-900/50 p-6 shadow-2xl backdrop-blur-2xl">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="space-y-2">
              <div className="inline-flex items-center gap-2 rounded-full bg-emerald-500/10 border border-emerald-500/30 px-3 py-1 text-xs font-semibold text-emerald-400">
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>Payment Confirmed via Razorpay ({order.rzp_payment_id || "Verified"})</span>
              </div>

              <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
                {currentStage === "preparing"
                  ? `Being prepared — ${etaMinutes} mins total 🔥`
                  : currentStage === "arriving"
                  ? `Almost there! ~${etaMinutes} min 🏡`
                  : `Arriving in ~${etaMinutes} mins (${distanceKm} km) 🛵`}
              </h2>
              <p className="text-sm text-zinc-400 mt-1">
                {currentStage === "preparing"
                  ? `Your order is being freshly prepared at ${merchantName} (${storeAddress}).`
                  : `${driverName} is en route — ${distanceKm} km from ${merchantName} at ~${trackingData?.average_speed_kmh || 24} km/h.`}
              </p>
            </div>

            {/* Quick Actions */}
            <div className="flex items-center gap-2">
              <button onClick={() => setShowCallModal(true)} className="flex items-center gap-2 rounded-2xl bg-zinc-800 hover:bg-zinc-700 px-4 py-3 text-xs font-semibold text-zinc-100 transition border border-zinc-700">
                <Phone className="h-4 w-4 text-emerald-400" />
                <span>Call Driver</span>
              </button>
              <button onClick={() => alert(`Message sent to ${driverName}: 'Please ring the bell!'`)} className="flex items-center gap-2 rounded-2xl bg-zinc-800 hover:bg-zinc-700 px-4 py-3 text-xs font-semibold text-zinc-100 transition border border-zinc-700">
                <MessageSquare className="h-4 w-4 text-indigo-400" />
                <span>Message</span>
              </button>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mt-6 pt-6 border-t border-zinc-800/80">
            <div className="relative h-2 w-full rounded-full bg-zinc-800 overflow-hidden">
              <div
                className="absolute top-0 left-0 h-full bg-gradient-to-r from-emerald-500 via-indigo-500 to-violet-500 transition-all duration-1000 ease-out"
                style={{ width: `${simulatedProgress}%` }}
              />
            </div>

            <div className="mt-4 grid grid-cols-4 text-center text-xs font-semibold">
              {/* Step 1: Order Placed */}
              <div className="space-y-1 text-emerald-400">
                <div className="mx-auto flex h-6 w-6 items-center justify-center rounded-full bg-emerald-500/20 border border-emerald-500 text-[10px]">✓</div>
                <div className="text-[11px]">Order Placed</div>
                <div className="text-[10px] text-zinc-500 font-normal">{formattedDate}</div>
              </div>

              {/* Step 2: Preparing */}
              <div className={`space-y-1 ${currentStage === "preparing" ? "text-amber-400 font-bold" : "text-emerald-400"}`}>
                <div className={`mx-auto flex h-6 w-6 items-center justify-center rounded-full ${currentStage === "preparing" ? "bg-amber-500/20 border border-amber-500 animate-pulse" : "bg-emerald-500/20 border border-emerald-500"} text-[10px]`}>
                  {currentStage === "preparing" ? "🔥" : "✓"}
                </div>
                <div className="text-[11px]">Preparing</div>
                <div className="text-[10px] text-zinc-500 font-normal">~{prepTime} min prep</div>
              </div>

              {/* Step 3: Out for Delivery */}
              <div className={`space-y-1 ${currentStage === "out_for_delivery" ? "text-indigo-400 font-bold" : currentStage === "arriving" ? "text-emerald-400" : "text-zinc-500"}`}>
                <div className={`mx-auto flex h-6 w-6 items-center justify-center rounded-full ${currentStage === "out_for_delivery" ? "bg-indigo-500/20 border border-indigo-500 animate-pulse" : currentStage === "arriving" ? "bg-emerald-500/20 border border-emerald-500" : "bg-zinc-800 border border-zinc-700"} text-[10px]`}>
                  {currentStage === "out_for_delivery" ? "🛵" : currentStage === "arriving" ? "✓" : "3"}
                </div>
                <div className="text-[11px]">Out for Delivery</div>
                <div className="text-[10px] text-zinc-500 font-normal">{distanceKm > 0 ? `${distanceKm} km` : "On the way"}</div>
              </div>

              {/* Step 4: Delivered */}
              <div className={`space-y-1 ${currentStage === "arriving" ? "text-emerald-400 font-bold" : "text-zinc-500"}`}>
                <div className={`mx-auto flex h-6 w-6 items-center justify-center rounded-full ${currentStage === "arriving" ? "bg-emerald-500/20 border border-emerald-500 animate-pulse" : "bg-zinc-800 border border-zinc-700"} text-[10px]`}>
                  🏡
                </div>
                <div className="text-[11px]">Delivered</div>
                <div className="text-[10px] text-zinc-600 font-normal">ETA ~{etaMinutes} min</div>
              </div>
            </div>
          </div>
        </section>

        {/* GRID: MAP + DRIVER CARD */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Live Map Simulation */}
          <div className="lg:col-span-2 overflow-hidden rounded-3xl border border-zinc-800 bg-zinc-900/80 p-5 shadow-xl flex flex-col justify-between min-h-[320px] relative">
            <div className="absolute inset-0 bg-[#0c1017] pointer-events-none opacity-90">
              <svg className="w-full h-full opacity-20" xmlns="http://www.w3.org/2000/svg">
                <defs>
                  <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                    <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#6366f1" strokeWidth="0.8" />
                  </pattern>
                </defs>
                <rect width="100%" height="100%" fill="url(#grid)" />
                <path d="M 60 220 Q 200 120 400 180 T 700 80" fill="none" stroke="#10b981" strokeWidth="4" strokeDasharray="8 6" className="animate-pulse" />
              </svg>
            </div>

            <div className="relative z-10 flex items-center justify-between">
              <div className="flex items-center gap-2 rounded-xl bg-zinc-900/90 border border-zinc-700/80 px-3 py-1.5 text-xs font-semibold backdrop-blur-md">
                <Navigation className="h-3.5 w-3.5 text-emerald-400 animate-spin" />
                <span>Live GPS Tracking (Bangalore)</span>
              </div>
              <div className="flex items-center gap-1.5 rounded-xl bg-zinc-900/90 border border-zinc-700/80 px-3 py-1.5 text-xs font-semibold text-zinc-300">
                <Clock className="h-3.5 w-3.5 text-indigo-400" />
                <span>ETA: {etaMinutes} Min</span>
              </div>
            </div>

            <div className="relative z-10 my-10 flex items-center justify-between px-6">
              {/* Store Marker */}
              <div className="flex flex-col items-center space-y-1">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-600 text-white shadow-lg shadow-indigo-600/40 border border-indigo-400">
                  <Store className="h-6 w-6" />
                </div>
                <span className="text-[11px] font-bold text-white bg-zinc-900/90 px-2 py-0.5 rounded-md border border-zinc-800 truncate max-w-[120px]">{merchantName}</span>
                <span className="text-[10px] text-zinc-400 truncate max-w-[120px]">{storeAddress.split(",")[0]}</span>
              </div>

              {/* Moving Delivery Icon */}
              <div className="flex flex-col items-center space-y-1 animate-bounce">
                <div className="relative flex h-14 w-14 items-center justify-center rounded-full bg-emerald-500 text-zinc-950 font-bold shadow-2xl shadow-emerald-500/60 border-2 border-white">
                  <Truck className="h-7 w-7" />
                  <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-indigo-600 text-[9px] font-bold text-white">🛵</span>
                </div>
                <span className="text-[11px] font-bold text-emerald-300 bg-emerald-950/90 px-2 py-0.5 rounded-md border border-emerald-500/40">
                  {driverName} ({distanceKm} km)
                </span>
              </div>

              {/* Customer Marker */}
              <div className="flex flex-col items-center space-y-1">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-rose-600 text-white shadow-lg shadow-rose-600/40 border border-rose-400">
                  <MapPin className="h-6 w-6" />
                </div>
                <span className="text-[11px] font-bold text-white bg-zinc-900/90 px-2 py-0.5 rounded-md border border-zinc-800 truncate max-w-[120px]">Your Address</span>
                <span className="text-[10px] text-zinc-400 truncate max-w-[120px]">
                  {trackingData?.delivery_address?.split(",")[0] || order.delivery_address?.split(",")[0] || "Bangalore"}
                </span>
              </div>
            </div>

            {/* Address Bar */}
            <div className="relative z-10 rounded-2xl bg-zinc-900/95 border border-zinc-800 p-3 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-zinc-800 text-indigo-400">
                  <MapPin className="h-4 w-4" />
                </div>
                <div className="text-xs">
                  <div className="font-semibold text-zinc-200">Delivering To:</div>
                  <div className="text-zinc-400 truncate max-w-sm">
                    {order.delivery_address || "Bangalore"}
                  </div>
                </div>
              </div>
              <a href={`https://maps.google.com/?q=${encodeURIComponent(order.delivery_address || "Bangalore")}`} target="_blank" rel="noreferrer" className="flex items-center gap-1 text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition">
                <span>Maps</span>
                <ChevronRight className="h-3.5 w-3.5" />
              </a>
            </div>
          </div>

          {/* Driver Card + Payment */}
          <div className="space-y-4">
            <div className="rounded-3xl border border-zinc-800 bg-zinc-900/90 p-5 shadow-xl space-y-4">
              <div className="flex items-center gap-3.5">
                <div className="h-12 w-12 rounded-2xl bg-gradient-to-tr from-indigo-500 to-violet-600 flex items-center justify-center text-lg font-bold text-white shadow-md">
                  👨🏽‍🚀
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h4 className="font-bold text-sm text-zinc-100">{driverName}</h4>
                    <span className="rounded-md bg-emerald-500/10 text-emerald-400 text-[10px] font-bold px-1.5 py-0.5 border border-emerald-500/20">
                      4.9 ★
                    </span>
                  </div>
                  <p className="text-[11px] text-zinc-400">{driverVehicle}</p>
                </div>
              </div>

              <div className="space-y-2 rounded-2xl bg-zinc-950/60 border border-zinc-800/80 p-3 text-xs">
                <div className="flex items-center gap-2 text-emerald-400 text-[11px] font-semibold">
                  <ShieldCheck className="h-4 w-4" />
                  <span>Vaccinated & Sanitized Delivery</span>
                </div>
                <p className="text-[11px] text-zinc-400">
                  Order is securely sealed in temperature-controlled bag.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-2 pt-1">
                <button onClick={() => setShowCallModal(true)} className="flex items-center justify-center gap-1.5 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 py-2 text-xs font-semibold transition">
                  <Phone className="h-3.5 w-3.5" />
                  <span>Call Driver</span>
                </button>
                <button onClick={() => alert(`Message sent to ${driverName}: 'Please leave at door!'`)} className="flex items-center justify-center gap-1.5 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700 py-2 text-xs font-semibold transition">
                  <MessageSquare className="h-3.5 w-3.5" />
                  <span>Leave Note</span>
                </button>
              </div>
            </div>

            {/* Razorpay Proof Card */}
            <div className="rounded-3xl border border-zinc-800 bg-zinc-900/60 p-4 space-y-2.5">
              <div className="flex items-center justify-between text-xs font-semibold">
                <span className="text-zinc-400 flex items-center gap-1.5">
                  <ShieldCheck className="h-4 w-4 text-indigo-400" />
                  Razorpay Verified Payment
                </span>
                <span className="text-emerald-400 font-mono">Captured</span>
              </div>
              <div className="text-[11px] text-zinc-400 space-y-1 font-mono">
                <div>Payment ID: <span className="text-zinc-200">{order.rzp_payment_id || "Verified"}</span></div>
                <div>Amount Paid: <span className="text-white font-bold">₹{order.total.toFixed(2)}</span></div>
              </div>
            </div>
          </div>
        </div>

        {/* Order Items */}
        <OrderItemsSection items={items} order={order} />

        {/* Bottom Actions */}
        <BottomActions />
      </main>

      {/* Call Driver Modal */}
      {showCallModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-150">
          <div className="w-full max-w-sm rounded-3xl bg-zinc-900 border border-zinc-800 p-6 shadow-2xl text-center space-y-4">
            <div className="flex h-14 w-14 mx-auto items-center justify-center rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
              <Phone className="h-7 w-7 text-emerald-400" />
            </div>
            <h3 className="text-base font-bold text-white">Call Delivery Partner</h3>
            <p className="text-xs text-zinc-400">
              Connected via secure masked call bridge to <strong className="text-zinc-200">{driverName}</strong>.
            </p>
            <div className="rounded-2xl bg-zinc-950 border border-zinc-800 p-3 font-mono text-emerald-400 text-base font-bold">
              +91 98765 43210
            </div>
            <div className="grid grid-cols-2 gap-2">
              <a href="tel:+919876543210" className="flex items-center justify-center gap-1.5 rounded-xl bg-emerald-600 py-2.5 text-xs font-semibold text-white hover:bg-emerald-500 transition">
                <Phone className="h-3.5 w-3.5" />
                <span>Call Now</span>
              </a>
              <button onClick={() => setShowCallModal(false)} className="rounded-xl bg-zinc-800 py-2.5 text-xs font-semibold text-zinc-300 hover:bg-zinc-700 transition">
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// Shared Sub-Components
// ═══════════════════════════════════════════════════════════════

function OrderItemsSection({ items, order }: { items: any[]; order: OrderResponse }) {
  return (
    <section className="rounded-3xl border border-zinc-800 bg-zinc-900/90 p-6 shadow-xl space-y-4">
      <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
        <div className="flex items-center gap-2">
          <Receipt className="h-5 w-5 text-indigo-400" />
          <h3 className="font-bold text-base text-zinc-100">Order Summary ({items.length} {items.length === 1 ? "item" : "items"})</h3>
        </div>
        <span className="text-xs font-semibold text-zinc-400">Total: ₹{order.total.toFixed(0)}</span>
      </div>

      <div className="divide-y divide-zinc-800/60">
        {items.map((item, index) => (
          <div key={index} className="flex items-center justify-between py-3">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-zinc-800 border border-zinc-700 text-base">
                🎂
              </div>
              <div>
                <h5 className="font-semibold text-xs text-zinc-100">{item.name}</h5>
                <p className="text-[10px] text-zinc-500">Qty: {item.quantity} × ₹{item.price}</p>
              </div>
            </div>
            <div className="text-xs font-bold text-zinc-200">
              ₹{(item.price * item.quantity).toFixed(0)}
            </div>
          </div>
        ))}
      </div>

      <div className="border-t border-zinc-800 pt-3 space-y-1.5 text-xs text-zinc-400">
        <div className="flex justify-between">
          <span>Item Subtotal:</span>
          <span className="text-zinc-200">₹{order.subtotal.toFixed(2)}</span>
        </div>
        <div className="flex justify-between">
          <span>Delivery / Service Fee:</span>
          <span className="text-emerald-400 font-semibold">FREE (Promotional)</span>
        </div>
        <div className="flex justify-between text-sm font-bold text-white border-t border-zinc-800/80 pt-2 mt-2">
          <span>Total Paid via Razorpay:</span>
          <span className="text-emerald-400 font-black">₹{order.total.toFixed(2)}</span>
        </div>
      </div>
    </section>
  );
}

function BottomActions() {
  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
      <Link href="/chat" className="w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-2xl bg-indigo-600 hover:bg-indigo-500 px-6 py-3 text-xs font-semibold text-white shadow-lg shadow-indigo-600/30 transition">
        <Sparkles className="h-4 w-4" />
        <span>Chat with AI Concierge / Reorder</span>
      </Link>
      <button onClick={() => window.print()} className="w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-2xl border border-zinc-800 bg-zinc-900 hover:bg-zinc-800 px-5 py-3 text-xs font-semibold text-zinc-300 transition">
        <Download className="h-4 w-4 text-zinc-400" />
        <span>Download Invoice Receipt</span>
      </button>
    </div>
  );
}

function QrModal({ orderId, pickupOtp, merchantName, onClose }: { orderId: string; pickupOtp: string; merchantName: string; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-150">
      <div className="w-full max-w-sm rounded-3xl bg-zinc-900 border border-zinc-800 p-6 shadow-2xl text-center space-y-4">
        <div className="flex justify-between items-center pb-2 border-b border-zinc-800">
          <span className="text-sm font-bold text-zinc-100">Store Pickup QR Badge</span>
          <button onClick={onClose} className="text-zinc-400 hover:text-white text-xs font-bold">✕</button>
        </div>

        <div className="flex flex-col items-center justify-center py-4 bg-white rounded-2xl p-4 shadow-inner">
          <svg className="h-44 w-44" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="100" height="100" fill="white" />
            <rect x="10" y="10" width="30" height="30" fill="black" />
            <rect x="15" y="15" width="20" height="20" fill="white" />
            <rect x="20" y="20" width="10" height="10" fill="black" />
            <rect x="60" y="10" width="30" height="30" fill="black" />
            <rect x="65" y="15" width="20" height="20" fill="white" />
            <rect x="70" y="20" width="10" height="10" fill="black" />
            <rect x="10" y="60" width="30" height="30" fill="black" />
            <rect x="15" y="65" width="20" height="20" fill="white" />
            <rect x="20" y="70" width="10" height="10" fill="black" />
            <rect x="45" y="45" width="10" height="10" fill="black" />
            <rect x="60" y="60" width="10" height="10" fill="black" />
            <rect x="75" y="60" width="15" height="10" fill="black" />
            <rect x="60" y="75" width="10" height="15" fill="black" />
            <rect x="75" y="75" width="15" height="15" fill="black" />
          </svg>
          <span className="mt-2 text-xs font-mono font-bold text-zinc-900">OTP: {pickupOtp} • Order #{orderId.slice(0, 8)}</span>
        </div>

        <p className="text-xs text-zinc-400">
          Present this QR badge or state OTP <strong className="text-white">{pickupOtp}</strong> at {merchantName} counter for instant collection.
        </p>

        <button onClick={onClose} className="w-full rounded-xl bg-amber-600 py-2.5 text-xs font-semibold text-white hover:bg-amber-500 transition">
          Close
        </button>
      </div>
    </div>
  );
}
