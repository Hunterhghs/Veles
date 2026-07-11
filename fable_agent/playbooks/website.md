# Playbook: Websites

Marketing sites, landing pages, and client microsites. The bar: looks
professionally designed, loads fast, works on a phone.

## Default technical approach

- **Static single/multi-page site** (default): semantic HTML + modern CSS
  (custom properties, grid/flexbox) or Tailwind via CDN. No build step
  unless the project already has one. Vanilla JS for interactivity.
- **Framework (Next.js/Astro)** only when the client needs a CMS, many
  pages, or an existing stack dictates it.
- Deploy targets in order of preference: GitHub Pages, Netlify, Vercel —
  all free-tier friendly for freelance work. Include deploy instructions.

## Page anatomy (landing/marketing)

```
Header   — logo, ≤5 nav links, one CTA button; sticky, collapses to burger
Hero     — headline (benefit, not feature), subhead, primary CTA,
           supporting stat or visual
Proof    — stats row / logos / testimonial
Sections — one idea per section, alternating layout, generous whitespace
CTA      — repeated call-to-action before the footer
Footer   — contact, links, legal
```

## Design system (pick deliberately, apply consistently)

- Palette: one accent, 2–3 neutrals, defined as CSS custom properties.
  Check contrast (WCAG AA).
- Type: two families max (display + body), a modular scale (e.g. 1.25),
  line-height ≥ 1.5 for body, ~65ch max line length.
- Spacing: a fixed scale (4/8/16/24/40/64px); section padding consistent.
- Motion: subtle only — 150–300ms transitions, respect
  `prefers-reduced-motion`.

## Non-negotiables

- Responsive at 375 / 768 / 1440px; no horizontal scroll at any width.
- `<title>`, meta description, Open Graph tags, favicon; one `<h1>` per page.
- Images: real dimensions set (no layout shift), compressed, `alt` text,
  `loading="lazy"` below the fold.
- Lighthouse sanity: no render-blocking font walls, system-font fallbacks.
- Working contact path (form with validation + mailto fallback, or clear
  contact info).

## Quality gate before delivery

Open the site locally, click every link, submit every form, resize to
mobile, and run the console — zero errors, zero broken paths.
