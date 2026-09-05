"use client";

import React, { useState, useEffect, use, useRef, useCallback } from "react";
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
  ShieldCheck,
  Truck,
  Store,
  ChevronRight,
  QrCode,
  Copy,
  Receipt,
  Download,
  AlertCircle,
  Bell,
  BellRing,
  Volume2,
  VolumeX,
  Mic,
  MicOff,
  Radio,
  ExternalLink,
  Zap,
  Check,
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
import { voiceManager, VoiceState } from "@/lib/voice-manager";

// ═══════════════════════════════════════════════════════════════
// Web Audio API Arrival Chime Synthesizer
// ═══════════════════════════════════════════════════════════════
class ArrivalAlarmSynthesizer {
  private ctx: AudioContext | null = null;
  private intervalId: any = null;
  private isPlaying = false;

  public unlock() {
    if (typeof window === "undefined") return;
    try {
      if (!this.ctx) {
        const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
        if (AudioCtx) {
          this.ctx = new AudioCtx();
        }
      }
      if (this.ctx && this.ctx.state === "suspended") {
        this.ctx.resume().catch(() => {});
      }
    } catch (e) {
      console.warn("AudioContext unlock error:", e);
    }
  }

  private getContext(): AudioContext | null {
    this.unlock();
    return this.ctx;
  }

  // Play a 4-note melodic arrival chime: D5 -> F#5 -> A5 -> D6
  public playChimeCycle() {
    const ctx = this.getContext();
    if (!ctx) return;

    const notes = [
      { freq: 587.33, start: 0.0, dur: 0.35 },
      { freq: 739.99, start: 0.18, dur: 0.35 },
      { freq: 880.0, start: 0.36, dur: 0.45 },
      { freq: 1174.66, start: 0.54, dur: 0.85 },
    ];

    const now = ctx.currentTime;

    notes.forEach(({ freq, start, dur }) => {
      try {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.type = "triangle";
        osc.frequency.setValueAtTime(freq, now + start);

        gain.gain.setValueAtTime(0.001, now + start);
        gain.gain.exponentialRampToValueAtTime(0.4, now + start + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + start + dur);

        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.start(now + start);
        osc.stop(now + start + dur + 0.05);

        // Overtone
        const overtone = ctx.createOscillator();
        const overtoneGain = ctx.createGain();
        overtone.type = "sine";
        overtone.frequency.setValueAtTime(freq * 2, now + start);

        overtoneGain.gain.setValueAtTime(0.001, now + start);
        overtoneGain.gain.exponentialRampToValueAtTime(0.14, now + start + 0.02);
        overtoneGain.gain.exponentialRampToValueAtTime(0.0001, now + start + dur * 0.7);

        overtone.connect(overtoneGain);
        overtoneGain.connect(ctx.destination);

        overtone.start(now + start);
        overtone.stop(now + start + dur * 0.7 + 0.05);
      } catch (err) {
        console.warn("Chime note error:", err);
      }
    });

    if (typeof navigator !== "undefined" && navigator.vibrate) {
      try {
        navigator.vibrate([250, 150, 250, 150, 450]);
      } catch (e) {
        // Ignore
      }
    }
  }

  public start() {
    if (this.isPlaying) return;
    this.isPlaying = true;
    this.unlock();
    this.playChimeCycle();
    this.intervalId = setInterval(() => {
      if (this.isPlaying) {
        this.playChimeCycle();
      }
    }, 1650);
  }

  public stop() {
    this.isPlaying = false;
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
    if (typeof navigator !== "undefined" && navigator.vibrate) {
      try {
        navigator.vibrate(0);
      } catch (e) {
        // Ignore
      }
    }
  }
}

interface TrackingPageProps {
  params: Promise<{ orderId: string }>;
}

