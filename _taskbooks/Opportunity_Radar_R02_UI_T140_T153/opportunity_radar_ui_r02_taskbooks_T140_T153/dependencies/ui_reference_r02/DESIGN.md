---
name: Opportunity Radar
colors:
  surface: '#f7f9fb'
  surface-dim: '#d8dadc'
  surface-bright: '#f7f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#eceef0'
  surface-container-high: '#e6e8ea'
  surface-container-highest: '#e0e3e5'
  on-surface: '#191c1e'
  on-surface-variant: '#434655'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#737686'
  outline-variant: '#c3c6d7'
  surface-tint: '#0053db'
  primary: '#004ac6'
  on-primary: '#ffffff'
  primary-container: '#2563eb'
  on-primary-container: '#eeefff'
  inverse-primary: '#b4c5ff'
  secondary: '#505f76'
  on-secondary: '#ffffff'
  secondary-container: '#d0e1fb'
  on-secondary-container: '#54647a'
  tertiary: '#4d556b'
  on-tertiary: '#ffffff'
  tertiary-container: '#656d84'
  on-tertiary-container: '#eef0ff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dbe1ff'
  primary-fixed-dim: '#b4c5ff'
  on-primary-fixed: '#00174b'
  on-primary-fixed-variant: '#003ea8'
  secondary-fixed: '#d3e4fe'
  secondary-fixed-dim: '#b7c8e1'
  on-secondary-fixed: '#0b1c30'
  on-secondary-fixed-variant: '#38485d'
  tertiary-fixed: '#dae2fd'
  tertiary-fixed-dim: '#bec6e0'
  on-tertiary-fixed: '#131b2e'
  on-tertiary-fixed-variant: '#3f465c'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  mono-data:
    fontFamily: monospace
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 16px
  margin-mobile: 16px
  margin-desktop: 32px
---

## Brand & Style
The design system is engineered for high-stakes B2B decision-making, where clarity and data density take precedence over decorative flair. The brand personality is clinical, efficient, and authoritative.

The aesthetic follows a **Modern Minimalist** framework. It intentionally strips away visual noise—eliminating gradients, blurs, and illustrations—to focus entirely on information hierarchy. The emotional response should be one of "calm control," allowing users to process complex data sets without cognitive fatigue. Every element must serve a functional purpose; if a component doesn't aid in data interpretation, it is removed.

## Colors
The palette is rooted in a "Utility First" philosophy. 

- **Primary (#2563EB):** Reserved strictly for primary actions, active states, and critical indicators.
- **Surface (#FFFFFF):** Used for data containers and cards to provide maximum contrast against the background.
- **Background (#F8FAFC):** A cool-toned slate white used to reduce screen glare during long work sessions.
- **Text (#0F172A):** Deep slate ensures AAA accessibility and high legibility for dense tabular data.
- **Status Colors:** Success (#10B981), Warning (#F59E0B), and Destructive (#EF4444) should be used sparingly as small indicators or text labels, never as large surface fills.

## Typography
**Inter** is the sole typeface, chosen for its exceptional legibility in UI and numerical data. For Chinese characters, the system defaults to standard system sans-serif fallbacks (PingFang SC, Microsoft YaHei) to maintain native rendering performance.

- **Data Density:** Use `body-sm` (13px) for primary table content and sidebars to maximize information per screen.
- **Numerical Data:** For financial figures or IDs, use a monospaced variant of Inter or the system monospace fallback to ensure tabular alignment.
- **Hierarchy:** Use font weight rather than size to establish hierarchy in dense views. Reserved Bold (700) for page titles and Semibold (600) for section headers.

## Layout & Spacing
The layout follows a **Strict Grid** model based on a 4px baseline.

- **Desktop:** 12-column grid with a fixed maximum width of 1440px for content containers.
- **Information Density:** Use compact vertical padding (8px - 12px) for table rows and list items.
- **Alignment:** All elements must align to the 4px grid. Use 16px (md) for standard component spacing and 24px (lg) for section separation.
- **Mobile:** Reflow to a single column with 16px side margins. Hide non-essential secondary data columns in tables, replacing them with expandable rows.

## Elevation & Depth
This design system avoids traditional shadows to maintain a flat, professional "architectural" feel. 

- **Tonal Layering:** Depth is communicated through color, not shadows. Use the background (#F8FAFC) as the base and White (#FFFFFF) for the interactive "Surface" layer.
- **Outlines:** Use 1px solid borders (#E2E8F0) to define all boundaries. 
- **Active State:** On hover or focus, borders should darken to #CBD5E1 or change to the primary color (#2563EB).
- **Modals:** Use a subtle, large-radius neutral shadow (0px 10px 15px -3px rgba(0,0,0,0.05)) only when an element must physically float over the UI to maintain context.

## Shapes
Geometry is disciplined and consistent. An **8px (0.5rem) border radius** is the standard for almost all UI components including buttons, input fields, and cards.

- **Containers:** Large page sections or cards use the standard 8px radius.
- **Inner Elements:** Small tags or status dots may use a 4px radius to feel nested correctly within larger containers.
- **Icons:** Use 20px or 24px bounding boxes with a 2px stroke weight to match the clean, professional aesthetic of the typography.

## Components
- **Buttons:** Primary buttons are solid #2563EB with white text. Secondary buttons use a white fill with a #E2E8F0 border and #0F172A text. No gradients.
- **Data Tables:** The core of the product. Use 1px horizontal borders only. Header cells should have a subtle #F1F5F9 background and `label-md` typography.
- **Input Fields:** 1px #E2E8F0 border, 8px radius. On focus, the border transitions to #2563EB with a 0px 0px 0px 2px soft blue ring.
- **Cards:** White background, 1px solid #E2E8F0 border, 8px radius. No shadow. Use 24px internal padding for standard cards, 16px for data-heavy cards.
- **Status Badges:** Small, subtle fills with high-contrast text. For example, a "Success" badge uses a #DCFCE7 background with #166534 text.
- **Navigation:** Vertical sidebar using a condensed width (240px) with icons and `body-md` text. Active states indicated by a 2px primary color vertical bar on the left edge.