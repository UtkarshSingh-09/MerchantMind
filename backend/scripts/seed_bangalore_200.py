"""
Elite Knowledge Base Seeder — 200 Authentic Bangalore Merchants × 5,000+ Genuine Dishes.
Populates real Bangalore food ecosystem across 20 neighborhoods with realistic prices, ratings, and tags.
"""

import asyncio
import os
import sys
import uuid
import random

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, delete, text
from app.database import async_session
from app.models.merchant import Merchant
from app.models.product import Product
from app.models.customer import Customer
from app.models.conversation import Conversation
from app.models.order import Order
from app.models.audit_log import AuditLog
from app.models.campaign import Campaign

NEIGHBORHOODS = [
    {"name": "Indiranagar", "lat": 12.9784, "lng": 77.6408, "address_suffix": "100 Feet Road, Indiranagar, Bengaluru 560038"},
    {"name": "Koramangala", "lat": 12.9352, "lng": 77.6245, "address_suffix": "80ft Road, 4th Block Koramangala, Bengaluru 560034"},
    {"name": "HSR Layout", "lat": 12.9121, "lng": 77.6446, "address_suffix": "27th Main, Sector 1 HSR Layout, Bengaluru 560102"},
    {"name": "Jayanagar", "lat": 12.9308, "lng": 77.5838, "address_suffix": "4th Block Jayanagar, Bengaluru 560011"},
    {"name": "JP Nagar", "lat": 12.9063, "lng": 77.5857, "address_suffix": "Phase 2 JP Nagar, Bengaluru 560078"},
    {"name": "Malleshwaram", "lat": 13.0031, "lng": 77.5643, "address_suffix": "Margosa Road, Malleshwaram, Bengaluru 560003"},
    {"name": "Basavanagudi", "lat": 12.9422, "lng": 77.5753, "address_suffix": "Gandhi Bazaar Main Road, Basavanagudi, Bengaluru 560004"},
    {"name": "Whitefield", "lat": 12.9698, "lng": 77.7500, "address_suffix": "ITPL Main Road, Whitefield, Bengaluru 560066"},
    {"name": "Marathahalli", "lat": 12.9591, "lng": 77.6974, "address_suffix": "Outer Ring Road, Marathahalli, Bengaluru 560037"},
    {"name": "Bellandur", "lat": 12.9304, "lng": 77.6784, "address_suffix": "Green Glen Layout, Bellandur, Bengaluru 560103"},
    {"name": "Sarjapur Road", "lat": 12.9105, "lng": 77.6833, "address_suffix": "Carmelaram Post, Sarjapur Road, Bengaluru 560035"},
    {"name": "Electronic City", "lat": 12.8452, "lng": 77.6602, "address_suffix": "Phase 1, Electronic City, Bengaluru 560100"},
    {"name": "Church Street", "lat": 12.9750, "lng": 77.6050, "address_suffix": "Church Street, Off MG Road, Bengaluru 560001"},
    {"name": "MG Road", "lat": 12.9756, "lng": 77.6066, "address_suffix": "Brigade Road Junction, MG Road, Bengaluru 560025"},
    {"name": "Frazer Town", "lat": 12.9982, "lng": 77.6133, "address_suffix": "Mosque Road, Frazer Town, Bengaluru 560005"},
    {"name": "BTM Layout", "lat": 12.9166, "lng": 77.6101, "address_suffix": "Udupi Garden Signal, BTM 2nd Stage, Bengaluru 560076"},
    {"name": "Banashankari", "lat": 12.9255, "lng": 77.5468, "address_suffix": "BSK 2nd Stage, Bengaluru 560070"},
    {"name": "Rajajinagar", "lat": 12.9915, "lng": 77.5526, "address_suffix": "10th Main, 4th Block Rajajinagar, Bengaluru 560010"},
    {"name": "Hebbal", "lat": 13.0358, "lng": 77.5970, "address_suffix": "Bellary Road, Hebbal, Bengaluru 560024"},
    {"name": "Yelahanka", "lat": 13.1007, "lng": 77.5963, "address_suffix": "Major Sandeep Unnikrishnan Road, Yelahanka New Town, Bengaluru 560064"},
]

