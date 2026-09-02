"use client";

import React, { useState } from "react";
import Image from "next/image";
import { motion } from "framer-motion";
import {
  Plus,
  Check,
  Sparkles,
  Tag,
  Cake,
  UtensilsCrossed,
  Salad,
  Shirt,
  Coffee,
  ShoppingBag,
  ShieldCheck,
  Store,
} from "lucide-react";
import { ProductRecommendation } from "@/lib/api";

interface ProductCardProps {
  product: ProductRecommendation;
  onAddToCart: (product: ProductRecommendation) => void;
  isAdding?: boolean;
}

// Curated high-resolution, perfectly-framed dish photo dictionary
const DISH_IMAGE_MAP: Array<{ match: string[]; url: string }> = [
  {
    match: ["pav bhaji", "pav-bhaji"],
    url: "https://images.unsplash.com/photo-1606491956689-2ea866880c84?w=600&auto=format&fit=crop&q=80",
  },
  {
    match: ["raj kachori", "kachori", "chaat", "samosa"],
    url: "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&auto=format&fit=crop&q=80",
  },
  {
    match: ["chole bhature", "bhatura", "chole"],
    url: "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=600&auto=format&fit=crop&q=80",
  },
  {
    match: ["jalebi", "gulab jamun", "rasgulla", "rasmalai", "mithai"],
    url: "https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?w=600&auto=format&fit=crop&q=80",
  },
  {
    match: ["dosa", "masala dosa", "plain dosa", "rava dosa", "ghee roast"],
    url: "https://images.unsplash.com/photo-1668236543090-82eba5ee5976?w=600&auto=format&fit=crop&q=80",
  },
  {
    match: ["idli", "vada", "medu vada", "rava idli"],
    url: "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=600&auto=format&fit=crop&q=80",
  },
  {
    match: ["biryani", "pulao", "dum biryani", "hyderabadi"],
    url: "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&auto=format&fit=crop&q=80",
  },
  {
    match: ["paneer", "paneer butter", "paneer tikka", "dal makhani", "shahi paneer"],
    url: "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=600&auto=format&fit=crop&q=80",
  },
  {
    match: ["kebab", "tandoori", "tikka", "chicken tikka", "platter"],
    url: "https://images.unsplash.com/photo-1544025162-d76694265947?w=600&auto=format&fit=crop&q=80",
  },
  {
    match: ["chocolate cake", "truffle cake", "black forest", "fudge cake", "lava cake"],
    url: "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=600&auto=format&fit=crop&q=80",
  },
  {
    match: ["red velvet", "strawberry cake"],
    url: "https://images.unsplash.com/photo-1616541823729-00fe0aacd32c?w=600&auto=format&fit=crop&q=80",
  },
  {
    match: ["butterscotch", "caramel cake", "pineapple cake"],
    url: "https://images.unsplash.com/photo-1621303837174-89787a7d4729?w=600&auto=format&fit=crop&q=80",
  },
  {
    match: ["cheesecake", "pastry", "eclair", "muffin", "tiramisu", "tart"],
    url: "https://images.unsplash.com/photo-1533134242443-d4fd215305ad?w=600&auto=format&fit=crop&q=80",
  },
  {
    match: ["croissant", "sourdough", "bread", "bun", "bagel", "garlic bread"],
    url: "https://images.unsplash.com/photo-1555507036-ab1f4038024a?w=600&auto=format&fit=crop&q=80",
  },
  {
    match: ["ice cream", "sundae", "death by chocolate", "brownie with ice cream", "fudge"],
    url: "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=600&auto=format&fit=crop&q=80",
  },
  {
    match: ["burger", "sandwich", "wrap", "roll"],
    url: "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=600&auto=format&fit=crop&q=80",
  },
  {
    match: ["coffee", "latte", "cappuccino", "filter coffee", "espresso", "frappe"],
    url: "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=600&auto=format&fit=crop&q=80",
  },
  {
    match: ["pizza", "margherita", "pasta"],
    url: "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=600&auto=format&fit=crop&q=80",
  },
  {
    match: ["curry", "chicken curry", "mutton", "rogan josh", "fish"],
    url: "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=600&auto=format&fit=crop&q=80",
  },
  {
    match: ["shirt", "kurta", "linen", "apparel", "dress", "t-shirt"],
    url: "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=600&auto=format&fit=crop&q=80",
  },
  {
    match: ["grocery", "apple", "vegetable", "fruit", "organic"],
    url: "https://images.unsplash.com/photo-1610832958506-aa56368176cf?w=600&auto=format&fit=crop&q=80",
  },
];

