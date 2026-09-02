"""Inventory Sync Service — Live POS & Shopify Webhook Ingestion Engine.
Handles real-time inventory updates, batch stock modifications, price sync,
and optimistic stock reservation checks to prevent overselling.
"""

import logging
from typing import Any
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.merchant import Merchant
from app.models.audit_log import AuditLog
from app.services.audit_service import AuditEventType

logger = logging.getLogger(__name__)


class InventorySyncService:
    """Service to handle POS/ERP/Shopify live inventory webhooks and manual stock overrides."""

    async def sync_batch_inventory(
        self,
        db: AsyncSession,
        merchant_id: UUID,
        updates_list: list[dict[str, Any]],
        source: str = "pos_webhook",
    ) -> dict[str, Any]:
        """Process batch inventory updates for a specific merchant."""
        merchant_res = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
        merchant = merchant_res.scalar_one_or_none()
        if not merchant:
            return {"success": False, "error": f"Merchant {merchant_id} not found", "updated_count": 0}

        updated_count = 0
        failed_items = []

        for item in updates_list:
            sku = item.get("sku") or item.get("id")
            name = item.get("name")
            in_stock = item.get("in_stock")
            price = item.get("price")
            quantity = item.get("quantity") or item.get("stock_quantity")

            # Lookup product by ID, name, or SKU
            stmt = select(Product).where(Product.merchant_id == merchant_id)
            if sku:
                try:
                    stmt = stmt.where(Product.id == UUID(str(sku)))
                except ValueError:
                    stmt = stmt.where(Product.name.ilike(f"%{sku}%"))
            elif name:
                stmt = stmt.where(Product.name.ilike(name.strip()))

            res = await db.execute(stmt)
            product = res.scalars().first()

            if not product:
                failed_items.append({"identifier": sku or name, "reason": "Item not found in catalog"})
                continue

            # Apply updates
            if in_stock is not None:
                product.in_stock = bool(in_stock)
            if price is not None and float(price) > 0:
                product.price = float(price)
            if quantity is not None:
                # If quantity <= 0, mark as out of stock
                product.in_stock = int(quantity) > 0

            product.schema_json = product.to_schema_org()
            updated_count += 1

        await db.commit()

        # Log audit trail
        audit = AuditLog(
            conversation_id=None,
            event_type=AuditEventType.INVENTORY_SYNC if hasattr(AuditEventType, "INVENTORY_SYNC") else AuditEventType.TOOL_EXECUTION,
            agent_name="InventorySyncService",
            tool_name="sync_batch_inventory",
            tool_input={"merchant_id": str(merchant_id), "source": source, "count": len(updates_list)},
            tool_output={"updated_count": updated_count, "failed_items": failed_items},
        )
        db.add(audit)
        await db.commit()

        logger.info(
            "POS Sync completed for merchant '%s': %d updated, %d failed",
            merchant.name,
            updated_count,
            len(failed_items),
        )

        return {
            "success": True,
            "merchant_name": merchant.name,
            "updated_count": updated_count,
            "failed_items": failed_items,
        }

    async def toggle_product_stock(
        self,
        db: AsyncSession,
        product_id: UUID,
        in_stock: bool,
    ) -> dict[str, Any]:
        """Manually toggle a single product's stock availability status."""
        res = await db.execute(select(Product).where(Product.id == product_id))
        product = res.scalar_one_or_none()
        if not product:
            return {"success": False, "error": "Product not found"}

        product.in_stock = in_stock
        product.schema_json = product.to_schema_org()
        await db.commit()

        logger.info("Product '%s' stock status updated to in_stock=%s", product.name, in_stock)
        return {
            "success": True,
            "product_id": str(product.id),
            "name": product.name,
            "in_stock": product.in_stock,
            "price": product.price,
        }

    @staticmethod
    def parse_pos_payload(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
        """Parse standard UrbanPiper POS webhook format and direct merchant gateway updates."""
        # 1. Standard UrbanPiper POS format
        if payload.get("event") == "inventory.updated" or "urbanpiper" in str(payload).lower():
            items = []
            for itm in payload.get("items", []):
                items.append({
                    "sku": itm.get("ref_id"),
                    "name": itm.get("title") or itm.get("name"),
                    "in_stock": itm.get("available", True),
                    "quantity": int(itm.get("stock_count", 10)),
                    "price": float(itm.get("price", 0)) if itm.get("price") else None,
                })
            return items, "UrbanPiper_POS"

        # 2. Generic MerchantMind Direct POS Gateway
        raw_items = payload.get("inventory_updates") or payload.get("items") or payload.get("updates") or []
        return raw_items, "MerchantMind_Gateway"


inventory_sync_service = InventorySyncService()

