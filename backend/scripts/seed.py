"""
Seed script — populate database with sample merchant and products.
Run: python -m scripts.seed
"""

import asyncio
import sys
import os

# Add parent dir to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, async_session, Base
from app.models.merchant import Merchant
from app.models.product import Product


SAMPLE_MERCHANT = {
    "name": "Sweet Bakes Bakery",
    "email": "hello@sweetbakes.in",
    "phone": "+919876543210",
    "description": "Artisan bakery in Koramangala, Bangalore. Fresh cakes, pastries, and custom orders. Delivering happiness since 2019.",
    "whatsapp_number": "+919876543210",
}

SAMPLE_PRODUCTS = [
    # Cakes
    {"name": "Classic Chocolate Truffle Cake", "price": 650, "category": "Cakes", "description": "Rich Belgian chocolate layers with ganache frosting. Serves 8-10.", "tags": ["chocolate", "birthday", "bestseller"], "image_url": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=400"},
    {"name": "Red Velvet Dream Cake", "price": 750, "category": "Cakes", "description": "Moist red velvet with cream cheese frosting. Serves 8-10.", "tags": ["red velvet", "birthday", "premium"], "image_url": "https://images.unsplash.com/photo-1616541823729-00fe0aacd32c?w=400"},
    {"name": "Butterscotch Crunch Cake", "price": 550, "category": "Cakes", "description": "Light butterscotch sponge with caramel crunch topping. Serves 6-8.", "tags": ["butterscotch", "kids-favourite"], "image_url": "https://images.unsplash.com/photo-1621303837174-89787a7d4729?w=400"},
    {"name": "Fresh Fruit Gateau", "price": 850, "category": "Cakes", "description": "Vanilla sponge layered with seasonal fruits and whipped cream. Serves 8-10.", "tags": ["fruit", "light", "healthy"], "image_url": "https://images.unsplash.com/photo-1565958011703-44f9829ba187?w=400"},
    {"name": "Black Forest Cake", "price": 600, "category": "Cakes", "description": "Classic German recipe with cherries and chocolate shavings. Serves 8.", "tags": ["chocolate", "cherry", "classic"], "image_url": "https://images.unsplash.com/photo-1606890737304-57a1ca8a5b62?w=400"},
    {"name": "Pineapple Upside Down Cake", "price": 500, "category": "Cakes", "description": "Caramelized pineapple rings on moist vanilla sponge. Serves 6-8.", "tags": ["pineapple", "classic", "budget"], "image_url": "https://images.unsplash.com/photo-1464349095431-e9a21285b5f3?w=400"},

    # Pastries
    {"name": "Chocolate Eclair (Pack of 3)", "price": 180, "category": "Pastries", "description": "Classic French eclairs with chocolate cream filling.", "tags": ["chocolate", "french", "snack"], "image_url": "https://images.unsplash.com/photo-1525059696034-4967a8e1dca2?w=400"},
    {"name": "Blueberry Cheesecake Slice", "price": 220, "category": "Pastries", "description": "New York style cheesecake with blueberry compote.", "tags": ["cheesecake", "blueberry", "premium"], "image_url": "https://images.unsplash.com/photo-1533134242443-d4fd215305ad?w=400"},
    {"name": "Almond Croissant", "price": 120, "category": "Pastries", "description": "Buttery, flaky croissant with almond cream and sliced almonds.", "tags": ["croissant", "french", "breakfast"], "image_url": "https://images.unsplash.com/photo-1555507036-ab1f4038024a?w=400"},

    # Party Supplies
    {"name": "Birthday Candles Set (24 pcs)", "price": 50, "category": "Party Supplies", "description": "Colorful spiral candles with holders. Perfect for any birthday cake.", "tags": ["birthday", "candles", "addon"], "image_url": "https://images.unsplash.com/photo-1513151233558-d860c5398176?w=400"},
    {"name": "Party Combo: Cake + Candles + Balloons", "price": 999, "category": "Combos", "description": "Chocolate Truffle Cake (1kg) + Birthday Candles + 10 Helium Balloons. Save ₹200!", "tags": ["birthday", "combo", "value", "bestseller"], "image_url": "https://images.unsplash.com/photo-1530103862676-de8c9debad1d?w=400"},

    # Breads
    {"name": "Sourdough Loaf", "price": 200, "category": "Breads", "description": "Artisan sourdough with a perfect crust. 500g.", "tags": ["bread", "sourdough", "artisan"], "image_url": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400"},
    {"name": "Garlic Herb Focaccia", "price": 180, "category": "Breads", "description": "Italian flatbread with roasted garlic, rosemary, and olive oil.", "tags": ["bread", "garlic", "italian"], "image_url": "https://images.unsplash.com/photo-1573140401552-3fab0b24306f?w=400"},

    # Beverages
    {"name": "Hot Chocolate (Large)", "price": 150, "category": "Beverages", "description": "Rich Belgian hot chocolate with marshmallows.", "tags": ["beverage", "chocolate", "hot"], "image_url": "https://images.unsplash.com/photo-1542990253-0d0f5be5f0ed?w=400"},
    {"name": "Cold Coffee Frappe", "price": 180, "category": "Beverages", "description": "Blended iced coffee with cream and chocolate drizzle.", "tags": ["beverage", "coffee", "cold"], "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=400"},

    # Custom
    {"name": "Custom Photo Cake (1kg)", "price": 1200, "category": "Custom", "description": "Personalized cake with your photo printed on edible paper. Allow 24 hours.", "tags": ["custom", "photo", "premium", "birthday"], "image_url": "https://images.unsplash.com/photo-1558301211-0d8c8ddee6ec?w=400"},
]


async def seed():
    """Seed the database with sample data."""
    print("🌱 Seeding database...")

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Check if merchant already exists
        from sqlalchemy import select
        result = await session.execute(
            select(Merchant).where(Merchant.email == SAMPLE_MERCHANT["email"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"⚠️  Merchant '{existing.name}' already exists. Skipping seed.")
            return

        # Create merchant
        merchant = Merchant(**SAMPLE_MERCHANT)
        session.add(merchant)
        await session.flush()
        print(f"✅ Created merchant: {merchant.name} (ID: {merchant.id})")

        # Create products
        for prod_data in SAMPLE_PRODUCTS:
            product = Product(merchant_id=merchant.id, **prod_data)
            product.schema_json = product.to_schema_org()
            session.add(product)

        await session.commit()
        print(f"✅ Created {len(SAMPLE_PRODUCTS)} products")
        print(f"\n🎉 Seed complete! Merchant ID: {merchant.id}")
        print(f"   Try: GET /api/merchants/{merchant.id}/catalog.json")


if __name__ == "__main__":
    asyncio.run(seed())