// Resolves a pristine, correctly-aligned dish image based on name and category
function resolveDishImage(name: string, category?: string, originalUrl?: string): string {
  const query = `${name} ${category || ""}`.toLowerCase();

  // Known problematic/generic Unsplash images that need specific dish matching
  const isGenericImage =
    !originalUrl ||
    originalUrl.includes("photo-1504674900247") || // Generic meat platter
    originalUrl.includes("photo-1571877227200") || // Generic tiramisu slice
    originalUrl.includes("photo-1585937421612") || // Generic double pot
    originalUrl.includes("photo-1525059696034");

  // If we find an exact culinary match, prioritize it for accurate visual alignment
  for (const item of DISH_IMAGE_MAP) {
    if (item.match.some((m) => query.includes(m))) {
      return item.url;
    }
  }

  return originalUrl && !isGenericImage ? originalUrl : DISH_IMAGE_MAP[0].url;
}

export function ProductCard({ product, onAddToCart, isAdding = false }: ProductCardProps) {
  const [justAdded, setJustAdded] = useState(false);
  const [imgError, setImgError] = useState(false);

  const handleAdd = () => {
    onAddToCart(product);
    setJustAdded(true);
    setTimeout(() => setJustAdded(false), 1500);
  };

  const getCategoryVisual = (cat?: string, name?: string) => {
    const combined = `${cat || ""} ${name || ""}`.toLowerCase();
    if (
      combined.includes("cake") ||
      combined.includes("bake") ||
      combined.includes("dessert") ||
      combined.includes("truffle") ||
      combined.includes("pastry") ||
      combined.includes("jalebi") ||
      combined.includes("sweet")
    ) {
      return {
        icon: <Cake className="h-7 w-7 text-[#A78BFA]" />,
        badgeColor: "from-purple-500/20 to-indigo-500/10 border-purple-500/30 text-[#A78BFA]",
        label: "Bakery & Desserts",
      };
    }
    if (
      combined.includes("biryani") ||
      combined.includes("food") ||
      combined.includes("curry") ||
      combined.includes("rice") ||
      combined.includes("meal") ||
      combined.includes("pav bhaji") ||
      combined.includes("chole") ||
      combined.includes("kachori")
    ) {
      return {
        icon: <UtensilsCrossed className="h-7 w-7 text-amber-400" />,
        badgeColor: "from-amber-500/20 to-orange-500/10 border-amber-500/30 text-amber-300",
        label: "Hot Kitchen",
      };
    }
    if (
      combined.includes("veg") ||
      combined.includes("groc") ||
      combined.includes("fruit") ||
      combined.includes("salad") ||
      combined.includes("organic")
    ) {
      return {
        icon: <Salad className="h-7 w-7 text-emerald-400" />,
        badgeColor: "from-emerald-500/20 to-teal-500/10 border-emerald-500/30 text-emerald-300",
        label: "Fresh Produce",
      };
    }
    if (
      combined.includes("coffee") ||
      combined.includes("tea") ||
      combined.includes("beverage") ||
      combined.includes("drink")
    ) {
      return {
        icon: <Coffee className="h-7 w-7 text-amber-300" />,
        badgeColor: "from-amber-500/20 to-yellow-500/10 border-amber-500/30 text-amber-200",
        label: "Beverages",
      };
    }
    if (
      combined.includes("cloth") ||
      combined.includes("apparel") ||
      combined.includes("shirt") ||
      combined.includes("dress")
    ) {
      return {
        icon: <Shirt className="h-7 w-7 text-pink-400" />,
        badgeColor: "from-pink-500/20 to-rose-500/10 border-pink-500/30 text-pink-300",
        label: "Apparel",
      };
    }
    return {
      icon: <ShoppingBag className="h-7 w-7 text-[#0891B2]" />,
      badgeColor: "from-cyan-500/20 to-blue-500/10 border-cyan-500/30 text-[#0891B2]",
      label: "Store Item",
    };
  };

  const visual = getCategoryVisual(product.category, product.name);
  const resolvedImage = resolveDishImage(product.name, product.category, product.image_url);

  return (
    <motion.div
      whileHover={{ y: -3 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className="group relative flex h-full flex-col justify-between overflow-hidden rounded-2xl border border-[#2A2A3E] bg-[#12121E]/95 p-3.5 shadow-xl backdrop-blur-xl transition-all duration-300 hover:border-[#7C3AED]/50 hover:shadow-2xl hover:shadow-[#7C3AED]/15"
    >
      {/* 1. Top Image Banner with Perfect Aspect Ratio & Alignment */}
      <div className="relative mb-3 h-44 w-full shrink-0 overflow-hidden rounded-xl bg-gradient-to-br from-[#1A1A2C] to-[#0D0D18] border border-[#2A2A3E]/60">
        {resolvedImage && !imgError ? (
          <div className="relative h-full w-full">
            <Image
              src={resolvedImage}
              alt={product.name}
              fill
              sizes="(max-width: 768px) 100vw, 320px"
              className="object-cover object-center transition-transform duration-500 group-hover:scale-105"
              onError={() => setImgError(true)}
              unoptimized
            />
            {/* Subtle Vignette Gradient for Clean Badge Contrast */}
            <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-[#0A0A12]/80 via-transparent to-black/30" />
          </div>
        ) : (
          <div className="flex h-full w-full flex-col items-center justify-center p-3 text-center">
            <div
              className={`flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br ${visual.badgeColor} shadow-inner`}
            >
              {visual.icon}
            </div>
            <span className="mt-2 text-[11px] font-semibold text-zinc-300 line-clamp-1">
              {product.name}
            </span>
          </div>
        )}

        {/* Category Pill (Top Left) */}
        <span className="absolute left-2.5 top-2.5 inline-flex items-center gap-1 rounded-full bg-[#0A0A12]/90 px-2 py-0.5 text-[10px] font-semibold text-zinc-200 backdrop-blur-md border border-[#2A2A3E] shadow-sm">
          <Tag className="h-2.5 w-2.5 text-[#0891B2]" />
          {product.category || visual.label}
        </span>

        {/* Verified In-Stock Badge (Top Right) */}
        <span className="absolute right-2.5 top-2.5 inline-flex items-center gap-1 rounded-full bg-[#0A0A12]/90 px-2 py-0.5 text-[9px] font-semibold text-emerald-400 backdrop-blur-md border border-emerald-500/35 shadow-sm">
          <ShieldCheck className="h-2.5 w-2.5" />
          In Stock
        </span>
      </div>

      {/* 2. Structured Product Details with Fixed Baselines */}
      <div className="flex flex-1 flex-col justify-between">
        <div>
          {/* Title & Price Header */}
          <div className="flex items-start justify-between gap-2 min-h-[38px]">
            <h4 className="font-semibold text-xs sm:text-sm text-[#F0EEFF] group-hover:text-[#A78BFA] transition-colors leading-snug line-clamp-2">
              {product.name}
            </h4>
            <span className="text-sm font-bold text-[#0891B2] shrink-0 font-mono">
              ₹{product.price.toFixed(0)}
            </span>
          </div>

          {/* Description line */}
          <div className="min-h-[32px] mt-1">
            {product.description ? (
              <p className="line-clamp-2 text-[11px] text-zinc-400 leading-relaxed">
                {product.description}
              </p>
            ) : (
              <p className="text-[11px] text-zinc-500 italic">Freshly prepared order</p>
            )}
          </div>

          {/* AI Reasoning / Store Pill */}
          {product.reasoning && (
            <div className="mt-2 flex items-start gap-1.5 rounded-xl bg-[#7C3AED]/10 border border-[#7C3AED]/25 p-2 text-xs text-[#A78BFA]">
              <Sparkles className="mt-0.5 h-3 w-3 shrink-0 text-[#7C3AED]" />
              <span className="text-[11px] font-normal leading-relaxed line-clamp-2">
                {product.reasoning}
              </span>
            </div>
          )}
        </div>

        {/* 3. Bottom Action Button Locked to Baseline */}
        <div className="mt-3 pt-1">
          <motion.button
            whileTap={{ scale: 0.96 }}
            whileHover={{ scale: 1.01 }}
            onClick={handleAdd}
            disabled={isAdding}
            className={`flex w-full items-center justify-center gap-1.5 rounded-xl py-2.5 text-xs font-semibold text-white shadow-md transition-all disabled:opacity-50 cursor-pointer ${
              justAdded
                ? "bg-emerald-600 hover:bg-emerald-500 shadow-emerald-600/20"
                : "bg-gradient-to-r from-[#7C3AED] via-[#6D28D9] to-[#5B21B6] hover:from-[#6D28D9] hover:to-[#4C1D95] shadow-[#7C3AED]/25 hover:shadow-lg hover:shadow-[#7C3AED]/35"
            }`}
          >
            {justAdded ? (
              <>
                <Check className="h-3.5 w-3.5" />
                <span>Added to Cart</span>
              </>
            ) : (
              <>
                <Plus className="h-3.5 w-3.5" />
                <span>Add to Order</span>
              </>
            )}
          </motion.button>
        </div>
      </div>
    </motion.div>
  );
}
