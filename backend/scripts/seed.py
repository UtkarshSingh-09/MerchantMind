"""
Seed script — populate database with 50 diverse Bangalore food merchants and 300+ catalog products.
Run: python -m scripts.seed
"""

import asyncio
import sys
import os

# Add parent dir to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.database import engine, async_session, Base
from app.models.merchant import Merchant
from app.models.product import Product


MERCHANTS_DATA = [
    # ═══════════════════════════════════════════════════════════════
    # 1. Sweet Bakes Bakery — Koramangala
    # ═══════════════════════════════════════════════════════════════
    {
        "merchant": {
            "name": "Sweet Bakes Bakery",
            "email": "hello@sweetbakes.in",
            "phone": "+919876543210",
            "description": "Artisan bakery in Koramangala, Bangalore. Fresh designer cakes, pastries, sourdough breads, and custom party orders.",
            "whatsapp_number": "+919876543210",
            "store_latitude": 12.9352,
            "store_longitude": 77.6245,
            "store_address": "80ft Road, Koramangala 4th Block, Bengaluru 560034",
        },
        "products": [
            {"name": "Classic Chocolate Truffle Cake", "price": 650, "category": "Cakes", "description": "Rich Belgian dark chocolate layers with silky ganache frosting. Serves 8-10.", "tags": ["chocolate", "birthday", "bestseller", "eggless"], "image_url": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=500"},
            {"name": "Red Velvet Dream Cake", "price": 750, "category": "Cakes", "description": "Moist red velvet sponge with smooth cream cheese frosting. Serves 8-10.", "tags": ["red velvet", "birthday", "premium"], "image_url": "https://images.unsplash.com/photo-1616541823729-00fe0aacd32c?w=500"},
            {"name": "Butterscotch Crunch Cake", "price": 550, "category": "Cakes", "description": "Light butterscotch sponge with golden praline caramel crunch. Serves 6-8.", "tags": ["butterscotch", "kids-favourite", "budget"], "image_url": "https://images.unsplash.com/photo-1621303837174-89787a7d4729?w=500"},
            {"name": "Chocolate Eclair (Box of 3)", "price": 180, "category": "Pastries", "description": "French choux pastry filled with silky vanilla cream & topped with chocolate.", "tags": ["chocolate", "french", "snack"], "image_url": "https://images.unsplash.com/photo-1525059696034-4967a8e1dca2?w=500"},
            {"name": "Blueberry Cheesecake Slice", "price": 220, "category": "Pastries", "description": "Creamy baked New York cheesecake topped with wild blueberry compote.", "tags": ["cheesecake", "blueberry", "premium"], "image_url": "https://images.unsplash.com/photo-1533134242443-d4fd215305ad?w=500"},
            {"name": "Almond Butter Croissant", "price": 140, "category": "Pastries", "description": "Flaky French butter croissant loaded with roasted almond frangipane.", "tags": ["croissant", "french", "breakfast"], "image_url": "https://images.unsplash.com/photo-1555507036-ab1f4038024a?w=500"},
            {"name": "Rustic Sourdough Boule (500g)", "price": 200, "category": "Breads", "description": "36-hour slow fermented sourdough with blistered crust and open crumb.", "tags": ["bread", "sourdough", "artisan", "vegan"], "image_url": "https://images.unsplash.com/photo-1586444248902-2f64eddc13df?w=500"},
            {"name": "Belgian Hot Chocolate (Large)", "price": 150, "category": "Beverages", "description": "Thick steamed milk blended with real dark chocolate buttons and marshmallows.", "tags": ["beverage", "chocolate", "hot"], "image_url": "https://images.unsplash.com/photo-1542990253-0d0f5be5f0ed?w=500"},
        ],
    },
    # ═══════════════════════════════════════════════════════════════
    # 2. Iyengar Bakery — KR Puram
    # ═══════════════════════════════════════════════════════════════
    {
        "merchant": {
            "name": "Iyengar Bakery KR Puram",
            "email": "krpuram@iyengarbakery.in",
            "phone": "+919845012345",
            "description": "Traditional Iyengar bakery in KR Puram serving fresh bread, buns, cakes and snacks since 1985.",
            "whatsapp_number": "+919845012345",
            "store_latitude": 13.0074,
            "store_longitude": 77.6969,
            "store_address": "KR Puram Main Road, Near Railway Station, Bengaluru 560036",
        },
        "products": [
            {"name": "Honey Cake", "price": 350, "category": "Cakes", "description": "Classic Iyengar bakery honey cake with caramel drizzle. Serves 6.", "tags": ["honey", "classic", "budget"], "image_url": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=500"},
            {"name": "Khara Bun", "price": 15, "category": "Breads", "description": "Spicy masala-filled savory bun, a Bangalore classic.", "tags": ["bread", "snack", "spicy", "budget"], "image_url": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500"},
            {"name": "Dilkush", "price": 20, "category": "Pastries", "description": "Sweet tutti-frutti filled pastry puff, bakery signature.", "tags": ["sweet", "pastry", "classic"], "image_url": "https://images.unsplash.com/photo-1525059696034-4967a8e1dca2?w=500"},
            {"name": "Veg Puff", "price": 25, "category": "Pastries", "description": "Crispy flaky puff pastry with spiced potato-peas filling.", "tags": ["snack", "veg", "budget"], "image_url": "https://images.unsplash.com/photo-1525059696034-4967a8e1dca2?w=500"},
            {"name": "Plum Cake", "price": 280, "category": "Cakes", "description": "Rich fruit-loaded plum cake with rum essence.", "tags": ["plum", "christmas", "classic"], "image_url": "https://images.unsplash.com/photo-1606890737304-57a1ca8a5b62?w=500"},
            {"name": "Filter Coffee", "price": 30, "category": "Beverages", "description": "Strong South Indian filter coffee with fresh milk.", "tags": ["coffee", "hot", "desi"], "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=500"},
        ],
    },
    # ═══════════════════════════════════════════════════════════════
    # 3. Meghana Foods — Marathahalli
    # ═══════════════════════════════════════════════════════════════
    {
        "merchant": {
            "name": "Meghana Foods Marathahalli",
            "email": "marathahalli@meghanafoods.in",
            "phone": "+919900112233",
            "description": "Iconic Bangalore biryani and Andhra restaurant in Marathahalli. Known for bone-in chicken biryani and fiery Andhra meals.",
            "whatsapp_number": "+919900112233",
            "store_latitude": 12.9591,
            "store_longitude": 77.6974,
            "store_address": "Marathahalli Bridge, Near Innovative Multiplex, Bengaluru 560037",
        },
        "products": [
            {"name": "Chicken Dum Biryani", "price": 320, "category": "Biryani", "description": "Slow-cooked Hyderabadi style bone-in chicken biryani with raita.", "tags": ["biryani", "chicken", "bestseller", "non-veg"], "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500"},
            {"name": "Mutton Biryani", "price": 420, "category": "Biryani", "description": "Premium goat meat biryani cooked in sealed handi for 2 hours.", "tags": ["biryani", "mutton", "premium", "non-veg"], "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500"},
            {"name": "Andhra Chicken Curry Meal", "price": 250, "category": "Main Course", "description": "Spicy Andhra chicken curry with rice, dal, and pickles.", "tags": ["andhra", "chicken", "spicy", "meal"], "image_url": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=500"},
            {"name": "Paneer Butter Masala", "price": 220, "category": "North Indian", "description": "Creamy tomato-cashew gravy with soft paneer cubes.", "tags": ["paneer", "veg", "north-indian", "creamy"], "image_url": "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=500"},
            {"name": "Apollo Fish", "price": 280, "category": "Starters", "description": "Crispy fried fish fillets in tangy Andhra masala coating.", "tags": ["fish", "starter", "andhra", "spicy"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Gulab Jamun (4 pcs)", "price": 80, "category": "Desserts", "description": "Soft melt-in-mouth milk solid dumplings in sugar syrup.", "tags": ["dessert", "sweet", "indian"], "image_url": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=500"},
        ],
    },
    # ═══════════════════════════════════════════════════════════════
    # 4. Corner House — Residency Road
    # ═══════════════════════════════════════════════════════════════
    {
        "merchant": {
            "name": "Corner House Ice Cream",
            "email": "residency@cornerhouse.in",
            "phone": "+919845678901",
            "description": "Legendary Bangalore ice cream parlour on Residency Road. Famous for Death by Chocolate since 1982.",
            "whatsapp_number": "+919845678901",
            "store_latitude": 12.9719,
            "store_longitude": 77.6062,
            "store_address": "131, Residency Road, Ashok Nagar, Bengaluru 560025",
        },
        "products": [
            {"name": "Death by Chocolate", "price": 190, "category": "Desserts", "description": "Iconic DBC — chocolate ice cream, brownie, hot fudge, nuts, and whipped cream.", "tags": ["chocolate", "ice-cream", "legendary", "bestseller"], "image_url": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=500"},
            {"name": "Hot Chocolate Fudge", "price": 160, "category": "Desserts", "description": "Vanilla ice cream drowned in warm Belgian chocolate fudge sauce.", "tags": ["chocolate", "ice-cream", "classic"], "image_url": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=500"},
            {"name": "Corner House Sundae", "price": 170, "category": "Desserts", "description": "Mixed ice cream sundae with fruits, nuts, and caramel sauce.", "tags": ["sundae", "ice-cream", "fruity"], "image_url": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=500"},
            {"name": "Mango Mastani", "price": 150, "category": "Beverages", "description": "Thick mango milkshake topped with ice cream scoop.", "tags": ["mango", "shake", "summer"], "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=500"},
            {"name": "Brownie with Ice Cream", "price": 140, "category": "Desserts", "description": "Warm fudgy brownie served with vanilla ice cream.", "tags": ["brownie", "warm", "ice-cream"], "image_url": "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=500"},
        ],
    },
    # ═══════════════════════════════════════════════════════════════
    # 5. Vidyarthi Bhavan — Basavanagudi
    # ═══════════════════════════════════════════════════════════════
    {
        "merchant": {
            "name": "Vidyarthi Bhavan",
            "email": "info@vidyarthibhavan.in",
            "phone": "+919880012345",
            "description": "Heritage South Indian restaurant in Basavanagudi since 1943. Famous for crispy butter masala dosa.",
            "whatsapp_number": "+919880012345",
            "store_latitude": 12.9434,
            "store_longitude": 77.5712,
            "store_address": "32, Gandhi Bazaar Main Road, Basavanagudi, Bengaluru 560004",
        },
        "products": [
            {"name": "Masala Dosa", "price": 90, "category": "South Indian", "description": "Crispy golden dosa with spiced potato filling, served with chutney and sambar.", "tags": ["dosa", "south-indian", "bestseller", "veg"], "image_url": "https://images.unsplash.com/photo-1630383249896-424e482df921?w=500"},
            {"name": "Plain Dosa", "price": 60, "category": "South Indian", "description": "Paper-thin crispy dosa with coconut chutney and lentil sambar.", "tags": ["dosa", "south-indian", "budget", "veg"], "image_url": "https://images.unsplash.com/photo-1630383249896-424e482df921?w=500"},
            {"name": "Khara Bath", "price": 50, "category": "South Indian", "description": "Spiced rava upma with cashews, mustard seeds, and curry leaves.", "tags": ["breakfast", "south-indian", "budget"], "image_url": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=500"},
            {"name": "Kesari Bath", "price": 50, "category": "Desserts", "description": "Sweet saffron semolina halwa with ghee and cashews.", "tags": ["sweet", "south-indian", "saffron"], "image_url": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=500"},
            {"name": "Filter Coffee", "price": 25, "category": "Beverages", "description": "Authentic South Indian filter kaapi in steel tumbler.", "tags": ["coffee", "hot", "south-indian"], "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=500"},
            {"name": "Idli Vada Combo", "price": 70, "category": "South Indian", "description": "2 soft idlis + 1 crispy medu vada with chutney and sambar.", "tags": ["idli", "vada", "breakfast", "veg"], "image_url": "https://images.unsplash.com/photo-1630383249896-424e482df921?w=500"},
        ],
    },
    # ═══════════════════════════════════════════════════════════════
    # 6. MTR — Lalbagh Road
    # ═══════════════════════════════════════════════════════════════
    {
        "merchant": {
            "name": "MTR 1924",
            "email": "lalbagh@mavallitiffinrooms.in",
            "phone": "+919845098765",
            "description": "Mavalli Tiffin Rooms — Bangalore's most iconic restaurant since 1924. Known for rava idli and filter coffee.",
            "whatsapp_number": "+919845098765",
            "store_latitude": 12.9508,
            "store_longitude": 77.5806,
            "store_address": "14, Lalbagh Road, Mavalli, Bengaluru 560004",
        },
        "products": [
            {"name": "Rava Idli (3 pcs)", "price": 80, "category": "South Indian", "description": "MTR's legendary rava idli — the dish they invented. Served with chutney and sambar.", "tags": ["idli", "rava", "legendary", "veg"], "image_url": "https://images.unsplash.com/photo-1630383249896-424e482df921?w=500"},
            {"name": "Masala Dosa", "price": 100, "category": "South Indian", "description": "Thin crispy dosa with classic potato palya and accompaniments.", "tags": ["dosa", "south-indian", "classic"], "image_url": "https://images.unsplash.com/photo-1630383249896-424e482df921?w=500"},
            {"name": "Bisi Bele Bath", "price": 110, "category": "South Indian", "description": "Spicy lentil-rice one-pot dish with vegetables, ghee, and boondi.", "tags": ["rice", "south-indian", "spicy", "veg"], "image_url": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=500"},
            {"name": "MTR Filter Coffee", "price": 35, "category": "Beverages", "description": "Rich decoction coffee served in traditional dabarah set.", "tags": ["coffee", "hot", "legendary"], "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=500"},
            {"name": "Badam Halwa", "price": 90, "category": "Desserts", "description": "Rich almond halwa slow-cooked with ghee and saffron.", "tags": ["sweet", "halwa", "premium"], "image_url": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=500"},
        ],
    },
    # ═══════════════════════════════════════════════════════════════
    # 7. Truffles — Indiranagar
    # ═══════════════════════════════════════════════════════════════
    {
        "merchant": {
            "name": "Truffles Indiranagar",
            "email": "indiranagar@truffles.in",
            "phone": "+919900334455",
            "description": "Bangalore's favorite burger joint in Indiranagar. Massive burgers, steaks, and legendary desserts.",
            "whatsapp_number": "+919900334455",
            "store_latitude": 12.9784,
            "store_longitude": 77.6408,
            "store_address": "93, 12th Main, HAL 2nd Stage, Indiranagar, Bengaluru 560038",
        },
        "products": [
            {"name": "Classic Beef Burger", "price": 350, "category": "Main Course", "description": "Juicy hand-pressed beef patty with lettuce, tomato, cheese, and signature sauce.", "tags": ["burger", "beef", "bestseller", "non-veg"], "image_url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=500"},
            {"name": "Paneer Steak", "price": 280, "category": "Main Course", "description": "Grilled cottage cheese steak with mashed potatoes and gravy.", "tags": ["paneer", "steak", "veg"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Loaded Cheese Fries", "price": 220, "category": "Starters", "description": "Crispy fries smothered in cheddar cheese sauce and jalapeños.", "tags": ["fries", "cheese", "snack"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Death by Chocolate Waffle", "price": 290, "category": "Desserts", "description": "Belgian waffle drowned in chocolate sauce, ice cream, and brownie chunks.", "tags": ["waffle", "chocolate", "dessert"], "image_url": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=500"},
            {"name": "Cold Coffee Frappe", "price": 180, "category": "Beverages", "description": "Thick iced coffee frappe blended with ice cream.", "tags": ["coffee", "cold", "beverage"], "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=500"},
        ],
    },
    # ═══════════════════════════════════════════════════════════════
    # 8. Empire Restaurant — Jayanagar
    # ═══════════════════════════════════════════════════════════════
    {
        "merchant": {
            "name": "Empire Restaurant Jayanagar",
            "email": "jayanagar@empirerestaurant.in",
            "phone": "+919845112233",
            "description": "Iconic Bangalore non-veg restaurant chain. 24/7 biryani, kebabs, and Andhra meals in Jayanagar 4th Block.",
            "whatsapp_number": "+919845112233",
            "store_latitude": 12.9272,
            "store_longitude": 77.5838,
            "store_address": "36th Cross, Jayanagar 4th Block, Bengaluru 560011",
        },
        "products": [
            {"name": "Empire Special Biryani", "price": 280, "category": "Biryani", "description": "Signature Empire chicken biryani with boiled egg and raita.", "tags": ["biryani", "chicken", "bestseller"], "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500"},
            {"name": "Chicken Kebab Platter", "price": 320, "category": "Starters", "description": "Assorted tandoori kebabs — seekh, tikka, and malai.", "tags": ["kebab", "tandoori", "non-veg"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Mutton Rogan Josh", "price": 350, "category": "North Indian", "description": "Kashmiri-style slow-cooked mutton in aromatic gravy.", "tags": ["mutton", "kashmiri", "premium"], "image_url": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=500"},
            {"name": "Rumali Roti (2 pcs)", "price": 50, "category": "Breads", "description": "Paper-thin handkerchief bread, freshly tossed.", "tags": ["bread", "roti", "budget"], "image_url": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500"},
            {"name": "Phirni", "price": 70, "category": "Desserts", "description": "Creamy rice pudding flavored with cardamom and pistachios.", "tags": ["dessert", "sweet", "cold"], "image_url": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=500"},
        ],
    },
    # ═══════════════════════════════════════════════════════════════
    # 9. Third Wave Coffee — HSR Layout
    # ═══════════════════════════════════════════════════════════════
    {
        "merchant": {
            "name": "Third Wave Coffee HSR",
            "email": "hsr@thirdwavecoffee.in",
            "phone": "+919900556677",
            "description": "Specialty coffee roasters and café in HSR Layout. Single-origin pour-overs, cold brews, and artisan food.",
            "whatsapp_number": "+919900556677",
            "store_latitude": 12.9116,
            "store_longitude": 77.6389,
            "store_address": "27th Main, HSR Layout Sector 1, Bengaluru 560102",
        },
        "products": [
            {"name": "Pour Over V60 (Single Origin)", "price": 250, "category": "Beverages", "description": "Hand-brewed V60 pour over with single-origin Chikmagalur beans.", "tags": ["coffee", "specialty", "hot", "premium"], "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=500"},
            {"name": "Iced Hazelnut Latte", "price": 280, "category": "Beverages", "description": "Espresso with hazelnut syrup, cold milk, and ice.", "tags": ["coffee", "cold", "hazelnut"], "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=500"},
            {"name": "Avocado Toast", "price": 320, "category": "Main Course", "description": "Sourdough toast with smashed avocado, cherry tomatoes, and poached egg.", "tags": ["breakfast", "healthy", "avocado"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Blueberry Muffin", "price": 150, "category": "Pastries", "description": "Freshly baked jumbo muffin loaded with wild blueberries.", "tags": ["muffin", "blueberry", "bakery"], "image_url": "https://images.unsplash.com/photo-1525059696034-4967a8e1dca2?w=500"},
            {"name": "Matcha Latte", "price": 300, "category": "Beverages", "description": "Ceremonial grade matcha whisked with steamed oat milk.", "tags": ["matcha", "latte", "healthy"], "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=500"},
        ],
    },
    # ═══════════════════════════════════════════════════════════════
    # 10. Brahmin's Coffee Bar — Shankarapuram
    # ═══════════════════════════════════════════════════════════════
    {
        "merchant": {
            "name": "Brahmin's Coffee Bar",
            "email": "info@brahminscoffeebar.in",
            "phone": "+919845567890",
            "description": "Legendary standing-only tiffin spot near Shankarapuram since 1960s. Famous for idli-vada and filter coffee.",
            "whatsapp_number": "+919845567890",
            "store_latitude": 12.9592,
            "store_longitude": 77.5694,
            "store_address": "Ranga Rao Road, Shankarapuram, Bengaluru 560004",
        },
        "products": [
            {"name": "Idli (3 pcs)", "price": 30, "category": "South Indian", "description": "Pillowy soft steamed rice cakes with chutney and sambar.", "tags": ["idli", "breakfast", "budget", "veg"], "image_url": "https://images.unsplash.com/photo-1630383249896-424e482df921?w=500"},
            {"name": "Medu Vada (2 pcs)", "price": 30, "category": "South Indian", "description": "Crispy golden urad dal vada, perfectly shaped.", "tags": ["vada", "crispy", "breakfast"], "image_url": "https://images.unsplash.com/photo-1630383249896-424e482df921?w=500"},
            {"name": "Khara Bath + Kesari Bath Combo", "price": 40, "category": "South Indian", "description": "Savory rava khara bath paired with sweet saffron kesari.", "tags": ["combo", "south-indian", "budget"], "image_url": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=500"},
            {"name": "Strong Filter Coffee", "price": 15, "category": "Beverages", "description": "No-frills strong filter kaapi in steel tumbler.", "tags": ["coffee", "hot", "budget"], "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=500"},
        ],
    },
    # ═══════════════════════════════════════════════════════════════
    # 11. Chinita — Whitefield
    # ═══════════════════════════════════════════════════════════════
    {
        "merchant": {
            "name": "Chinita Real Mexican Food",
            "email": "whitefield@chinita.in",
            "phone": "+919900778899",
            "description": "Authentic Mexican restaurant in Whitefield. Tacos, burritos, quesadillas, and margaritas.",
            "whatsapp_number": "+919900778899",
            "store_latitude": 12.9698,
            "store_longitude": 77.7500,
            "store_address": "ITPL Main Road, Whitefield, Bengaluru 560066",
        },
        "products": [
            {"name": "Chicken Burrito Bowl", "price": 380, "category": "Main Course", "description": "Grilled chicken with Mexican rice, beans, salsa, sour cream, and guacamole.", "tags": ["mexican", "burrito", "chicken", "non-veg"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Paneer Tacos (3 pcs)", "price": 320, "category": "Main Course", "description": "Corn tortilla tacos with spiced paneer, pico de gallo, and chipotle.", "tags": ["tacos", "mexican", "veg"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Loaded Nachos", "price": 280, "category": "Starters", "description": "Crispy tortilla chips with cheese sauce, jalapeños, salsa, and sour cream.", "tags": ["nachos", "cheese", "snack"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Churros with Chocolate Dip", "price": 220, "category": "Desserts", "description": "Freshly fried cinnamon churros with warm Nutella dip.", "tags": ["churros", "dessert", "sweet"], "image_url": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=500"},
            {"name": "Virgin Mojito", "price": 180, "category": "Beverages", "description": "Refreshing lime, mint, and soda mocktail.", "tags": ["mocktail", "cold", "refreshing"], "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=500"},
        ],
    },
    # ═══════════════════════════════════════════════════════════════
    # 12. Shivaji Military Hotel — VV Puram
    # ═══════════════════════════════════════════════════════════════
    {
        "merchant": {
            "name": "Shivaji Military Hotel",
            "email": "vvpuram@shivajimilitary.in",
            "phone": "+919845234567",
            "description": "Old-school military hotel in VV Puram food street. Ragi mudde, mutton curry, and donne biryani specialists.",
            "whatsapp_number": "+919845234567",
            "store_latitude": 12.9486,
            "store_longitude": 77.5746,
            "store_address": "VV Puram Food Street, Chamarajpet, Bengaluru 560018",
        },
        "products": [
            {"name": "Ragi Mudde + Mutton Curry", "price": 200, "category": "Main Course", "description": "Traditional ragi ball with spicy bone-in mutton saaru.", "tags": ["ragi", "mutton", "traditional", "non-veg"], "image_url": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=500"},
            {"name": "Donne Biryani (Chicken)", "price": 180, "category": "Biryani", "description": "Bangalore-style biryani served in areca leaf cup (donne).", "tags": ["biryani", "donne", "chicken", "local"], "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500"},
            {"name": "Keema Ball Curry", "price": 160, "category": "Main Course", "description": "Spiced minced meat balls in thick onion-tomato gravy.", "tags": ["keema", "non-veg", "spicy"], "image_url": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=500"},
            {"name": "Jowar Roti (2 pcs)", "price": 30, "category": "Breads", "description": "Handmade sorghum flatbread, nutritious and gluten-free.", "tags": ["bread", "healthy", "budget"], "image_url": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500"},
        ],
    },
    # ═══════════════════════════════════════════════════════════════
    # 13. Hole in the Wall Café — Koramangala
    # ═══════════════════════════════════════════════════════════════
    {
        "merchant": {
            "name": "Hole in the Wall Café",
            "email": "koramangala@holeinthewall.in",
            "phone": "+919900223344",
            "description": "Charming European-style café in Koramangala. Brunch, pasta, wood-fired pizzas, and craft cocktails.",
            "whatsapp_number": "+919900223344",
            "store_latitude": 12.9343,
            "store_longitude": 77.6150,
            "store_address": "4th B Cross, Koramangala 5th Block, Bengaluru 560095",
        },
        "products": [
            {"name": "Margherita Wood-Fired Pizza", "price": 420, "category": "Main Course", "description": "Classic Neapolitan pizza with San Marzano tomatoes, mozzarella, and fresh basil.", "tags": ["pizza", "italian", "wood-fired", "veg"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Truffle Mushroom Pasta", "price": 480, "category": "Main Course", "description": "Penne in creamy truffle oil sauce with sautéed mushrooms and parmesan.", "tags": ["pasta", "truffle", "italian", "veg"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Eggs Benedict", "price": 350, "category": "Main Course", "description": "Poached eggs on English muffin with hollandaise sauce and smoked salmon.", "tags": ["brunch", "eggs", "premium"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Banoffee Pie Slice", "price": 250, "category": "Desserts", "description": "Layered banana, toffee, and whipped cream on digestive biscuit base.", "tags": ["pie", "banana", "dessert"], "image_url": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=500"},
            {"name": "Fresh Squeezed Orange Juice", "price": 180, "category": "Beverages", "description": "100% fresh Nagpur orange juice, no sugar added.", "tags": ["juice", "fresh", "healthy"], "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=500"},
        ],
    },
    # ═══════════════════════════════════════════════════════════════
    # 14. Nagarjuna — Brigade Road
    # ═══════════════════════════════════════════════════════════════
    {
        "merchant": {
            "name": "Nagarjuna Brigade Road",
            "email": "brigade@nagarjuna.in",
            "phone": "+919845345678",
            "description": "Famous Andhra meals restaurant on Brigade Road. Unlimited thali and fiery chicken curries.",
            "whatsapp_number": "+919845345678",
            "store_latitude": 12.9736,
            "store_longitude": 77.6033,
            "store_address": "44/1, Brigade Road, Ashok Nagar, Bengaluru 560025",
        },
        "products": [
            {"name": "Andhra Meals (Unlimited)", "price": 250, "category": "South Indian", "description": "Full unlimited Andhra thali — rice, sambar, rasam, 3 curries, curd, pickle, papad.", "tags": ["thali", "andhra", "unlimited", "veg"], "image_url": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=500"},
            {"name": "Chicken Curry Meals", "price": 300, "category": "Main Course", "description": "Andhra chicken curry with rice, sambar, rasam, and sides.", "tags": ["chicken", "andhra", "spicy", "non-veg"], "image_url": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=500"},
            {"name": "Guntur Chilli Chicken", "price": 280, "category": "Starters", "description": "Fiery dry chilli chicken with Guntur red chillies.", "tags": ["chicken", "spicy", "andhra", "starter"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Pesarattu", "price": 80, "category": "South Indian", "description": "Green moong dal dosa, Andhra specialty breakfast.", "tags": ["dosa", "healthy", "andhra", "veg"], "image_url": "https://images.unsplash.com/photo-1630383249896-424e482df921?w=500"},
            {"name": "Payasam", "price": 60, "category": "Desserts", "description": "Sweet vermicelli kheer with cardamom and cashews.", "tags": ["dessert", "sweet", "south-indian"], "image_url": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=500"},
        ],
    },
    # ═══════════════════════════════════════════════════════════════
    # 15. Toscano — UB City
    # ═══════════════════════════════════════════════════════════════
    {
        "merchant": {
            "name": "Toscano UB City",
            "email": "ubcity@toscano.in",
            "phone": "+919900445566",
            "description": "Premium Italian fine dining at UB City Mall. Hand-rolled pasta, risottos, and imported wines.",
            "whatsapp_number": "+919900445566",
            "store_latitude": 12.9715,
            "store_longitude": 77.5960,
            "store_address": "UB City Mall, 24 Vittal Mallya Road, Bengaluru 560001",
        },
        "products": [
            {"name": "Truffle Risotto", "price": 750, "category": "Main Course", "description": "Arborio rice slow-cooked with black truffle, parmesan, and white wine.", "tags": ["risotto", "truffle", "italian", "premium"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Four Cheese Pizza", "price": 650, "category": "Main Course", "description": "Wood-fired pizza with mozzarella, gorgonzola, fontina, and parmesan.", "tags": ["pizza", "cheese", "italian"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Tiramisu", "price": 450, "category": "Desserts", "description": "Classic Italian tiramisu with espresso-soaked ladyfingers and mascarpone.", "tags": ["tiramisu", "dessert", "italian", "premium"], "image_url": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=500"},
            {"name": "Bruschetta Trio", "price": 480, "category": "Starters", "description": "Three artisan bruschetta — tomato basil, mushroom truffle, ricotta honey.", "tags": ["bruschetta", "starter", "italian"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Espresso Martini", "price": 550, "category": "Beverages", "description": "Coffee liqueur shaken with fresh espresso and vodka.", "tags": ["cocktail", "coffee", "premium"], "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=500"},
        ],
    },
    # ═══════════════════════════════════════════════════════════════
    # 16-50: More Bangalore Food Merchants
    # ═══════════════════════════════════════════════════════════════
    {
        "merchant": {
            "name": "Daddy's Deli Bakery",
            "email": "btm@daddysdeli.in", "phone": "+919845456789",
            "description": "Neighborhood bakery in BTM Layout. Fresh breads, cakes, and affordable snacks.",
            "whatsapp_number": "+919845456789",
            "store_latitude": 12.9166, "store_longitude": 77.6101,
            "store_address": "16th Main, BTM Layout 2nd Stage, Bengaluru 560076",
        },
        "products": [
            {"name": "Vanilla Sponge Cake", "price": 400, "category": "Cakes", "description": "Light and fluffy vanilla cake with buttercream frosting.", "tags": ["vanilla", "cake", "birthday"], "image_url": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=500"},
            {"name": "Chicken Puff", "price": 35, "category": "Pastries", "description": "Flaky puff pastry with spiced chicken filling.", "tags": ["snack", "non-veg", "budget"], "image_url": "https://images.unsplash.com/photo-1525059696034-4967a8e1dca2?w=500"},
            {"name": "Masala Bread", "price": 40, "category": "Breads", "description": "Soft bread topped with spiced masala and onions.", "tags": ["bread", "snack", "spicy"], "image_url": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500"},
            {"name": "Pineapple Pastry", "price": 50, "category": "Pastries", "description": "Classic pineapple cream pastry slice.", "tags": ["pastry", "pineapple", "budget"], "image_url": "https://images.unsplash.com/photo-1525059696034-4967a8e1dca2?w=500"},
        ],
    },
    {
        "merchant": {
            "name": "Bangalore Iyengar Bakery Whitefield",
            "email": "whitefield@blriyengar.in", "phone": "+919845567890",
            "description": "Traditional South Indian bakery in Whitefield with fresh buns, cakes, and filter coffee.",
            "whatsapp_number": "+919845567890",
            "store_latitude": 12.9698, "store_longitude": 77.7499,
            "store_address": "Whitefield Main Road, Near ITPL, Bengaluru 560066",
        },
        "products": [
            {"name": "Butter Cake", "price": 300, "category": "Cakes", "description": "Rich butter pound cake with golden crust.", "tags": ["butter", "cake", "classic"], "image_url": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=500"},
            {"name": "Egg Puff", "price": 20, "category": "Pastries", "description": "Puff pastry with whole boiled egg inside.", "tags": ["egg", "snack", "budget"], "image_url": "https://images.unsplash.com/photo-1525059696034-4967a8e1dca2?w=500"},
            {"name": "Bread Toast with Butter", "price": 25, "category": "Breads", "description": "Crispy toasted bread slices with Amul butter.", "tags": ["toast", "breakfast", "budget"], "image_url": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500"},
            {"name": "Badam Milk", "price": 40, "category": "Beverages", "description": "Warm almond-flavored milk with saffron.", "tags": ["milk", "almond", "hot"], "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=500"},
        ],
    },
    {
        "merchant": {
            "name": "Chung Wah Chinese Kitchen",
            "email": "jp@chungwah.in", "phone": "+919900667788",
            "description": "Indo-Chinese restaurant near JP Nagar. Manchurian, fried rice, and dragon chicken.",
            "whatsapp_number": "+919900667788",
            "store_latitude": 12.9077, "store_longitude": 77.5857,
            "store_address": "15th Cross, JP Nagar 2nd Phase, Bengaluru 560078",
        },
        "products": [
            {"name": "Dragon Chicken", "price": 280, "category": "Chinese", "description": "Crispy fried chicken tossed in spicy dragon sauce.", "tags": ["chinese", "chicken", "spicy"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Veg Manchurian Gravy", "price": 200, "category": "Chinese", "description": "Mixed vegetable dumplings in tangy soy-chilli gravy.", "tags": ["chinese", "veg", "manchurian"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Chicken Fried Rice", "price": 220, "category": "Chinese", "description": "Wok-tossed rice with chicken, egg, and vegetables.", "tags": ["rice", "chinese", "chicken"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Hakka Noodles", "price": 180, "category": "Chinese", "description": "Stir-fried egg noodles with vegetables and soy sauce.", "tags": ["noodles", "chinese", "veg"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Sweet Corn Soup", "price": 120, "category": "Starters", "description": "Creamy sweet corn soup with crunchy corn kernels.", "tags": ["soup", "starter", "veg"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
        ],
    },
    {
        "merchant": {
            "name": "Adigas Vegetarian Restaurant",
            "email": "malleshwaram@adigas.in", "phone": "+919845678912",
            "description": "Pure vegetarian South Indian restaurant in Malleshwaram. Classic tiffin, meals, and sweets.",
            "whatsapp_number": "+919845678912",
            "store_latitude": 13.0035, "store_longitude": 77.5645,
            "store_address": "Sampige Road, Malleshwaram, Bengaluru 560003",
        },
        "products": [
            {"name": "Benne Masala Dosa", "price": 80, "category": "South Indian", "description": "Crispy butter-laden dosa with potato masala.", "tags": ["dosa", "butter", "south-indian", "veg"], "image_url": "https://images.unsplash.com/photo-1630383249896-424e482df921?w=500"},
            {"name": "Curd Rice", "price": 60, "category": "South Indian", "description": "Cooling yogurt rice with tempering and pomegranate.", "tags": ["rice", "curd", "comfort", "veg"], "image_url": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=500"},
            {"name": "Mysore Pak (250g)", "price": 180, "category": "Desserts", "description": "Traditional ghee-rich gram flour sweet, soft and melt-in-mouth.", "tags": ["sweet", "mysore-pak", "traditional"], "image_url": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=500"},
            {"name": "Mini Meals Thali", "price": 130, "category": "South Indian", "description": "Mini South Indian thali with rice, sambar, rasam, palya, and curd.", "tags": ["thali", "meals", "veg", "budget"], "image_url": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=500"},
            {"name": "Badam Milk", "price": 50, "category": "Beverages", "description": "Hot almond milk with saffron and cardamom.", "tags": ["milk", "almond", "hot"], "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=500"},
        ],
    },
    {
        "merchant": {
            "name": "Rameshwaram Cafe",
            "email": "brookefield@rameshwaramcafe.in", "phone": "+919900889900",
            "description": "Viral South Indian tiffin chain in Brookefield. Famous for ghee-loaded dosas and butter idlis.",
            "whatsapp_number": "+919900889900",
            "store_latitude": 12.9860, "store_longitude": 77.7150,
            "store_address": "ITPL Road, Brookefield, Bengaluru 560037",
        },
        "products": [
            {"name": "Ghee Podi Dosa", "price": 150, "category": "South Indian", "description": "Crispy dosa drizzled with ghee and spicy gun powder.", "tags": ["dosa", "ghee", "spicy", "bestseller"], "image_url": "https://images.unsplash.com/photo-1630383249896-424e482df921?w=500"},
            {"name": "Butter Idli (4 pcs)", "price": 120, "category": "South Indian", "description": "Soft idlis tossed in butter with podi and chutney.", "tags": ["idli", "butter", "breakfast"], "image_url": "https://images.unsplash.com/photo-1630383249896-424e482df921?w=500"},
            {"name": "Mysore Masala Dosa", "price": 130, "category": "South Indian", "description": "Dosa with red chutney spread, potato masala, and ghee.", "tags": ["dosa", "mysore", "spicy", "veg"], "image_url": "https://images.unsplash.com/photo-1630383249896-424e482df921?w=500"},
            {"name": "Pani Puri (6 pcs)", "price": 80, "category": "Starters", "description": "Crispy puris filled with spiced potato and tangy pani.", "tags": ["chaat", "snack", "street-food"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Buttermilk", "price": 40, "category": "Beverages", "description": "Spiced churned buttermilk with curry leaves and ginger.", "tags": ["buttermilk", "cold", "healthy"], "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=500"},
        ],
    },
    {
        "merchant": {
            "name": "The Fatty Bao",
            "email": "indiranagar@thefattybao.in", "phone": "+919900112244",
            "description": "Pan-Asian gastropub in Indiranagar. Dim sum, bao buns, ramen, and Asian cocktails.",
            "whatsapp_number": "+919900112244",
            "store_latitude": 12.9810, "store_longitude": 77.6389,
            "store_address": "12th Main, HAL 2nd Stage, Indiranagar, Bengaluru 560008",
        },
        "products": [
            {"name": "Pork Belly Bao (2 pcs)", "price": 450, "category": "Main Course", "description": "Steamed fluffy bao buns with braised pork belly, hoisin, and pickled cucumber.", "tags": ["bao", "pork", "asian", "premium"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Truffle Edamame Dumplings (6 pcs)", "price": 380, "category": "Starters", "description": "Pan-fried dumplings with truffle edamame filling.", "tags": ["dumplings", "truffle", "veg"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Tonkotsu Ramen", "price": 520, "category": "Main Course", "description": "Rich pork bone broth ramen with chashu, soft egg, and nori.", "tags": ["ramen", "japanese", "pork"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Mochi Ice Cream (3 pcs)", "price": 280, "category": "Desserts", "description": "Japanese rice cake wrapped around matcha, mango, and strawberry ice cream.", "tags": ["mochi", "dessert", "japanese"], "image_url": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=500"},
        ],
    },
    {
        "merchant": {
            "name": "Meghana Foods Electronic City",
            "email": "ecity@meghanafoods.in", "phone": "+919845789012",
            "description": "Meghana Foods outlet in Electronic City. Biryani, Andhra meals, and kebabs.",
            "whatsapp_number": "+919845789012",
            "store_latitude": 12.8456, "store_longitude": 77.6603,
            "store_address": "Electronic City Phase 1, Hosur Road, Bengaluru 560100",
        },
        "products": [
            {"name": "Chicken Dum Biryani", "price": 310, "category": "Biryani", "description": "Slow-cooked Hyderabadi biryani with bone-in chicken pieces.", "tags": ["biryani", "chicken", "bestseller"], "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500"},
            {"name": "Egg Biryani", "price": 220, "category": "Biryani", "description": "Aromatic biryani rice with boiled eggs and gravy.", "tags": ["biryani", "egg", "budget"], "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500"},
            {"name": "Chicken 65", "price": 240, "category": "Starters", "description": "Deep-fried spicy chicken with curry leaves and red chillies.", "tags": ["chicken", "starter", "spicy"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Paneer Tikka", "price": 200, "category": "Starters", "description": "Tandoor-roasted paneer cubes with bell peppers and onions.", "tags": ["paneer", "tikka", "veg"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Double Ka Meetha", "price": 90, "category": "Desserts", "description": "Hyderabadi bread pudding soaked in saffron milk.", "tags": ["dessert", "hyderabadi", "sweet"], "image_url": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=500"},
        ],
    },
    {
        "merchant": {
            "name": "Onesta Pizza Banashankari",
            "email": "bsk@onesta.in", "phone": "+919900334466",
            "description": "Unlimited pizza, pasta, and starter chain in Banashankari.",
            "whatsapp_number": "+919900334466",
            "store_latitude": 12.9177, "store_longitude": 77.5600,
            "store_address": "80ft Road, Banashankari 2nd Stage, Bengaluru 560070",
        },
        "products": [
            {"name": "Farmhouse Pizza", "price": 350, "category": "Main Course", "description": "Loaded with onion, capsicum, tomato, mushroom, and olives.", "tags": ["pizza", "veg", "loaded"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "BBQ Chicken Pizza", "price": 420, "category": "Main Course", "description": "BBQ sauce base with grilled chicken, onions, and jalapeños.", "tags": ["pizza", "bbq", "chicken"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Penne Arrabiata", "price": 280, "category": "Main Course", "description": "Penne pasta in spicy tomato sauce with chilli flakes and garlic.", "tags": ["pasta", "spicy", "italian"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Garlic Bread (4 pcs)", "price": 150, "category": "Starters", "description": "Crispy garlic bread with herb butter and cheese.", "tags": ["bread", "garlic", "snack"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Brownie Sundae", "price": 180, "category": "Desserts", "description": "Warm chocolate brownie with vanilla ice cream and chocolate sauce.", "tags": ["brownie", "sundae", "dessert"], "image_url": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=500"},
        ],
    },
    {
        "merchant": {
            "name": "Veena Stores",
            "email": "malleshwaram@veenastores.in", "phone": "+919845890123",
            "description": "Iconic breakfast joint in Malleshwaram. Queue-worthy idli, vada, and kesari bath.",
            "whatsapp_number": "+919845890123",
            "store_latitude": 13.0087, "store_longitude": 77.5695,
            "store_address": "15th Cross, Margosa Road, Malleshwaram, Bengaluru 560003",
        },
        "products": [
            {"name": "Idli (4 pcs)", "price": 40, "category": "South Indian", "description": "Legendary soft pillowy idlis served with three chutneys.", "tags": ["idli", "breakfast", "legendary", "veg"], "image_url": "https://images.unsplash.com/photo-1630383249896-424e482df921?w=500"},
            {"name": "Vada (2 pcs)", "price": 30, "category": "South Indian", "description": "Perfectly crispy medu vadas, Bangalore's best.", "tags": ["vada", "crispy", "budget"], "image_url": "https://images.unsplash.com/photo-1630383249896-424e482df921?w=500"},
            {"name": "Kesari Bath", "price": 30, "category": "Desserts", "description": "Sweet saffron rava halwa with ghee and cashews.", "tags": ["sweet", "saffron", "budget"], "image_url": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=500"},
            {"name": "Filter Coffee", "price": 15, "category": "Beverages", "description": "Strong filter kaapi, the perfect companion.", "tags": ["coffee", "hot", "budget"], "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=500"},
        ],
    },
    {
        "merchant": {
            "name": "Café Azzure Bellandur",
            "email": "bellandur@cafeazzure.in", "phone": "+919900556688",
            "description": "Modern café and bakery in Bellandur serving continental food, cakes, and specialty coffee.",
            "whatsapp_number": "+919900556688",
            "store_latitude": 12.9260, "store_longitude": 77.6762,
            "store_address": "Bellandur Main Road, Near Sony Signal, Bengaluru 560103",
        },
        "products": [
            {"name": "Red Velvet Pastry", "price": 180, "category": "Pastries", "description": "Moist red velvet slice with cream cheese frosting.", "tags": ["pastry", "red-velvet", "premium"], "image_url": "https://images.unsplash.com/photo-1525059696034-4967a8e1dca2?w=500"},
            {"name": "Club Sandwich", "price": 280, "category": "Main Course", "description": "Triple-decker sandwich with chicken, bacon, lettuce, and mayo.", "tags": ["sandwich", "non-veg", "lunch"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Cappuccino", "price": 180, "category": "Beverages", "description": "Classic Italian cappuccino with velvety milk foam art.", "tags": ["coffee", "hot", "italian"], "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=500"},
            {"name": "Chocolate Lava Cake", "price": 250, "category": "Desserts", "description": "Warm chocolate cake with molten center, served with ice cream.", "tags": ["chocolate", "lava", "warm", "dessert"], "image_url": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=500"},
        ],
    },
    {
        "merchant": {
            "name": "A2B Adyar Ananda Bhavan Yelahanka",
            "email": "yelahanka@a2b.in", "phone": "+919845901234",
            "description": "Pure veg South Indian chain restaurant in Yelahanka. Sweets, snacks, and meals.",
            "whatsapp_number": "+919845901234",
            "store_latitude": 13.1005, "store_longitude": 77.5941,
            "store_address": "Yelahanka New Town Main Road, Bengaluru 560064",
        },
        "products": [
            {"name": "Mini Tiffin Combo", "price": 120, "category": "South Indian", "description": "2 idli + 1 vada + mini dosa + coffee. Complete breakfast.", "tags": ["combo", "breakfast", "south-indian", "veg"], "image_url": "https://images.unsplash.com/photo-1630383249896-424e482df921?w=500"},
            {"name": "Ghee Roast Dosa", "price": 100, "category": "South Indian", "description": "Extra-crispy dosa generously coated in pure ghee.", "tags": ["dosa", "ghee", "crispy", "veg"], "image_url": "https://images.unsplash.com/photo-1630383249896-424e482df921?w=500"},
            {"name": "Kaju Katli (250g)", "price": 350, "category": "Desserts", "description": "Silver-foiled cashew fudge, premium quality.", "tags": ["sweet", "kaju", "gift", "premium"], "image_url": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=500"},
            {"name": "Samosa (2 pcs)", "price": 40, "category": "Starters", "description": "Crispy triangular pastry with spiced potato filling.", "tags": ["samosa", "snack", "budget", "veg"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Jigarthanda", "price": 80, "category": "Beverages", "description": "Madurai-style chilled almond milk dessert drink.", "tags": ["cold", "sweet", "traditional"], "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=500"},
        ],
    },
    {
        "merchant": {
            "name": "Khan Saheb Grills & Rolls",
            "email": "hsr@khansaheb.in", "phone": "+919900778800",
            "description": "Mughlai rolls and kebabs joint in HSR Layout. Seekh rolls, shawarma, and biryani.",
            "whatsapp_number": "+919900778800",
            "store_latitude": 12.9116, "store_longitude": 77.6474,
            "store_address": "14th Main, HSR Layout Sector 4, Bengaluru 560102",
        },
        "products": [
            {"name": "Chicken Seekh Roll", "price": 180, "category": "Main Course", "description": "Flaky paratha wrapped around juicy chicken seekh kebab with chutney.", "tags": ["roll", "kebab", "chicken", "non-veg"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Paneer Tikka Roll", "price": 160, "category": "Main Course", "description": "Grilled paneer tikka in rumali roti with mint chutney.", "tags": ["roll", "paneer", "veg"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Chicken Shawarma", "price": 150, "category": "Main Course", "description": "Lebanese-style grilled chicken in pita with garlic sauce.", "tags": ["shawarma", "chicken", "budget"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Mutton Galouti Kebab (4 pcs)", "price": 320, "category": "Starters", "description": "Melt-in-mouth Lucknowi mutton kebabs on ulte tawa.", "tags": ["kebab", "mutton", "premium"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
        ],
    },
    {
        "merchant": {
            "name": "Pot Belly Rooftop Café",
            "email": "koramangala@potbelly.in", "phone": "+919900112255",
            "description": "Rooftop Bihari café in Koramangala. Litti chokha, sattu paratha, and desi thali.",
            "whatsapp_number": "+919900112255",
            "store_latitude": 12.9343, "store_longitude": 77.6263,
            "store_address": "1st Cross, Koramangala 6th Block, Bengaluru 560095",
        },
        "products": [
            {"name": "Litti Chokha (3 pcs)", "price": 200, "category": "Main Course", "description": "Roasted wheat balls with sattu filling, served with mashed brinjal chokha.", "tags": ["bihari", "litti", "traditional", "veg"], "image_url": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=500"},
            {"name": "Sattu Paratha", "price": 120, "category": "Main Course", "description": "Stuffed flatbread with roasted gram flour filling.", "tags": ["paratha", "sattu", "healthy", "veg"], "image_url": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=500"},
            {"name": "Mutton Champaran", "price": 380, "category": "Main Course", "description": "Slow-cooked Bihar-style mutton in earthen pot with mustard oil.", "tags": ["mutton", "bihari", "premium", "non-veg"], "image_url": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=500"},
            {"name": "Makhana Kheer", "price": 100, "category": "Desserts", "description": "Creamy fox nut pudding with saffron and dry fruits.", "tags": ["dessert", "kheer", "traditional"], "image_url": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=500"},
        ],
    },
    {
        "merchant": {
            "name": "Brik Oven Sadashivanagar",
            "email": "palace@brikoven.in", "phone": "+919845012378",
            "description": "Wood-fired pizza and Italian restaurant near Palace Grounds, Sadashivanagar.",
            "whatsapp_number": "+919845012378",
            "store_latitude": 12.9950, "store_longitude": 77.5780,
            "store_address": "Bellary Road, Sadashivanagar, Bengaluru 560080",
        },
        "products": [
            {"name": "Diavola Pizza", "price": 550, "category": "Main Course", "description": "Spicy salami, nduja, and chilli flakes on Neapolitan base.", "tags": ["pizza", "spicy", "italian", "non-veg"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Burrata Salad", "price": 480, "category": "Starters", "description": "Creamy burrata with heirloom tomatoes, basil, and balsamic reduction.", "tags": ["salad", "burrata", "italian", "veg"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Panna Cotta", "price": 350, "category": "Desserts", "description": "Silky vanilla panna cotta with mixed berry compote.", "tags": ["dessert", "italian", "premium"], "image_url": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=500"},
            {"name": "Limoncello Soda", "price": 250, "category": "Beverages", "description": "Italian lemon liqueur soda with fresh mint.", "tags": ["soda", "lemon", "italian"], "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=500"},
        ],
    },
    {
        "merchant": {
            "name": "Ambur Star Biryani",
            "email": "silk@amburstar.in", "phone": "+919845123450",
            "description": "Authentic Ambur-style biryani joint near Silk Board. Short-grain seeraga samba rice biryani.",
            "whatsapp_number": "+919845123450",
            "store_latitude": 12.9172, "store_longitude": 77.6227,
            "store_address": "Silk Board Junction, BTM Layout, Bengaluru 560076",
        },
        "products": [
            {"name": "Ambur Chicken Biryani", "price": 250, "category": "Biryani", "description": "Tamil-style biryani with seeraga samba rice and spiced chicken.", "tags": ["biryani", "ambur", "chicken", "bestseller"], "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500"},
            {"name": "Ambur Mutton Biryani", "price": 350, "category": "Biryani", "description": "Premium goat meat Ambur biryani with brinjal gravy (kuska).", "tags": ["biryani", "mutton", "premium"], "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500"},
            {"name": "Chicken Fry (Quarter)", "price": 180, "category": "Starters", "description": "Crispy South Indian style chicken fry with curry leaves.", "tags": ["chicken", "fry", "spicy"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Birista Raita", "price": 40, "category": "Starters", "description": "Yogurt with crispy fried onions and spices.", "tags": ["raita", "side", "budget"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
        ],
    },
    {
        "merchant": {
            "name": "CTR Shri Sagar",
            "email": "malleshwaram@ctrsagar.in", "phone": "+919845234590",
            "description": "Legendary benne dosa place in Malleshwaram since 1920s.",
            "whatsapp_number": "+919845234590",
            "store_latitude": 13.0044, "store_longitude": 77.5644,
            "store_address": "7th Cross, Margosa Road, Malleshwaram, Bengaluru 560003",
        },
        "products": [
            {"name": "Benne Dosa", "price": 60, "category": "South Indian", "description": "Famous thick butter-soaked dosa, crispy outside and soft inside.", "tags": ["dosa", "benne", "legendary", "veg"], "image_url": "https://images.unsplash.com/photo-1630383249896-424e482df921?w=500"},
            {"name": "Benne Masala Dosa", "price": 80, "category": "South Indian", "description": "Butter dosa with spiced potato filling.", "tags": ["dosa", "masala", "butter", "veg"], "image_url": "https://images.unsplash.com/photo-1630383249896-424e482df921?w=500"},
            {"name": "Khali Dosa", "price": 45, "category": "South Indian", "description": "Plain paper-thin dosa without filling.", "tags": ["dosa", "plain", "budget"], "image_url": "https://images.unsplash.com/photo-1630383249896-424e482df921?w=500"},
            {"name": "Filter Coffee", "price": 20, "category": "Beverages", "description": "Hot South Indian filter coffee.", "tags": ["coffee", "hot", "budget"], "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=500"},
        ],
    },
    {
        "merchant": {
            "name": "Café Noir Cunningham Road",
            "email": "cunningham@cafenoir.in", "phone": "+919900223355",
            "description": "French-inspired café on Cunningham Road. Crepes, quiches, and artisan coffee.",
            "whatsapp_number": "+919900223355",
            "store_latitude": 12.9856, "store_longitude": 77.5907,
            "store_address": "38, Cunningham Road, Vasanth Nagar, Bengaluru 560052",
        },
        "products": [
            {"name": "Nutella Crepe", "price": 280, "category": "Desserts", "description": "Thin French crepe filled with warm Nutella and sliced bananas.", "tags": ["crepe", "nutella", "dessert"], "image_url": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=500"},
            {"name": "Mushroom Quiche", "price": 320, "category": "Main Course", "description": "Savory tart with sautéed mushrooms, gruyere, and cream.", "tags": ["quiche", "mushroom", "french", "veg"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Croque Monsieur", "price": 350, "category": "Main Course", "description": "French grilled ham and cheese sandwich with béchamel.", "tags": ["sandwich", "french", "premium"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "French Press Coffee", "price": 200, "category": "Beverages", "description": "Rich French press brewed single-origin coffee.", "tags": ["coffee", "french-press", "hot"], "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=500"},
        ],
    },
    {
        "merchant": {
            "name": "Al-Sham Shawarma",
            "email": "frazer@alsham.in", "phone": "+919845345690",
            "description": "Authentic Middle Eastern shawarma and falafel near Frazer Town.",
            "whatsapp_number": "+919845345690",
            "store_latitude": 12.9929, "store_longitude": 77.6196,
            "store_address": "Mosque Road, Frazer Town, Bengaluru 560005",
        },
        "products": [
            {"name": "Chicken Shawarma Plate", "price": 200, "category": "Main Course", "description": "Spit-roasted chicken with hummus, pickles, garlic sauce, and pita.", "tags": ["shawarma", "chicken", "middle-eastern"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Falafel Wrap", "price": 180, "category": "Main Course", "description": "Crispy chickpea falafel in pita with tahini and salad.", "tags": ["falafel", "veg", "middle-eastern"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Hummus with Pita", "price": 150, "category": "Starters", "description": "Creamy chickpea hummus with warm pita bread.", "tags": ["hummus", "veg", "starter"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Turkish Tea", "price": 80, "category": "Beverages", "description": "Strong black tea served in traditional tulip glass.", "tags": ["tea", "hot", "turkish"], "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=500"},
        ],
    },
    {
        "merchant": {
            "name": "Mani's Dum Biryani Sarjapur",
            "email": "sarjapur@manisbiryani.in", "phone": "+919845456701",
            "description": "Hyderabadi dum biryani specialist in Sarjapur Road.",
            "whatsapp_number": "+919845456701",
            "store_latitude": 12.9100, "store_longitude": 77.6850,
            "store_address": "Sarjapur Road, Near Wipro Corporate Office, Bengaluru 560035",
        },
        "products": [
            {"name": "Special Dum Biryani", "price": 290, "category": "Biryani", "description": "Slow-cooked dum biryani with marinated chicken and saffron rice.", "tags": ["biryani", "dum", "chicken"], "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500"},
            {"name": "Veg Dum Biryani", "price": 220, "category": "Biryani", "description": "Mixed vegetable dum biryani with paneer and cashews.", "tags": ["biryani", "veg", "paneer"], "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500"},
            {"name": "Chicken Lollipop", "price": 220, "category": "Starters", "description": "Crispy Indo-Chinese chicken drumettes in spicy glaze.", "tags": ["chicken", "starter", "chinese"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Shahi Tukda", "price": 80, "category": "Desserts", "description": "Royal bread pudding soaked in cardamom-saffron rabri.", "tags": ["dessert", "mughlai", "sweet"], "image_url": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=500"},
        ],
    },
    {
        "merchant": {
            "name": "Glen's Bakehouse",
            "email": "indiranagar@glensbakehouse.in", "phone": "+919900445577",
            "description": "Artisan European bakery in Indiranagar. Sourdough, croissants, quiches, and cakes.",
            "whatsapp_number": "+919900445577",
            "store_latitude": 12.9787, "store_longitude": 77.6389,
            "store_address": "100ft Road, Indiranagar, Bengaluru 560038",
        },
        "products": [
            {"name": "Classic Croissant", "price": 120, "category": "Pastries", "description": "Buttery laminated French croissant with 27 layers.", "tags": ["croissant", "french", "breakfast"], "image_url": "https://images.unsplash.com/photo-1555507036-ab1f4038024a?w=500"},
            {"name": "Sourdough Loaf", "price": 250, "category": "Breads", "description": "24-hour fermented country sourdough with open crumb.", "tags": ["sourdough", "bread", "artisan"], "image_url": "https://images.unsplash.com/photo-1586444248902-2f64eddc13df?w=500"},
            {"name": "Baked Cheesecake", "price": 350, "category": "Cakes", "description": "New York-style baked cheesecake with graham cracker base.", "tags": ["cheesecake", "baked", "premium"], "image_url": "https://images.unsplash.com/photo-1533134242443-d4fd215305ad?w=500"},
            {"name": "Spinach Feta Quiche", "price": 280, "category": "Main Course", "description": "Savory tart with spinach, feta, and sun-dried tomatoes.", "tags": ["quiche", "veg", "brunch"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Flat White", "price": 200, "category": "Beverages", "description": "Double ristretto with velvety microfoam milk.", "tags": ["coffee", "hot", "specialty"], "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=500"},
        ],
    },
    {
        "merchant": {
            "name": "Nandini Sweets Rajajinagar",
            "email": "rajaji@nandinisweets.in", "phone": "+919845567812",
            "description": "Traditional Indian sweets and namkeen shop in Rajajinagar.",
            "whatsapp_number": "+919845567812",
            "store_latitude": 12.9920, "store_longitude": 77.5520,
            "store_address": "10th Main, Rajajinagar 1st Block, Bengaluru 560010",
        },
        "products": [
            {"name": "Gulab Jamun (500g)", "price": 200, "category": "Desserts", "description": "Soft milk-solid dumplings in rose-flavored sugar syrup.", "tags": ["sweet", "gulab-jamun", "traditional"], "image_url": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=500"},
            {"name": "Rasmalai (6 pcs)", "price": 250, "category": "Desserts", "description": "Soft cottage cheese patties in saffron-cardamom milk.", "tags": ["sweet", "rasmalai", "premium"], "image_url": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=500"},
            {"name": "Besan Ladoo (250g)", "price": 180, "category": "Desserts", "description": "Gram flour ladoos with ghee, cardamom, and dry fruits.", "tags": ["sweet", "ladoo", "traditional"], "image_url": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=500"},
            {"name": "Mixture Namkeen (200g)", "price": 80, "category": "Starters", "description": "Crunchy South Indian style mixture with peanuts and curry leaves.", "tags": ["snack", "namkeen", "savoury"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
        ],
    },
    {
        "merchant": {
            "name": "Paradise Biryani Hebbal",
            "email": "hebbal@paradisebiryani.in", "phone": "+919845678923",
            "description": "Hyderabadi biryani chain outlet in Hebbal. Dum biryani and kebabs.",
            "whatsapp_number": "+919845678923",
            "store_latitude": 13.0358, "store_longitude": 77.5970,
            "store_address": "Outer Ring Road, Hebbal, Bengaluru 560024",
        },
        "products": [
            {"name": "Paradise Special Biryani", "price": 340, "category": "Biryani", "description": "Signature Hyderabadi chicken dum biryani with mirchi ka salan.", "tags": ["biryani", "hyderabadi", "chicken", "bestseller"], "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500"},
            {"name": "Mutton Dum Biryani", "price": 450, "category": "Biryani", "description": "Premium bone-in mutton biryani slow-cooked for 3 hours.", "tags": ["biryani", "mutton", "premium"], "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500"},
            {"name": "Tangdi Kebab (4 pcs)", "price": 320, "category": "Starters", "description": "Tandoori chicken drumsticks marinated in yogurt and spices.", "tags": ["kebab", "tandoori", "chicken"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Qubani Ka Meetha", "price": 100, "category": "Desserts", "description": "Traditional Hyderabadi apricot dessert with cream.", "tags": ["dessert", "hyderabadi", "traditional"], "image_url": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=500"},
        ],
    },
    {
        "merchant": {
            "name": "Bob's Bar & Grill Sarjapur",
            "email": "sarjapur@bobsbar.in", "phone": "+919900667799",
            "description": "Casual bar and grill in Sarjapur. Wings, burgers, craft beer, and game nights.",
            "whatsapp_number": "+919900667799",
            "store_latitude": 12.9060, "store_longitude": 77.6900,
            "store_address": "Sarjapur Road, Near Total Mall, Bengaluru 560102",
        },
        "products": [
            {"name": "Buffalo Wings (12 pcs)", "price": 380, "category": "Starters", "description": "Crispy chicken wings tossed in hot buffalo sauce.", "tags": ["wings", "spicy", "bar-snack"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Smoked BBQ Burger", "price": 420, "category": "Main Course", "description": "Smoked beef patty with BBQ sauce, coleslaw, and pickles.", "tags": ["burger", "bbq", "non-veg"], "image_url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=500"},
            {"name": "Loaded Potato Skins", "price": 280, "category": "Starters", "description": "Baked potato skins with cheese, bacon bits, and sour cream.", "tags": ["potato", "cheese", "bar-snack"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Chocolate Mud Pie", "price": 250, "category": "Desserts", "description": "Dense chocolate pie with Oreo crust and whipped cream.", "tags": ["chocolate", "dessert", "premium"], "image_url": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=500"},
            {"name": "Virgin Pina Colada", "price": 220, "category": "Beverages", "description": "Creamy coconut and pineapple blended mocktail.", "tags": ["mocktail", "cold", "tropical"], "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=500"},
        ],
    },
    {
        "merchant": {
            "name": "Dose Corner Majestic",
            "email": "majestic@dosecorner.in", "phone": "+919845789023",
            "description": "24/7 dosa joint near Majestic Bus Stand. Quick, affordable South Indian tiffin.",
            "whatsapp_number": "+919845789023",
            "store_latitude": 12.9767, "store_longitude": 77.5713,
            "store_address": "Dhanvanthri Road, Near Majestic Bus Stand, Bengaluru 560009",
        },
        "products": [
            {"name": "Set Dosa (3 pcs)", "price": 50, "category": "South Indian", "description": "Soft spongy set dosas served with coconut chutney.", "tags": ["dosa", "set", "budget", "veg"], "image_url": "https://images.unsplash.com/photo-1630383249896-424e482df921?w=500"},
            {"name": "Onion Rava Dosa", "price": 70, "category": "South Indian", "description": "Crispy semolina dosa with onions and green chillies.", "tags": ["dosa", "rava", "crispy", "veg"], "image_url": "https://images.unsplash.com/photo-1630383249896-424e482df921?w=500"},
            {"name": "Pongal", "price": 50, "category": "South Indian", "description": "Comfort food — rice-lentil porridge tempered with ghee and cashews.", "tags": ["pongal", "breakfast", "comfort", "veg"], "image_url": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=500"},
            {"name": "Masala Chai", "price": 20, "category": "Beverages", "description": "Strong ginger-cardamom tea.", "tags": ["tea", "chai", "hot", "budget"], "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=500"},
        ],
    },
    {
        "merchant": {
            "name": "Smoor Chocolate Lounge",
            "email": "church@smoor.in", "phone": "+919900889911",
            "description": "Premium chocolate lounge on Church Street. Artisan chocolates, desserts, and hot chocolate.",
            "whatsapp_number": "+919900889911",
            "store_latitude": 12.9749, "store_longitude": 77.6059,
            "store_address": "Church Street, Ashok Nagar, Bengaluru 560001",
        },
        "products": [
            {"name": "Belgian Dark Truffle Box (6 pcs)", "price": 550, "category": "Desserts", "description": "Hand-crafted Belgian dark chocolate truffles in premium gift box.", "tags": ["chocolate", "truffle", "gift", "premium"], "image_url": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=500"},
            {"name": "Single Origin Hot Chocolate", "price": 350, "category": "Beverages", "description": "Rich hot chocolate made with 72% single-origin cacao.", "tags": ["chocolate", "hot", "premium"], "image_url": "https://images.unsplash.com/photo-1542990253-0d0f5be5f0ed?w=500"},
            {"name": "Chocolate Fondant", "price": 420, "category": "Desserts", "description": "Warm chocolate lava cake with vanilla bean ice cream.", "tags": ["fondant", "chocolate", "warm"], "image_url": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=500"},
            {"name": "Macaron Box (8 pcs)", "price": 480, "category": "Pastries", "description": "Assorted French macarons — pistachio, rose, chocolate, salted caramel.", "tags": ["macaron", "french", "gift"], "image_url": "https://images.unsplash.com/photo-1525059696034-4967a8e1dca2?w=500"},
        ],
    },
    {
        "merchant": {
            "name": "Meghana Foods HSR Layout",
            "email": "hsr@meghanafoods.in", "phone": "+919845890134",
            "description": "Another beloved Meghana outlet in HSR Layout. Same great biryani and Andhra meals.",
            "whatsapp_number": "+919845890134",
            "store_latitude": 12.9120, "store_longitude": 77.6380,
            "store_address": "27th Main, HSR Layout Sector 1, Bengaluru 560102",
        },
        "products": [
            {"name": "Chicken Dum Biryani", "price": 310, "category": "Biryani", "description": "Meghana's famous bone-in chicken biryani.", "tags": ["biryani", "chicken", "bestseller"], "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500"},
            {"name": "Paneer Biryani", "price": 250, "category": "Biryani", "description": "Aromatic biryani with marinated paneer cubes.", "tags": ["biryani", "paneer", "veg"], "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500"},
            {"name": "Mutton Pepper Fry", "price": 300, "category": "Starters", "description": "Dry-roasted mutton with cracked black pepper.", "tags": ["mutton", "pepper", "spicy"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Buttermilk", "price": 30, "category": "Beverages", "description": "Refreshing spiced buttermilk with curry leaves.", "tags": ["buttermilk", "cold", "healthy"], "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=500"},
        ],
    },
    {
        "merchant": {
            "name": "Udupi Sri Krishna Bhavan",
            "email": "magadi@udupikrishna.in", "phone": "+919845901245",
            "description": "Traditional Udupi vegetarian restaurant near Magadi Road.",
            "whatsapp_number": "+919845901245",
            "store_latitude": 12.9700, "store_longitude": 77.5500,
            "store_address": "Magadi Road, Near Chord Road Junction, Bengaluru 560023",
        },
        "products": [
            {"name": "Masala Dosa", "price": 70, "category": "South Indian", "description": "Classic Udupi masala dosa with potato bhaji.", "tags": ["dosa", "udupi", "classic", "veg"], "image_url": "https://images.unsplash.com/photo-1630383249896-424e482df921?w=500"},
            {"name": "North Karnataka Jolada Rotti Oota", "price": 150, "category": "Main Course", "description": "Jowar roti meals with ennegai, palya, and dal.", "tags": ["meals", "karnataka", "traditional", "veg"], "image_url": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=500"},
            {"name": "Goli Baje (6 pcs)", "price": 50, "category": "Starters", "description": "Mangalorean fluffy deep-fried dal fritters.", "tags": ["snack", "mangalore", "crispy", "veg"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Payasa", "price": 40, "category": "Desserts", "description": "Udupi-style sweet vermicelli payasam with jaggery.", "tags": ["sweet", "payasam", "traditional"], "image_url": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=500"},
        ],
    },
    {
        "merchant": {
            "name": "Cream Stone Marathahalli",
            "email": "marathon@creamstone.in", "phone": "+919900112266",
            "description": "Custom ice cream on stone counter. Mix your own toppings in Marathahalli.",
            "whatsapp_number": "+919900112266",
            "store_latitude": 12.9560, "store_longitude": 77.7010,
            "store_address": "Marathahalli Bridge, Bengaluru 560037",
        },
        "products": [
            {"name": "Cookie Monster Ice Cream", "price": 220, "category": "Desserts", "description": "Vanilla ice cream mixed with Oreo cookies and chocolate chips on frozen stone.", "tags": ["ice-cream", "oreo", "custom"], "image_url": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=500"},
            {"name": "Mango Tango", "price": 200, "category": "Desserts", "description": "Fresh mango ice cream with mango chunks and whipped cream.", "tags": ["mango", "ice-cream", "summer"], "image_url": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=500"},
            {"name": "Nutella Overload", "price": 250, "category": "Desserts", "description": "Chocolate ice cream with Nutella swirl, hazelnuts, and brownies.", "tags": ["nutella", "chocolate", "premium"], "image_url": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=500"},
            {"name": "Fresh Fruit Smoothie", "price": 180, "category": "Beverages", "description": "Blended seasonal fruits with yogurt.", "tags": ["smoothie", "healthy", "cold"], "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=500"},
        ],
    },
    {
        "merchant": {
            "name": "Kabab Magic Bellandur",
            "email": "bellandur@kababmagic.in", "phone": "+919845012367",
            "description": "Late-night kebab and biryani spot in Bellandur. Open till 2 AM.",
            "whatsapp_number": "+919845012367",
            "store_latitude": 12.9259, "store_longitude": 77.6744,
            "store_address": "Bellandur Gate, Outer Ring Road, Bengaluru 560103",
        },
        "products": [
            {"name": "Seekh Kebab Plate", "price": 200, "category": "Starters", "description": "Charcoal-grilled minced chicken kebabs with mint chutney.", "tags": ["kebab", "chicken", "grilled"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Chicken Shawarma Roll", "price": 130, "category": "Main Course", "description": "Grilled chicken wrap with garlic mayo and pickled onions.", "tags": ["shawarma", "roll", "budget"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Hyderabadi Biryani", "price": 260, "category": "Biryani", "description": "Late-night special dum biryani with raita.", "tags": ["biryani", "chicken", "late-night"], "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500"},
            {"name": "Tandoori Chai", "price": 40, "category": "Beverages", "description": "Smoky chai poured into kulhad from tandoor.", "tags": ["chai", "tandoori", "hot"], "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=500"},
        ],
    },
    {
        "merchant": {
            "name": "Anand Sweets & Savories Jayanagar",
            "email": "jayanagar@anandsweets.in", "phone": "+919845123478",
            "description": "Premium sweets, savories, and chaat in Jayanagar. Gift hampers and festive boxes.",
            "whatsapp_number": "+919845123478",
            "store_latitude": 12.9250, "store_longitude": 77.5838,
            "store_address": "11th Main, Jayanagar 4th Block, Bengaluru 560011",
        },
        "products": [
            {"name": "Motichoor Ladoo (250g)", "price": 220, "category": "Desserts", "description": "Fine boondi ladoos with saffron and cardamom.", "tags": ["sweet", "ladoo", "festive"], "image_url": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=500"},
            {"name": "Badam Halwa (250g)", "price": 300, "category": "Desserts", "description": "Rich almond halwa slow-cooked in ghee.", "tags": ["sweet", "halwa", "premium"], "image_url": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=500"},
            {"name": "Pani Puri Kit (serves 4)", "price": 120, "category": "Starters", "description": "DIY pani puri kit with puris, spiced water, and filling.", "tags": ["chaat", "snack", "party"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Festive Sweet Box (1kg)", "price": 800, "category": "Combos", "description": "Assorted premium sweets in gift box — kaju katli, peda, ladoo, barfi.", "tags": ["gift", "festive", "combo", "premium"], "image_url": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=500"},
        ],
    },
    {
        "merchant": {
            "name": "Darshini Fast Food Nagarbhavi",
            "email": "nagarbhavi@darshini.in", "phone": "+919845234501",
            "description": "Typical Bangalore darshini (standing restaurant) with quick South Indian tiffin and meals.",
            "whatsapp_number": "+919845234501",
            "store_latitude": 12.9600, "store_longitude": 77.5100,
            "store_address": "BDA Complex, Nagarbhavi Circle, Bengaluru 560072",
        },
        "products": [
            {"name": "Paper Dosa", "price": 55, "category": "South Indian", "description": "Extra-crispy paper-thin dosa, a foot long.", "tags": ["dosa", "paper", "crispy", "veg"], "image_url": "https://images.unsplash.com/photo-1630383249896-424e482df921?w=500"},
            {"name": "Gobi Manchurian (Dry)", "price": 100, "category": "Chinese", "description": "Crispy cauliflower tossed in Indo-Chinese dry sauce.", "tags": ["chinese", "gobi", "veg", "snack"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Chapati Meals", "price": 80, "category": "North Indian", "description": "2 chapatis with dal, rice, and vegetable curry.", "tags": ["meals", "chapati", "budget", "veg"], "image_url": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=500"},
            {"name": "Lime Soda", "price": 25, "category": "Beverages", "description": "Fresh lime soda, sweet or salty.", "tags": ["soda", "lime", "cold", "budget"], "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=500"},
        ],
    },
    {
        "merchant": {
            "name": "Black Pearl Seafood Frazer Town",
            "email": "frazer@blackpearl.in", "phone": "+919900334477",
            "description": "Coastal and Mangalorean seafood restaurant in Frazer Town. Fresh catch daily.",
            "whatsapp_number": "+919900334477",
            "store_latitude": 12.9940, "store_longitude": 77.6180,
            "store_address": "Mosque Road, Frazer Town, Bengaluru 560005",
        },
        "products": [
            {"name": "Mangalorean Fish Curry Meals", "price": 300, "category": "Main Course", "description": "Coconut-based tangy fish curry with red rice and pickle.", "tags": ["fish", "mangalore", "coastal", "non-veg"], "image_url": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=500"},
            {"name": "Prawn Ghee Roast", "price": 380, "category": "Starters", "description": "Mangalorean prawn ghee roast with curry leaves and spice.", "tags": ["prawn", "ghee-roast", "spicy", "premium"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Crab Masala", "price": 420, "category": "Main Course", "description": "Fresh crab in thick Mangalorean masala gravy.", "tags": ["crab", "masala", "premium", "coastal"], "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Neer Dosa (4 pcs)", "price": 80, "category": "South Indian", "description": "Thin rice crepes, perfect with seafood curries.", "tags": ["dosa", "neer", "mangalore"], "image_url": "https://images.unsplash.com/photo-1630383249896-424e482df921?w=500"},
            {"name": "Sol Kadhi", "price": 50, "category": "Beverages", "description": "Refreshing kokum and coconut milk digestif.", "tags": ["sol-kadhi", "kokum", "cold"], "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=500"},
        ],
    },
    {
        "merchant": {
            "name": "Kanti Sweets Vijayanagar",
            "email": "vijayanagar@kantisweets.in", "phone": "+919845345612",
            "description": "North Indian sweets and chaat joint in Vijayanagar.",
            "whatsapp_number": "+919845345612",
            "store_latitude": 12.9700, "store_longitude": 77.5360,
            "store_address": "MC Layout, Vijayanagar, Bengaluru 560040",
        },
        "products": [
            {"name": "Chole Bhature", "price": 100, "category": "North Indian", "description": "Spicy chickpea curry with fluffy deep-fried bhatura.", "tags": ["north-indian", "chole", "budget"], "image_url": "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=600&auto=format&fit=crop&q=80"},
            {"name": "Pav Bhaji", "price": 90, "category": "North Indian", "description": "Spiced mixed vegetable mash with butter pav.", "tags": ["pav-bhaji", "street-food", "veg"], "image_url": "https://images.unsplash.com/photo-1606491956689-2ea866880c84?w=600&auto=format&fit=crop&q=80"},
            {"name": "Raj Kachori", "price": 80, "category": "Starters", "description": "Large crispy kachori filled with curd, chutneys, and sev.", "tags": ["chaat", "snack", "festive"], "image_url": "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&auto=format&fit=crop&q=80"},
            {"name": "Jalebi (250g)", "price": 120, "category": "Desserts", "description": "Crispy spiral sweets dipped in sugar syrup, served warm.", "tags": ["jalebi", "sweet", "hot"], "image_url": "https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?w=600&auto=format&fit=crop&q=80"},
        ],
    },
]


async def seed():
    """Seed the database with 50 Bangalore food merchants and 250+ products."""
    print("🌱 Initializing MerchantMind 50-Merchant Bangalore Seed...")

    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        total_seeded_merchants = 0
        total_seeded_products = 0

        for entry in MERCHANTS_DATA:
            m_data = entry["merchant"]
            p_data_list = entry["products"]

            # 1. Check if merchant already exists
            res = await session.execute(
                select(Merchant).where(Merchant.email == m_data["email"])
            )
            merchant = res.scalar_one_or_none()

            if not merchant:
                merchant = Merchant(**m_data)
                session.add(merchant)
                await session.flush()
                print(f"✨ Created Merchant: '{merchant.name}' ({m_data.get('store_address', '')})")
                total_seeded_merchants += 1
            else:
                # Update merchant metadata including coordinates
                for key, val in m_data.items():
                    setattr(merchant, key, val)
                print(f"🔄 Updated Merchant: '{merchant.name}' ({m_data.get('store_address', '')})")

            # 2. Add or update products for this merchant
            for p_dict in p_data_list:
                p_stmt = select(Product).where(
                    Product.merchant_id == merchant.id,
                    Product.name == p_dict["name"],
                )
                p_res = await session.execute(p_stmt)
                existing_p = p_res.scalar_one_or_none()

                if not existing_p:
                    prod = Product(merchant_id=merchant.id, **p_dict)
                    prod.schema_json = prod.to_schema_org()
                    session.add(prod)
                    total_seeded_products += 1
                else:
                    existing_p.price = p_dict["price"]
                    existing_p.category = p_dict.get("category")
                    existing_p.description = p_dict.get("description")
                    existing_p.image_url = p_dict.get("image_url")
                    existing_p.tags = p_dict.get("tags")
                    existing_p.schema_json = existing_p.to_schema_org()

        await session.commit()
        print(f"\n🎉 Bangalore 50-Merchant Seed Complete!")
        print(f"   • Total Merchants: {len(MERCHANTS_DATA)}")
        print(f"   • New Products Added: {total_seeded_products}")
        print(f"   • Neighborhoods covered: Koramangala, KR Puram, Marathahalli, Indiranagar,")
        print(f"     HSR, Whitefield, Jayanagar, Basavanagudi, Malleshwaram, Banashankari,")
        print(f"     Electronic City, Hebbal, Yelahanka, Frazer Town, Sarjapur, and more!")


if __name__ == "__main__":
    asyncio.run(seed())
