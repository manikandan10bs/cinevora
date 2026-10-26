# FRONTEND-DNA.md

## Purpose

This file defines the visual and interaction DNA of `streamXie-ui`.
Read it before changing UI code. The existing streaming product experience is the source of truth.

---

## Product Tone

**Primary tone:** cinematic, premium, focused, and content-first.  
**Secondary tone:** energetic enough for entertainment discovery, but still controlled and usable.  
**Must never feel:** generic SaaS dashboard, bright corporate landing page, cluttered marketplace, or playful gamified app.

Reference direction:

- Netflix-style content density and horizontal discovery.
- Modern anime/drama streaming catalog surfaces.
- Dark theatrical media UI with restrained neon accents.

---

## Core Visual Principles

- Content imagery leads the interface. UI chrome supports discovery instead of competing with posters and backdrops.
- Dark mode is the baseline experience. Do not introduce a light theme without a dedicated design pass.
- Use the teal/cyan brand gradient for high-value actions, active states, and hero accents.
- Keep page sections unframed. Cards are for individual titles, modals, empty states, and compact tools.
- Preserve the cinematic hierarchy: large hero, dense content rows, compact metadata, strong poster imagery.
- Avoid decorative blobs, unrelated gradients, and marketing-style hero split layouts.

---

## Color System

Colors are defined as HSL custom properties in `src/index.css` and mapped in `tailwind.config.js`.

### Brand Tokens

```text
background:          hsl(220 15% 7%)
foreground:          hsl(0 0% 98%)
primary:             hsl(160 80% 45%)
primary-foreground:  hsl(0 0% 100%)
secondary:           hsl(160 60% 30%)
tertiary:            hsl(210 20% 20%)
accent:              hsl(190 90% 45%)
ring:                hsl(160 80% 50%)
```

### Surface Tokens

```text
card:                hsl(220 15% 12%)
popover:             hsl(220 15% 12%)
surface:             hsl(220 15% 10%)
border:              hsl(220 10% 30%)
input:               hsl(220 15% 15%)
muted:               hsl(220 10% 20%)
muted-foreground:    hsl(220 10% 80%)
```

### Semantic Tokens

```text
success: hsl(145 65% 45%)
warning: hsl(40 90% 50%)
error:   hsl(0 80% 55%)
info:    hsl(200 90% 60%)
```

### Color Rules

Do:

- Use `bg-gradient-primary` for primary streaming actions such as play/watch.
- Use `text-muted-foreground` for metadata, helper text, and secondary descriptions.
- Use transparent dark overlays on imagery so titles and metadata remain readable.
- Use semantic colors only for actual state, feedback, and risk.

Do not:

- Add large bright sections that break the dark cinematic baseline.
- Introduce unrelated accent colors for categories unless they are contained to small badges.
- Use color as the only state indicator.
- Hardcode new color values when an existing token works.

---

## Typography

### Fonts

```text
Display / headings: DM Sans
Body:               Inter
Mono:               IBM Plex Mono
Serif:              not used
```

### Type Behavior

- Hero titles can use uppercase, wide tracking, and large sizes.
- Section titles use compact uppercase treatment with moderate tracking.
- Cards use tight hierarchy: title, one metadata row, one short genre/rating row.
- Body copy stays readable and restrained; avoid oversized explanatory text inside app surfaces.
- Do not scale fonts with viewport width.
- Do not use negative letter spacing.

---

## Layout And Spacing

```text
Max content width:       1440px
Desktop page padding:    48px
Tablet page padding:     24px to 48px
Mobile page padding:     24px
Hero minimum height:     about 90vh
Card radius:             12px for streaming cards
Standard control radius: 8px to 12px
```

Spacing scale:

```text
4px   micro gaps
8px   tight internal gaps
12px  compact component padding
16px  standard component padding
24px  related groups
32px  page group spacing
48px  major page spacing
64px+ large hero/section separation
```

Rules:

- Horizontal carousels should keep fixed card widths so scroll behavior is predictable.
- Poster cards use `aspect-[2/3]`; landscape cards use wide media ratios.
- Avoid layout shift from hover states, badges, buttons, or dynamic labels.
- Mobile layouts should keep primary discovery actions reachable without hiding all navigation.

