import type { Metadata } from "next";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import { DM_Sans, JetBrains_Mono, Outfit, Plus_Jakarta_Sans, Sora, Syne } from "next/font/google";

import "./globals.css";
import { Providers } from "@/components/providers";

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
  display: "swap",
});

const syne = Syne({
  subsets: ["latin"],
  variable: "--font-syne",
  display: "swap",
});

const jakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-jakarta",
  display: "swap",
});

const sora = Sora({
  subsets: ["latin"],
  variable: "--font-sora",
  display: "swap",
});

const dmSans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-dm-sans",
  display: "swap",
});

const jetbrains = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Intellact",
    template: "%s · Intellact",
  },
  description:
    "Intellact is an AI-powered commerce CRM for Indian merchants. It unifies customer conversations, campaign deployment, payment intelligence, and revenue operations.",
  applicationName: "Intellact",
  openGraph: {
    images: ["/og.svg"],
  },
};

const fontVariables = [
  outfit.variable,
  syne.variable,
  jakarta.variable,
  sora.variable,
  dmSans.variable,
  jetbrains.variable,
  GeistSans.variable,
  GeistMono.variable,
].join(" ");

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning className={`${fontVariables} h-full`}>
      <body className="min-h-full bg-background font-sans text-foreground antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