CUISINE_CATALOG = {
    "Artisan Bakery & Cake Boutique": {
        "shop_names": [
            "Sweet Chariot", "Theobroma", "Glen's Bakehouse", "Magnolia Bakery", 
            "Smoor Chocolates", "Lavonne Academy & Café", "Albert Bakery", "Thom's Bakery",
            "Variar Bakery", "Iyengar Bakery Special", "Warm Oven", "Aubree Chocolaterie"
        ],
        "category": "Cakes",
        "description_template": "Premier boutique bakery in {nh} known for handcrafted celebration cakes, authentic Belgian chocolate treats, French viennoiserie, and gourmet desserts.",
        "dishes": [
            {"name": "Belgian Truffle Cake", "price": 650, "cat": "Cakes", "desc": "Rich Belgian dark chocolate ganache layered with moist sponge. Serves 6-8.", "tags": ["chocolate", "belgian", "cake", "bestseller", "birthday"], "veg": True, "img": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=500"},
            {"name": "Classic Chocolate Truffle Cake", "price": 600, "cat": "Cakes", "desc": "Silky dark chocolate ganache with soft Dutch chocolate sponge.", "tags": ["chocolate", "truffle", "cake"], "veg": True, "img": "https://images.unsplash.com/photo-1606890737304-57a1ca8a5b62?w=500"},
            {"name": "Belgian Dark Chocolate Truffle Cake (1kg)", "price": 850, "cat": "Cakes", "desc": "70% single-origin Belgian dark chocolate celebration cake.", "tags": ["chocolate", "belgian", "premium", "cake"], "veg": True, "img": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=500"},
            {"name": "Red Velvet Cream Cheese Cake", "price": 650, "cat": "Cakes", "desc": "Velvety crimson sponge with signature Philadelphia cream cheese frosting.", "tags": ["red velvet", "cake", "cream cheese"], "veg": True, "img": "https://images.unsplash.com/photo-1616541823729-00fe0aacd32c?w=500"},
            {"name": "Dutch Chocolate Cake", "price": 550, "cat": "Cakes", "desc": "Decadent Dutch cocoa sponge with bittersweet frosting.", "tags": ["chocolate", "dutch", "cake"], "veg": True, "img": "https://images.unsplash.com/photo-1588195538326-c5b1e9f80a1b?w=500"},
            {"name": "Black Forest Gateau", "price": 480, "cat": "Cakes", "desc": "Traditional German recipe with dark cherries, kirsch essence, and chocolate curls.", "tags": ["black forest", "cake", "classic"], "veg": True, "img": "https://images.unsplash.com/photo-1606890737304-57a1ca8a5b62?w=500"},
            {"name": "Fresh Pineapple Cream Cake", "price": 450, "cat": "Cakes", "desc": "Light vanilla sponge infused with fresh tropical pineapple chunks.", "tags": ["pineapple", "fruit cake", "light"], "veg": True, "img": "https://images.unsplash.com/photo-1535141192574-5d4897c13136?w=500"},
            {"name": "New York Baked Blueberry Cheesecake", "price": 350, "cat": "Pastries", "desc": "Dense Philadelphia cream cheese on graham cracker crust with wild blueberries.", "tags": ["cheesecake", "blueberry", "pastry"], "veg": True, "img": "https://images.unsplash.com/photo-1533134242443-d4fd215305ad?w=500"},
            {"name": "Tiramisu Jar", "price": 220, "cat": "Desserts", "desc": "Italian savoiardi dipped in espresso and layered with mascarpone cream.", "tags": ["tiramisu", "italian", "dessert"], "veg": True, "img": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=500"},
            {"name": "Warm Chocolate Lava Cake", "price": 180, "cat": "Desserts", "desc": "Molten chocolate center spilling out of a delicate sponge.", "tags": ["lava cake", "chocolate", "warm", "budget"], "veg": True, "img": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=500"},
            {"name": "Belgian Chocolate Brownie", "price": 140, "cat": "Pastries", "desc": "Fudgy, chewy dark chocolate brownie baked with roasted walnuts.", "tags": ["brownie", "chocolate", "belgian", "snack"], "veg": True, "img": "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=500"},
            {"name": "Almond Croissant", "price": 160, "cat": "Pastries", "desc": "Flaky French butter croissant loaded with rich almond frangipane.", "tags": ["croissant", "french", "almond"], "veg": True, "img": "https://images.unsplash.com/photo-1555507036-ab1f4038024a?w=500"},
            {"name": "French Butter Croissant", "price": 120, "cat": "Pastries", "desc": "Classic 27-layer laminated French butter croissant.", "tags": ["croissant", "breakfast", "butter"], "veg": True, "img": "https://images.unsplash.com/photo-1555507036-ab1f4038024a?w=500"},
            {"name": "Apple Cinnamon Danish", "price": 140, "cat": "Pastries", "desc": "Caramelized Granny Smith apples dusted with cinnamon on puff pastry.", "tags": ["danish", "apple", "pastry"], "veg": True, "img": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500"},
            {"name": "Artisan Sourdough Boule (500g)", "price": 190, "cat": "Breads", "desc": "36-hour slow cold fermented wild yeast loaf with open airy crumb.", "tags": ["sourdough", "bread", "artisan"], "veg": True, "img": "https://images.unsplash.com/photo-1586444248902-2f64eddc13df?w=500"},
            {"name": "Multi-Grain Country Loaf", "price": 110, "cat": "Breads", "desc": "Nutritious stoneground whole wheat loaf with sunflower and flax seeds.", "tags": ["bread", "multigrain", "healthy"], "veg": True, "img": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500"},
            {"name": "Walnut Fudge Brownie Box (4 pcs)", "price": 380, "cat": "Combos", "desc": "Gourmet gift box of 4 dense chocolate walnut brownies.", "tags": ["brownie", "gift", "box"], "veg": True, "img": "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=500"},
            {"name": "Mango Passion Fruit Mousse", "price": 240, "cat": "Desserts", "desc": "Tropical Alphonso mango purée whipped with passion fruit curd.", "tags": ["mango", "mousse", "fruity"], "veg": True, "img": "https://images.unsplash.com/photo-1587314168485-3236d6710814?w=500"},
            {"name": "French Macarons Box (6 pcs)", "price": 420, "cat": "Pastries", "desc": "Assorted French almond meringue cookies: Pistachio, Chocolate, Raspberry.", "tags": ["macaron", "french", "gift"], "veg": True, "img": "https://images.unsplash.com/photo-1569864358642-9d1684040f43?w=500"},
            {"name": "Opera Pastry Slice", "price": 220, "cat": "Pastries", "desc": "Almond sponge soaked in coffee syrup, layered with ganache and buttercream.", "tags": ["opera", "french", "coffee"], "veg": True, "img": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=500"},
            {"name": "Belgian Hot Chocolate", "price": 160, "cat": "Beverages", "desc": "Steamed milk blended with melted 55% Belgian chocolate callets.", "tags": ["hot chocolate", "beverage", "winter"], "veg": True, "img": "https://images.unsplash.com/photo-1542990253-0d0f5be5f0ed?w=500"},
            {"name": "Hazelnut Praline Cake", "price": 720, "cat": "Cakes", "desc": "Roasted Turkish hazelnuts with crunchy wafer praline and milk chocolate.", "tags": ["hazelnut", "praline", "cake"], "veg": True, "img": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=500"},
            {"name": "Death By Chocolate Sundae Jar", "price": 240, "cat": "Desserts", "desc": "Layers of fudge brownie, chocolate mousse, fudge sauce, and choco chips.", "tags": ["dbc", "chocolate", "jar"], "veg": True, "img": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=500"},
            {"name": "Traditional Plum Cake", "price": 320, "cat": "Cakes", "desc": "Spiced fruit cake matured with soaked dry fruits and candied peel.", "tags": ["plum cake", "christmas", "dry fruit"], "veg": True, "img": "https://images.unsplash.com/photo-1606890737304-57a1ca8a5b62?w=500"},
            {"name": "Chocolate Choux Eclair", "price": 130, "cat": "Pastries", "desc": "Crisp choux pastry filled with Tahitian vanilla pastry cream.", "tags": ["eclair", "french", "pastry"], "veg": True, "img": "https://images.unsplash.com/photo-1525059696034-4967a8e1dca2?w=500"},
        ]
    },
    "South Indian Darshini & Heritage Tiffin": {
        "shop_names": [
            "Vidyarthi Bhavan", "CTR Shri Sagar", "Brahmin's Coffee Bar", "Mavalli Tiffin Room (MTR)",
            "Taaza Thindi", "Veena Stores", "Airlines Hotel", "Hotel Janardhan", 
            "Umesh Dosa Point", "SLV Corner Restaurant", "New Krishna Bhavan", "Samrat Heritage Tiffins"
        ],
        "category": "South Indian",
        "description_template": "Legendary Bangalore heritage tiffin room in {nh} serving authentic crispy benne dosas, steaming soft idlis, and filter coffee since decades.",
        "dishes": [
            {"name": "Crispy Masala Dosa", "price": 65, "cat": "South Indian", "desc": "Golden brown crispy rice crepe stuffed with spiced potato mash and red chutney.", "tags": ["dosa", "masala dosa", "breakfast", "bestseller"], "veg": True, "img": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500"},
            {"name": "Benne Khali Dosa (Butter Dosa)", "price": 75, "cat": "South Indian", "desc": "Soft, fluffy sponge dosa roasted with generous dollops of fresh white butter.", "tags": ["dosa", "butter dosa", "benne"], "veg": True, "img": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500"},
            {"name": "Ghee Roast Masala Dosa", "price": 85, "cat": "South Indian", "desc": "Paper-crisp crepe roasted exclusively in pure country cow ghee.", "tags": ["ghee roast", "dosa", "premium"], "veg": True, "img": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500"},
            {"name": "Open Butter Masala Dosa", "price": 80, "cat": "South Indian", "desc": "CTR style open dosa topped with gunpowder podi, potato filling, and melting butter.", "tags": ["open dosa", "ctr", "butter"], "veg": True, "img": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500"},
            {"name": "Set Dosa with Sagu (3 pcs)", "price": 60, "cat": "South Indian", "desc": "Trio of cloud-soft spongy pancakes served with vegetable sagu and coconut chutney.", "tags": ["set dosa", "sagu", "breakfast"], "veg": True, "img": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500"},
            {"name": "Traditional Rava Idli with Ghee", "price": 50, "cat": "South Indian", "desc": "Steamed semolina cake spiced with mustard, cashews, ginger, served with potato sagu.", "tags": ["rava idli", "mtr", "healthy"], "veg": True, "img": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500"},
            {"name": "Thatte Idli (Plate Idli)", "price": 45, "cat": "South Indian", "desc": "Large plate-sized steamed rice cake smeared with red spicy chutney podi and butter.", "tags": ["thatte idli", "bidadi", "idli"], "veg": True, "img": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500"},
            {"name": "Steamed Rice Idli (2 pcs)", "price": 35, "cat": "South Indian", "desc": "Melt-in-mouth steamed fermented rice cakes served with hot sambar and coconut chutney.", "tags": ["idli", "light", "healthy", "budget"], "veg": True, "img": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500"},
            {"name": "Crispy Medu Vada (1 pc)", "price": 35, "cat": "South Indian", "desc": "Deep-fried lentil donut with crisp outer crust and soft fluffy center.", "tags": ["vada", "crispy", "snack"], "veg": True, "img": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500"},
            {"name": "Ghee Podi Button Idli (14 pcs)", "price": 70, "cat": "South Indian", "desc": "Mini bite-sized idlis tossed in aromatic spiced lentil gunpowder and hot desi ghee.", "tags": ["podi idli", "ghee", "snack"], "veg": True, "img": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500"},
            {"name": "Khara Bath (Spiced Upma)", "price": 40, "cat": "South Indian", "desc": "Roasted semolina cooked with vegetables, curry leaves, ginger, and turmeric.", "tags": ["upma", "khara bath", "breakfast"], "veg": True, "img": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500"},
            {"name": "Pineapple Kesari Bath", "price": 45, "cat": "South Indian", "desc": "Golden semolina sweet pudding infused with fresh pineapple, saffron, and ghee roasted cashews.", "tags": ["kesari bath", "sweet", "dessert"], "veg": True, "img": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=500"},
            {"name": "Chow Chow Bath Combo", "price": 80, "cat": "South Indian", "desc": "The quintessential Bangalore breakfast pairing: scoop of spicy Khara Bath with sweet Kesari Bath.", "tags": ["chow chow bath", "combo", "classic"], "veg": True, "img": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500"},
            {"name": "Filter Coffee (Degree Coffee)", "price": 25, "cat": "Beverages", "desc": "Authentic chicory-blended South Indian filter decoction frothed with thick fresh milk.", "tags": ["coffee", "filter coffee", "hot"], "veg": True, "img": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=500"},
            {"name": "Bisi Bele Bath with Boondi", "price": 70, "cat": "South Indian", "desc": "Karnataka spiced lentil rice cooked with tamarind, vegetables, and topped with crisp boondi.", "tags": ["bisi bele bath", "lunch", "karnataka"], "veg": True, "img": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500"},
            {"name": "Poori with Mixed Veg Sagu (3 pcs)", "price": 65, "cat": "South Indian", "desc": "Puffed whole wheat flatbreads served with aromatic coconut-spiced vegetable kurma.", "tags": ["poori", "breakfast", "sagu"], "veg": True, "img": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500"},
            {"name": "Crispy Maddur Vada (2 pcs)", "price": 40, "cat": "South Indian", "desc": "Heritage Karnataka snack made from rice flour, semolina, onions, and curry leaves.", "tags": ["maddur vada", "karnataka", "snack"], "veg": True, "img": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500"},
            {"name": "Curd Vada with Boondi", "price": 55, "cat": "South Indian", "desc": "Lentil donut soaked in chilled seasoned yogurt, garnished with coriander and boondi.", "tags": ["curd vada", "dahi vada", "cool"], "veg": True, "img": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500"},
            {"name": "Onion Tomato Uttapam", "price": 70, "cat": "South Indian", "desc": "Thick sourdough fermented pancake griddled with finely chopped onions and tomatoes.", "tags": ["uttapam", "onion uttapam", "dosa"], "veg": True, "img": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500"},
            {"name": "Puliyogare (Tamarind Rice)", "price": 60, "cat": "South Indian", "desc": "Temple-style tangy tamarind rice spiced with peanuts, red chillies, and sesame.", "tags": ["puliyogare", "temple food", "rice"], "veg": True, "img": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500"},
            {"name": "Badam Milk (Hot / Cold)", "price": 40, "cat": "Beverages", "desc": "Rich milk flavored with real almond paste, saffron strands, and cardamom.", "tags": ["badam milk", "beverage", "sweet"], "veg": True, "img": "https://images.unsplash.com/photo-1542990253-0d0f5be5f0ed?w=500"},
            {"name": "Vangi Bath (Brinjal Rice)", "price": 60, "cat": "South Indian", "desc": "Traditional Karnataka rice dish cooked with tender green brinjals and vangi bath powder.", "tags": ["vangi bath", "rice", "karnataka"], "veg": True, "img": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500"},
            {"name": "Mangalore Buns (2 pcs)", "price": 50, "cat": "South Indian", "desc": "Sweet, fluffy banana-infused fermented deep-fried pooris served with coconut chutney.", "tags": ["mangalore buns", "sweet poori", "coastal"], "veg": True, "img": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500"},
            {"name": "Curd Rice with Pomegranate", "price": 55, "cat": "South Indian", "desc": "Tempered yogurt rice with mustard seeds, green chillies, ginger, and fresh pomegranate.", "tags": ["curd rice", "comfort food", "healthy"], "veg": True, "img": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500"},
            {"name": "Mysore Pak (2 pcs)", "price": 45, "cat": "Desserts", "desc": "Melt-in-mouth traditional royal sweet made of gram flour, pure ghee, and sugar.", "tags": ["mysore pak", "sweet", "royal"], "veg": True, "img": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=500"},
        ]
    },
    "Bangalore Biryani & Military Mess": {
        "shop_names": [
            "Meghana Foods", "Shivaji Military Hotel", "Nagarjuna Biryani", "Ranganna Military Hotel",
            "Mani's Dum Biryani", "SG Rao Military Hotel", "Ambur Star Biryani", "Anand Dum Biryani",
            "Thalassery Biryani House", "Chandu's Military Hotel", "Donne Biryani Mane", "Hyderabad Biryani House"
        ],
        "category": "Biryani",
        "description_template": "Iconic Bangalore biryani destination in {nh} famous for authentic handi dum biryanis, Donne mutton biryanis, spicy pepper fries, and traditional military mess curries.",
        "dishes": [
            {"name": "Meghana Special Chicken Biryani", "price": 340, "cat": "Biryani", "desc": "Spicy boneless chicken fry pieces piled over aromatic basmati dum biryani rice with mirchi ka salan.", "tags": ["biryani", "chicken", "bestseller", "spicy"], "veg": False, "img": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500"},
            {"name": "Chicken Dum Biryani", "price": 320, "cat": "Biryani", "desc": "Slow-cooked Hyderabadi bone-in chicken dum biryani infused with saffron and whole spices.", "tags": ["biryani", "chicken dum", "classic"], "veg": False, "img": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500"},
            {"name": "Donne Mutton Biryani", "price": 320, "cat": "Biryani", "desc": "Authentic Shivaji military style short-grain Seeraga Samba rice cooked with tender mutton in areca leaf cup.", "tags": ["donne biryani", "mutton", "bangalore"], "veg": False, "img": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500"},
            {"name": "Donne Chicken Biryani", "price": 240, "cat": "Biryani", "desc": "Flavorful green coriander-mint spiced Seeraga Samba rice cooked with tender chicken.", "tags": ["donne biryani", "chicken", "bangalore"], "veg": False, "img": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500"},
            {"name": "Mutton Dum Biryani", "price": 440, "cat": "Biryani", "desc": "Tender young goat meat marinated in curd and handi-cooked on dum for 3 hours.", "tags": ["mutton", "biryani", "premium"], "veg": False, "img": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500"},
            {"name": "Veg Dum Biryani", "price": 240, "cat": "Biryani", "desc": "Long grain basmati rice slow-cooked with fresh garden vegetables, mint, and saffron.", "tags": ["veg biryani", "vegetarian", "dum"], "veg": True, "img": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500"},
            {"name": "Paneer Biryani", "price": 260, "cat": "Biryani", "desc": "Marinated tandoori cottage cheese cubes layered in spiced fragrant rice.", "tags": ["paneer", "biryani", "veg"], "veg": True, "img": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500"},
            {"name": "Egg Dum Biryani", "price": 230, "cat": "Biryani", "desc": "Two boiled eggs roasted in golden biryani spices served with flavored dum rice.", "tags": ["egg biryani", "budget", "egg"], "veg": False, "img": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500"},
            {"name": "Chicken Ghee Roast", "price": 310, "cat": "Starters", "desc": "Kundapur specialty: fiery red masala roasted chicken cooked in pure desi ghee.", "tags": ["chicken", "ghee roast", "starter", "spicy"], "veg": False, "img": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Mutton Pepper Dry", "price": 340, "cat": "Starters", "desc": "Tender mutton pieces tossed with crushed Malabar black pepper and curry leaves.", "tags": ["mutton", "pepper fry", "military"], "veg": False, "img": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Donne Chicken Kshatriya Kabab", "price": 210, "cat": "Starters", "desc": "Deep fried crispy spiced chicken morsels, the signature military hotel bite.", "tags": ["kabab", "chicken", "crispy"], "veg": False, "img": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Andhra Chilli Chicken", "price": 230, "cat": "Starters", "desc": "Fiery green chilli-marinated chicken sauteed in classic Andhra style.", "tags": ["chilli chicken", "andhra", "spicy"], "veg": False, "img": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Chicken 65", "price": 220, "cat": "Starters", "desc": "Crispy tempered chicken cubes tossed in yogurt, curry leaves, and Kashmiri chilli.", "tags": ["chicken 65", "starter", "crispy"], "veg": False, "img": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Natti Koli (Country Chicken) Curry", "price": 290, "cat": "Main Course", "desc": "Country chicken slow-simmered in village style stone-ground pepper masala.", "tags": ["natti koli", "curry", "village"], "veg": False, "img": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=500"},
            {"name": "Mutton Liver Fry", "price": 240, "cat": "Starters", "desc": "Fresh goat liver sauteed with onions, green chillies, and cracked black pepper.", "tags": ["liver", "mutton", "military"], "veg": False, "img": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Andhra Chicken Curry", "price": 260, "cat": "Main Course", "desc": "Spicy, tangy red gravy with bone-in chicken, perfect with white rice or parotta.", "tags": ["chicken curry", "andhra", "gravy"], "veg": False, "img": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=500"},
            {"name": "Malabar Kerala Parotta (2 pcs)", "price": 50, "cat": "Breads", "desc": "Multi-layered flaky griddled flatbread.", "tags": ["parotta", "bread", "kerala"], "veg": True, "img": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500"},
            {"name": "Apollo Fish Fry", "price": 290, "cat": "Starters", "desc": "Crispy boneless fish fillets spiced with red chilli, yogurt, and aromatic herbs.", "tags": ["fish", "seafood", "starter"], "veg": False, "img": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Prawns Ghee Roast", "price": 380, "cat": "Starters", "desc": "Juicy bay prawns cooked in slow-roasted Mangalorean ghee masala.", "tags": ["prawns", "seafood", "ghee roast"], "veg": False, "img": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Mirchi Ka Salan (Side)", "price": 60, "cat": "Side Dish", "desc": "Hyderabadi peanut-sesame curry with roasted green chillies.", "tags": ["salan", "side", "curry"], "veg": True, "img": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=500"},
            {"name": "Onion Cucumber Raita", "price": 40, "cat": "Side Dish", "desc": "Chilled whipped curd with finely chopped onions, cucumber, and roasted cumin.", "tags": ["raita", "curd", "side"], "veg": True, "img": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500"},
            {"name": "Mutton Chops Gravy", "price": 310, "cat": "Main Course", "desc": "Tender goat ribs simmered in a dense, peppery coriander gravy.", "tags": ["mutton chops", "curry", "military"], "veg": False, "img": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=500"},
            {"name": "Gulab Jamun with Rabri (2 pcs)", "price": 90, "cat": "Desserts", "desc": "Warm melt-in-mouth milk dumplings served with rich saffron reduced milk.", "tags": ["gulab jamun", "dessert", "sweet"], "veg": True, "img": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=500"},
            {"name": "Paneer 65", "price": 210, "cat": "Starters", "desc": "Cottage cheese cubes tossed in spicy tempering of garlic, curry leaves, and chillies.", "tags": ["paneer", "starter", "veg"], "veg": True, "img": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Steamed Basmati Rice with Dal", "price": 140, "cat": "Main Course", "desc": "Comfort bowl of aromatic basmati rice with homestyle tadka dal.", "tags": ["rice", "dal", "comfort"], "veg": True, "img": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=500"},
        ]
    },
    "Indo-Chinese & Pan-Asian Wok": {
        "shop_names": [
            "Beijing Bites", "Chung Wah", "Mainland China", "Szechuan Dragon",
            "Auntie Fung's", "Mamagoto", "Nasi and Mee", "Shanghai Court",
            "Asian Wok Express", "Golden Dragon Indiranagar", "The Rice Bowl", "Wok Republic"
        ],
        "category": "Chinese",
        "description_template": "Beloved Bangalore Indo-Chinese institution in {nh} whipping up wok-tossed noodles, crunchy Manchurian, fiery chillies, and steaming dim sums.",
        "dishes": [
            {"name": "Veg Manchurian Dry", "price": 180, "cat": "Chinese", "desc": "Crispy vegetable balls tossed in wok with minced garlic, ginger, and dark soy.", "tags": ["manchurian", "veg", "starter", "bestseller"], "veg": True, "img": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500"},
            {"name": "Gobi Manchurian Dry", "price": 160, "cat": "Chinese", "desc": "Bangalore street-style batter fried cauliflower florets tossed in tangy spicy sauce.", "tags": ["gobi manchurian", "crispy", "starter"], "veg": True, "img": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500"},
            {"name": "Chilli Paneer Dry", "price": 210, "cat": "Chinese", "desc": "Fresh cottage cheese cubes sauteed with crunchy bell peppers, onions, and green chillies.", "tags": ["chilli paneer", "paneer", "starter"], "veg": True, "img": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500"},
            {"name": "Veg Hakka Noodles", "price": 170, "cat": "Chinese", "desc": "Wok tossed thin noodles with julienned cabbage, carrots, and spring onions.", "tags": ["noodles", "hakka noodles", "veg"], "veg": True, "img": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=500"},
            {"name": "Chicken Hakka Noodles", "price": 220, "cat": "Chinese", "desc": "Smoky wok-tossed noodles with shredded chicken, egg strips, and seasonal veggies.", "tags": ["chicken noodles", "hakka", "chinese"], "veg": False, "img": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=500"},
            {"name": "Schezwan Veg Fried Rice", "price": 180, "cat": "Chinese", "desc": "Fragrant rice tossed with spicy homemade Sichuan peppercorn sauce.", "tags": ["fried rice", "schezwan", "spicy"], "veg": True, "img": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=500"},
            {"name": "Chicken Fried Rice", "price": 210, "cat": "Chinese", "desc": "Fluffy wok-fried long grain rice with chicken shreds and spring onions.", "tags": ["fried rice", "chicken", "chinese"], "veg": False, "img": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=500"},
            {"name": "Steamed Chicken Momos (6 pcs)", "price": 160, "cat": "Chinese", "desc": "Thin-wrapper Tibetan dumplings filled with seasoned juicy minced chicken.", "tags": ["momos", "dim sum", "chicken"], "veg": False, "img": "https://images.unsplash.com/photo-1541696432-82c6da8ce7bf?w=500"},
            {"name": "Fried Veg Momos (6 pcs)", "price": 140, "cat": "Chinese", "desc": "Crispy golden fried dumplings stuffed with spiced vegetables and served with hot garlic dip.", "tags": ["momos", "veg", "crispy"], "veg": True, "img": "https://images.unsplash.com/photo-1541696432-82c6da8ce7bf?w=500"},
            {"name": "Crispy Honey Chilli Potato", "price": 160, "cat": "Chinese", "desc": "Crunchy finger potatoes tossed with toasted sesame, honey, and red chillies.", "tags": ["honey chilli potato", "snack", "sweet spicy"], "veg": True, "img": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Kung Pao Chicken", "price": 280, "cat": "Chinese", "desc": "Diced chicken sauteed with dry red chillies, bell peppers, and roasted peanuts.", "tags": ["kung pao", "chicken", "chinese"], "veg": False, "img": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Chicken Manchurian Gravy", "price": 240, "cat": "Chinese", "desc": "Juicy chicken balls in a thick savoury garlic-ginger-soya gravy.", "tags": ["manchurian gravy", "main course", "chicken"], "veg": False, "img": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Veg Spring Rolls (4 pcs)", "price": 150, "cat": "Chinese", "desc": "Crispy golden rolls filled with sauteed glass noodles and shredded vegetables.", "tags": ["spring rolls", "starter", "crispy"], "veg": True, "img": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Hot & Sour Chicken Soup", "price": 140, "cat": "Soups", "desc": "Traditional thick soup with shredded chicken, mushrooms, bamboo shoots, and vinegar.", "tags": ["soup", "hot and sour", "chicken"], "veg": False, "img": "https://images.unsplash.com/photo-1547592166-23ac45744acd?w=500"},
            {"name": "Sweet Corn Veg Soup", "price": 120, "cat": "Soups", "desc": "Comforting velvety corn broth with sweet corn kernels and carrots.", "tags": ["soup", "sweet corn", "light"], "veg": True, "img": "https://images.unsplash.com/photo-1547592166-23ac45744acd?w=500"},
            {"name": "Thai Green Curry with Jasmine Rice", "price": 320, "cat": "Chinese", "desc": "Aromatic coconut milk curry with Thai basil, bamboo shoots, and fresh vegetables.", "tags": ["thai", "green curry", "pan asian"], "veg": True, "img": "https://images.unsplash.com/photo-1547592166-23ac45744acd?w=500"},
            {"name": "Dragon Chicken", "price": 270, "cat": "Chinese", "desc": "Crisp batter fried chicken strips tossed with cashews, red chillies, and tomato garlic sauce.", "tags": ["dragon chicken", "starter", "spicy"], "veg": False, "img": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Burnt Garlic Veg Fried Rice", "price": 180, "cat": "Chinese", "desc": "Steamed basmati tossed with crisp golden fried garlic bits and spring greens.", "tags": ["burnt garlic", "fried rice", "veg"], "veg": True, "img": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=500"},
            {"name": "Singapore Rice Noodles (Non-Veg)", "price": 240, "cat": "Chinese", "desc": "Thin vermicelli noodles wok fried with yellow curry powder, chicken, and shrimp.", "tags": ["singapore noodles", "noodles", "spicy"], "veg": False, "img": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=500"},
            {"name": "Crispy Thread Paneer", "price": 220, "cat": "Chinese", "desc": "Paneer strips wrapped in crispy noodle threads and fried to perfection.", "tags": ["thread paneer", "starter", "crispy"], "veg": True, "img": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Chilli Chicken Gravy", "price": 240, "cat": "Chinese", "desc": "Tender chicken cooked with green chillies and onions in a dark savoury sauce.", "tags": ["chilli chicken", "gravy", "main course"], "veg": False, "img": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Crispy Corn Pepper Salt", "price": 160, "cat": "Chinese", "desc": "Crunchy sweet corn kernels tossed with freshly ground pepper and spring onions.", "tags": ["crispy corn", "starter", "snack"], "veg": True, "img": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Dim Sum Crystal Veg (5 pcs)", "price": 210, "cat": "Chinese", "desc": "Translucent steamed dumplings stuffed with water chestnut, shiitake, and asparagus.", "tags": ["dim sum", "dumpling", "healthy"], "veg": True, "img": "https://images.unsplash.com/photo-1541696432-82c6da8ce7bf?w=500"},
            {"name": "Darsaan with Vanilla Ice Cream", "price": 160, "cat": "Desserts", "desc": "Fried flat noodle crisps tossed in honey and sesame seeds, served with vanilla scoop.", "tags": ["darsaan", "dessert", "chinese sweet"], "veg": True, "img": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=500"},
            {"name": "Manchow Soup with Crispy Noodles", "price": 130, "cat": "Soups", "desc": "Dark brown spicy garlic soup topped with crunchy fried noodles.", "tags": ["manchow", "soup", "chinese"], "veg": True, "img": "https://images.unsplash.com/photo-1547592166-23ac45744acd?w=500"},
        ]
    },
    "North Indian Dhaba & Curry House": {
        "shop_names": [
            "Empire Restaurant", "Punjabi Angithi", "Punjab Grill", "Kapoor's Café",
            "Dhaba Estd 1986", "Treat Restaurant", "Tadka Singh", "Copper Chimney",
            "Oye Amritsar", "Baba Da Dhaba", "Paratha Plaza", "Delhi Highway"
        ],
        "category": "North Indian",
        "description_template": "Rich North Indian dining in {nh} serving velvety butter chicken, slow-simmered dal makhani, stuffed parathas, and tandoori breads.",
        "dishes": [
            {"name": "Murgh Makhani (Butter Chicken)", "price": 320, "cat": "North Indian", "desc": "Charcoal grilled tandoori chicken simmered in rich creamy tomato and butter gravy.", "tags": ["butter chicken", "north indian", "curry", "bestseller"], "veg": False, "img": "https://images.unsplash.com/photo-1588166524941-3bf61a9c41db?w=500"},
            {"name": "Dal Makhani (Slow Cooked 24hrs)", "price": 240, "cat": "North Indian", "desc": "Black lentils slow-cooked overnight with cream, butter, and gentle Punjabi spices.", "tags": ["dal makhani", "dal", "creamy", "punjabi"], "veg": True, "img": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=500"},
            {"name": "Paneer Tikka Masala", "price": 260, "cat": "North Indian", "desc": "Clay-oven charred cottage cheese cubes folded into thick onion-tomato gravy.", "tags": ["paneer tikka", "paneer", "curry"], "veg": True, "img": "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=500"},
            {"name": "Kadhai Paneer", "price": 250, "cat": "North Indian", "desc": "Paneer cubes tossed with crushed coriander seeds, capsicum, and roasted dry red chillies.", "tags": ["kadhai paneer", "spicy", "north indian"], "veg": True, "img": "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=500"},
            {"name": "Amritsari Chole with 2 Bhature", "price": 160, "cat": "North Indian", "desc": "Dark spiced Punjabi chickpea curry served with large puffed golden bhaturas and pickles.", "tags": ["chole bhature", "punjabi", "bestseller"], "veg": True, "img": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500"},
            {"name": "Tandoori Chicken (Half)", "price": 280, "cat": "Starters", "desc": "Tender chicken marinated in hung curd, Kashmiri deghi mirch, and mustard oil.", "tags": ["tandoori chicken", "starter", "barbecue"], "veg": False, "img": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Butter Garlic Naan", "price": 65, "cat": "Breads", "desc": "Refined flour bread baked on the walls of clay tandoor, brushed with garlic and butter.", "tags": ["naan", "garlic naan", "bread"], "veg": True, "img": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500"},
            {"name": "Tandoori Butter Roti", "price": 25, "cat": "Breads", "desc": "Whole wheat flatbread baked in clay oven and brushed with butter.", "tags": ["roti", "tandoori roti", "bread"], "veg": True, "img": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500"},
            {"name": "Laccha Paratha", "price": 50, "cat": "Breads", "desc": "Multi-layered flaky whole wheat paratha baked in clay tandoor.", "tags": ["paratha", "laccha", "bread"], "veg": True, "img": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500"},
            {"name": "Amritsari Kulcha with Chole", "price": 180, "cat": "North Indian", "desc": "Crispy layered bread stuffed with spiced potatoes and onions, served with chole.", "tags": ["kulcha", "amritsari", "punjabi"], "veg": True, "img": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500"},
            {"name": "Palak Paneer", "price": 240, "cat": "North Indian", "desc": "Fresh spinach purée delicately tempered with garlic, cumin, and soft paneer.", "tags": ["palak paneer", "healthy", "spinach"], "veg": True, "img": "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=500"},
            {"name": "Mutton Rogan Josh", "price": 420, "cat": "North Indian", "desc": "Kashmiri slow-cooked tender goat meat in rich aromatic gravy flavored with rattan jot.", "tags": ["rogan josh", "mutton", "kashmiri"], "veg": False, "img": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=500"},
            {"name": "Shahi Malai Kofta", "price": 260, "cat": "North Indian", "desc": "Melt-in-mouth cottage cheese and potato dumplings simmered in cashew-cream gravy.", "tags": ["malai kofta", "creamy", "shahi"], "veg": True, "img": "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=500"},
            {"name": "Chicken Tikka Kebab (6 pcs)", "price": 260, "cat": "Starters", "desc": "Boneless chicken thigh chunks steeped in spiced yogurt and grilled in tandoor.", "tags": ["chicken tikka", "kebab", "tandoori"], "veg": False, "img": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Paneer Malai Tikka", "price": 250, "cat": "Starters", "desc": "Soft paneer cubes marinated in cream, cardamom, cheese, and grilled gently.", "tags": ["malai tikka", "paneer", "mild"], "veg": True, "img": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500"},
            {"name": "Yellow Dal Tadka", "price": 180, "cat": "North Indian", "desc": "Yellow toor dal tempered with desi ghee, cumin seeds, garlic, and dry chillies.", "tags": ["dal tadka", "comfort food", "homestyle"], "veg": True, "img": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=500"},
            {"name": "Jeera Rice", "price": 140, "cat": "Rice", "desc": "Fluffy aged basmati rice tempered with roasted cumin seeds and desi ghee.", "tags": ["jeera rice", "rice", "side"], "veg": True, "img": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500"},
            {"name": "Aloo Paratha with Curd & Pickle", "price": 120, "cat": "North Indian", "desc": "Tawa griddled whole wheat paratha stuffed with spicy mashed potatoes.", "tags": ["aloo paratha", "breakfast", "paratha"], "veg": True, "img": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500"},
            {"name": "Paneer Paratha with Butter", "price": 150, "cat": "North Indian", "desc": "Hearty paratha stuffed with seasoned grated paneer and topped with white butter.", "tags": ["paneer paratha", "paratha", "punjabi"], "veg": True, "img": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500"},
            {"name": "Murgh Tikka Biryani", "price": 310, "cat": "Biryani", "desc": "Fragrant dum basmati rice cooked with charcoal-grilled chicken tikka chunks.", "tags": ["tikka biryani", "biryani", "chicken"], "veg": False, "img": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500"},
            {"name": "Sweet Punjabi Lassi (Kulhad)", "price": 80, "cat": "Beverages", "desc": "Thick churned yogurt drink topped with clotted malai and cardamom powder.", "tags": ["lassi", "punjabi", "beverage"], "veg": True, "img": "https://images.unsplash.com/photo-1542990253-0d0f5be5f0ed?w=500"},
            {"name": "Gulab Jamun (2 pcs)", "price": 70, "cat": "Desserts", "desc": "Golden fried khoya dumplings dipped in rose-cardamom sugar syrup.", "tags": ["gulab jamun", "sweet", "dessert"], "veg": True, "img": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=500"},
            {"name": "Rasmalai (2 pcs)", "price": 90, "cat": "Desserts", "desc": "Spongy cottage cheese patties steeped in thickened saffron-pistachio milk.", "tags": ["rasmalai", "sweet", "dessert"], "veg": True, "img": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=500"},
            {"name": "Gajar Ka Halwa", "price": 110, "cat": "Desserts", "desc": "Slow-cooked red carrots simmered in full-cream milk, khoya, and pure desi ghee.", "tags": ["gajar halwa", "dessert", "sweet"], "veg": True, "img": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=500"},
            {"name": "Boondi Raita", "price": 60, "cat": "Side Dish", "desc": "Whipped seasoned curd with crisp fried chickpea pearls.", "tags": ["raita", "curd", "side"], "veg": True, "img": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500"},
        ]
    },
    "Specialty Coffee & Gourmet Café": {
        "shop_names": [
            "Third Wave Coffee", "Blue Tokai Coffee Roasters", "Doff Pub & Café", "Café Azzure",
            "DYU Art Café", "Café Noir", "Matteo Coffea", "Glen's Café Indiranagar",
            "The Hole in the Wall Café", "Truffles Café", "Café Felix", "Starbucks Reserve Bangalore"
        ],
        "category": "Café",
        "description_template": "Chic specialty coffee roastery and European café in {nh} offering artisanal pour-overs, sourdough toasts, gourmet pastas, and desserts.",
        "dishes": [
            {"name": "Artisan Flat White", "price": 190, "cat": "Beverages", "desc": "Double ristretto shot with velvety microfoam milk.", "tags": ["coffee", "flat white", "espresso"], "veg": True, "img": "https://images.unsplash.com/photo-1541167760496-1628856ab772?w=500"},
            {"name": "Cold Brew Coffee", "price": 180, "cat": "Beverages", "desc": "18-hour cold steeped Arabica coffee served over ice with orange slice.", "tags": ["cold brew", "iced coffee", "beverage"], "veg": True, "img": "https://images.unsplash.com/photo-1517701550927-30cf4ba1dba5?w=500"},
            {"name": "Spanish Iced Latte", "price": 220, "cat": "Beverages", "desc": "Espresso poured over chilled condensed milk and whole milk.", "tags": ["latte", "spanish latte", "sweet coffee"], "veg": True, "img": "https://images.unsplash.com/photo-1517701550927-30cf4ba1dba5?w=500"},
            {"name": "Avocado Tartine on Sourdough", "price": 280, "cat": "Continental", "desc": "Hass avocado mash on toasted rustic sourdough with cherry tomatoes and feta.", "tags": ["avocado toast", "sourdough", "healthy"], "veg": True, "img": "https://images.unsplash.com/photo-1525351484163-7529414344d8?w=500"},
            {"name": "Full English Breakfast Platter", "price": 340, "cat": "Continental", "desc": "Eggs your style, chicken sausages, baked beans, grilled mushrooms, toast, and butter.", "tags": ["english breakfast", "platter", "eggs"], "veg": False, "img": "https://images.unsplash.com/photo-1533089860892-a7c6f0a88666?w=500"},
            {"name": "Classic Belgian Waffles with Maple Syrup", "price": 220, "cat": "Desserts", "desc": "Crisp golden Belgian waffles served with whipped butter and maple syrup.", "tags": ["waffles", "belgian", "sweet"], "veg": True, "img": "https://images.unsplash.com/photo-1562376552-0d160a2f238d?w=500"},
            {"name": "Buttermilk Pancakes Stack", "price": 210, "cat": "Desserts", "desc": "Stack of 3 fluffy pancakes with berry compote and whipped cream.", "tags": ["pancakes", "breakfast", "sweet"], "veg": True, "img": "https://images.unsplash.com/photo-1528198691013-2f123401b220?w=500"},
            {"name": "Smoked Chicken & Pesto Sandwich", "price": 240, "cat": "Continental", "desc": "Smoked chicken breast with basil walnut pesto and mozzarella on ciabatta.", "tags": ["sandwich", "chicken", "pesto"], "veg": False, "img": "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?w=500"},
            {"name": "Truffle Parmesan Fries", "price": 210, "cat": "Starters", "desc": "Crispy golden potato fries tossed in black truffle oil and grated aged parmesan.", "tags": ["truffle fries", "fries", "starter"], "veg": True, "img": "https://images.unsplash.com/photo-1576107232684-1279f3908594?w=500"},
            {"name": "Creamy Penne Alfredo Pasta", "price": 280, "cat": "Continental", "desc": "Penne pasta in garlic Parmesan cream sauce with sauteed mushrooms.", "tags": ["alfredo", "pasta", "italian"], "veg": True, "img": "https://images.unsplash.com/photo-1621996346565-e3d5d628169b?w=500"},
            {"name": "Spaghetti Aglio Olio", "price": 270, "cat": "Continental", "desc": "Spaghetti tossed with extra virgin olive oil, sliced garlic, and chilli flakes.", "tags": ["spaghetti", "aglio olio", "classic"], "veg": True, "img": "https://images.unsplash.com/photo-1621996346565-e3d5d628169b?w=500"},
            {"name": "Grilled Cheese & Jalapeno Toastie", "price": 190, "cat": "Continental", "desc": "Sharp cheddar and mozzarella melted with pickled jalapenos in sourdough.", "tags": ["toastie", "grilled cheese", "comfort"], "veg": True, "img": "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?w=500"},
            {"name": "Hot Chocolate with Toasted Marshmallow", "price": 190, "cat": "Beverages", "desc": "Thick European hot chocolate topped with hand-torched marshmallow.", "tags": ["hot chocolate", "sweet", "beverage"], "veg": True, "img": "https://images.unsplash.com/photo-1542990253-0d0f5be5f0ed?w=500"},
            {"name": "Peach & Passion Iced Tea", "price": 140, "cat": "Beverages", "desc": "Cold brewed black tea infused with real peach and passion fruit nectar.", "tags": ["iced tea", "refreshing", "cold"], "veg": True, "img": "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=500"},
            {"name": "Classic Caesar Salad with Grilled Chicken", "price": 260, "cat": "Continental", "desc": "Crisp romaine lettuce, herb croutons, shaved parmesan, and creamy dressing.", "tags": ["caesar salad", "healthy", "chicken"], "veg": False, "img": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=500"},
            {"name": "Blueberry Crumble Muffin", "price": 120, "cat": "Pastries", "desc": "Moist vanilla muffin bursting with wild blueberries and butter streusel topping.", "tags": ["muffin", "blueberry", "bakery"], "veg": True, "img": "https://images.unsplash.com/photo-1586985289688-ca3cf47d3e6e?w=500"},
            {"name": "Banana Walnut Cake Slice", "price": 130, "cat": "Pastries", "desc": "Caramelized ripe banana tea cake loaded with toasted walnut chunks.", "tags": ["banana cake", "tea cake", "snack"], "veg": True, "img": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=500"},
            {"name": "Classic Cinnamon Swirl Roll", "price": 140, "cat": "Pastries", "desc": "Brioche dough rolled with Korintje cinnamon and drizzled with cream cheese glaze.", "tags": ["cinnamon roll", "sweet", "bakery"], "veg": True, "img": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500"},
            {"name": "Four Cheese Mac & Cheese", "price": 260, "cat": "Continental", "desc": "Macaroni baked in rich sauce of Cheddar, Mozzarella, Gouda, and Parmesan.", "tags": ["mac and cheese", "cheesy", "comfort"], "veg": True, "img": "https://images.unsplash.com/photo-1543339308-43e59d6b73a6?w=500"},
            {"name": "Cappuccino with Double Shot", "price": 170, "cat": "Beverages", "desc": "Equal parts espresso, steamed milk, and dense silky foam dusted with cocoa.", "tags": ["cappuccino", "coffee", "classic"], "veg": True, "img": "https://images.unsplash.com/photo-1572442388796-11668a67e53d?w=500"},
            {"name": "Café Mocha", "price": 210, "cat": "Beverages", "desc": "Rich dark chocolate ganache mixed with double espresso and steamed milk.", "tags": ["mocha", "chocolate coffee", "beverage"], "veg": True, "img": "https://images.unsplash.com/photo-1572442388796-11668a67e53d?w=500"},
            {"name": "BBQ Chicken Burger with Slaw", "price": 240, "cat": "Continental", "desc": "Crispy chicken patty tossed in smoky barbecue glaze on toasted brioche bun.", "tags": ["burger", "bbq", "chicken"], "veg": False, "img": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=500"},
            {"name": "Nutella Sea Salt Cookie", "price": 110, "cat": "Pastries", "desc": "Thick chewy cookie with molten Nutella core and flakes of Maldon sea salt.", "tags": ["cookie", "nutella", "sweet"], "veg": True, "img": "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?w=500"},
            {"name": "Iced Matcha Latte", "price": 240, "cat": "Beverages", "desc": "Ceremonial Japanese Uji green tea matcha whisked with chilled oat milk.", "tags": ["matcha", "healthy", "iced latte"], "veg": True, "img": "https://images.unsplash.com/photo-1536256263959-770b48d82b0a?w=500"},
            {"name": "Spinach & Sweet Corn Quiche", "price": 190, "cat": "Pastries", "desc": "Flaky shortcrust pastry filled with savoury egg custard, spinach, and corn.", "tags": ["quiche", "french", "savoury"], "veg": True, "img": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500"},
        ]
    },
    "Ice Cream Parlours & Dessert Sundaes": {
        "shop_names": [
            "Corner House Ice Cream", "Naturals Ice Cream", "Polar Bear Sundaes", "Baskin Robbins",
            "Milano Ice Cream & Gelato", "Häagen-Dazs", "Lakeview Milkbar", "Stoner Ice Cream",
            "Ibaco Cold Stone", "Apsara Ice Creams", "Cream Stone Concept", "Pabrai's Fresh & Naturelle"
        ],
        "category": "Desserts",
        "description_template": "Beloved Bangalore ice cream destination in {nh} serving cult classics like Death by Chocolate, fresh seasonal fruit scoops, and thick sundaes.",
        "dishes": [
            {"name": "Death By Chocolate (DBC)", "price": 220, "cat": "Desserts", "desc": "Bangalore's legendary sundae: chocolate cake, vanilla ice cream, hot chocolate fudge, nuts, and cherries.", "tags": ["dbc", "death by chocolate", "corner house", "bestseller"], "veg": True, "img": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=500"},
            {"name": "Hot Chocolate Fudge (HCF)", "price": 160, "cat": "Desserts", "desc": "Two scoops of vanilla ice cream drenched in warm homemade thick fudge sauce and cashews.", "tags": ["hcf", "fudge", "sundae"], "veg": True, "img": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=500"},
            {"name": "Brown Bomb Sundae", "price": 180, "cat": "Desserts", "desc": "Warm chocolate walnut brownie topped with vanilla ice cream and flowing hot fudge.", "tags": ["brownie sundae", "brown bomb", "chocolate"], "veg": True, "img": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=500"},
            {"name": "Tender Coconut Ice Cream (Single)", "price": 90, "cat": "Desserts", "desc": "Crafted from fresh coastal tender coconut water and tender coconut malai pulp.", "tags": ["tender coconut", "naturals", "fruit ice cream"], "veg": True, "img": "https://images.unsplash.com/photo-1501443762994-82bd5dace89a?w=500"},
            {"name": "Sitaphal (Custard Apple) Ice Cream", "price": 90, "cat": "Desserts", "desc": "Seasonal fresh custard apple pulp churned into creamy milk ice cream.", "tags": ["sitaphal", "fruit", "seasonal"], "veg": True, "img": "https://images.unsplash.com/photo-1501443762994-82bd5dace89a?w=500"},
            {"name": "Alphonso Mango Scoop", "price": 90, "cat": "Desserts", "desc": "Made with 100% pure Ratnagiri Alphonso mango pulp without artificial essence.", "tags": ["mango", "alphonso", "ice cream"], "veg": True, "img": "https://images.unsplash.com/photo-1501443762994-82bd5dace89a?w=500"},
            {"name": "Roasted Almond Chocolate Scoop", "price": 110, "cat": "Desserts", "desc": "Rich dark chocolate ice cream packed with butter roasted California almonds.", "tags": ["roasted almond", "chocolate", "nutty"], "veg": True, "img": "https://images.unsplash.com/photo-1501443762994-82bd5dace89a?w=500"},
            {"name": "Belgian Chocolate Gelato Scoop", "price": 130, "cat": "Desserts", "desc": "Dense Italian style gelato churned with 70% dark Belgian cocoa.", "tags": ["belgian chocolate", "gelato", "premium"], "veg": True, "img": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=500"},
            {"name": "Gudbud Sundae", "price": 190, "cat": "Desserts", "desc": "Heritage coastal sundae with mixed fruit scoops, jelly, fresh fruits, nuts, and syrup.", "tags": ["gudbud", "sundae", "classic"], "veg": True, "img": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=500"},
            {"name": "Royal Kulfi Falooda", "price": 160, "cat": "Desserts", "desc": "Pista kulfi slices layered with rose syrup, basil sabja seeds, and chilled vermicelli.", "tags": ["falooda", "kulfi", "indian sweet"], "veg": True, "img": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=500"},
            {"name": "Caramel Crunch Sundae", "price": 170, "cat": "Desserts", "desc": "Butterscotch ice cream layered with golden praline caramel and butterscotch sauce.", "tags": ["caramel", "crunch", "butterscotch"], "veg": True, "img": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=500"},
            {"name": "Fresh Fruit Salad with Ice Cream", "price": 150, "cat": "Desserts", "desc": "Chilled diced seasonal fruits (apple, papaya, melon, pomegranate) with vanilla ice cream.", "tags": ["fruit salad", "healthy dessert", "fresh"], "veg": True, "img": "https://images.unsplash.com/photo-1501443762994-82bd5dace89a?w=500"},
            {"name": "Mississippi Mud Pie Sundae", "price": 210, "cat": "Desserts", "desc": "Chocolate fudge cake with coffee ice cream and dark cookie crumbs.", "tags": ["mud pie", "coffee", "chocolate"], "veg": True, "img": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=500"},
            {"name": "Banana Split Classic", "price": 200, "cat": "Desserts", "desc": "Ripe banana split lengthwise with scoops of chocolate, vanilla, and strawberry.", "tags": ["banana split", "sundae", "retro"], "veg": True, "img": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=500"},
            {"name": "Sicilian Pistachio Gelato", "price": 160, "cat": "Desserts", "desc": "Authentic Italian gelato made with roasted green Sicilian pistachios.", "tags": ["pistachio", "gelato", "premium"], "veg": True, "img": "https://images.unsplash.com/photo-1501443762994-82bd5dace89a?w=500"},
            {"name": "Black Forest Sundae", "price": 180, "cat": "Desserts", "desc": "Chocolate gateau chunks with vanilla cream, sour cherry syrup, and chocolate shavings.", "tags": ["black forest", "sundae", "cherry"], "veg": True, "img": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=500"},
            {"name": "Trifle Pudding Bowl", "price": 170, "cat": "Desserts", "desc": "Layers of sponge cake, custard, strawberry jelly, fresh fruits, and cream.", "tags": ["trifle", "pudding", "classic"], "veg": True, "img": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=500"},
            {"name": "Nutty Chocolate Fondue Platter", "price": 240, "cat": "Desserts", "desc": "Warm dark chocolate pot served with brownie bites, marshmallows, and banana slices.", "tags": ["fondue", "chocolate", "sharing"], "veg": True, "img": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=500"},
            {"name": "Choco Hazelnut Thickshake", "price": 180, "cat": "Beverages", "desc": "Ultra thick milkshake blended with pure chocolate ice cream and Ferrero spread.", "tags": ["thickshake", "milkshake", "nutella"], "veg": True, "img": "https://images.unsplash.com/photo-1572498815684-263a6697022a?w=500"},
            {"name": "Mango Mastani Sundae Shake", "price": 190, "cat": "Desserts", "desc": "Pune style thick mango shake topped with ice cream, dry fruits, and tutti frutti.", "tags": ["mango mastani", "shake", "mango"], "veg": True, "img": "https://images.unsplash.com/photo-1572498815684-263a6697022a?w=500"},
            {"name": "Red Velvet Sundae in a Jar", "price": 190, "cat": "Desserts", "desc": "Red velvet sponge with cream cheese ice cream and white chocolate crumble.", "tags": ["red velvet", "jar", "sundae"], "veg": True, "img": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=500"},
            {"name": "Malai Kulfi on Stick", "price": 60, "cat": "Desserts", "desc": "Slow simmered rabri kulfi enriched with almonds, pistachios, and saffron.", "tags": ["kulfi", "malai", "budget"], "veg": True, "img": "https://images.unsplash.com/photo-1501443762994-82bd5dace89a?w=500"},
            {"name": "Oreo Overload Waffle Cone", "price": 140, "cat": "Desserts", "desc": "Cookies and cream ice cream in chocolate-dipped waffle cone with crushed Oreos.", "tags": ["oreo", "waffle cone", "cookies"], "veg": True, "img": "https://images.unsplash.com/photo-1501443762994-82bd5dace89a?w=500"},
            {"name": "Choco Dip Vanilla Soft Serve", "price": 80, "cat": "Desserts", "desc": "Creamy vanilla soft serve cone dipped into hard-crack warm dark chocolate shell.", "tags": ["soft serve", "choco dip", "quick"], "veg": True, "img": "https://images.unsplash.com/photo-1501443762994-82bd5dace89a?w=500"},
            {"name": "Lychee with Vanilla Ice Cream", "price": 160, "cat": "Desserts", "desc": "Juicy canned lychees swimming in sweet syrup, topped with rich vanilla scoops.", "tags": ["lychee", "fruit", "refreshing"], "veg": True, "img": "https://images.unsplash.com/photo-1501443762994-82bd5dace89a?w=500"},
        ]
    }
}

ADDITIONAL_CUISINES = [
    ("Gourmet Burgers & Wings", "Burgers", [
        "Truffles Burgers", "Burger Seigneur", "Leon's Burgers & Wings", "Plan B Koramangala",
        "Peppabowl", "Biggies Burger", "Louis Burger", "Wendy's Bangalore",
        "Rollsking Express", "Tibbs Frankie House"
    ], [
        ("All American Cheese Burger", 220, "Burgers", "Juicy grilled beef or chicken patty with cheddar cheese and gherkins.", ["burger", "cheese", "american"], False),
        ("Crispy Chicken Supreme Burger", 190, "Burgers", "Panko breaded fried chicken breast with garlic mayo on brioche.", ["burger", "crispy chicken"], False),
        ("Truffle Mushroom Swiss Burger", 260, "Burgers", "Grilled patty with wild sauteed mushrooms, truffle aioli, and Swiss cheese.", ["truffle", "burger", "gourmet"], True),
        ("Peri Peri Crispy Chicken Wings (6 pcs)", 210, "Starters", "Crispy fried wings tossed in fiery African peri-peri dust.", ["wings", "peri peri", "spicy"], False),
        ("Classic Chicken Shawarma Roll", 130, "Wraps", "Thin rumali roti rolled with slow-roasted chicken and garlic toum.", ["shawarma", "wrap", "budget"], False),
        ("Paneer Tikka Kathi Roll", 140, "Wraps", "Flaky paratha stuffed with charred paneer cubes, mint chutney, and onions.", ["kathi roll", "paneer", "veg"], True),
        ("Loaded Cheesy Nachos", 180, "Starters", "Tortilla chips with melted warm cheese, pico de gallo, and jalapenos.", ["nachos", "cheese", "snack"], True),
        ("Crispy Onion Rings with Garlic Dip", 120, "Starters", "Golden panko battered thick cut sweet onion rings.", ["onion rings", "crispy", "starter"], True),
        ("Chocolate Hazelnut Thickshake", 160, "Beverages", "Creamy milkshake blended with Belgian chocolate and Nutella.", ["shake", "chocolate", "beverage"], True),
    ]),
    ("Artisan Pizza & Pasta House", "Italian", [
        "Toit Brewpub Kitchen", "Onesta Pizzeria", "Brik Oven Neapolitan", "The Pizza Bakery",
        "Chianti Italian Ristorante", "Jamie's Pizzeria", "Tossin Pizza", "Nomad Pizza",
        "Little Italy Pure Veg", "Baked Pizza Co"
    ], [
        ("Classic Margherita Pizza (10\")", 280, "Pizza", "San Marzano tomato sauce, fresh buffalo mozzarella, and fresh basil.", ["pizza", "margherita", "classic"], True),
        ("Farmhouse Special Veggie Pizza", 360, "Pizza", "Loaded with bell peppers, sweet corn, mushrooms, black olives, and onions.", ["pizza", "farmhouse", "veggie"], True),
        ("Pepperoni & Mozzarella Pizza", 490, "Pizza", "Imported cured pork pepperoni with stringy mozzarella and chilli oil.", ["pepperoni", "pizza", "non veg"], False),
        ("Truffle & Wild Mushroom Pizza", 460, "Pizza", "White sauce base with portobello mushrooms and fragrant black truffle drizzle.", ["truffle pizza", "gourmet", "mushrooms"], True),
        ("Creamy Fettuccine Alfredo", 320, "Pasta", "Handmade egg fettuccine in rich garlic butter parmesan reduction.", ["alfredo", "pasta", "italian"], True),
        ("Penne Arrabiata with Garlic Bread", 290, "Pasta", "Penne tossed in spicy San Marzano tomato sauce with chilli and garlic.", ["arrabiata", "pasta", "spicy"], True),
        ("Cheesy Stuffed Garlic Bread", 160, "Starters", "Pull-apart fresh dough loaf stuffed with garlic herb butter and cheese.", ["garlic bread", "cheesy", "starter"], True),
        ("Traditional Italian Tiramisu", 240, "Desserts", "Ladyfingers dipped in espresso layered with mascarpone custard.", ["tiramisu", "dessert", "italian"], True),
    ]),
    ("Bangalore Street Chaats & Bhel", "Street Food", [
        "Sri Sairam's Chaats", "Karnataka Bhelpuri Center", "Gullu's Chaat Malleshwaram",
        "Anand Sweets Chaat Corner", "DVG Road Chaat Hub", "Bangarpet Pani Puri",
        "Calcutta Famous Chaats", "Delhi Chaat Bhandar", "Kartik's Mithai Chaat", "Sanman Chaat Center"
    ], [
        ("Bangarpet Clear Pani Puri (6 pcs)", 40, "Street Food", "Famous spicy clear water puris with warm spiced white peas.", ["pani puri", "golgappa", "street food", "bestseller"], True),
        ("Bangalore Masala Puri", 45, "Street Food", "Crushed crisp puris drenched in piping hot spiced green pea gravy and sev.", ["masala puri", "bangalore street food", "chaat"], True),
        ("Dahi Batata Puri (Dahi Puri)", 60, "Street Food", "Puris filled with potato and topped with chilled sweetened yogurt, tamarind, and sev.", ["dahi puri", "chaat", "sweet tangy"], True),
        ("Mumbai Style Sev Puri", 50, "Street Food", "Flat puris layered with potatoes, onions, trio of chutneys, and crisp sev.", ["sev puri", "chaat", "snack"], True),
        ("Special Bhel Puri", 45, "Street Food", "Puffed rice tossed with raw mango, onions, tomatoes, coriander, and chutneys.", ["bhel puri", "light", "crispy"], True),
        ("Amritsari Aloo Tikki Chaat", 65, "Street Food", "Crispy pan-fried potato patties topped with chole, curd, and date chutney.", ["aloo tikki", "chaat", "punjabi"], True),
        ("Cheese Pav Bhaji", 120, "Street Food", "Spiced vegetable mash loaded with melting Amul cheese, served with 2 butter toasted pavs.", ["pav bhaji", "cheese", "comfort"], True),
        ("Bombay Vada Pav (1 pc)", 35, "Street Food", "Spiced potato dumpling fried in chickpea batter inside pav with dry garlic chutney.", ["vada pav", "bombay", "budget"], True),
    ]),
    ("Traditional Sweets & Mithai Boutiques", "Sweets", [
        "Kanti Sweets", "Asha Sweet Center", "Sri Krishna Sweets", "KC Das",
        "Bhagatram Sweets", "Anand Sweets & Savouries", "Gangotree Sweets",
        "Adyar Ananda Bhavan Sweets", "Banchharam's Bengali Sweets", "Annapoorna Mithai"
    ], [
        ("Authentic Mysore Pak (250g)", 180, "Sweets", "Karnataka's royal sweet crafted from gram flour, pure country ghee, and sugar.", ["mysore pak", "ghee sweet", "traditional", "bestseller"], True),
        ("Pure Kaju Katli (250g)", 290, "Sweets", "Diamond cut rich cashew nut fudge decorated with silver foil.", ["kaju katli", "cashew", "festive"], True),
        ("Ghee Motichoor Ladoo (250g)", 160, "Sweets", "Tiny chickpea pearls fried in desi ghee and shaped into aromatic round laddoos.", ["motichoor", "ladoo", "mithai"], True),
        ("Spongy Kolkata Rasgulla (4 pcs)", 80, "Sweets", "Heritage cottage cheese dumplings poached in fragrant sugar syrup.", ["rasgulla", "bengali sweet", "light"], True),
        ("Kesar Rasmalai (2 pcs)", 90, "Sweets", "Delicate chenna patties soaked in chilled saffron and pistachio milk.", ["rasmalai", "kesar", "sweet"], True),
        ("Badam Halwa (100g)", 180, "Sweets", "Rich royal paste of California almonds slow-cooked in pure cow ghee.", ["badam halwa", "almond", "rich"], True),
        ("Special Mixture Namkeen (250g)", 85, "Savories", "Crisp spicy savory blend of sev, boondi, fried peanuts, and curry leaves.", ["mixture", "namkeen", "snack"], True),
    ]),
    ("Coastal Seafood & Mangalorean", "Coastal", [
        "Karavalli", "Mangalore Pearl", "Kudla Seafood Restaurant", "Coast Kafe",
        "Machali Coastal Dining", "Giri Manja's Seafood Express", "Sea Rock Coastal",
        "Coastal Bay Indiranagar", "Maravanthe Seafood Mess", "Anupam's Coast II Coast"
    ], [
        ("Neer Dosa with Chutney (3 pcs)", 60, "Coastal", "Delicate, lace-thin steamed rice crepes that melt in your mouth.", ["neer dosa", "coastal", "light"], True),
        ("Anjal (Kingfish) Tawa Fry", 360, "Seafood", "Fresh Kingfish steak marinated in fiery Kundapur red chilli paste and pan-seared.", ["fish fry", "anjal", "kingfish"], False),
        ("Kori Rotti with Chicken Gassi", 280, "Coastal", "Crisp dry rice wafers served with rich, spicy Mangalorean coconut chicken curry.", ["kori rotti", "mangalore", "chicken"], False),
        ("Mangalorean Prawns Ghee Roast", 390, "Seafood", "Plump coastal prawns slow-roasted in spicy Byadgi chilli and clarified butter.", ["prawns", "ghee roast", "bestseller"], False),
        ("Kane (Ladyfish) Rava Fry", 320, "Seafood", "Fresh ladyfish coated with semolina and fried golden and crisp.", ["kane fry", "fish", "rava fry"], False),
        ("Mangalore Buns (2 pcs)", 50, "Coastal", "Fluffy, golden banana-infused fried puris served with coconut chutney.", ["mangalore buns", "breakfast", "sweet"], True),
        ("Crab Sukka Masala", 420, "Seafood", "Fresh sea mud crab tossed with dry roasted coconut, curry leaves, and spices.", ["crab", "seafood", "sukka"], False),
    ]),
    ("Juices, Smoothies & Healthy Bowls", "Healthy", [
        "Juice Junction", "Fresh Pressery Café", "Fruitbae Shakes", "Keventers Shakes",
        "Dr. Juice Organic", "EatFit Health Kitchen", "Salad Days", "Smoothie Factory",
        "Cane-o-la Fresh Sugarcane", "Healthie Bowls"
    ], [
        ("ABC Immunity Juice (Apple Beetroot Carrot)", 120, "Juices", "Cold-pressed fresh juice with ginger and mint, rich in antioxidants.", ["abc juice", "detox", "healthy"], True),
        ("Cold Pressed Valencia Orange Juice", 110, "Juices", "100% pure squeezed sweet oranges without added water or sugar.", ["orange juice", "cold pressed", "fresh"], True),
        ("Avocado Honey Banana Smoothie", 160, "Smoothies", "Fresh avocado blended with banana, Greek yogurt, and organic honey.", ["smoothie", "avocado", "protein"], True),
        ("Watermelon Mint Cooler", 80, "Juices", "Chilled sweet watermelon crushed with fresh garden mint leaves.", ["watermelon", "hydrating", "summer"], True),
        ("Keventers Classic Thick Chocolate Shake", 180, "Beverages", "Legendary glass bottle thick milkshake with rich chocolate fudge.", ["thickshake", "keventers", "chocolate"], True),
        ("Greek Quinoa & Grilled Paneer Bowl", 240, "Salads", "Tricolor quinoa, Mediterranean roasted paneer, feta, and olive oil dressing.", ["salad", "quinoa", "healthy bowl"], True),
        ("Tender Coconut Shake with Malai", 120, "Beverages", "Fresh tender coconut water blended with sweet soft kernel pulp.", ["tender coconut", "shake", "coastal"], True),
    ]),
    ("Authentic Kerala & Malabar Dining", "Kerala", [
        "Calicut Paragon", "Ente Keralam", "Malabar Bay", "Kumarakom Restaurant",
        "Achayans Kitchen", "Kaayal Seafood", "Thalassery Kitchen", "Kudumbashree Mess",
        "Meen Curry House", "Kerala Hut"
    ], [
        ("Malabar Parotta with Beef Fry", 260, "Kerala", "Layered flaky parottas paired with slow-roasted caramelized coconut beef.", ["parotta", "beef fry", "kerala"], False),
        ("Appam with Vegetable Stew (2 pcs)", 180, "Kerala", "Bowl-shaped soft fermented rice hoppers with sweet coconut milk veg stew.", ["appam", "stew", "breakfast"], True),
        ("Karimeen Pollichathu (Pearl Spot)", 450, "Seafood", "Fresh backwater pearl spot fish baked in banana leaves with shallots and spices.", ["karimeen", "kerala", "seafood"], False),
        ("Thalassery Dum Biryani (Chicken)", 280, "Biryani", "Small grain Kaima rice slow cooked with Malabar whole spices and fried onions.", ["thalassery biryani", "biryani", "kerala"], False),
        ("Fish Moilee (Seer Fish)", 340, "Seafood", "Tender seer fish steaks gently poached in mild coconut milk and green chillies.", ["fish moilee", "curry", "mild"], False),
        ("Puttu with Kadala Curry", 120, "Kerala", "Steamed cylindrical rice and coconut flour cake served with spicy black chickpea curry.", ["puttu", "kadala curry", "kerala"], True),
        ("Pazham Pori (Banana Fritters - 2 pcs)", 40, "Snacks", "Ripe Nendran bananas coated in sweet batter and crisp golden fried.", ["pazham pori", "snack", "sweet"], True),
    ]),
    ("Arabian Shawarma & Charcoal Grills", "Arabian", [
        "Savoury Restaurant", "Al Taza Shawarma", "Al-Amanah Café", "Empire Arabian",
        "Rahhams Arabic", "Zaatar Restaurant", "Imperial Arabian", "Arabian Treats",
        "Mandi King Koramangala", "Bait Al Mandi"
    ], [
        ("Special Jumbo Whole Meat Shawarma", 150, "Arabian", "100% slow spit-roasted chicken packed tightly into thin rumali with garlic toum.", ["shawarma", "jumbo", "chicken"], False),
        ("Chicken Alfahm (Half)", 240, "Grills", "Arabian charcoal-grilled chicken marinated in Arabian spice blend, served with kuboos.", ["alfahm", "grilled chicken", "arabian"], False),
        ("Chicken Mandi (Half Platter)", 380, "Arabian", "Yemeni slow-cooked fragrant basmati rice topped with tender steam-baked chicken.", ["mandi", "arabian rice", "sharing"], False),
        ("Mutton Mandi (Half Platter)", 490, "Arabian", "Fall-off-the-bone young mutton served over aromatic spiced Mandi rice.", ["mutton mandi", "yemeni", "premium"], False),
        ("Creamy Hummus with Olive Oil & 2 Pita", 160, "Starters", "Smooth chickpea tahini dip drizzled with extra virgin olive oil.", ["hummus", "pita", "dip"], True),
        ("Charcoal Shish Tawook Skewers (6 pcs)", 260, "Grills", "Garlic and lemon marinated chicken cubes grilled over hot charcoals.", ["shish tawook", "skewers", "kebab"], False),
        ("Authentic Kunafa with Cheese", 240, "Desserts", "Crispy shredded filo pastry filled with melted sweet Akkawi cheese and sugar syrup.", ["kunafa", "arabian sweet", "dessert"], True),
    ]),
    ("Pan-Asian, Sushi & Ramen", "Pan-Asian", [
        "Daily Sushi", "Taiki Japanese", "Harima Restaurant", "Soo Ra Sang Korean",
        "Arirang Korean", "Saku Sushi Bar", "Kiko-Bā", "Nasi Goreng House",
        "Misose Asian", "Seoul Kitchen"
    ], [
        ("California Roll (6 pcs)", 380, "Sushi", "Crabstick, ripe avocado, and cucumber rolled in seasoned sushi rice with tobiko.", ["sushi", "california roll", "japanese"], False),
        ("Avocado & Cucumber Maki (6 pcs)", 290, "Sushi", "Vegetarian sushi roll with Hass avocado and English cucumber.", ["sushi", "veg sushi", "maki"], True),
        ("Chicken Paitan Ramen Bowl", 390, "Ramen", "Rich collagen chicken broth with handmade ramen noodles, seasoned egg, and nori.", ["ramen", "soup", "japanese"], False),
        ("Spicy Veg Miso Ramen", 340, "Ramen", "Fermented miso vegetable broth with bok choy, corn, bamboo shoots, and noodles.", ["ramen", "veg ramen", "miso"], True),
        ("Korean Crispy Fried Chicken (6 pcs)", 340, "Korean", "Double-fried crunchy wings glazed with sweet and spicy gochujang sauce.", ["korean chicken", "fried chicken", "gochujang"], False),
        ("Veg Bibimbap Hot Stone Bowl", 320, "Korean", "Warm rice topped with seasoned sauteed vegetables, gochujang paste, and sesame.", ["bibimbap", "korean", "bowl"], True),
        ("Steamed Chicken Gyoza (5 pcs)", 260, "Dim Sum", "Pan-seared Japanese potstickers filled with minced chicken and cabbage.", ["gyoza", "dumplings", "japanese"], False),
    ]),
    ("Organic, Vegan & Farm-to-Table", "Vegan", [
        "Green Theory", "Enerjuvate Café", "Go Native Indiranagar", "Justbe Holistic Café",
        "Carrots Vegan Bistro", "The Yogisthaan Café", "Santē Spa Cuisine", "Fabcafe Bangalore",
        "Roots Organic Food", "Prakriti Natural Food"
    ], [
        ("Millet Khichdi with Desi Ghee", 180, "Healthy", "Wholesome blend of foxtail millet and moong dal tempered with cumin and ginger.", ["khichdi", "millet", "comfort"], True),
        ("Raw Jackfruit Biryani (Vegan)", 280, "Healthy", "Tender raw jackfruit chunks marinated in royal spices layered in brown basmati.", ["vegan biryani", "jackfruit", "vegan"], True),
        ("Red Rice Dosa with Organic Chutney", 110, "South Indian", "Crisp dosa made from organic unpolished red rice and urad dal.", ["red rice", "dosa", "organic"], True),
        ("Sweet Potato Gnocchi in Herb Pesto", 320, "Continental", "Handmade sweet potato dumplings tossed in fresh basil cashew pesto.", ["gnocchi", "vegan", "gluten free"], True),
        ("Vegan Avocado Chocolate Mousse", 210, "Desserts", "Decadent dairy-free chocolate mousse whipped from ripe avocados and cocoa.", ["vegan mousse", "chocolate", "healthy dessert"], True),
        ("Cold Pressed Wheatgrass Shot", 60, "Beverages", "Freshly harvested organic wheatgrass juice for instant detoxification.", ["wheatgrass", "detox", "healthy"], True),
    ]),
    ("Continental Steaks, Ribs & European Grills", "Continental", [
        "Windmills Craftworks", "Portland Steakhouse", "Millers 46 Steakhouse", "The Smoke Co.",
        "Hard Rock Café Bangalore", "The Permit Room", "Arbor Brewing Kitchen", "Simon Says Brew Works",
        "Communiti Bistro", "Biergarten Kitchen"
    ], [
        ("Herb Crusted Roast Chicken Steak", 420, "Grills", "Pan-roasted chicken breast in rosemary jus served with garlic mash and veggies.", ["steak", "chicken steak", "continental"], False),
        ("Classic Beer Battered Fish & Chips", 380, "Continental", "Crispy golden sea bass fillet with salted fries and house tartar sauce.", ["fish and chips", "british", "crispy"], False),
        ("Slow Cooked Shepherd's Pie", 360, "Continental", "Minced lamb cooked with peas and carrots, topped with gratin mashed potato crust.", ["shepherds pie", "lamb", "comfort"], False),
        ("Pan Seared Norwegian Salmon", 680, "Seafood", "Fresh Atlantic salmon fillet served on a bed of lemon dill risotto.", ["salmon", "seafood", "premium"], False),
        ("Classic Bacon & Cheddar Beef Burger", 340, "Burgers", "Chargrilled tenderloin patty with crispy bacon rashers and aged cheddar.", ["beef burger", "bacon", "classic"], False),
        ("Warm Apple Crumble with Gelato", 240, "Desserts", "Baked cinnamon apples with butter crumble topping and vanilla ice cream.", ["apple crumble", "dessert", "warm"], True),
    ]),
    ("Royal Rajasthani & Gujarati Thali", "Thali", [
        "Rajdhani Thali Restaurant", "Kesariya Heritage Thali", "Khandani Rajdhani", "Gramin Restaurant",
        "Suruchi Gujarati Thali", "Royal Rajasthani Bhoj", "Panchavati Gaurav", "Chokhi Dhani Express",
        "Marwadi Bhojanalaya", "Maharaja Heritage Thali"
    ], [
        ("Grand Royal Rajasthani Thali (Unlimited)", 380, "Thali", "Complete royal feast with Dal Baati Churma, Gatte ki Sabzi, Kadhi, Roti, and Sweets.", ["thali", "rajasthani", "unlimited", "bestseller"], True),
        ("Dal Baati Churma Special Platter", 240, "Thali", "Crispy wheat baked baatis crushed in yellow dal and served with sweet churma.", ["dal baati", "rajasthani", "classic"], True),
        ("Rajasthani Gatte Ki Sabzi", 180, "North Indian", "Gram flour dumplings simmered in a spiced tangy yogurt curry.", ["gatta", "curry", "rajasthan"], True),
        ("Moong Dal Halwa with Desi Ghee", 120, "Desserts", "Rich golden pudding of yellow lentils roasted in pure cow ghee and cardamom.", ["moong dal halwa", "dessert", "pure ghee"], True),
        ("Steamed Nylon Dhokla (4 pcs)", 60, "Snacks", "Light and spongy fermented chickpea snack tempered with mustard seeds and green chillies.", ["dhokla", "gujarati", "light"], True),
        ("Masala Chaas (Spiced Buttermilk)", 40, "Beverages", "Refreshing churned curd flavored with roasted cumin, mint, and black salt.", ["chaas", "buttermilk", "cool"], True),
    ]),
    ("Andhra Mess & Rayalaseema Ruchulu", "Andhra", [
        "Nandhana Palace", "Amaravathi Andhra Mess", "Bheema's Restaurant", "Rayalaseema Ruchulu",
        "Kritunga Restaurant", "Nellore Mess Koramangala", "Gongura Andhra Meals", "Coastal Andhra Kitchen",
        "Ruchira Andhra Mess", "Madurai & Andhra Mess"
    ], [
        ("Authentic Andhra Veg Meals Thali", 180, "Thali", "Unlimited rice with Guntur pappu, sambar, rasam, gongura pachadi, and curd.", ["andhra meals", "thali", "unlimited", "spicy"], True),
        ("Gongura Mutton Curry", 380, "Main Course", "Tender young goat pieces cooked in tangy sorrel leaf (gongura) paste.", ["gongura mutton", "andhra", "spicy"], False),
        ("Natu Kodi Pulusu (Country Chicken)", 320, "Main Course", "Country chicken simmered in fiery Rayalaseema village gravy.", ["natu kodi", "country chicken", "spicy"], False),
        ("Andhra Royyala Vepudu (Prawn Fry)", 360, "Starters", "Fresh prawns pan-fried in caramelized onions, green chillies, and curry leaves.", ["prawn fry", "andhra", "seafood"], False),
        ("Guntur Chicken Fry Piece Biryani", 290, "Biryani", "Spicy shallow-fried chicken pieces layered over seasoned Andhra biryani rice.", ["andhra biryani", "guntur", "chicken"], False),
        ("Hot Ghee & Gunpowder (Kandi Podi) Rice", 110, "Rice", "Steaming hot sona masoori rice mixed with roasted lentil gunpowder and desi ghee.", ["podi rice", "ghee", "comfort"], True),
    ])
]


async def seed_200_bangalore_shops():
    async with async_session() as session:
        print("🧹 Cleaning old test data while preserving customer profile...")
        # Clean existing conversations, orders, products, and merchants
        await session.execute(delete(AuditLog))
        await session.execute(delete(Campaign))
        await session.execute(delete(Order))
        await session.execute(delete(Conversation))
        await session.execute(delete(Product))
        await session.execute(delete(Merchant))
        await session.commit()
        print("✓ Tables cleaned successfully.")

        total_merchants = 0
        total_products = 0

        # Iterate through primary cuisines and additional cuisines
        all_cuisines = []
        for cuisine_name, data in CUISINE_CATALOG.items():
            all_cuisines.append((cuisine_name, data["category"], data["shop_names"], [
                (d["name"], d["price"], d["cat"], d["desc"], d["tags"], d["veg"], d.get("img"))
                for d in data["dishes"]
            ]))

        for cuisine_name, cat, shop_names, dishes in ADDITIONAL_CUISINES:
            all_cuisines.append((cuisine_name, cat, shop_names, [
                (d[0], d[1], d[2], d[3], d[4], d[5], "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500")
                for d in dishes
            ]))

        # Target: 200 merchants total
        merchant_counter = 0
        nh_idx = 0

        created_merchants_map = {}

        for cuisine_name, primary_cat, shop_names, dish_list in all_cuisines:
            for shop_base_name in shop_names:
                merchant_counter += 1
                nh = NEIGHBORHOODS[nh_idx % len(NEIGHBORHOODS)]
                nh_idx += 1

                merchant_name = f"{shop_base_name} {nh['name']}" if nh['name'] not in shop_base_name else shop_base_name
                email = f"{shop_base_name.lower().replace(' ', '').replace('&', 'and').replace('(', '').replace(')', '').replace('\'', '')}_{nh['name'].lower()}@merchantmind.in"
                phone = f"+91{9800000000 + merchant_counter}"
                store_addr = f"{merchant_name}, {nh['address_suffix']}"
                rating = round(random.uniform(4.2, 4.9), 1)

                m = Merchant(
                    id=uuid.uuid4(),
                    name=merchant_name,
                    email=email,
                    phone=phone,
                    description=f"Authentic {cuisine_name} specialist in {nh['name']}, Bangalore. Known for signature {dish_list[0][0]} and authentic local flavors.",
                    whatsapp_number=phone,
                    store_latitude=nh["lat"] + random.uniform(-0.005, 0.005),
                    store_longitude=nh["lng"] + random.uniform(-0.005, 0.005),
                    store_address=store_addr,
                    neighborhood=nh["name"],
                    cuisine_type=cuisine_name,
                    avg_rating=rating,
                    is_active=True,
                )
                session.add(m)
                created_merchants_map[shop_base_name] = m
                total_merchants += 1

                # Ensure every shop has at least 25 authentic items
                extended_dishes = list(dish_list)
                if len(extended_dishes) < 25:
                    needed = 25 - len(extended_dishes)
                    for i in range(needed):
                        base_d = dish_list[i % len(dish_list)]
                        var_types = [
                            (" (Chef's Special Edition)", 1.15, "Special gourmet preparation with handpicked organic spices."),
                            (" Combo (with Chilled Beverage)", 1.25, "Value meal pairing served with beverage."),
                            (" (Family / Party Pack)", 1.85, "Large generous sharing portion ideal for 2-3 people."),
                            (" (Jumbo Portion)", 1.35, "Loaded portion with extra specialty toppings and condiments."),
                        ]
                        suffix, multiplier, desc_note = var_types[i % len(var_types)]
                        var_name = f"{base_d[0]}{suffix}"
                        var_price = round((base_d[1] * multiplier) / 5) * 5
                        var_desc = f"{base_d[3]} {desc_note}"
                        var_tags = list(base_d[4]) + ["combo" if "Combo" in suffix else "special"]
                        extended_dishes.append((var_name, var_price, base_d[2], var_desc, var_tags, base_d[5], base_d[6]))

                products_to_add = []
                for dish in extended_dishes:
                    p_name, p_price, p_cat, p_desc, p_tags, p_veg, p_img = dish
                    # Add minor price variance per store location (+- 5%)
                    price_var = round(p_price * random.uniform(0.95, 1.05) / 5) * 5
                    p_rating = round(random.uniform(4.0, 4.9), 1)

                    p = Product(
                        id=uuid.uuid4(),
                        merchant_id=m.id,
                        name=p_name,
                        price=float(price_var),
                        price_paise=int(price_var * 100),
                        category=p_cat,
                        description=p_desc,
                        tags=p_tags,
                        image_url=p_img or "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500",
                        in_stock=True,
                        stock_quantity=random.randint(15, 60),
                        rating=p_rating,
                        is_veg=p_veg,
                    )
                    products_to_add.append(p)
                    total_products += 1

                session.add_all(products_to_add)

        # Re-create the demo customer Utkarsh Singh with rich ambient memory
        demo_cust = Customer(
            id=uuid.uuid4(),
            merchant_id=list(created_merchants_map.values())[0].id,
            name="Utkarsh Singh",
            phone="+919876543210",
            email="utkarsh@merchantmind.ai",
            total_spent=1420.0,
            order_count=4,
            saved_addresses=[
                {
                    "label": "Home",
                    "address": "Flat 402, 100 Feet Road, Indiranagar, Bangalore - 560038",
                    "lat": 12.9784,
                    "lng": 77.6408,
                    "is_default": True,
                },
                {
                    "label": "Office",
                    "address": "WeWork Galaxy, Residency Road, Shanthala Nagar, Bangalore - 560025",
                    "lat": 12.9716,
                    "lng": 77.5946,
                    "is_default": False,
                },
            ],
            preferences={
                "dietary": ["Vegetarian"],
                "preferred_spice": "Medium",
                "max_typical_budget": 500,
                "favorite_cuisines": ["Artisan Bakery", "Chinese", "Specialty Coffee"],
            },
            favorite_merchants=[
                {
                    "name": "Sweet Chariot",
                    "last_item": "Belgian Truffle Cake",
                    "rating": 4.9,
                    "order_count": 3,
                },
                {
                    "name": "Beijing Bites",
                    "last_item": "Veg Manchurian Dry",
                    "rating": 4.8,
                    "order_count": 2,
                },
                {
                    "name": "Third Wave Coffee",
                    "last_item": "Cold Brew Coffee",
                    "rating": 4.9,
                    "order_count": 2,
                }
            ],
        )
        session.add(demo_cust)

        await session.commit()
        print(f"\n🎉 Elite Bangalore Food Knowledge Pipeline Seeded Successfully!")
        print(f"   • Total Active Merchants: {total_merchants} (Bangalore across 20 neighborhoods)")
        print(f"   • Total In-Stock Products: {total_products} (All genuine dishes with ratings & prices)")
        print(f"   • Customer Memory Profile: Utkarsh Singh (+919876543210) active with saved addresses & favorites")


if __name__ == "__main__":
    asyncio.run(seed_200_bangalore_shops())
