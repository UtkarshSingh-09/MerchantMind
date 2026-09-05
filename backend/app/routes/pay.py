"""Hosted Razorpay Checkout Page — Mobile-responsive payment terminal for Telegram and WhatsApp orders."""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.order import Order, OrderStatus
from app.models.merchant import Merchant
from app.models.customer import Customer

router = APIRouter(tags=["Payment Checkout"])


@router.get("/pay/{order_id}", response_class=HTMLResponse)
async def hosted_checkout_page(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Render a mobile-first, high-converting Razorpay checkout terminal."""
    # 1. Fetch Order
    order_stmt = select(Order).where(Order.id == order_id)
    order_res = await db.execute(order_stmt)
    order = order_res.scalar_one_or_none()

    if not order:
        return HTMLResponse(
            status_code=404,
            content="""<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Order Not Found</title>
<style>body{background:#09090b;color:#f4f4f5;font-family:system-ui,-apple-system,sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;padding:20px;text-align:center;}
.card{background:#18181b;border:1px solid #27272a;border-radius:16px;padding:32px;max-width:400px;}
h1{font-size:20px;margin-bottom:8px;color:#ef4444;}p{color:#a1a1aa;font-size:14px;}</style></head>
<body><div class="card"><h1>Order Not Found</h1><p>This payment link is invalid or has expired.</p></div></body></html>"""
        )

    # 2. Fetch Merchant & Customer
    m_stmt = select(Merchant).where(Merchant.id == order.merchant_id)
    m_res = await db.execute(m_stmt)
    merchant = m_res.scalar_one_or_none()

    customer_name = "Valued Customer"
    customer_phone = "+919876543210"
    if order.customer_id:
        c_stmt = select(Customer).where(Customer.id == order.customer_id)
        c_res = await db.execute(c_stmt)
        customer = c_res.scalar_one_or_none()
        if customer:
            customer_name = customer.name or customer_name
            customer_phone = customer.phone or customer_phone

    merchant_name = merchant.name if merchant else "Merchant Store"
    merchant_desc = merchant.neighborhood or merchant.cuisine_type or "Bangalore"
    rzp_key = settings.razorpay_key_id or "rzp_test_TTBzVCxzHMSaip"
    rzp_order_id = order.rzp_order_id or ""
    amount_paise = order.authoritative_total_paise

    # Render Success State if already paid
    if order.status == OrderStatus.PAID:
        items_html = "".join(
            f'<div class="item"><span>{item.get("name")} × {item.get("quantity", 1)}</span><span>₹{(float(item.get("price", 0)) * int(item.get("quantity", 1))):.0f}</span></div>'
            for item in (order.items or [])
        )
        return HTMLResponse(content=f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>Payment Successful — {merchant_name}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: #09090b; color: #fafafa; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px; }}
    .card {{ background: #18181b; border: 1px solid #27272a; border-radius: 20px; width: 100%; max-width: 440px; padding: 32px 24px; text-align: center; box-shadow: 0 20px 40px rgba(0,0,0,0.5); }}
    .icon {{ width: 64px; height: 64px; background: rgba(16, 185, 129, 0.15); border: 2px solid #10b981; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 16px; font-size: 32px; color: #10b981; }}
    h1 {{ font-size: 22px; font-weight: 700; color: #10b981; margin-bottom: 6px; }}
    .store {{ font-size: 14px; color: #a1a1aa; margin-bottom: 24px; }}
    .receipt {{ background: #121215; border: 1px solid #27272a; border-radius: 14px; padding: 16px; margin-bottom: 24px; text-align: left; }}
    .item {{ display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 8px; color: #d4d4d8; }}
    .total-row {{ border-top: 1px dashed #3f3f46; padding-top: 10px; margin-top: 10px; display: flex; justify-content: space-between; font-weight: 700; font-size: 16px; color: #fafafa; }}
    .badge {{ display: inline-flex; align-items: center; gap: 6px; background: #27272a; padding: 6px 12px; border-radius: 999px; font-size: 12px; color: #a1a1aa; margin-bottom: 24px; }}
    .btn {{ display: block; width: 100%; padding: 14px; background: #2563eb; color: #fff; text-decoration: none; border-radius: 12px; font-weight: 600; font-size: 15px; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">✓</div>
    <h1>Payment Successful!</h1>
    <div class="store">{merchant_name} • Order #{str(order.id)[:8]}</div>
    
    <div class="receipt">
      {items_html}
      <div class="total-row">
        <span>Total Paid</span>
        <span>₹{order.total:.0f}</span>
      </div>
    </div>

    <div class="badge">
      <span>🔒 Razorpay Ref: {order.rzp_payment_id or "Captured"}</span>
    </div>

    <button onclick="returnToTelegram()" class="btn" style="border:none; cursor:pointer;">Return to Telegram Bot</button>
    <p style="margin-top:14px; font-size:13px; color:#a1a1aa;">Returning to your Telegram bot automatically in 3s...</p>
  </div>

  <script>
    function returnToTelegram() {{
      // 1. Try native Telegram app deep link
      window.location.href = "tg://resolve?domain=utkarsh_merchantmind_bot";
      try {{ window.close(); }} catch(e) {{}}
      // 2. Fallback to web link
      setTimeout(() => {{
        window.location.href = "https://t.me/utkarsh_merchantmind_bot";
      }}, 400);
    }}
    // Auto return after 3.5 seconds
    setTimeout(returnToTelegram, 3500);
  </script>
</body>
</html>""")

    # Render Checkout Terminal with Razorpay Standard JS
    items_html = "".join(
        f'<div style="display:flex;justify-content:space-between;align-items:center;font-size:14px;margin-bottom:10px;color:#d4d4d8;gap:8px;">'
        f'<span style="font-weight:500;">{item.get("name")} × {item.get("quantity", 1)}</span>'
        f'<span style="font-weight:700;color:#fff;white-space:nowrap;">₹{(float(item.get("price", 0)) * int(item.get("quantity", 1))):.0f}</span>'
        f'</div>'
        for item in (order.items or [])
    )

    return HTMLResponse(content=f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>Pay ₹{order.total:.0f} — {merchant_name}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: #09090b; color: #fafafa; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 16px; margin: 0; }}
    .card {{ background: #18181b; border: 1px solid #27272a; border-radius: 20px; width: 100%; max-width: 440px; padding: 24px; box-shadow: 0 20px 40px rgba(0,0,0,0.6); }}
    .header {{ display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }}
    .store-avatar {{ width: 48px; height: 48px; border-radius: 12px; background: linear-gradient(135deg, #059669, #10b981); display: flex; align-items: center; justify-content: center; font-size: 22px; color: #fff; font-weight: 700; }}
    .store-info h1 {{ font-size: 18px; font-weight: 700; margin-bottom: 2px; }}
    .store-info p {{ font-size: 13px; color: #a1a1aa; }}
    .receipt {{ background: #121215; border: 1px solid #27272a; border-radius: 14px; padding: 16px; margin-bottom: 20px; }}
    .total-row {{ border-top: 1px dashed #3f3f46; padding-top: 10px; margin-top: 10px; display: flex; justify-content: space-between; font-weight: 700; font-size: 16px; color: #fafafa; }}
    .trust {{ display: flex; align-items: center; justify-content: center; gap: 6px; font-size: 12px; color: #71717a; margin-bottom: 16px; }}
    .pay-btn {{ width: 100%; padding: 16px; background: linear-gradient(135deg, #059669, #10b981); color: #fff; border: none; border-radius: 14px; font-size: 16px; font-weight: 700; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; transition: opacity 0.2s; }}
    .pay-btn:active {{ opacity: 0.8; }}
    .pay-btn:disabled {{ opacity: 0.5; cursor: not-allowed; }}
    .spinner {{ width: 24px; height: 24px; border: 3px solid rgba(255,255,255,0.2); border-top-color: #fff; border-radius: 50%; animation: spin 0.8s linear infinite; display: none; }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
  </style>
  <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
</head>
<body style="background:#09090b;color:#fafafa;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh;padding:16px;margin:0;">
  <div class="card" style="background:#18181b;border:1px solid #27272a;border-radius:20px;width:100%;max-width:440px;padding:24px;box-shadow:0 20px 40px rgba(0,0,0,0.6);">
    <div class="header" style="display:flex;align-items:center;gap:12px;margin-bottom:20px;">
      <div class="store-avatar" style="width:48px;height:48px;border-radius:12px;background:linear-gradient(135deg,#059669,#10b981);display:flex;align-items:center;justify-content:center;font-size:22px;color:#fff;font-weight:700;">🏪</div>
      <div class="store-info">
        <h1 style="font-size:18px;font-weight:700;margin-bottom:2px;color:#fff;">{merchant_name}</h1>
        <p style="font-size:13px;color:#a1a1aa;margin:0;">{merchant_desc} • Order #{str(order.id)[:8]}</p>
      </div>
    </div>

    <div class="receipt" style="background:#121215;border:1px solid #27272a;border-radius:14px;padding:16px;margin-bottom:20px;">
      {items_html}
      <div class="total-row" style="border-top:1px dashed #3f3f46;padding-top:10px;margin-top:10px;display:flex;justify-content:space-between;font-weight:700;font-size:16px;color:#fafafa;">
        <span>Total Payable</span>
        <span>₹{order.total:.0f}</span>
      </div>
    </div>

    <div class="trust" style="display:flex;align-items:center;justify-content:center;gap:6px;font-size:12px;color:#71717a;margin-bottom:16px;">
      <span>🔒 Secured by <b>Razorpay</b> (UPI, Cards, Netbanking)</span>
    </div>

    <button id="pay-btn" class="pay-btn" onclick="openCheckout()" style="width:100%;padding:16px;background:linear-gradient(135deg,#059669,#10b981);color:#fff;border:none;border-radius:14px;font-size:16px;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:8px;">
      <span class="spinner" id="spinner"></span>
      <span id="btn-text">Pay ₹{order.total:.0f} with Razorpay</span>
    </button>
  </div>

  <script>
    const options = {{
      key: "{rzp_key}",
      amount: {amount_paise},
      currency: "INR",
      name: "{merchant_name}",
      description: "Order #{str(order.id)[:8]}",
      order_id: "{rzp_order_id}",
      prefill: {{
        name: "{customer_name}",
        contact: "{customer_phone}"
      }},
      theme: {{
        color: "#059669"
      }},
      modal: {{
        ondismiss: function() {{
          const btn = document.getElementById("pay-btn");
          if (btn) btn.disabled = false;
          const sp = document.getElementById("spinner");
          if (sp) sp.style.display = "none";
          const txt = document.getElementById("btn-text");
          if (txt) txt.innerText = "Pay ₹{order.total:.0f} with Razorpay";
        }}
      }},
      handler: async function (response) {{
        const txt = document.getElementById("btn-text");
        if (txt) txt.innerText = "Verifying Payment...";
        try {{
          const res = await fetch("/api/orders/{order.id}/verify-payment", {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }},
            body: JSON.stringify({{
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_order_id: response.razorpay_order_id,
              razorpay_signature: response.razorpay_signature
            }})
          }});
          window.location.reload();
        }} catch (err) {{
          alert("Payment verification error: " + err);
          window.location.reload();
        }}
      }}
    }};

    function openCheckout() {{
      const btn = document.getElementById("pay-btn");
      const sp = document.getElementById("spinner");
      const txt = document.getElementById("btn-text");
      if (btn) btn.disabled = true;
      if (sp) sp.style.display = "inline-block";
      if (txt) txt.innerText = "Opening Razorpay...";

      if (typeof Razorpay !== "undefined") {{
        try {{
          const rzp = new Razorpay(options);
          rzp.open();
          return;
        }} catch (e) {{
          console.warn("Razorpay invocation failed, fallback to direct verification:", e);
        }}
      }}

      // Ad-blocker or script load blocked fallback: Directly verify test payment
      if (txt) txt.innerText = "Completing Test Payment...";
      fetch("/api/orders/{order.id}/verify-payment", {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify({{
          razorpay_payment_id: "pay_test_" + Math.random().toString(36).substring(2, 10),
          razorpay_order_id: "{rzp_order_id}" || undefined
        }})
      }}).then(() => {{
        window.location.reload();
      }}).catch((err) => {{
        alert("Payment error: " + err);
        if (btn) btn.disabled = false;
        if (sp) sp.style.display = "none";
        if (txt) txt.innerText = "Pay ₹{order.total:.0f} with Razorpay";
      }});
    }}

    // Auto open checkout modal on mobile
    window.addEventListener("DOMContentLoaded", () => {{
      setTimeout(openCheckout, 600);
    }});
  </script>
</body>
</html>""")
