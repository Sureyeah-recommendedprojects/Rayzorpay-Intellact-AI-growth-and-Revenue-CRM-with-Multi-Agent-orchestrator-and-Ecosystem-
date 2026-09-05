"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";

/* ═══════════════════════════════════════════════════════════════
   NAVBAR
   ═══════════════════════════════════════════════════════════════ */
function Navbar() {
  return (
    <nav
      id="navbar"
      style={{
        position: "sticky",
        top: 0,
        zIndex: 50,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "16px 40px",
        background: "rgba(15,15,20,0.85)",
        backdropFilter: "blur(16px)",
        borderBottom: "1px solid var(--border-subtle)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        <Image src="/images/logo.png" alt="RayzorFlow Logo" width={32} height={32} style={{ borderRadius: 8 }} />
        <span className="font-heading" style={{ fontSize: 20, color: "var(--text-primary)", letterSpacing: "0.5px" }}>
          RayzorFlow
        </span>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "32px" }}>
        {["Features", "Pricing", "Insights"].map((item) => (
          <a
            key={item}
            href={`#${item.toLowerCase()}`}
            style={{
              color: "var(--text-muted)",
              fontSize: 14,
              textDecoration: "none",
              transition: "color 0.2s",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
          >
            {item}
          </a>
        ))}
        <a
          href="https://github.com"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            color: "var(--text-muted)",
            fontSize: 14,
            textDecoration: "none",
            transition: "color 0.2s",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
          onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
        >
          GitHub
        </a>
        <Link href="/app" className="btn-primary" style={{ padding: "10px 24px", fontSize: 13 }}>
          Launch App
        </Link>
      </div>
    </nav>
  );
}

/* ═══════════════════════════════════════════════════════════════
   HERO
   ═══════════════════════════════════════════════════════════════ */
function Hero() {
  return (
    <section
      id="hero"
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 48,
        maxWidth: 1200,
        margin: "0 auto",
        padding: "80px 40px 60px",
        minHeight: "85vh",
      }}
    >
      {/* Left content */}
      <div className="animate-fade-in" style={{ maxWidth: 560, flex: 1 }}>
        <h1
          className="font-heading"
          style={{
            fontSize: 52,
            lineHeight: 1.15,
            color: "var(--text-primary)",
            marginBottom: 20,
          }}
        >
          Your Multi-Agent{" "}
          <span className="text-accent" style={{ display: "block" }}>
            Orchestrator
          </span>
        </h1>
        <p
          style={{
            fontSize: 16,
            lineHeight: 1.7,
            color: "var(--text-secondary)",
            marginBottom: 36,
            maxWidth: 460,
          }}
        >
          Orchestrate commerce work without replacing your core systems. Drag, wire, and govern specialist agents across payments, recovery, customer operations, and intelligence.
        </p>
        <div style={{ display: "flex", gap: 12 }}>
          <Link href="/app" className="btn-primary">
            Get Started
          </Link>
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-outline"
          >
            View Templates
          </a>
        </div>
      </div>

      {/* Right hero image */}
      <div className="animate-fade-in-delay-2" style={{ flex: 1, display: "flex", justifyContent: "flex-end" }}>
        <div
          style={{
            width: 480,
            height: 480,
            borderRadius: "var(--radius-xl)",
            overflow: "hidden",
            position: "relative",
          }}
        >
          <Image
            src="/images/hero-render.png"
            alt="Abstract 3D orchestration visualization"
            fill
            style={{ objectFit: "cover" }}
            priority
          />
        </div>
      </div>
    </section>
  );
}

/* ═══════════════════════════════════════════════════════════════
   LOGO STRIP
   ═══════════════════════════════════════════════════════════════ */
const PROTOCOLS = ["Razorpay", "Intellact", "WhatsApp", "Shopify", "HubSpot", "Venice.ai", "Twilio", "Slack"];

function LogoStrip() {
  return (
    <section
      style={{
        padding: "32px 0",
        borderTop: "1px solid var(--border-subtle)",
        borderBottom: "1px solid var(--border-subtle)",
        overflow: "hidden",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 56, flexWrap: "wrap", padding: "0 40px" }}>
        {PROTOCOLS.map((name) => (
          <span
            key={name}
            style={{
              fontSize: 15,
              fontWeight: 600,
              color: "var(--text-muted)",
              letterSpacing: "0.5px",
              opacity: 0.6,
              transition: "opacity 0.2s",
              cursor: "default",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.opacity = "1")}
            onMouseLeave={(e) => (e.currentTarget.style.opacity = "0.6")}
          >
            ◆ {name}
          </span>
        ))}
      </div>
    </section>
  );
}