---

## Component Patterns

### Navigation

- Top navigation is fixed and transparent on the home hero until scrolled.
- Scrolled nav uses dark background, subtle border, and backdrop blur.
- Desktop navigation uses centered links and a Browse dropdown.
- Mobile navigation uses a slide/dropdown menu with icon-supported items.
- Active states use primary color and a small underline or dot.

### Buttons

- Primary action: gradient fill, white text, 12px radius, subtle brightness hover.
- Secondary action: translucent or bordered surface, hover border/foreground emphasis.
- Icon-only action: square-ish hit area, visible focus state, accessible label.
- Destructive action: use error token sparingly and only for real destructive behavior.
- Primary actions should not sit in competition with multiple equal-weight CTAs.

### Cards

- Poster cards prioritize artwork first, then title and metadata.
- Use overlays for watch/list controls instead of adding heavy card footers.
- Hover may add a restrained glow or border emphasis.
- Do not nest cards inside cards.
- Empty states may use dashed borders and centered content, but should stay visually quiet.

### Forms

- Labels are visible and associated with inputs.
- Inputs use dark surfaces, border tokens, and primary focus rings.
- Validation should appear inline or as small status feedback.
- Auth screens are currently mock UI; avoid implying real account security until backend auth exists.

### Modals And Overlays

- Trailer/player modals use dark backdrop overlays and strong focus containment.
- Close controls must remain visible and keyboard accessible.
- Media modals should keep aspect ratio stable across viewport sizes.

### Player Surface

- Controls should feel like a streaming app: compact, overlayed, and content-aware.
- Progress, volume, fullscreen, and episode actions must not resize the video frame.
- Use icons for familiar media controls.
- Preserve readable contrast over video/backdrop surfaces.

---

## Motion

- Motion should support cinematic transitions and state clarity.
- Use short durations, generally 150ms to 500ms.
- Hero rotation and progress indicators are acceptable because they reinforce featured content.
- Avoid bounce, excessive sequential animation, and decorative motion that does not explain a transition.
- Respect `prefers-reduced-motion` for any future complex animation.

---

## Accessibility

Required for future UI work:

- Visible focus states for buttons, links, inputs, menus, and player controls.
- ARIA labels on icon-only controls.
- Keyboard navigation for menus, dialogs, and media controls.
- Text contrast at least 4.5:1 for body text and 3:1 for large text.
- Do not use placeholder text as the only label.
- Do not rely on color alone to communicate active, success, warning, or error states.

---

## Responsive Rules

| Surface | Desktop | Mobile |
| --- | --- | --- |
| Home hero | Full cinematic hero with metadata and actions | Preserve image impact and keep actions reachable |
| Content rows | Horizontal carousels with fixed card widths | Horizontal scroll with hidden scrollbar and clear spacing |
| Browse | Filter controls above responsive grid | Chips and filters stack without crowding |
| Detail pages | Backdrop-led layout with sections below | Metadata stacks and media remains readable |
| Watch page | Player plus side/secondary content | Player first, episode/recommendation content below |
| Navigation | Full nav with dropdown | Compact nav with mobile menu |

---

## Forbidden Outcomes

- Public-facing screens that feel like generic dashboard UI.
- New large white/light sections.
- UI cards inside other UI cards.
- Decorative gradient blobs, orbs, or unrelated abstract backgrounds.
- Text overlapping media, controls, cards, or adjacent sections.
- Poster or player components that resize when controls appear.
- New component styles that bypass the token system.

---

## Design Assets

- App and public docs logo asset: `src/assets/streamxie-brand-logo.png`
- Content imagery: `src/assets/content/`
- Avatar imagery: `src/assets/avatars/`
- Design tokens: `src/index.css` and `tailwind.config.js`
- Storybook: not implemented
- Figma file: not available

---

## Change Log

| Date | Author | Change | Reason |
| --- | --- | --- | --- |
| 2026-04-28 | Codex | Replaced generic template with streamXie-specific visual rules | Prepare repository for public reuse |