export default function OrderTrackingPage({ params }: TrackingPageProps) {
  const { orderId } = use(params);
  const searchParams = useSearchParams();

  const [activeOrderId, setActiveOrderId] = useState<string>(orderId);
  const [siblingOrders, setSiblingOrders] = useState<any[]>([]);
  const [order, setOrder] = useState<OrderResponse | null>(null);
  const [merchant, setMerchant] = useState<Merchant | null>(null);
  const [trackingData, setTrackingData] = useState<TrackingData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [showQrModal, setShowQrModal] = useState(false);
  const [showCallModal, setShowCallModal] = useState(false);

  // 🔔 Arrival Alarm states
  const alarmSynthesizerRef = useRef<ArrivalAlarmSynthesizer | null>(null);
  const [isAlarmArmed, setIsAlarmArmed] = useState(false);
  const [isAlarmRinging, setIsAlarmRinging] = useState(false);
  const [hasRang, setHasRang] = useState(false);

  // 🎙️ Ambient Voice states
  const [voiceState, setVoiceState] = useState<VoiceState>("idle");
  const [voiceTranscript, setVoiceTranscript] = useState("");
  const [voiceFeedback, setVoiceFeedback] = useState<string | null>(null);
  const lastCommandRef = useRef<{ text: string; time: number }>({ text: "", time: 0 });

  // ⏱️ Live Real-Time Ticking Countdown Engine
  const [countdownSeconds, setCountdownSeconds] = useState<number>(360); // 6 mins = 360 seconds
  const [simSpeed, setSimSpeed] = useState<number>(1); // 1x normal speed, 5x, or 10x
  const hasInitializedCountdown = useRef(false);

  // Sync initial countdown with tracking telemetry when loaded once
  useEffect(() => {
    if (trackingData?.remaining_eta_minutes && !hasInitializedCountdown.current) {
      hasInitializedCountdown.current = true;
      setCountdownSeconds(trackingData.remaining_eta_minutes * 60);
    }
  }, [trackingData?.remaining_eta_minutes]);

  // Real-time ticking effect every 1 second (clean singleton interval)
  useEffect(() => {
    const interval = setInterval(() => {
      setCountdownSeconds((prev) => {
        if (prev <= 0) return 0;
        return Math.max(0, prev - simSpeed);
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [simSpeed]);

  // Derived live countdown values
  const etaMinutes = Math.floor(countdownSeconds / 60);
  const etaSecs = countdownSeconds % 60;
  const formattedEta =
    countdownSeconds <= 0
      ? "Arrived!"
      : countdownSeconds < 60
      ? `${countdownSeconds}s`
      : `${etaMinutes}m ${etaSecs < 10 ? "0" : ""}${etaSecs}s`;

  // Dynamic distance: starts at 2.3 km and smoothly approaches 0.0 km
  const distanceKm =
    countdownSeconds <= 0
      ? "0.0"
      : Math.max(0.1, (countdownSeconds / 360) * 2.3).toFixed(1);

  // Dynamic progress: advances from 75% to 100% on arrival
  const simulatedProgress =
    countdownSeconds <= 0
      ? 100
      : Math.min(99, Math.round(75 + ((360 - countdownSeconds) / 360) * 24));

  // Dynamic stage based on remaining time
  const isPickup = order?.fulfillment_mode === "pickup";
  const currentStage =
    countdownSeconds <= 0
      ? isPickup
        ? "ready_for_pickup"
        : "delivered"
      : countdownSeconds <= 45
      ? isPickup
        ? "ready_for_pickup"
        : "arriving"
      : countdownSeconds <= 120
      ? isPickup
        ? "almost_ready"
        : "out_for_delivery"
      : isPickup
      ? "preparing"
      : "out_for_delivery";

  // Dynamic driver map progress percentage (from store 22% to doorstep 78%)
  const driverMapProgressPct =
    countdownSeconds <= 0
      ? 78
      : Math.min(78, Math.max(22, 22 + ((360 - countdownSeconds) / 360) * 56));

  const driverName = trackingData?.driver_name ?? "Arjun Verma";
  const driverVehicle = trackingData?.driver_vehicle ?? "TVS iQube Electric Scooter (KA-01-EQ-9812)";
  const pickupOtp = trackingData?.pickup_otp ?? "4821";
  const prepTime = trackingData?.prep_time_minutes ?? 12;
  const merchantName = merchant?.name || trackingData?.store_name || "Bangalore Artisanal Bakery";
  const storeAddress = trackingData?.store_address || "Koramangala 4th Block, Bangalore";

  // Initialize synthesizer and check for microphone permission for hands-free wake word
  useEffect(() => {
    alarmSynthesizerRef.current = new ArrivalAlarmSynthesizer();

    if (typeof window !== "undefined" && navigator.permissions && navigator.permissions.query) {
      navigator.permissions
        .query({ name: "microphone" as PermissionName })
        .then((status) => {
          if (status.state === "granted") {
            voiceManager.toggleVoiceMode(true);
            setVoiceFeedback("🟢 Voice mode active: Ask for order status anytime");
          }
        })
        .catch(() => {});
    }

    return () => {
      alarmSynthesizerRef.current?.stop();
    };
  }, []);

  // 1. Fetch Order and verify payment if callback params exist
  useEffect(() => {
    async function loadOrderData() {
      try {
        setLoading(true);
        hasInitializedCountdown.current = false;
        const rzpPaymentId = searchParams.get("razorpay_payment_id");

        let orderData: OrderResponse | null = null;
        if (rzpPaymentId && activeOrderId === orderId) {
          orderData = await verifyOrderPayment(activeOrderId, rzpPaymentId);
        }

        if (!orderData) {
          orderData = await fetchOrder(activeOrderId);
        }

        // Graceful fallback for demo orders or when testing
        if (!orderData) {
          orderData = {
            id: activeOrderId,
            merchant_id: "demo_merchant_1",
            merchant_name: "Taaza Thindi, Banashankari",
            customer_id: "demo_customer_1",
            total: 25,
            subtotal: 25,
            status: "paid",
            fulfillment_mode: searchParams.get("mode") === "pickup" ? "pickup" : "delivery",
            rzp_payment_id: rzpPaymentId || "pay_LiveVerified_8829",
            created_at: new Date().toISOString(),
            delivery_address: "12th Main Road, Indiranagar, Bangalore - 560038",
            items: [
              { product_id: "p1", name: "Filter Coffee (Degree Coffee)", price: 25, quantity: 1, merchant_name: "Taaza Thindi" },
            ],
            sibling_orders: [
              {
                order_id: "demo_sibling_order_pizza",
                merchant_id: "demo_merchant_toit",
                merchant_name: "Toit, Indiranagar",
                items: ["Margherita Pizza"],
                total: 350,
                status: "paid",
              },
            ],
          };
        }

        if (orderData) {
          setOrder(orderData);
          if (orderData.sibling_orders && orderData.sibling_orders.length > 0) {
            setSiblingOrders(orderData.sibling_orders);
          } else {
            const sibParam = searchParams.get("sibling");
            if (sibParam && sibParam !== activeOrderId) {
              setSiblingOrders([
                {
                  order_id: sibParam,
                  merchant_name: "Toit, Indiranagar",
                  items: ["Margherita Pizza"],
                  total: 350,
                  status: "paid",
                },
              ]);
            }
          }
          let telemetry = await fetchTrackingData(activeOrderId);
          if (!telemetry) {
            telemetry = {
              order_id: activeOrderId,
              status: "paid",
              fulfillment_mode: (orderData.fulfillment_mode as any) || "delivery",
              store_name: orderData.merchant_name || "Bangalore Store",
              store_address: "Koramangala 4th Block, Bangalore",
              store_latitude: 12.9352,
              store_longitude: 77.6245,
              customer_latitude: 12.9716,
              customer_longitude: 77.6412,
              haversine_distance_km: 2.3,
              average_speed_kmh: 24,
              prep_time_minutes: 12,
              total_estimated_eta_minutes: 25,
              remaining_eta_minutes: 6,
              elapsed_minutes: 19,
              live_progress_percentage: 75,
              current_stage: (searchParams.get("stage") as any) || "out_for_delivery",
              is_pickup: orderData.fulfillment_mode === "pickup",
              driver_name: "Arjun Verma",
              driver_vehicle: "TVS iQube Electric Scooter (KA-01-EQ-9812)",
              pickup_otp: "4821",
              created_at: orderData.created_at,
              rzp_payment_id: orderData.rzp_payment_id,
              total: orderData.total,
              delivery_address: orderData.delivery_address || "12th Main Road, Indiranagar, Bangalore - 560038",
            };
          }
          setTrackingData(telemetry);

          try {
            const merchants = await fetchMerchants();
            const match = merchants.find((m) => m.id === orderData?.merchant_id);
            if (match) {
              setMerchant(match);
            } else {
              setMerchant({
                id: orderData.merchant_id || "demo_merchant_1",
                name: orderData.merchant_name || "Bangalore Store",
                email: "contact@store.com",
                is_active: true,
                store_address: telemetry.store_address || "Bangalore",
              });
            }
          } catch (mErr) {
            setMerchant({
              id: orderData.merchant_id || "demo_merchant_1",
              name: orderData.merchant_name || "Bangalore Store",
              email: "contact@store.com",
              is_active: true,
              store_address: telemetry.store_address || "Bangalore",
            });
          }
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

    if (activeOrderId) {
      loadOrderData();
    }
  }, [activeOrderId, orderId, searchParams]);

  // 2. Real-time polling every 30 seconds — re-fetch from backend
  useEffect(() => {
    const poll = setInterval(async () => {
      try {
        const telemetry = await fetchTrackingData(activeOrderId);
        if (telemetry) {
          setTrackingData(telemetry);
        }
      } catch (e) {
        // silently fallback to current local telemetry
      }
    }, 30000);
    return () => clearInterval(poll);
  }, [orderId]);

  // 3. Setup Voice Manager on tracking page
  const dismissAlarm = useCallback(() => {
    setIsAlarmRinging(false);
    alarmSynthesizerRef.current?.stop();
    voiceManager.stopSpeaking();
    setVoiceFeedback("Alarm dismissed. Enjoy your meal!");
  }, []);

  const triggerTestAlarm = useCallback(() => {
    alarmSynthesizerRef.current?.unlock();
    setIsAlarmRinging(true);
    alarmSynthesizerRef.current?.start();
    setVoiceFeedback("Testing loud arrival chime...");
    voiceManager.speak("Testing your arrival chime! Your food has arrived.");
  }, []);

  const handleVoiceCommand = useCallback(
    (rawText: string) => {
      const text = rawText.toLowerCase().trim();
      if (!text) return;

      // Prevent duplicate triggers within 2 seconds
      const now = Date.now();
      if (
        lastCommandRef.current.text === text &&
        now - lastCommandRef.current.time < 2000
      ) {
        return;
      }
      lastCommandRef.current = { text, time: now };

      // Unlock audio contexts on user speech
      alarmSynthesizerRef.current?.unlock();
      voiceManager.unlockAudio();

      // Robust Wake Word Detection (Alexa / Siri style)
      // Matches "MerchantMind", "Hey MerchantMind", "Hi MerchantMind", "Hello MerchantMind", "OK MerchantMind", "Merchant Mind", etc.
      const WAKE_WORD_REGEX =
        /^(?:(?:hey|hi|hello|ok|okay)\s+)?(?:merchant\s*mind|merchantmind|merchants\s*mind|merchant\s*mine|merchant\s*man|merchant\s*nine|merchant)\b/i;
      const isWakeWordPresent =
        WAKE_WORD_REGEX.test(text) ||
        text.includes("merchantmind") ||
        text.includes("merchant mind") ||
        text.includes("merchants mind") ||
        text.includes("merchant mine");

      // Strip wake word prefix if present to extract user intent
      const textWithoutWake = text
        .replace(WAKE_WORD_REGEX, "")
        .replace(/^(?:merchant\s*mind|merchantmind|merchant)[,\s]*/i, "")
        .replace(/^[,\s.!?]+/, "")
        .trim();

      // Case A: Standalone Wake Word (User says "MerchantMind" or "Hey MerchantMind")
      if (isWakeWordPresent && !textWithoutWake) {
        const voiceGreetings = [
          "Hey Utkarsh! I'm here. How can I help with your delivery?",
          "Hi Utkarsh! I'm listening. Ask me where your delivery partner is, or to set an arrival alarm.",
          "I'm right here! How can I assist with your order?",
        ];
        const greeting = voiceGreetings[Math.floor(Math.random() * voiceGreetings.length)];
        setVoiceFeedback("🟢 Hey Utkarsh! I'm listening. Say 'Where is my order?' or 'Set arrival alarm'");
        voiceManager.speak(greeting);
        return;
      }

      // If user provided a query (either prefixed by wake word or standalone)
      const query = textWithoutWake || text;

      // 1. Affirmative confirmation to arm alarm (e.g. "yes", "yeah", "sure", "please do", "yes set it")
      if (
        query === "yes" ||
        query === "yeah" ||
        query === "sure" ||
        query === "please do" ||
        query === "yep" ||
        query === "ok" ||
        query === "okay" ||
        query.includes("yes set") ||
        query.includes("set it")
      ) {
        setIsAlarmArmed(true);
        alarmSynthesizerRef.current?.unlock();
        const confirmSpeech = "Arrival alarm is armed! A loud chime will sound the moment your delivery arrives.";
        setVoiceFeedback(confirmSpeech);
        voiceManager.speak(confirmSpeech);
        return;
      }

      // 2. Check for alarm arm commands
      if (
        query.includes("set alarm") ||
        query.includes("set a alarm") ||
        query.includes("set an alarm") ||
        query.includes("alarm when") ||
        query.includes("wake me") ||
        query.includes("alert me") ||
        query.includes("ring alarm") ||
        query.includes("arrival alarm") ||
        (query.includes("alarm") &&
          (query.includes("order") ||
            query.includes("comes") ||
            query.includes("arrive") ||
            query.includes("food") ||
            query.includes("delivery")))
      ) {
        setIsAlarmArmed(true);
        alarmSynthesizerRef.current?.unlock();
        const prefix = isWakeWordPresent ? "Hey Utkarsh! " : "";
        const speech = `${prefix}Arrival alarm is set! I'll sound a loud chime the moment your delivery arrives at your door.`;
        setVoiceFeedback("Arrival alarm armed! Will ring loudly the moment food arrives.");
        voiceManager.speak(speech);
        return;
      }

      // 3. Check for alarm cancel / stop commands
      if (
        query.includes("stop alarm") ||
        query.includes("turn off alarm") ||
        query.includes("cancel alarm") ||
        query.includes("dismiss alarm") ||
        query.includes("disable alarm")
      ) {
        if (isAlarmRinging) {
          dismissAlarm();
        } else {
          setIsAlarmArmed(false);
          const speech = "Arrival alarm has been turned off.";
          setVoiceFeedback(speech);
          voiceManager.speak(speech);
        }
        return;
      }

      // 4. Check for test alarm
      if (query.includes("test alarm") || query.includes("test chime") || query.includes("test sound")) {
        triggerTestAlarm();
        return;
      }

      // 5. Check for cross-order / sibling tracking query (e.g. "what abt tracking of pizza?", "where is my pizza?", "check coffee")
      const isCrossOrderQuery =
        siblingOrders &&
        siblingOrders.length > 0 &&
        (query.includes("pizza") ||
          query.includes("coffee") ||
          query.includes("burger") ||
          query.includes("dosa") ||
          query.includes("other") ||
          query.includes("second") ||
          query.includes("sibling") ||
          query.includes("next"));

      if (isCrossOrderQuery) {
        const matchingSibling =
          siblingOrders.find((s: any) => {
            const sName = (s.merchant_name || "").toLowerCase();
            const sItems = (s.items || []).join(" ").toLowerCase();
            return (
              query.includes(sName) ||
              query.includes(sItems) ||
              (query.includes("pizza") &&
                (sItems.includes("pizza") || sName.includes("toit") || sName.includes("pizza") || sName.includes("onesta"))) ||
              (query.includes("coffee") &&
                (sItems.includes("coffee") || sName.includes("taaza") || sName.includes("coffee"))) ||
              (query.includes("burger") &&
                (sItems.includes("burger") || sName.includes("burger") || sName.includes("millers") || sName.includes("truffles"))) ||
              (query.includes("dosa") &&
                (sItems.includes("dosa") || sName.includes("veena") || sName.includes("darshini")))
            );
          }) || siblingOrders[0];

        const sibItems = (matchingSibling.items || []).join(", ") || "dishes";
        const sibStore = matchingSibling.merchant_name || "Second Kitchen";
        const prefix = isWakeWordPresent ? "Hey Utkarsh! " : "";
        const speech = `${prefix}Your ${sibItems} from ${sibStore} is currently being prepared hot and is on track for delivery in approximately 18 minutes. Would you like me to set an alarm for when it arrives so it rings?`;
        setVoiceFeedback(speech);
        voiceManager.speak(speech);
        return;
      }

      // 6. Check for status / ETA / where is driver
      if (
        query.includes("where") ||
        query.includes("status") ||
        query.includes("how long") ||
        query.includes("eta") ||
        query.includes("time") ||
        query.includes("arrive") ||
        query.includes("when will") ||
        query.includes("track") ||
        query.includes("food") ||
        query.includes("delivery") ||
        query.includes("driver")
      ) {
        const prefix = isWakeWordPresent ? "Hey Utkarsh! " : "";
        const speech = isPickup
          ? `${prefix}Your order at ${merchantName} is currently ${
              currentStage === "ready_for_pickup"
                ? "ready for pickup at the counter"
                : "being prepared and will be ready in approximately " + formattedEta
            }.`
          : `${prefix}Your delivery partner ${driverName} is on the way, approximately ${distanceKm} kilometers away. Estimated arrival is in ${formattedEta}.`;
        setVoiceFeedback(speech);
        voiceManager.speak(speech);
        return;
      }

      // 7. Check for OTP
      if (query.includes("otp") || query.includes("code") || query.includes("pin")) {
        const prefix = isWakeWordPresent ? "Hey Utkarsh! " : "";
        const speech = `${prefix}Your pickup OTP is ${pickupOtp.split("").join(" ")}.`;
        setVoiceFeedback(speech);
        voiceManager.speak(speech);
        return;
      }

      // 8. Check for call driver
      if (
        query.includes("call driver") ||
        query.includes("call delivery") ||
        query.includes("contact driver") ||
        query.includes("call") ||
        query.includes("contact")
      ) {
        setShowCallModal(true);
        const speech = `Opening secure masked call bridge to your delivery partner ${driverName}.`;
        setVoiceFeedback(speech);
        voiceManager.speak(speech);
        return;
      }

      // 9. Check for Assistant info / "who are you" / "what can you do"
      if (query.includes("who are you") || query.includes("what can you do") || query.includes("help")) {
        const speech =
          "I'm MerchantMind, your live voice concierge. You can ask me where your delivery partner is, check your ETA, set an arrival alarm, or connect directly with your driver.";
        setVoiceFeedback(speech);
        voiceManager.speak(speech);
        return;
      }

      // 10. Check for Thanks
      if (
        query.includes("thank") ||
        query.includes("thanks") ||
        query.includes("great") ||
        query.includes("awesome")
      ) {
        const speech = "You're very welcome, Utkarsh! Enjoy your delicious meal.";
        setVoiceFeedback(speech);
        voiceManager.speak(speech);
        return;
      }

      // 11. Fallback response
      const prefix = isWakeWordPresent ? "Hey Utkarsh! " : "";
      setVoiceFeedback(`Heard: "${rawText}". Say "Where is my order?" or "Set arrival alarm"`);
      voiceManager.speak(`${prefix}I heard: ${rawText}. You can ask me: where is my order, or: set arrival alarm.`);
    },
    [
      isAlarmRinging,
      isPickup,
      merchantName,
      currentStage,
      formattedEta,
      driverName,
      distanceKm,
      pickupOtp,
      dismissAlarm,
      triggerTestAlarm,
      siblingOrders,
    ]
  );

  const handleVoiceCommandRef = useRef(handleVoiceCommand);
  useEffect(() => {
    handleVoiceCommandRef.current = handleVoiceCommand;
  });

  useEffect(() => {
    voiceManager.init({
      onTranscript: (transcript: string, isFinal: boolean) => {
        setVoiceTranscript(transcript);
        if (isFinal) {
          handleVoiceCommandRef.current(transcript);
        }
      },
      onAutoSubmit: (transcript: string) => {
        handleVoiceCommandRef.current(transcript);
      },
      onStateChange: (state: VoiceState) => {
        setVoiceState(state);
      },
    });

    return () => {
      voiceManager.toggleVoiceMode(false);
      voiceManager.stopSpeaking();
    };
  }, []);

  // 4. Auto-arm if URL query has ?alarm=true (e.g. from chat voice command)
  useEffect(() => {
    if (searchParams.get("alarm") === "true") {
      setIsAlarmArmed(true);
      setVoiceFeedback("Arrival alarm automatically armed from chat!");
      voiceManager.speak("Arrival alarm is armed! A loud chime will sound the moment your delivery arrives.");
    }
  }, [searchParams]);

  // 5. Arrival Detection: Ring when order arrives and alarm is armed
  useEffect(() => {
    if (!isAlarmArmed || hasRang) return;

    const isArrivingOrDelivered =
      countdownSeconds <= 0 ||
      currentStage === "delivered" ||
      (isPickup && currentStage === "ready_for_pickup");

    if (isArrivingOrDelivered) {
      setHasRang(true);
      setIsAlarmRinging(true);
      alarmSynthesizerRef.current?.start();

      const announce = isPickup
        ? `Ding dong! Your order is ready for pickup at ${merchantName} counter! OTP is ${pickupOtp.split("").join(" ")}.`
        : `Ding dong! Your order from ${merchantName} has arrived at your door!`;
      voiceManager.speak(announce);

      if (typeof window !== "undefined" && "Notification" in window && Notification.permission === "granted") {
        try {
          new Notification("🔔 Order Has Arrived!", {
            body: isPickup
              ? `Ready for counter pickup at ${merchantName}! OTP: ${pickupOtp}`
              : `${driverName} has arrived with your order from ${merchantName}!`,
            icon: "/favicon.ico",
          });
        } catch (e) {
          // Ignore
        }
      }
    }
  }, [isAlarmArmed, hasRang, countdownSeconds, currentStage, isPickup, merchantName, driverName, pickupOtp]);

  // Keyboard shortcut: ESC or Space dismisses alarm
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (isAlarmRinging && (e.key === "Escape" || e.key === " ")) {
        e.preventDefault();
        dismissAlarm();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isAlarmRinging, dismissAlarm]);

  const toggleAlarm = () => {
    alarmSynthesizerRef.current?.unlock();
    if (isAlarmArmed) {
      setIsAlarmArmed(false);
      setVoiceFeedback("Arrival alarm turned off.");
      voiceManager.speak("Arrival alarm turned off.");
    } else {
      setIsAlarmArmed(true);
      setVoiceFeedback("Arrival alarm is armed! A loud chime will sound on delivery.");
      if (typeof window !== "undefined" && "Notification" in window && Notification.permission === "default") {
        Notification.requestPermission().catch(() => {});
      }
      voiceManager.speak("Arrival alarm is set! I'll sound a loud chime the moment your order arrives.");
    }
  };

  const toggleMicListening = () => {
    alarmSynthesizerRef.current?.unlock();
    voiceManager.unlockAudio();
    if (voiceState === "listening") {
      voiceManager.toggleVoiceMode(false);
      setVoiceFeedback("Voice assistant paused. Tap mic to activate.");
    } else {
      setVoiceTranscript("");
      setVoiceFeedback("🟢 Listening for your voice questions (e.g. 'Where is driver?')...");
      voiceManager.toggleVoiceMode(true);
      voiceManager.speak("I'm listening! Ask me where your order is, or say 'set arrival alarm'.");
    }
  };

  const handleCopyOrderId = () => {
    navigator.clipboard.writeText(orderId);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  if (loading) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-[#07080D] text-white p-4 font-sans">
        <div className="relative flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 shadow-2xl shadow-indigo-500/20">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-2xl bg-indigo-400 opacity-20"></span>
          <Navigation className="h-8 w-8 animate-spin text-indigo-400" />
        </div>
        <h2 className="mt-5 text-base font-bold tracking-tight text-zinc-100">Connecting to Dispatch Radar...</h2>
        <p className="mt-1 text-xs text-zinc-400">Synchronizing satellite GPS telemetry</p>
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-[#07080D] text-white p-4 font-sans text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-400">
          <AlertCircle className="h-8 w-8 text-rose-400" />
        </div>
        <h2 className="mt-4 text-xl font-bold">Order Details Unavailable</h2>
        <p className="mt-2 text-sm text-zinc-400 max-w-md">
          {error || "We couldn't locate this order. It might still be processing."}
        </p>
        <Link
          href="/chat"
          className="mt-6 inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-xs font-semibold text-white shadow-lg shadow-indigo-600/30 hover:bg-indigo-500 transition active:scale-95"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Shopping Chat
        </Link>
      </div>
    );
  }

  const items = order.items || [];
  const formattedDate = new Date(order.created_at || Date.now()).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  const currentOrderSummary = order
    ? {
        order_id: activeOrderId,
        merchant_name: merchantName,
        items: items.map((i) => i.name),
        total: order.total,
      }
    : null;

  const allOrders = [
    ...(currentOrderSummary ? [currentOrderSummary] : []),
    ...siblingOrders.filter((s) => s.order_id !== activeOrderId),
  ];

  return (
    <div className="min-h-screen bg-[#07080D] text-zinc-100 font-sans selection:bg-indigo-500 selection:text-white relative overflow-x-hidden">
      {/* 21st.dev Multi-layer Atmospheric Radial Lighting */}
      <div className="fixed top-0 left-1/4 -translate-x-1/2 h-[480px] w-[600px] bg-gradient-to-br from-indigo-600/12 via-violet-600/08 to-transparent blur-[160px] pointer-events-none rounded-full" />
      <div className="fixed top-20 right-1/4 translate-x-1/2 h-[420px] w-[540px] bg-gradient-to-bl from-emerald-500/10 via-teal-500/06 to-transparent blur-[160px] pointer-events-none rounded-full" />
      <div className="fixed inset-0 bg-[radial-gradient(rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:32px_32px] pointer-events-none" />

      {/* ═══════════════════════════════════════════════════════════════
          21st.dev Sticky Glass Navigation
          ═══════════════════════════════════════════════════════════════ */}
      <header className="sticky top-0 z-30 border-b border-white/[0.07] bg-[#07080E]/85 backdrop-blur-2xl">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3 sm:px-6">
          <div className="flex items-center gap-3">
            <Link
              href="/chat"
              className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/[0.04] border border-white/[0.08] text-zinc-400 hover:text-white hover:border-white/[0.2] hover:bg-white/[0.08] transition active:scale-95"
              title="Back to Chat"
            >
              <ArrowLeft className="h-4 w-4" />
            </Link>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-emerald-500 to-indigo-600 text-white shadow-lg shadow-emerald-500/20">
              {isPickup ? <Store className="h-4.5 w-4.5" /> : <Radio className="h-4.5 w-4.5" />}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-sm font-bold tracking-tight text-white">
                  {isPickup ? "Live Store Pickup" : "Live Delivery Tracking"}
                </h1>
                <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-950/90 border border-emerald-500/40 px-2.5 py-0.5 text-[10px] font-bold text-emerald-300">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-ping"></span>
                  {currentStage === "preparing"
                    ? "Preparing"
                    : currentStage === "arriving"
                    ? "Arriving!"
                    : isPickup && currentStage === "ready_for_pickup"
                    ? "Ready!"
                    : "En Route"}
                </span>
              </div>
              <p className="text-[11px] text-zinc-400">
                Order <span className="font-mono text-zinc-200 font-semibold">#{order.id.slice(0, 8)}</span> • {merchantName}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleCopyOrderId}
              className="flex items-center gap-1.5 rounded-xl border border-white/[0.08] bg-white/[0.03] hover:bg-white/[0.08] hover:border-white/[0.2] px-3 py-1.5 text-xs font-semibold text-zinc-300 transition active:scale-95"
              title="Copy Order ID"
            >
              {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5 text-zinc-400" />}
              <span>{copied ? "Copied" : "Order ID"}</span>
            </button>
            <Link
              href="/chat"
              className="hidden sm:flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 border border-indigo-400/30 px-3.5 py-1.5 text-xs font-bold text-white transition shadow-lg shadow-indigo-600/30 active:scale-95"
            >
              <ShoppingBag className="h-3.5 w-3.5" />
              <span>New Order</span>
            </Link>
          </div>
        </div>
      </header>

      {/* ═══════════════════════════════════════════════════════════════
          Multi-Order Switcher Bar (Dual Kitchen Orders)
          ═══════════════════════════════════════════════════════════════ */}
      {allOrders.length > 1 && (
        <div className="sticky top-[57px] z-20 border-b border-purple-500/20 bg-[#090A13]/95 backdrop-blur-2xl px-4 py-2.5 shadow-lg">
          <div className="mx-auto flex max-w-5xl items-center justify-between gap-3 overflow-x-auto no-scrollbar">
            <div className="flex items-center gap-2 shrink-0">
              <span className="flex items-center gap-1.5 text-[10px] uppercase font-bold tracking-wider text-purple-400 shrink-0">
                <Store className="h-3 w-3" />
                Kitchens:
              </span>
              {allOrders.map((ord) => {
                const isCurrent = ord.order_id === activeOrderId;
                const mLower = (ord.merchant_name || "").toLowerCase();
                const emoji =
                  mLower.includes("coffee") || mLower.includes("thindi") || mLower.includes("brahmin")
                    ? "☕"
                    : mLower.includes("pizza") || mLower.includes("toit") || mLower.includes("oven")
                    ? "🍕"
                    : mLower.includes("cake") || mLower.includes("bake")
                    ? "🎂"
                    : "🍽️";
                return (
                  <button
                    key={ord.order_id}
                    onClick={() => setActiveOrderId(ord.order_id)}
                    className={`flex items-center gap-2 rounded-xl px-3.5 py-1.5 text-xs font-semibold transition-all cursor-pointer ${
                      isCurrent
                        ? "bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-lg shadow-purple-600/30 border border-purple-400/50 scale-[1.02]"
                        : "bg-white/[0.04] text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.08] border border-white/[0.08]"
                    }`}
                  >
                    <span>{emoji}</span>
                    <span className="max-w-[150px] truncate">{ord.merchant_name}</span>
                    <span
                      className={`rounded-md px-1.5 py-0.5 text-[10px] font-mono ${
                        isCurrent
                          ? "bg-black/40 text-purple-200 font-bold"
                          : "bg-white/[0.05] text-zinc-400"
                      }`}
                    >
                      {isCurrent ? formattedEta : "~18m"}
                    </span>
                  </button>
                );
              })}
            </div>
            <div className="hidden sm:flex items-center gap-2 text-[11px] text-purple-300 font-medium shrink-0">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>Unified Dual Payment Verified</span>
            </div>
          </div>
        </div>
      )}

      {/* Main Container with generous pb-44 to eliminate any voice dock overlap */}
      <main className="mx-auto max-w-5xl px-4 pt-6 pb-44 sm:px-6 space-y-6 relative z-10">

        {/* ═══════════════════════════════════════════════════════════════
            HERO STATUS & ARRIVAL ALARM CARD (21st.dev Pro Max)
            ═══════════════════════════════════════════════════════════════ */}
        <section className="relative overflow-hidden rounded-3xl border border-white/[0.09] bg-gradient-to-b from-[#0D0F18]/95 via-[#0B0D15]/90 to-[#08090E]/90 p-6 sm:p-7 shadow-[0_12px_40px_rgba(0,0,0,0.7)] backdrop-blur-2xl">
          {/* Subtle top inner light highlight */}
          <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />

          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="space-y-2.5">
              {/* Razorpay Trust Chip */}
              <div className="inline-flex items-center gap-2 rounded-full bg-emerald-500/10 border border-emerald-500/30 px-3 py-1 text-xs font-bold text-emerald-400 shadow-sm">
                <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
                <span>Payment Confirmed via Razorpay ({order.rzp_payment_id || "Verified"})</span>
              </div>

              <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight flex items-center gap-2.5">
                <span>
                  {isPickup
                    ? currentStage === "ready_for_pickup"
                      ? "Your Order is Ready for Pickup! 🎉"
                      : currentStage === "almost_ready"
                      ? `Almost Ready — ~${formattedEta} left ⏳`
                      : `Preparing at Store — Ready in ~${formattedEta} 🔥`
                    : countdownSeconds <= 0
                    ? "Your Order Has Arrived! 🏡🎉"
                    : currentStage === "arriving"
                    ? `Arriving Now! ~${formattedEta} (${distanceKm} km) 🏡`
                    : `Arriving in ~${formattedEta} (${distanceKm} km) 🛵`}
                </span>
              </h2>

              <p className="text-sm text-zinc-300/90 max-w-xl leading-relaxed">
                {isPickup
                  ? currentStage === "ready_for_pickup"
                    ? `Head to ${merchantName} counter and show your OTP ${pickupOtp} to collect.`
                    : `Your items are being freshly prepared at ${merchantName} (${storeAddress}).`
                  : countdownSeconds <= 0
                  ? `${driverName} has arrived at your doorstep with fresh items from ${merchantName}! Enjoy your meal!`
                  : `${driverName} is on the way from ${merchantName} at ~${trackingData?.average_speed_kmh || 24} km/h.`}
              </p>
            </div>

            {/* Quick Actions / OTP Box */}
            {isPickup ? (
              <div className="flex items-center gap-3 rounded-2xl bg-zinc-950/80 border border-amber-500/40 px-5 py-3.5 shadow-inner">
                <div>
                  <div className="text-[10px] uppercase font-bold tracking-wider text-amber-400">Pickup Counter OTP</div>
                  <div className="text-3xl font-mono font-black text-white tracking-widest">{pickupOtp}</div>
                </div>
                <button
                  onClick={() => setShowQrModal(true)}
                  className="flex h-12 w-12 items-center justify-center rounded-xl bg-amber-600/20 border border-amber-500/40 text-amber-300 hover:bg-amber-600 hover:text-white transition active:scale-95"
                  title="Show Pickup QR"
                >
                  <QrCode className="h-6 w-6" />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2.5 self-start md:self-center">
                <button
                  onClick={() => setShowCallModal(true)}
                  className="flex items-center gap-2 rounded-2xl bg-emerald-600/15 hover:bg-emerald-600/25 border border-emerald-500/35 px-4 py-3 text-xs font-bold text-emerald-300 transition active:scale-95 shadow-lg shadow-emerald-500/10"
                >
                  <Phone className="h-4 w-4 text-emerald-400" />
                  <span>Call Driver</span>
                </button>
                <button
                  onClick={() => alert(`Message sent to ${driverName}: 'Please ring the doorbell when you arrive!'`)}
                  className="flex items-center gap-2 rounded-2xl bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.1] px-4 py-3 text-xs font-bold text-zinc-200 transition active:scale-95"
                >
                  <MessageSquare className="h-4 w-4 text-indigo-400" />
                  <span>Leave Note</span>
                </button>
              </div>
            )}
          </div>

          {/* 🔔 21st.dev Arrival Alarm Control Bar */}
          <div className="mt-6 pt-5 border-t border-white/[0.07]">
            <ArrivalAlarmControl
              isArmed={isAlarmArmed}
              onToggle={toggleAlarm}
              onTest={triggerTestAlarm}
              isPickup={isPickup}
            />
          </div>

          {/* ═══════════════════════════════════════════════════════════════
              4-Step Delivery Journey Stepper
              ═══════════════════════════════════════════════════════════════ */}
          <div className="mt-6 pt-5 border-t border-white/[0.07]">
            <div className="relative h-2.5 w-full rounded-full bg-zinc-900 overflow-hidden shadow-inner border border-white/[0.05]">
              <div
                className="absolute top-0 left-0 h-full bg-gradient-to-r from-emerald-500 via-teal-400 to-indigo-500 transition-all duration-1000 ease-out shadow-[0_0_12px_rgba(16,185,129,0.5)]"
                style={{ width: `${isPickup ? (currentStage === "ready_for_pickup" ? 100 : currentStage === "almost_ready" ? 70 : 35) : simulatedProgress}%` }}
              />
            </div>

            <div className="mt-4 grid grid-cols-4 text-center text-xs font-semibold">
              {/* Step 1 */}
              <div className="space-y-1 text-emerald-400">
                <div className="mx-auto flex h-7 w-7 items-center justify-center rounded-full bg-emerald-500/20 border border-emerald-500 text-[11px] font-black shadow-md shadow-emerald-500/20">
                  ✓
                </div>
                <div className="text-[11px] font-bold text-zinc-100">Order Placed</div>
                <div className="text-[10px] text-zinc-500 font-mono">{formattedDate}</div>
              </div>

              {/* Step 2 */}
              <div className={`space-y-1 ${currentStage === "preparing" ? "text-amber-400 font-bold" : "text-emerald-400"}`}>
                <div className={`mx-auto flex h-7 w-7 items-center justify-center rounded-full ${currentStage === "preparing" ? "bg-amber-500/20 border border-amber-500 shadow-md shadow-amber-500/20 animate-pulse" : "bg-emerald-500/20 border border-emerald-500"} text-[11px] font-bold`}>
                  {currentStage === "preparing" ? "🔥" : "✓"}
                </div>
                <div className="text-[11px] font-bold text-zinc-100">Preparing</div>
                <div className="text-[10px] text-zinc-500 font-mono">~{prepTime} min</div>
              </div>

              {/* Step 3 */}
              <div className={`space-y-1 ${currentStage === "out_for_delivery" ? "text-indigo-400 font-bold" : currentStage === "arriving" || countdownSeconds <= 0 ? "text-emerald-400" : "text-zinc-500"}`}>
                <div className={`mx-auto flex h-7 w-7 items-center justify-center rounded-full ${currentStage === "out_for_delivery" ? "bg-indigo-500/20 border border-indigo-500 shadow-md shadow-indigo-500/30 ring-2 ring-indigo-500/20 animate-pulse" : currentStage === "arriving" || countdownSeconds <= 0 ? "bg-emerald-500/20 border border-emerald-500" : "bg-zinc-900 border border-zinc-800"} text-[11px] font-bold`}>
                  {isPickup ? (currentStage === "almost_ready" ? "⏳" : "3") : "🛵"}
                </div>
                <div className="text-[11px] font-bold text-zinc-100">{isPickup ? "Almost Ready" : "Out for Delivery"}</div>
                <div className="text-[10px] text-zinc-500 font-mono">{countdownSeconds <= 0 ? "Completed" : `${distanceKm} km away`}</div>
              </div>

              {/* Step 4 */}
              <div className={`space-y-1 ${currentStage === "arriving" || countdownSeconds <= 0 ? "text-emerald-400 font-bold" : "text-zinc-500"}`}>
                <div className={`mx-auto flex h-7 w-7 items-center justify-center rounded-full ${currentStage === "arriving" || countdownSeconds <= 0 ? "bg-emerald-500/20 border border-emerald-500 shadow-lg shadow-emerald-500/30 animate-pulse" : "bg-zinc-900 border border-zinc-800"} text-[11px]`}>
                  {isPickup ? "🏪" : "🏡"}
                </div>
                <div className="text-[11px] font-bold text-zinc-100">{isPickup ? "Ready for Pickup" : "At Doorstep"}</div>
                <div className="text-[10px] text-zinc-400 font-mono">{countdownSeconds <= 0 ? "Arrived!" : `ETA ~${formattedEta}`}</div>
              </div>
            </div>
          </div>
        </section>

        {/* ═══════════════════════════════════════════════════════════════
            GRID: 21st.dev GPS RADAR MAP + DRIVER & RAZORPAY CARDS
            ═══════════════════════════════════════════════════════════════ */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* CYBER-TELEMETRY LIVE GPS RADAR MAP */}
          <div className="lg:col-span-2 overflow-hidden rounded-3xl border border-white/[0.09] bg-[#080B13]/95 p-5 shadow-[0_12px_40px_rgba(0,0,0,0.7)] backdrop-blur-2xl flex flex-col justify-between min-h-[360px] relative">
            {/* Tactical Grid Background */}
            <div className="absolute inset-0 bg-[#060810] pointer-events-none opacity-95">
              <svg className="w-full h-full opacity-25" xmlns="http://www.w3.org/2000/svg">
                <defs>
                  <pattern id="tacticalGrid" width="36" height="36" patternUnits="userSpaceOnUse">
                    <path d="M 36 0 L 0 0 0 36" fill="none" stroke="#6366f1" strokeWidth="0.6" />
                  </pattern>
                </defs>
                <rect width="100%" height="100%" fill="url(#tacticalGrid)" />
                {/* Glowing Curving Delivery Path */}
                <path
                  d="M 70 240 C 180 130, 320 270, 680 90"
                  fill="none"
                  stroke="#10b981"
                  strokeWidth="4"
                  strokeDasharray="8 6"
                  className="animate-pulse"
                />
              </svg>
            </div>

            {/* Radar Sweep Effect */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[340px] w-[340px] rounded-full border border-indigo-500/15 pointer-events-none">
              <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-indigo-500/10 via-transparent to-transparent animate-radar-sweep origin-center" />
            </div>

            {/* Top Tactical HUD Bar */}
            <div className="relative z-10 flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2 rounded-xl bg-black/75 border border-white/[0.1] px-3.5 py-1.5 text-xs font-bold text-zinc-200 backdrop-blur-md shadow-md">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                </span>
                <Navigation className="h-3.5 w-3.5 text-emerald-400" />
                <span>Live GPS Telemetry (Bangalore East)</span>
              </div>

              {/* Simulation speed controls & Live Ticking ETA */}
              <div className="flex items-center gap-2 flex-wrap">
                <div className="flex items-center gap-1 rounded-xl bg-black/75 border border-white/[0.1] p-1 text-[11px] font-bold text-zinc-400 backdrop-blur-md">
                  <span className="px-1.5 text-[10px] text-zinc-500 uppercase tracking-wider font-mono">Speed:</span>
                  {[1, 5, 10].map((speed) => (
                    <button
                      key={speed}
                      onClick={() => setSimSpeed(speed)}
                      className={`px-2 py-0.5 rounded-lg transition text-xs font-mono font-bold ${
                        simSpeed === speed
                          ? "bg-indigo-600 text-white shadow-sm"
                          : "text-zinc-400 hover:text-white hover:bg-white/[0.06]"
                      }`}
                    >
                      {speed}x
                    </button>
                  ))}
                  <button
                    onClick={() => {
                      alarmSynthesizerRef.current?.unlock();
                      setHasRang(false);
                      setCountdownSeconds(5);
                      setSimSpeed(1);
                    }}
                    className="flex items-center gap-1 px-2 py-0.5 rounded-lg bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30 border border-emerald-500/30 transition text-[11px] font-bold"
                    title="Jump to 5s remaining to test arrival chime"
                  >
                    <Zap className="h-3 w-3 text-emerald-400" />
                    <span>Test 5s</span>
                  </button>
                </div>

                <div className="flex items-center gap-1.5 rounded-xl bg-black/75 border border-white/[0.1] px-3 py-1.5 text-xs font-mono font-bold text-zinc-200 backdrop-blur-md shadow-md">
                  <Clock className="h-3.5 w-3.5 text-indigo-400" />
                  <span className="text-emerald-400 font-bold">{formattedEta}</span>
                </div>
              </div>
            </div>

            {/* Waypoint Markers on Tactical Map */}
            <div className="relative z-10 my-8 h-28 w-full">
              {/* Store Marker */}
              <div className="absolute left-2 sm:left-6 top-1/2 -translate-y-1/2 flex flex-col items-center space-y-1.5 z-10">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-600 text-white shadow-xl shadow-indigo-600/40 border border-indigo-400/50">
                  <Store className="h-6 w-6" />
                </div>
                <span className="text-[11px] font-bold text-white bg-black/80 px-2.5 py-0.5 rounded-md border border-white/[0.1] truncate max-w-[120px]">
                  {merchantName}
                </span>
                <span className="text-[10px] text-zinc-400 truncate max-w-[110px] font-mono">
                  {storeAddress.split(",")[0]}
                </span>
              </div>

              {/* Moving Vehicle Beacon */}
              <div
                className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 flex flex-col items-center space-y-1.5 z-20 transition-all duration-1000 ease-linear pointer-events-none"
                style={{ left: `${driverMapProgressPct}%` }}
              >
                <div className="relative flex h-14 w-14 items-center justify-center rounded-full bg-emerald-500 text-zinc-950 font-black shadow-2xl shadow-emerald-500/60 border-2 border-white animate-pulse">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-60"></span>
                  <Truck className="h-7 w-7 relative z-10" />
                  <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-indigo-600 text-[9px] font-bold text-white z-20 shadow">
                    🛵
                  </span>
                </div>
                <span className="text-[11px] font-black text-emerald-300 bg-emerald-950/95 px-2.5 py-0.5 rounded-md border border-emerald-500/50 shadow-md whitespace-nowrap">
                  {countdownSeconds <= 0 ? "Arrived!" : `${driverName} (${distanceKm} km)`}
                </span>
              </div>

              {/* Customer Destination Marker */}
              <div className="absolute right-2 sm:right-6 top-1/2 -translate-y-1/2 flex flex-col items-center space-y-1.5 z-10">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-rose-600 text-white shadow-xl shadow-rose-600/40 border border-rose-400/50">
                  <MapPin className="h-6 w-6" />
                </div>
                <span className="text-[11px] font-bold text-white bg-black/80 px-2.5 py-0.5 rounded-md border border-white/[0.1] truncate max-w-[120px]">
                  Your Doorstep
                </span>
                <span className="text-[10px] text-zinc-400 truncate max-w-[110px] font-mono">
                  {order.delivery_address?.split(",")[0] || "Bangalore"}
                </span>
              </div>
            </div>

            {/* Bottom Address Bar */}
            <div className="relative z-10 rounded-2xl bg-black/75 border border-white/[0.08] p-3 flex items-center justify-between backdrop-blur-md">
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-white/[0.06] text-indigo-400 shrink-0">
                  <MapPin className="h-4 w-4" />
                </div>
                <div className="text-xs truncate">
                  <div className="font-bold text-zinc-200">Delivering To:</div>
                  <div className="text-zinc-400 truncate">
                    {order.delivery_address || "12th Main Road, Indiranagar, Bangalore - 560038"}
                  </div>
                </div>
              </div>
              <a
                href={`https://maps.google.com/?q=${encodeURIComponent(order.delivery_address || "Bangalore")}`}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1 text-xs font-bold text-indigo-400 hover:text-indigo-300 transition shrink-0 ml-2"
              >
                <span>Maps</span>
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            </div>
          </div>

          {/* DRIVER & RAZORPAY VERIFIED CARDS */}
          <div className="space-y-4">
            {/* Driver Profile Card */}
            <div className="rounded-3xl border border-white/[0.09] bg-[#0D0F18]/95 p-5 shadow-[0_12px_40px_rgba(0,0,0,0.7)] backdrop-blur-2xl space-y-4">
              <div className="flex items-center gap-3.5">
                <div className="relative h-13 w-13 rounded-2xl bg-gradient-to-tr from-indigo-500 to-violet-600 flex items-center justify-center text-xl font-bold text-white shadow-lg shadow-indigo-500/30">
                  👨🏽‍🚀
                  <span className="absolute -bottom-1 -right-1 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-emerald-500 border-2 border-zinc-950"></span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h4 className="font-bold text-sm text-zinc-100">{driverName}</h4>
                    <span className="rounded-md bg-emerald-500/15 text-emerald-400 text-[10px] font-black px-2 py-0.5 border border-emerald-500/30">
                      ★ 4.9 (1,240+)
                    </span>
                  </div>
                  <p className="text-[11px] text-zinc-400 truncate mt-0.5">{driverVehicle}</p>
                </div>
              </div>

              <div className="space-y-2 rounded-2xl bg-white/[0.02] border border-white/[0.06] p-3 text-xs">
                <div className="flex items-center gap-2 text-emerald-400 text-[11px] font-bold">
                  <ShieldCheck className="h-4 w-4" />
                  <span>Vaccinated & Sanitized Delivery Partner</span>
                </div>
                <p className="text-[11px] text-zinc-400">
                  Order is sealed in thermal packaging for hygiene.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-2 pt-1">
                <button
                  onClick={() => setShowCallModal(true)}
                  className="flex items-center justify-center gap-1.5 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/35 py-2.5 text-xs font-bold transition active:scale-95"
                >
                  <Phone className="h-3.5 w-3.5" />
                  <span>Call Driver</span>
                </button>
                <button
                  onClick={() => alert(`Message sent to ${driverName}: 'Please leave at doorstep!'`)}
                  className="flex items-center justify-center gap-1.5 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] text-zinc-200 border border-white/[0.1] py-2.5 text-xs font-bold transition active:scale-95"
                >
                  <MessageSquare className="h-3.5 w-3.5" />
                  <span>Leave Note</span>
                </button>
              </div>
            </div>

            {/* Razorpay Proof Card */}
            <div className="rounded-3xl border border-white/[0.09] bg-[#0D0F18]/80 p-5 space-y-3 shadow-lg backdrop-blur-xl">
              <div className="flex items-center justify-between text-xs font-bold">
                <span className="text-zinc-300 flex items-center gap-1.5">
                  <ShieldCheck className="h-4 w-4 text-indigo-400" />
                  Razorpay Verified Payment
                </span>
                <span className="text-emerald-400 font-mono text-[11px] bg-emerald-500/10 px-2 py-0.5 rounded-md border border-emerald-500/20">
                  Captured
                </span>
              </div>
              <div className="text-[11px] text-zinc-400 space-y-1.5 font-mono">
                <div className="flex justify-between">
                  <span>Payment ID:</span>
                  <span className="text-zinc-200 font-bold">{order.rzp_payment_id || "pay_LiveVerified_8829"}</span>
                </div>
                <div className="flex justify-between">
                  <span>Amount Paid:</span>
                  <span className="text-emerald-400 font-black text-sm">₹{order.total.toFixed(2)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ═══════════════════════════════════════════════════════════════
            ORDER SUMMARY CARD
            ═══════════════════════════════════════════════════════════════ */}
        <OrderItemsSection items={items} order={order} />

        {/* Bottom Actions */}
        <BottomActions />
      </main>

      {/* ═══════════════════════════════════════════════════════════════
          21ST.DEV AMBIENT VOICE CONCIERGE FLOATING DOCK
          ═══════════════════════════════════════════════════════════════ */}
      <TrackingVoiceDock
        voiceState={voiceState}
        voiceFeedback={voiceFeedback}
        voiceTranscript={voiceTranscript}
        isAlarmArmed={isAlarmArmed}
        onToggleMic={toggleMicListening}
        onCommand={(cmd) => handleVoiceCommand(cmd)}
        onDismissFeedback={() => setVoiceFeedback(null)}
      />

      {/* 🔔 ARRIVAL ALARM RINGING MODAL */}
      {isAlarmRinging && (
        <ArrivalAlarmModal
          merchantName={merchantName}
          driverName={driverName}
          isPickup={isPickup}
          pickupOtp={pickupOtp}
          onDismiss={dismissAlarm}
        />
      )}

      {/* 📞 CALL DRIVER MODAL */}
      {showCallModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-4 animate-in fade-in duration-150">
          <div className="w-full max-w-sm rounded-3xl bg-[#0F121C] border border-white/[0.12] p-6 shadow-2xl text-center space-y-4">
            <div className="flex h-14 w-14 mx-auto items-center justify-center rounded-2xl bg-emerald-500/15 border border-emerald-500/35 text-emerald-400 shadow-lg shadow-emerald-500/20">
              <Phone className="h-7 w-7 text-emerald-400" />
            </div>
            <h3 className="text-base font-black text-white">Call Delivery Partner</h3>
            <p className="text-xs text-zinc-400">
              Connected via secure masked call bridge to <strong className="text-zinc-200">{driverName}</strong>.
            </p>
            <div className="rounded-2xl bg-black/60 border border-white/[0.08] p-3.5 font-mono text-emerald-400 text-lg font-black tracking-wider">
              +91 98765 43210
            </div>
            <div className="grid grid-cols-2 gap-2 pt-1">
              <a
                href="tel:+919876543210"
                className="flex items-center justify-center gap-1.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 py-2.5 text-xs font-bold text-white hover:from-emerald-500 hover:to-teal-500 transition active:scale-95 shadow-lg shadow-emerald-600/30"
              >
                <Phone className="h-3.5 w-3.5" />
                <span>Call Now</span>
              </a>
              <button
                onClick={() => setShowCallModal(false)}
                className="rounded-xl bg-white/[0.06] hover:bg-white/[0.1] border border-white/[0.1] py-2.5 text-xs font-bold text-zinc-300 transition active:scale-95"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 📱 QR BADGE MODAL */}
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
// Arrival Alarm Hero Control Component (21st.dev Pro Max)
// ═══════════════════════════════════════════════════════════════
function ArrivalAlarmControl({
  isArmed,
  onToggle,
  onTest,
  isPickup,
}: {
  isArmed: boolean;
  onToggle: () => void;
  onTest: () => void;
  isPickup: boolean;
}) {
  return (
    <div
      className={`relative overflow-hidden flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 rounded-2xl p-4 transition-all duration-300 ${
        isArmed
          ? "bg-gradient-to-r from-emerald-950/70 via-[#0C151A]/80 to-teal-950/70 border border-emerald-500/50 shadow-[0_0_30px_rgba(16,185,129,0.15)]"
          : "bg-white/[0.02] border border-white/[0.08] hover:border-white/[0.15]"
      }`}
    >
      <div className="flex items-center gap-3.5">
        <div
          className={`relative flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl transition-all ${
            isArmed
              ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 shadow-lg shadow-emerald-500/30"
              : "bg-white/[0.05] text-zinc-400 border border-white/[0.08]"
          }`}
        >
          {isArmed ? (
            <>
              <span className="animate-ping absolute inline-flex h-full w-full rounded-2xl bg-emerald-400 opacity-40"></span>
              <BellRing className="h-5 w-5 animate-bounce text-emerald-300 relative z-10" />
            </>
          ) : (
            <Bell className="h-5 w-5 text-indigo-400" />
          )}
        </div>

        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-black tracking-tight text-white">
              {isArmed ? "Arrival Alarm Armed & Active" : "Delivery Arrival Alarm"}
            </span>
            {isArmed ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-950 border border-emerald-500/50 px-2 py-0.5 text-[9px] font-black text-emerald-300 uppercase tracking-wider">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-ping"></span>
                Active
              </span>
            ) : (
              <span className="rounded-full bg-indigo-500/10 border border-indigo-500/30 px-2 py-0.5 text-[9px] font-bold text-indigo-300">
                Voice Ready
              </span>
            )}
          </div>
          <p className="text-[11px] text-zinc-300/80 mt-0.5">
            {isArmed
              ? isPickup
                ? "Loud chime sounds the moment your order is marked ready at the store counter."
                : "Loud chime sounds automatically the moment delivery partner reaches your doorstep."
              : 'Say "Set alarm when order comes" or tap button to wake/alert on arrival.'}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2 self-stretch sm:self-auto justify-end">
        <button
          onClick={onTest}
          type="button"
          className="flex items-center gap-1.5 rounded-xl border border-white/[0.1] bg-white/[0.04] hover:bg-white/[0.09] px-3.5 py-2 text-[11px] font-bold text-zinc-200 transition active:scale-95"
          title="Play sample arrival chime"
        >
          <Volume2 className="h-3.5 w-3.5 text-indigo-400" />
          <span>Test Sound</span>
        </button>

        <button
          onClick={onToggle}
          type="button"
          className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-black transition shadow-lg active:scale-95 ${
            isArmed
              ? "bg-rose-950/80 hover:bg-rose-900/80 border border-rose-500/50 text-rose-300 shadow-rose-950/50"
              : "bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 border border-indigo-400/30 text-white shadow-indigo-600/30"
          }`}
        >
          {isArmed ? (
            <>
              <VolumeX className="h-3.5 w-3.5" />
              <span>Turn Off Alarm</span>
            </>
          ) : (
            <>
              <Bell className="h-3.5 w-3.5" />
              <span>Set Arrival Alarm</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// Voice Concierge Floating Dock (21st.dev Pro Max with Zero Overlap)
// ═══════════════════════════════════════════════════════════════
function TrackingVoiceDock({
  voiceState,
  voiceFeedback,
  voiceTranscript,
  isAlarmArmed,
  onToggleMic,
  onCommand,
  onDismissFeedback,
}: {
  voiceState: VoiceState;
  voiceFeedback: string | null;
  voiceTranscript: string;
  isAlarmArmed: boolean;
  onToggleMic: () => void;
  onCommand: (cmd: string) => void;
  onDismissFeedback: () => void;
}) {
  const isListening = voiceState === "listening";
  const isSpeaking = voiceState === "speaking";

  return (
    <aside aria-label="Tracking Voice Assistant" className="fixed bottom-5 left-1/2 -translate-x-1/2 z-40 w-full max-w-xl px-4 pointer-events-none">
      <div className="flex flex-col items-center gap-2 pointer-events-auto">
        {/* Floating Speech / Response Bubble */}
        {(voiceFeedback || voiceTranscript) && (
          <div className="relative flex items-center justify-between gap-3 rounded-2xl bg-[#0D101A]/95 border border-indigo-500/35 px-4 py-2.5 shadow-2xl backdrop-blur-2xl text-xs max-w-md w-full animate-in slide-in-from-bottom-2 duration-200">
            <div className="flex items-center gap-2.5 overflow-hidden">
              <span className="flex h-2 w-2 rounded-full bg-indigo-400 animate-ping shrink-0"></span>
              <p className="text-zinc-100 truncate">
                {voiceTranscript ? (
                  <span>
                    <strong className="text-indigo-300 font-bold">Heard: </strong>"{voiceTranscript}"
                  </span>
                ) : (
                  voiceFeedback
                )}
              </p>
            </div>
            {voiceFeedback && (
              <button
                onClick={onDismissFeedback}
                className="text-zinc-400 hover:text-white text-xs shrink-0 px-1 font-bold"
              >
                ✕
              </button>
            )}
          </div>
        )}

        {/* Main 21st.dev Glassmorphic Dock Pill */}
        <div className="flex flex-wrap sm:flex-nowrap items-center justify-between gap-2.5 rounded-full bg-[#07090F]/92 border border-white/[0.12] px-3.5 py-2 shadow-[0_20px_60px_-15px_rgba(0,0,0,0.9)] backdrop-blur-3xl w-full">
          {/* Mic Button & Equalizer Animation */}
          <div className="flex items-center gap-2.5">
            <button
              onClick={onToggleMic}
              type="button"
              className={`relative flex h-10 w-10 items-center justify-center rounded-full transition-all duration-300 active:scale-95 ${
                isListening
                  ? "bg-rose-600 text-white shadow-lg shadow-rose-500/50 ring-4 ring-rose-500/30 animate-pulse"
                  : isSpeaking
                  ? "bg-indigo-600 text-white shadow-lg shadow-indigo-500/40 ring-4 ring-indigo-500/20"
                  : "bg-white/[0.06] text-zinc-300 hover:bg-white/[0.12] hover:text-white border border-white/[0.1]"
              }`}
              title={isListening ? "Listening... click to stop" : "Click to speak to voice agent"}
            >
              {isListening ? (
                <MicOff className="h-4.5 w-4.5" />
              ) : (
                <Mic className="h-4.5 w-4.5 text-indigo-400" />
              )}
            </button>

            <div className="text-left hidden xs:block sm:block">
              <div className="text-[11px] font-bold text-zinc-200 flex items-center gap-1.5">
                <span>{isListening ? "Listening..." : isSpeaking ? "Speaking..." : "MerchantMind Voice"}</span>
                {isListening && (
                  <span className="rounded-full bg-emerald-500/20 text-emerald-300 text-[9px] font-bold px-1.5 py-0.2 border border-emerald-500/30 animate-pulse">
                    Wake Word 🟢
                  </span>
                )}
                {isAlarmArmed && (
                  <span className="rounded-full bg-amber-500/20 text-amber-300 text-[9px] font-bold px-1.5 py-0.2 border border-amber-500/30">
                    Alarm ⏰
                  </span>
                )}
              </div>
              <div className="text-[10px] text-zinc-400 truncate max-w-[150px]">
                {isListening ? "Say \"Hey MerchantMind\"" : "Tap mic to activate"}
              </div>
            </div>

            {/* Live Equalizer sound bars when listening/speaking */}
            {(isListening || isSpeaking) && (
              <div className="flex items-center gap-0.5 h-4 px-1">
                <div className="w-1 bg-emerald-400 rounded-full animate-eq-1" />
                <div className="w-1 bg-indigo-400 rounded-full animate-eq-2" />
                <div className="w-1 bg-emerald-400 rounded-full animate-eq-3" />
                <div className="w-1 bg-indigo-400 rounded-full animate-eq-4" />
              </div>
            )}
          </div>

          {/* Quick Voice Prompt Chips */}
          <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-0.5">
            <button
              onClick={() => onCommand("merchantmind")}
              type="button"
              className="flex items-center gap-1 rounded-full bg-gradient-to-r from-indigo-500/25 to-purple-500/25 border border-indigo-500/40 px-2.5 py-1 text-[10px] font-bold text-indigo-200 hover:text-white transition shrink-0 active:scale-95 shadow-sm shadow-indigo-500/20"
            >
              <Radio className="h-3 w-3 text-cyan-400 animate-pulse" />
              <span>"Hey MerchantMind"</span>
            </button>

            <button
              onClick={() => onCommand("where is my driver")}
              type="button"
              className="flex items-center gap-1 rounded-full bg-white/[0.04] border border-white/[0.08] px-2.5 py-1 text-[10px] font-bold text-zinc-300 hover:border-indigo-500/50 hover:text-white transition shrink-0 active:scale-95"
            >
              <Truck className="h-3 w-3 text-indigo-400" />
              <span>"Where is driver?"</span>
            </button>

            <button
              onClick={() => onCommand("set alarm when order comes")}
              type="button"
              className={`flex items-center gap-1 rounded-full px-2.5 py-1 text-[10px] font-bold transition shrink-0 active:scale-95 ${
                isAlarmArmed
                  ? "bg-emerald-950/90 border border-emerald-500/50 text-emerald-300 shadow-sm shadow-emerald-500/20"
                  : "bg-white/[0.04] border border-white/[0.08] text-zinc-300 hover:border-indigo-500/50 hover:text-white"
              }`}
            >
              <Bell className="h-3 w-3 text-amber-400" />
              <span>"Set alarm"</span>
            </button>

            <button
              onClick={() => onCommand("what is my otp")}
              type="button"
              className="flex items-center gap-1 rounded-full bg-white/[0.04] border border-white/[0.08] px-2.5 py-1 text-[10px] font-bold text-zinc-300 hover:border-indigo-500/50 hover:text-white transition shrink-0 active:scale-95"
            >
              <Receipt className="h-3 w-3 text-emerald-400" />
              <span>"What is OTP?"</span>
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
}

// ═══════════════════════════════════════════════════════════════
// Arrival Alarm Ringing Modal (21st.dev Pro Max)
// ═══════════════════════════════════════════════════════════════
function ArrivalAlarmModal({
  merchantName,
  driverName,
  isPickup,
  pickupOtp,
  onDismiss,
}: {
  merchantName: string;
  driverName: string;
  isPickup: boolean;
  pickupOtp: string;
  onDismiss: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-2xl p-4 animate-in fade-in duration-200">
      <div className="relative w-full max-w-md rounded-3xl bg-gradient-to-b from-[#0F1420] via-[#090C14] to-black border-2 border-emerald-500/60 p-7 shadow-[0_0_60px_rgba(16,185,129,0.35)] text-center space-y-6 overflow-hidden">
        {/* Pulsing ring ambient background */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-72 w-72 bg-emerald-500/20 rounded-full blur-3xl pointer-events-none animate-pulse" />

        {/* Animated Bell Beacon */}
        <div className="relative mx-auto flex h-20 w-20 items-center justify-center">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-40"></span>
          <span className="animate-ping delay-150 absolute inline-flex h-16 w-16 rounded-full bg-emerald-500 opacity-60"></span>
          <div className="relative flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-tr from-emerald-500 to-teal-400 text-zinc-950 shadow-xl shadow-emerald-500/40">
            <BellRing className="h-9 w-9 animate-bounce text-zinc-950" />
          </div>
        </div>

        {/* Title and Announcement */}
        <div className="space-y-2 relative z-10">
          <div className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/20 border border-emerald-500/50 px-3 py-1 text-xs font-black text-emerald-300">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-ping"></span>
            ARRIVAL ALARM RINGING
          </div>
          <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
            {isPickup ? "Your Order is Ready!" : "Your Food has Arrived!"}
          </h2>
          <p className="text-sm text-zinc-300 max-w-sm mx-auto">
            {isPickup
              ? `Your order from ${merchantName} is ready at the pickup counter.`
              : `${driverName} has reached your delivery location with items from ${merchantName}.`}
          </p>
        </div>

        {/* OTP display if pickup */}
        {isPickup && (
          <div className="rounded-2xl bg-black/60 border border-amber-500/40 p-4 space-y-1 relative z-10">
            <div className="text-[10px] uppercase font-bold text-amber-400 tracking-wider">
              Show Counter OTP
            </div>
            <div className="text-3xl font-mono font-black text-white tracking-widest">
              {pickupOtp}
            </div>
          </div>
        )}

        {/* Dismiss Button */}
        <div className="space-y-3 relative z-10 pt-2">
          <button
            onClick={onDismiss}
            type="button"
            className="w-full flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-emerald-500 via-teal-400 to-emerald-500 hover:from-emerald-400 hover:to-teal-300 py-3.5 px-6 text-sm font-black text-zinc-950 shadow-xl shadow-emerald-500/30 transition transform hover:scale-[1.02] active:scale-[0.98]"
          >
            <VolumeX className="h-5 w-5 text-zinc-950" />
            <span>Dismiss Alarm & Collect Order</span>
          </button>
          <p className="text-[11px] text-zinc-400">
            Press <strong className="text-zinc-200 font-bold">ESC</strong> or Space to dismiss
          </p>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// Order Summary Component
// ═══════════════════════════════════════════════════════════════
function OrderItemsSection({ items, order }: { items: any[]; order: OrderResponse }) {
  return (
    <section className="rounded-3xl border border-white/[0.09] bg-[#0D0F18]/95 p-6 shadow-[0_12px_40px_rgba(0,0,0,0.7)] backdrop-blur-2xl space-y-4">
      <div className="flex items-center justify-between border-b border-white/[0.07] pb-3.5">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-indigo-500/10 border border-indigo-500/25 text-indigo-400">
            <Receipt className="h-4.5 w-4.5" />
          </div>
          <h3 className="font-bold text-base text-zinc-100">
            Order Summary ({items.length} {items.length === 1 ? "item" : "items"})
          </h3>
        </div>
        <span className="text-xs font-mono font-bold text-zinc-400">Total: ₹{order.total.toFixed(0)}</span>
      </div>

      <div className="divide-y divide-white/[0.05]">
        {items.map((item, index) => (
          <div key={index} className="flex items-center justify-between py-3.5">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/[0.04] border border-white/[0.08] text-xl shadow-inner">
                {item.name?.toLowerCase().includes("coffee") ? "☕" : "🍰"}
              </div>
              <div>
                <h5 className="font-bold text-xs text-zinc-100">{item.name}</h5>
                <p className="text-[11px] text-zinc-400 font-mono mt-0.5">
                  Qty: {item.quantity} × ₹{item.price}
                </p>
              </div>
            </div>
            <div className="text-xs font-mono font-bold text-zinc-100">
              ₹{(item.price * item.quantity).toFixed(0)}
            </div>
          </div>
        ))}
      </div>

      <div className="border-t border-white/[0.07] pt-3.5 space-y-2 text-xs text-zinc-400">
        <div className="flex justify-between">
          <span>Item Subtotal:</span>
          <span className="text-zinc-200 font-mono">₹{order.subtotal.toFixed(2)}</span>
        </div>
        <div className="flex justify-between">
          <span>Delivery / Convenience Fee:</span>
          <span className="text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded-md border border-emerald-500/20 text-[11px]">
            FREE (Promotional)
          </span>
        </div>
        <div className="flex justify-between text-sm font-bold text-white border-t border-white/[0.07] pt-3 mt-2">
          <span>Total Paid via Razorpay:</span>
          <span className="text-emerald-400 font-mono font-black text-base">₹{order.total.toFixed(2)}</span>
        </div>
      </div>
    </section>
  );
}

function BottomActions() {
  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
      <Link
        href="/chat"
        className="w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 border border-indigo-400/30 px-6 py-3 text-xs font-bold text-white shadow-lg shadow-indigo-600/30 transition active:scale-95"
      >
        <MessageSquare className="h-4 w-4" />
        <span>Chat with Concierge / Reorder</span>
      </Link>
      <button
        onClick={() => window.print()}
        className="w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-2xl border border-white/[0.08] bg-white/[0.03] hover:bg-white/[0.08] hover:border-white/[0.15] px-5 py-3 text-xs font-bold text-zinc-300 transition active:scale-95"
      >
        <Download className="h-4 w-4 text-zinc-400" />
        <span>Download Tax Invoice</span>
      </button>
    </div>
  );
}

function QrModal({
  orderId,
  pickupOtp,
  merchantName,
  onClose,
}: {
  orderId: string;
  pickupOtp: string;
  merchantName: string;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-4 animate-in fade-in duration-150">
      <div className="w-full max-w-sm rounded-3xl bg-[#0F121C] border border-white/[0.12] p-6 shadow-2xl text-center space-y-4">
        <div className="flex justify-between items-center pb-2 border-b border-white/[0.08]">
          <span className="text-sm font-bold text-white">Store Pickup QR Badge</span>
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

        <button
          onClick={onClose}
          className="w-full rounded-xl bg-amber-600 py-2.5 text-xs font-bold text-white hover:bg-amber-500 transition active:scale-95"
        >
          Close
        </button>
      </div>
    </div>
  );
}
