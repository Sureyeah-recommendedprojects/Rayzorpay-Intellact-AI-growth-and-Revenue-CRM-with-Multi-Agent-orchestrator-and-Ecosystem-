import type { CSSProperties } from "react";

import type { LandingAccent, LandingFont, LandingTheme } from "./types";

/**
 * Public landing pages are conversion-optimized with their OWN per-template
 * styling, isolated from the dashboard chrome. The theme resolves to CSS
 * custom properties on the page root; section components reference them via
 * Tailwind arbitrary values so a page is fully self-contained.
 *
 * PURE + client-safe.
 */

interface AccentPalette {
  accent: string;
  accentHover: string;
  accentFg: string;
  soft: string;
  softFg: string;
}

/** WCAG-AA-minded accent palettes (accentFg contrasts on accent). */
export const LANDING_ACCENT_PALETTES: Record<LandingAccent, AccentPalette> = {
  violet: { accent: "#7c3aed", accentHover: "#6d28d9", accentFg: "#ffffff", soft: "#f5f3ff", softFg: "#5b21b6" },
  orange: { accent: "#ea580c", accentHover: "#c2410c", accentFg: "#ffffff", soft: "#fff7ed", softFg: "#9a3412" },
  emerald: { accent: "#059669", accentHover: "#047857", accentFg: "#ffffff", soft: "#ecfdf5", softFg: "#065f46" },
  blue: { accent: "#2563eb", accentHover: "#1d4ed8", accentFg: "#ffffff", soft: "#eff6ff", softFg: "#1e40af" },
  amber: { accent: "#d97706", accentHover: "#b45309", accentFg: "#ffffff", soft: "#fffbeb", softFg: "#92400e" },
  rose: { accent: "#e11d48", accentHover: "#be123c", accentFg: "#ffffff", soft: "#fff1f2", softFg: "#9f1239" },
  teal: { accent: "#0d9488", accentHover: "#0f766e", accentFg: "#ffffff", soft: "#f0fdfa", softFg: "#115e59" },
};

export const LANDING_FONT_LABELS: Record<LandingFont, string> = {
  syne: "Syne",
  outfit: "Outfit",
  jakarta: "Plus Jakarta",
  sora: "Sora",
  dm_sans: "DM Sans",
  geist: "Geist",
  grotesk: "Space Grotesk",
  serif: "Editorial serif",
};

const RADIUS_PX: Record<LandingTheme["radius"], string> = { sm: "8px", md: "12px", lg: "16px", xl: "22px" };

interface FontPair {
  display: string;
  body: string;
}

const FONT_PAIRS: Record<LandingFont, FontPair> = {
  syne: {
    display: "var(--font-syne), ui-sans-serif, system-ui, sans-serif",
    body: "var(--font-outfit), ui-sans-serif, system-ui, sans-serif",
  },
  outfit: {
    display: "var(--font-outfit), ui-sans-serif, system-ui, sans-serif",
    body: "var(--font-outfit), ui-sans-serif, system-ui, sans-serif",
  },
  jakarta: {
    display: "var(--font-jakarta), ui-sans-serif, system-ui, sans-serif",
    body: "var(--font-jakarta), ui-sans-serif, system-ui, sans-serif",
  },
  sora: {
    display: "var(--font-sora), ui-sans-serif, system-ui, sans-serif",
    body: "var(--font-outfit), ui-sans-serif, system-ui, sans-serif",
  },
  dm_sans: {
    display: "var(--font-dm-sans), ui-sans-serif, system-ui, sans-serif",
    body: "var(--font-dm-sans), ui-sans-serif, system-ui, sans-serif",
  },
  geist: {
    display: "var(--font-geist-sans), ui-sans-serif, system-ui, sans-serif",
    body: "var(--font-geist-sans), ui-sans-serif, system-ui, sans-serif",
  },
  grotesk: {
    display: "var(--font-sora), ui-sans-serif, system-ui, sans-serif",
    body: "var(--font-outfit), ui-sans-serif, system-ui, sans-serif",
  },
  serif: {
    display: "ui-serif, Georgia, 'Times New Roman', serif",
    body: "var(--font-outfit), ui-sans-serif, system-ui, sans-serif",
  },
};

interface SurfacePalette {
  bg: string;
  fg: string;
  muted: string;
  card: string;
  cardFg: string;
  border: string;
  subtle: string;
}

const LIGHT_SURFACE: SurfacePalette = {
  bg: "#fbf8ff",
  fg: "#1c1430",
  muted: "#5b5270",
  card: "#ffffff",
  cardFg: "#1c1430",
  border: "#e8dff5",
  subtle: "#f6f0ff",
};

const DARK_SURFACE: SurfacePalette = {
  bg: "#120c1c",
  fg: "#f6f1ff",
  muted: "#b8aec9",
  card: "#1c1428",
  cardFg: "#f6f1ff",
  border: "#3a2d4f",
  subtle: "#181022",
};

/** Resolves a theme to the CSS variable map applied on the landing page root. */
export function resolveThemeVars(theme: LandingTheme): CSSProperties {
  const accent = LANDING_ACCENT_PALETTES[theme.accent] ?? LANDING_ACCENT_PALETTES.violet;
  const fonts = FONT_PAIRS[theme.font] ?? FONT_PAIRS.syne;
  const surface = theme.mode === "dark" ? DARK_SURFACE : LIGHT_SURFACE;
  return {
    "--lp-accent": accent.accent,
    "--lp-accent-hover": accent.accentHover,
    "--lp-accent-fg": accent.accentFg,
    "--lp-soft": theme.mode === "dark" ? "rgba(255,255,255,0.06)" : accent.soft,
    "--lp-soft-fg": theme.mode === "dark" ? accent.accentFg : accent.softFg,
    "--lp-bg": surface.bg,
    "--lp-fg": surface.fg,
    "--lp-muted": surface.muted,
    "--lp-card": surface.card,
    "--lp-card-fg": surface.cardFg,
    "--lp-border": surface.border,
    "--lp-subtle": surface.subtle,
    "--lp-radius": RADIUS_PX[theme.radius] ?? RADIUS_PX.lg,
    "--lp-font": fonts.body,
    "--lp-display": fonts.display,
  } as CSSProperties;
}

/** Inline CSS-var string for the static HTML snapshot (no React). */
export function themeVarsToCss(theme: LandingTheme): string {
  const vars = resolveThemeVars(theme) as Record<string, string>;
  return Object.entries(vars)
    .map(([k, v]) => `${k}: ${v};`)
    .join(" ");
}