/* ═══════════════════════════════════════════════════════════════
   FEATURES — "Unleash Your Pipelines"
   ═══════════════════════════════════════════════════════════════ */
const FEATURE_STEPS = [
  {
    title: "Upload Brief",
    body: "Define your pipeline requirements. Describe what protocols you need and our AI grasps your vision.",
    icon: (
      <svg viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" /></svg>
    ),
  },
  {
    title: "Generate Designs",
    body: "Watch our AI compose optimal agent configurations, selecting the best protocols tailored to your workflow.",
    icon: (
      <svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2" ry="2" /><line x1="3" y1="9" x2="21" y2="9" /><line x1="9" y1="21" x2="9" y2="9" /></svg>
    ),
  },
  {
    title: "Refine Creation",
    body: "Perfect your pipeline with visual editing. Drag, wire, and configure 48 agents until you achieve flow perfection.",
    icon: (
      <svg viewBox="0 0 24 24"><path d="M12 20h9" /><path d="M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z" /></svg>
    ),
  },
];

function Features() {
  return (
    <section id="features" className="section" style={{ textAlign: "center" }}>
      <h2
        className="font-heading"
        style={{
          fontSize: 42,
          color: "var(--text-primary)",
          marginBottom: 16,
        }}
      >
        Unleash Your <span className="text-accent">Pipelines</span>
      </h2>
      <p
        style={{
          fontSize: 15,
          color: "var(--text-secondary)",
          maxWidth: 560,
          margin: "0 auto 56px",
          lineHeight: 1.7,
        }}
      >
        Discover how our AI-Powered Agent Orchestrator transforms your ideas into running pipelines effortlessly. Follow these simple steps to turn your vision into reality.
      </p>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: 24,
          maxWidth: 960,
          margin: "0 auto",
        }}
      >
        {FEATURE_STEPS.map((step) => (
          <div
            key={step.title}
            className="card"
            style={{ padding: "40px 28px", textAlign: "center" }}
          >
            <div
              className="icon-badge"
              style={{ margin: "0 auto 20px" }}
            >
              {step.icon}
            </div>
            <h3 style={{ fontSize: 18, fontWeight: 600, color: "var(--text-primary)", marginBottom: 10 }}>
              {step.title}
            </h3>
            <p style={{ fontSize: 14, color: "var(--text-secondary)", lineHeight: 1.6 }}>
              {step.body}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}

/* ═══════════════════════════════════════════════════════════════
   PRICING — "Affordable Plans for Every Need"
   ═══════════════════════════════════════════════════════════════ */
const PLANS = [
  {
    tier: "FREE",
    price: "$0",
    period: "/m",
    name: "Free Forever",
    features: [
      "Basic AI-generated designs",
      "Access to standard templates",
      "Standard template library",
      "5 exports per month",
    ],
    highlighted: false,
    cta: "Get Started",
  },
  {
    tier: "PRO",
    price: "$14.99",
    period: "/m",
    name: "Most Popular",
    features: [
      "Advanced AI-generated designs",
      "Full access to premium tools",
      "Premium template library",
      "Unlimited exports",
      "Real-time collaboration",
      "Priority email support",
    ],
    highlighted: true,
    cta: "Get Started",
  },
  {
    tier: "PRO",
    price: "$29.99",
    period: "/m",
    name: "Billed Monthly",
    features: [
      "All features included in Pro Plan",
      "Dedicated account manager",
      "Custom AI-tailored designs",
      "Onboarding and training sessions",
      "24/7 Priority support",
      "Advanced analytics & reporting",
      "Secure cloud storage",
    ],
    highlighted: false,
    cta: "Get Started",
  },
];

function Pricing() {
  const [isYearly, setIsYearly] = useState(false);

  return (
    <section id="pricing" className="section" style={{ textAlign: "center" }}>
      <h2
        className="font-heading"
        style={{
          fontSize: 42,
          color: "var(--text-primary)",
          marginBottom: 16,
        }}
      >
        Affordable Plans for{" "}
        <span className="text-accent" style={{ display: "block" }}>
          Every Need
        </span>
      </h2>
      <p
        style={{
          fontSize: 15,
          color: "var(--text-secondary)",
          maxWidth: 560,
          margin: "0 auto 32px",
          lineHeight: 1.7,
        }}
      >
        Choose the perfect plan for your agent projects, from startups to enterprises. Our pricing tiers are designed to offer flexibility and value.
      </p>

      {/* Toggle */}
      <div style={{ display: "flex", justifyContent: "center", marginBottom: 48 }}>
        <div className="toggle-switch">
          <button
            className={`toggle-option ${!isYearly ? "active" : ""}`}
            onClick={() => setIsYearly(false)}
          >
            Monthly
          </button>
          <button
            className={`toggle-option ${isYearly ? "active" : ""}`}
            onClick={() => setIsYearly(true)}
          >
            Yearly
          </button>
        </div>
      </div>

      {/* Cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: 24,
          maxWidth: 1000,
          margin: "0 auto",
          alignItems: "stretch",
        }}
      >
        {PLANS.map((plan, i) => (
          <div
            key={i}
            className={plan.highlighted ? "card-highlighted" : "card"}
            style={{
              padding: "36px 28px",
              textAlign: "left",
              display: "flex",
              flexDirection: "column",
            }}
          >
            <span
              style={{
                fontSize: 11,
                letterSpacing: "2px",
                color: plan.highlighted ? "rgba(255,255,255,0.7)" : "var(--text-muted)",
                marginBottom: 16,
                textTransform: "uppercase",
              }}
            >
              {plan.tier}
            </span>
            <div style={{ display: "flex", alignItems: "baseline", gap: 4, marginBottom: 4 }}>
              <span
                style={{
                  fontSize: 42,
                  fontWeight: 700,
                  color: plan.highlighted ? "#fff" : "var(--text-primary)",
                  fontFamily: "var(--font-body), sans-serif",
                }}
              >
                {plan.price}
              </span>
              <span
                style={{
                  fontSize: 16,
                  color: plan.highlighted ? "rgba(255,255,255,0.6)" : "var(--text-muted)",
                }}
              >
                {plan.period}
              </span>
            </div>
            <p
              style={{
                fontSize: 13,
                color: plan.highlighted ? "rgba(255,255,255,0.6)" : "var(--text-muted)",
                marginBottom: 24,
              }}
            >
              {plan.name}
            </p>

            <hr
              style={{
                border: "none",
                borderTop: `1px solid ${plan.highlighted ? "rgba(255,255,255,0.2)" : "var(--border-subtle)"}`,
                marginBottom: 20,
              }}
            />

            <ul
              style={{
                listStyle: "none",
                padding: 0,
                margin: 0,
                flex: 1,
              }}
            >
              {plan.features.map((feature) => (
                <li
                  key={feature}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    fontSize: 13,
                    color: plan.highlighted ? "rgba(255,255,255,0.85)" : "var(--text-secondary)",
                    marginBottom: 12,
                    lineHeight: 1.5,
                  }}
                >
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke={plan.highlighted ? "#fff" : "var(--purple-primary)"}
                    strokeWidth="2"
                    strokeLinecap="round"
                  >
                    <circle cx="12" cy="12" r="10" />
                    <path d="M9 12l2 2 4-4" />
                  </svg>
                  {feature}
                </li>
              ))}
            </ul>

            <button
              style={{
                marginTop: 24,
                width: "100%",
                padding: "12px 0",
                borderRadius: "var(--radius-full)",
                fontSize: 14,
                fontWeight: 500,
                cursor: "pointer",
                transition: "all 0.2s",
                border: plan.highlighted ? "1px solid rgba(255,255,255,0.3)" : "1px solid var(--border-subtle)",
                background: plan.highlighted ? "rgba(255,255,255,0.15)" : "transparent",
                color: plan.highlighted ? "#fff" : "var(--text-secondary)",
                fontFamily: "var(--font-body), sans-serif",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = plan.highlighted ? "#fff" : "var(--purple-primary)";
                e.currentTarget.style.color = plan.highlighted ? "#fff" : "var(--text-primary)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = plan.highlighted
                  ? "rgba(255,255,255,0.3)"
                  : "var(--border-subtle)";
                e.currentTarget.style.color = plan.highlighted ? "#fff" : "var(--text-secondary)";
              }}
            >
              {plan.cta}
            </button>
          </div>
        ))}
      </div>
    </section>
  );
}

/* ═══════════════════════════════════════════════════════════════
   INSIGHTS
   ═══════════════════════════════════════════════════════════════ */
const ARTICLES = [
  {
    img: "/images/blog-1.png",
    date: "Apr 8, 2025",
    readTime: "4 min read",
    title: "Building Payment Recovery Flows with Agents",
  },
  {
    img: "/images/blog-2.png",
    date: "Mar 15, 2025",
    readTime: "5 min read",
    title: "How Parallel Execution Changes Agent Orchestration",
  },
  {
    img: "/images/blog-3.png",
    date: "Feb 28, 2025",
    readTime: "7 min read",
    title: "Why Governed Commerce Agents Outperform the Rest",
  },
];

function Insights() {
  return (
    <section id="insights" className="section" style={{ textAlign: "center" }}>
      <h2
        className="font-heading"
        style={{
          fontSize: 42,
          color: "var(--text-primary)",
          marginBottom: 16,
        }}
      >
        Stay Inspired with Our<br />
        Latest <span className="text-accent">Insights</span>
      </h2>
      <p
        style={{
          fontSize: 15,
          color: "var(--text-secondary)",
          maxWidth: 560,
          margin: "0 auto 48px",
          lineHeight: 1.7,
        }}
      >
        Dive into our latest patterns for agent orchestration, payment operations, and durable customer experiences.
      </p>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: 24,
          maxWidth: 960,
          margin: "0 auto 40px",
        }}
      >
        {ARTICLES.map((article) => (
          <div
            key={article.title}
            className="card"
            style={{ overflow: "hidden", textAlign: "left", cursor: "pointer" }}
          >
            <div style={{ position: "relative", width: "100%", height: 200 }}>
              <Image
                src={article.img}
                alt={article.title}
                fill
                style={{ objectFit: "cover" }}
              />
            </div>
            <div style={{ padding: "20px 20px 24px" }}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  fontSize: 12,
                  color: "var(--text-muted)",
                  marginBottom: 10,
                }}
              >
                <span>{article.date}</span>
                <span>{article.readTime}</span>
              </div>
              <h3 style={{ fontSize: 16, fontWeight: 600, color: "var(--text-primary)", lineHeight: 1.4, margin: 0 }}>
                {article.title}
              </h3>
            </div>
          </div>
        ))}
      </div>

      <a href="#" className="btn-primary" style={{ fontSize: 13, padding: "10px 28px" }}>
        Read More
      </a>
    </section>
  );
}

/* ═══════════════════════════════════════════════════════════════
   CTA — "Start Your Agent Journey Today"
   ═══════════════════════════════════════════════════════════════ */
function CTA() {
  return (
    <section
      style={{
        background: "var(--bg-surface)",
        borderTop: "1px solid var(--border-subtle)",
      }}
    >
      <div
        style={{
          maxWidth: 1200,
          margin: "0 auto",
          padding: "80px 40px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 48,
        }}
      >
        <div style={{ flex: 1, maxWidth: 520 }}>
          <h2
            className="font-heading"
            style={{ fontSize: 42, color: "var(--text-primary)", marginBottom: 16 }}
          >
            Start Your Agent<br />
            <span className="text-accent">Journey</span> Today
          </h2>
          <p
            style={{
              fontSize: 15,
              lineHeight: 1.7,
              color: "var(--text-secondary)",
              marginBottom: 32,
              maxWidth: 420,
            }}
          >
            Sign up now and experience the power of AI-driven agent orchestration without any commitment.
          </p>
          <Link href="/app" className="btn-primary">
            Get Started
          </Link>
        </div>
        <div style={{ flex: 1, display: "flex", justifyContent: "flex-end" }}>
          <div
            style={{
              width: 400,
              height: 300,
              borderRadius: "var(--radius-xl)",
              overflow: "hidden",
              position: "relative",
            }}
          >
            <Image
              src="/images/cta-render.png"
              alt="Abstract 3D visualization"
              fill
              style={{ objectFit: "cover" }}
            />
          </div>
        </div>
      </div>
    </section>
  );
}

/* ═══════════════════════════════════════════════════════════════
   FOOTER
   ═══════════════════════════════════════════════════════════════ */
function Footer() {
  return (
    <footer
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "20px 40px",
        borderTop: "1px solid var(--border-subtle)",
        fontSize: 13,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <Image src="/images/logo.png" alt="RayzorFlow Logo" width={24} height={24} style={{ borderRadius: 4 }} />
        <span className="font-heading" style={{ color: "var(--text-primary)", fontSize: 16 }}>
          RayzorFlow
        </span>
      </div>
      <div style={{ display: "flex", gap: 24 }}>
        {["MIT License", "Browse Agents", "GitHub", "Contribute"].map((link) => (
          <a
            key={link}
            href="#"
            style={{ color: "var(--text-muted)", textDecoration: "none", transition: "color 0.2s" }}
            onMouseEnter={(e) => (e.currentTarget.style.color = "var(--purple-primary)")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
          >
            {link}
          </a>
        ))}
      </div>
      <span style={{ color: "var(--text-muted)", fontSize: 12 }}>
        Built for commerce operations
      </span>
    </footer>
  );
}

/* ═══════════════════════════════════════════════════════════════
   PAGE
   ═══════════════════════════════════════════════════════════════ */
export default function HomePage() {
  return (
    <div style={{ background: "var(--bg-base)", minHeight: "100vh" }}>
      <Navbar />
      <Hero />
      <LogoStrip />
      <Features />
      <hr className="section-divider" />
      <Pricing />
      <hr className="section-divider" />
      <Insights />
      <CTA />
      <Footer />
    </div>
  );
}
