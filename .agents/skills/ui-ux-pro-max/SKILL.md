---
name: ui-ux-pro-max
description: >-
  AI-powered design intelligence with 84 UI styles, 192 color palettes, 74 font pairings,
  98 UX guidelines, and 25 chart types across 22 tech stacks. Use for generating design systems,
  selecting color palettes, font pairings, UI styles, UX best practices, accessibility audits,
  and frontend component design.
---

# UI UX Pro Max Skill

AI-powered design intelligence toolkit providing searchable databases of UI styles, color palettes, font pairings, chart types, and UX guidelines.

## Quick CLI Search Reference

Run searches from project root using Python 3:

```bash
# Generate complete design system for a product/feature
python3 .agents/skills/ui-ux-pro-max/src/ui-ux-pro-max/scripts/search.py "<query>" --design-system [-p "Project Name"]

# Domain-specific search:
# Domains: product, style, typography, color, landing, chart, ux, icons, react, web, google-fonts, gsap
python3 .agents/skills/ui-ux-pro-max/src/ui-ux-pro-max/scripts/search.py "<query>" --domain <domain> [-n <max_results>]

# Stack guidelines:
# Stacks: nextjs, react, html-tailwind, shadcn, vue, svelte, astro, flutter, react-native, etc.
python3 .agents/skills/ui-ux-pro-max/src/ui-ux-pro-max/scripts/search.py "<query>" --stack <stack>
```

## Available Domains

| Domain | Use For | Example Keywords |
|--------|---------|------------------|
| `product` | Product type recommendations | SaaS, e-commerce, fintech, portfolio |
| `style` | UI styles, colors, effects | glassmorphism, minimalism, dark mode, brutalism, bento-grid |
| `typography` | Font pairings, Google Fonts | elegant, playful, professional, modern, geometric-sans |
| `color` | Color palettes by product type | fintech, ecommerce, saas, dark-mode |
| `landing` | Page structure, CTA strategies | hero, pricing, social-proof, testimonial |
| `chart` | Chart types & viz libraries | trend, comparison, timeline, funnel, realtime |
| `ux` | Best practices, anti-patterns | error-validation, loading, accessibility, modal-focus |
| `gsap` | Animation skeletons by tier | scroll-reveal, stagger, hover, page-transition |
| `react` | React/Next.js performance | suspense, streaming, rerender-memo, bundle |
| `icons` | Icon recommendations (Phosphor, Lucide, Heroicons) | arrow, navigation, payment, security |

## Standard Design Workflow

1. **Analyze Requirements**: Identify product category, target audience, vibe/tone, stack (e.g. Next.js 16 + Tailwind CSS v4).
2. **Generate Design System**: Run `search.py "<query>" --design-system -p "<Name>"`.
3. **Supplement with Details**: Query specific domains (e.g. `color`, `typography`, `ux`, `gsap`).
4. **Implement Tokens & Components**: Apply semantic design tokens, clean contrast ratios (≥4.5:1), and consistent micro-interactions.
