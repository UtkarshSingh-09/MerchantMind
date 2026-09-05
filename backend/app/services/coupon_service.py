"""Coupon & Promotion Application Service.
Simulates Razorpay ecosystem promotional discounts, cart discount calculations,
and merchant coupon code validation.
"""

import re
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Standard promotional offers catalogue
STANDARD_COUPONS: dict[str, dict[str, Any]] = {
    "WELCOME10": {
        "description": "New Customer Welcome: 10% OFF on your entire order",
        "discount_type": "percentage",
        "discount_value": 10.0,
        "min_order_value": 100.0,
        "max_discount": 150.0,
    },
    "SWEET20": {
        "description": "Artisan Sweet Feast: 20% OFF up to ₹200",
        "discount_type": "percentage",
        "discount_value": 20.0,
        "min_order_value": 250.0,
        "max_discount": 200.0,
    },
    "FLAT50": {
        "description": "Flat ₹50 Instant Discount on orders above ₹250",
        "discount_type": "flat",
        "discount_value": 50.0,
        "min_order_value": 250.0,
        "max_discount": 50.0,
    },
    "FESTIVE15": {
        "description": "Festive Celebration Special: 15% OFF",
        "discount_type": "percentage",
        "discount_value": 15.0,
        "min_order_value": 300.0,
        "max_discount": 250.0,
    },
    "RAZORPAY25": {
        "description": "Razorpay Magic Checkout: 25% OFF up to ₹300",
        "discount_type": "percentage",
        "discount_value": 25.0,
        "min_order_value": 400.0,
        "max_discount": 300.0,
    },
}


def apply_coupon_to_cart(
    coupon_code: str,
    cart: dict[str, Any],
) -> dict[str, Any]:
    """Validate and apply a coupon code to the shopping cart.
    
    Returns a dictionary with result details and the updated cart dictionary.
    """
    clean_code = (coupon_code or "").strip().upper().replace(" ", "")
    if not clean_code:
        return {
            "success": False,
            "error": "Please provide a valid coupon code.",
            "cart": cart,
        }

    items = cart.get("items", [])
    if not items:
        return {
            "success": False,
            "error": "Cannot apply coupon to an empty cart. Please add items first.",
            "cart": cart,
        }

    subtotal = sum(float(i.get("price", 0.0)) * int(i.get("quantity", 1)) for i in items)
    if subtotal <= 0:
        subtotal = float(cart.get("total", 0.0))

    # 1. Lookup in predefined coupons or parse dynamic codes like 'SAVE15', 'OFFER20', etc.
    coupon_info = STANDARD_COUPONS.get(clean_code)

    if not coupon_info:
        # Check dynamic pattern e.g. SAVE20, DISCOUNT15, OFFER10, FLAT100
        match = re.search(r"(\d+)", clean_code)
        if match:
            num = int(match.group(1))
            if "FLAT" in clean_code:
                coupon_info = {
                    "description": f"Special Promotional Offer: Flat ₹{num} OFF",
                    "discount_type": "flat",
                    "discount_value": float(num),
                    "min_order_value": float(num * 2),
                    "max_discount": float(num),
                }
            elif 5 <= num <= 50:
                coupon_info = {
                    "description": f"Merchant Campaign Offer: {num}% OFF",
                    "discount_type": "percentage",
                    "discount_value": float(num),
                    "min_order_value": 150.0,
                    "max_discount": float(num * 10),
                }

    if not coupon_info:
        valid_codes = ", ".join(list(STANDARD_COUPONS.keys())[:3])
        return {
            "success": False,
            "error": f"Coupon code '{clean_code}' is invalid or expired. Try codes like: {valid_codes}",
            "cart": cart,
        }

    min_val = coupon_info.get("min_order_value", 0.0)
    if subtotal < min_val:
        return {
            "success": False,
            "error": f"Coupon '{clean_code}' requires a minimum cart value of ₹{min_val:.0f}. Current subtotal is ₹{subtotal:.0f}.",
            "cart": cart,
        }

    # 2. Compute discount amount
    d_type = coupon_info.get("discount_type", "percentage")
    d_val = float(coupon_info.get("discount_value", 10.0))
    max_d = float(coupon_info.get("max_discount", 500.0))

    if d_type == "percentage":
        raw_discount = (subtotal * d_val) / 100.0
        discount_amount = min(raw_discount, max_d)
    else:
        discount_amount = min(d_val, max_d, subtotal)

    discount_amount = round(discount_amount, 2)
    new_total = max(0.0, round(subtotal - discount_amount, 2))

    # 3. Update cart structure
    cart["subtotal"] = round(subtotal, 2)
    cart["discount_amount"] = discount_amount
    cart["coupon_code"] = clean_code
    cart["total"] = new_total

    logger.info("Applied coupon %s: subtotal=₹%.2f, discount=₹%.2f, total=₹%.2f", clean_code, subtotal, discount_amount, new_total)

    return {
        "success": True,
        "coupon_code": clean_code,
        "description": coupon_info.get("description"),
        "subtotal": round(subtotal, 2),
        "discount_amount": discount_amount,
        "discount_percentage": d_val if d_type == "percentage" else round((discount_amount / subtotal) * 100, 1),
        "new_total": new_total,
        "message": f"🎉 Coupon '{clean_code}' applied! You saved ₹{discount_amount:.0f}. New total: ₹{new_total:.0f}",
        "cart": cart,
    }
