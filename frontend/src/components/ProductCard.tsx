"use client";

import React, { useState } from "react";
import Image from "next/image";
import { Plus, Check, Sparkles, Tag } from "lucide-react";
import { ProductRecommendation } from "@/lib/api";

interface ProductCardProps {
  product: ProductRecommendation;
  onAddToCart: (product: ProductRecommendation) => void;
  isAdding?: boolean;
}

export function ProductCard({ product, onAddToCart, isAdding = false }: ProductCardProps) {
  const [justAdded, setJustAdded] = useState(false);

  const handleAdd = () => {
    onAddToCart(product);
    setJustAdded(true);
    setTimeout(() => setJustAdded(false), 1500);
  };

  return (
    <div className="group relative flex flex-col overflow-hidden rounded-2xl border border-zinc-800/80 bg-zinc-900/90 p-4 shadow-lg backdrop-blur-md transition-all duration-300 hover:-translate-y-1 hover:border-indigo-500/50 hover:shadow-indigo-500/10">
      {/* Product Image */}
      <div className="relative mb-3.5 h-44 w-full overflow-hidden rounded-xl bg-gradient-to-tr from-zinc-800 to-zinc-900">
        {product.image_url ? (
          <Image
            src={product.image_url}
            alt={product.name}
            fill
            sizes="(max-width: 768px) 100vw, 300px"
            className="object-cover transition-transform duration-500 group-hover:scale-105"
            unoptimized
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-zinc-800/60 text-xs text-zinc-400">
            <span className="flex items-center gap-1.5 font-medium text-zinc-400">
              <Sparkles className="h-4 w-4 text-indigo-400" />
              {product.name}
            </span>
          </div>
        )}
        {product.category && (
          <span className="absolute left-2.5 top-2.5 inline-flex items-center gap-1 rounded-full bg-zinc-950/80 px-2.5 py-1 text-[11px] font-semibold text-zinc-200 backdrop-blur-md border border-zinc-700/50">
            <Tag className="h-3 w-3 text-indigo-400" />
            {product.category}
          </span>
        )}
      </div>

      {/* Product Info */}
      <div className="flex flex-1 flex-col justify-between">
        <div>
          <div className="flex items-start justify-between gap-2">
            <h4 className="font-semibold text-sm text-zinc-100 group-hover:text-indigo-300 transition-colors">
              {product.name}
            </h4>
            <span className="text-base font-bold text-indigo-400 shrink-0">
              ₹{product.price.toFixed(0)}
            </span>
          </div>

          {product.description && (
            <p className="mt-1.5 line-clamp-2 text-xs text-zinc-400 leading-relaxed">
              {product.description}
            </p>
          )}

          {/* AI Reasoning Pill */}
          {product.reasoning && (
            <div className="mt-3 flex items-start gap-2 rounded-xl bg-indigo-950/40 border border-indigo-500/20 p-2.5 text-xs text-indigo-200">
              <Sparkles className="mt-0.5 h-3.5 w-3.5 shrink-0 text-indigo-400" />
              <span className="text-[11px] font-medium leading-relaxed">{product.reasoning}</span>
            </div>
          )}
        </div>

        {/* Add to Cart Action */}
        <button
          onClick={handleAdd}
          disabled={isAdding}
          className={`mt-4 flex w-full items-center justify-center gap-2 rounded-xl py-2.5 text-xs font-semibold text-white shadow-md transition-all active:scale-[0.98] disabled:opacity-50 ${
            justAdded
              ? "bg-emerald-600 hover:bg-emerald-500"
              : "bg-indigo-600 hover:bg-indigo-500 hover:shadow-indigo-500/20"
          }`}
        >
          {justAdded ? (
            <>
              <Check className="h-4 w-4" />
              <span>Added to Cart!</span>
            </>
          ) : (
            <>
              <Plus className="h-4 w-4" />
              <span>{isAdding ? "Adding..." : "Add to Cart"}</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
