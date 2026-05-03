# Home Finds 🏠

Amazon Affiliate website for curated Home & Kitchen products. Built with **Astro** + **Tailwind CSS** — fast, SEO-optimized, and ready for Vercel deployment.

## Tech Stack

- **[Astro](https://astro.build)** v5 — Static Site Generator (0 JS by default)
- **[Tailwind CSS](https://tailwindcss.com)** v3 — Utility-first CSS
- **Content Collections** — Markdown-based product management
- **Vercel** — One-click deploy

## Project Structure

```
src/
├── content/posts/       # Product markdown files
├── layouts/             # Page layouts
├── components/          # Reusable UI components
├── pages/               # Route pages
│   ├── index.astro      # Home page
│   ├── posts/[slug].astro  # Product detail page
│   ├── categories/      # Category pages
│   └── about.astro      # About + Disclosure
public/                  # Static assets
```

## Local Development

```bash
# Install dependencies
npm install

# Start dev server (http://localhost:4321)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Adding a New Product

Create a new `.md` file in `src/content/posts/`:

```markdown
---
title: "Your Product Name"
image: "https://example.com/image.jpg"
price: "$29.99"
amazonLink: "https://www.amazon.com/dp/ASIN"
category: "Kitchen Gadgets"   # or "Living Room Decor" or "Organization Hacks"
features:
  - "Feature 1"
  - "Feature 2"
rating: 4.5
date: 2025-01-15
description: "SEO-friendly description for search engines."
---

Your detailed product description here...
```

The new product will automatically appear on the homepage and in its category page.

## Deploy to Vercel

### Option 1: One-click Deploy

1. Push this repo to GitHub
2. Go to [vercel.com](https://vercel.com) → "Add New Project"
3. Import your GitHub repository
4. Vercel auto-detects Astro — no config needed
5. Click "Deploy"

### Option 2: CLI

```bash
npm i -g vercel
vercel --prod
```

### Post-Deployment

1. Update the `site` URL in `astro.config.mjs` to your Vercel domain
2. Update `public/robots.txt` with your actual domain
3. Add your custom domain in Vercel dashboard (optional)

## Customization

- **Colors**: Edit `tailwind.config.mjs` (brand green, accent terracotta, cream background)
- **Font**: Change Google Fonts import in `src/styles/global.css`
- **Logo**: Update the SVG in `public/favicon.svg`

## Pinterest Tips

- Product images should be **vertical** (e.g., 1000×1500px) for best Pinterest results
- Each product page has Open Graph meta tags for rich social sharing
- The design is mobile-first for Pinterest referral traffic

---

Built with ♥ for affiliate marketing.
