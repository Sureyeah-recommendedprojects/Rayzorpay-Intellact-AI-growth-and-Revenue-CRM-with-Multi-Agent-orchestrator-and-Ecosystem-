// ============================================================
// API Route: /api/agent-x
// Natural language → pipeline spec via Venice.ai / Gemini.
// ============================================================

import { NextRequest, NextResponse } from "next/server";
import { clampTimeout } from "@/lib/server-timeout";
import { AGENT_REGISTRY } from "@/data/agent-registry";

export const maxDuration = 30;

const AGENT_IDS = AGENT_REGISTRY.map((a) => a.id);

const SYSTEM_PROMPT = `You are RayzorFlow's payment-operations pipeline builder. Given a user request, return ONLY a valid JSON object with this shape:
{
  "nodes": [
    { "agentId": "payment-health-agent", "position": { "x": 100, "y": 200 } }
  ],
  "edges": [
    { "source": "payment-health-agent", "target": "payment-link-agent" }
  ]
}
Only use agentIds from this list: ${JSON.stringify(AGENT_IDS)}.
Place nodes in a left-to-right layout. x increases by 280 per step. y=200 for linear pipes, stagger y for parallel branches.
Return ONLY the JSON object. No markdown, no explanation, no code fences.`;

export async function POST(request: NextRequest) {
  try {
    const { prompt } = (await request.json()) as { prompt: string };
    if (!prompt?.trim()) {
      return NextResponse.json({ success: false, error: "Empty prompt." }, { status: 400 });
    }

    const veniceKey = process.env.VENICE_API_KEY;
    const geminiKey = process.env.GEMINI_API_KEY;

    if (!veniceKey && !geminiKey) {
      return NextResponse.json({
        success: false,
        error: "Agent X requires VENICE_API_KEY or GEMINI_API_KEY. Add one in .env.local.",
      }, { status: 503 });
    }

    const messages = [
      { role: "system" as const, content: SYSTEM_PROMPT },
      { role: "user" as const, content: prompt },
    ];

    let rawResponse = "";

    // Venice primary
    if (veniceKey) {
      try {
        const veniceBase = process.env.VENICE_BASE_URL || "https://api.venice.ai/api/v1";
        const res = await fetch(`${veniceBase}/chat/completions`, {
          method: "POST",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${veniceKey}` },
          body: JSON.stringify({
            model: "llama-3.3-70b",
            messages,
            max_tokens: 1024,
            temperature: 0.1,
          }),
          signal: AbortSignal.timeout(clampTimeout(25000)),
        });
        if (res.ok) {
          const data = await res.json() as { choices?: { message?: { content?: string } }[] };
          rawResponse = data.choices?.[0]?.message?.content ?? "";
        }
      } catch {
        // Fall through to Gemini
      }
    }

    // Gemini fallback
    if (!rawResponse && geminiKey) {
      const res = await fetch("https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${geminiKey}` },
        body: JSON.stringify({
          model: "gemini-2.0-flash",
          messages,
          max_tokens: 1024,
        }),
        signal: AbortSignal.timeout(clampTimeout(25000)),
      });
      if (!res.ok) {
        const text = await res.text();
        return NextResponse.json({ success: false, error: `Gemini API error ${res.status}: ${text.slice(0, 200)}` }, { status: 502 });
      }
      const data = await res.json() as { choices?: { message?: { content?: string } }[] };
      rawResponse = data.choices?.[0]?.message?.content ?? "";
    }

    if (!rawResponse) {
      return NextResponse.json({ success: false, error: "No response from AI. Check your API keys." }, { status: 502 });
    }

    // Parse
    const parsed = parseResponse(rawResponse);
    if (!parsed) {
      return NextResponse.json({ success: false, error: "Could not parse AI response into a valid pipeline." }, { status: 422 });
    }

    return NextResponse.json({ success: true, ...parsed });
  } catch (error) {
    const msg = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ success: false, error: msg }, { status: 500 });
  }
}

function parseResponse(raw: string): { nodes: unknown[]; edges: unknown[] } | null {
  try {
    let cleaned = raw.trim();
    if (cleaned.startsWith("```")) {
      cleaned = cleaned.replace(/^```(?:json)?\s*/, "").replace(/\s*```$/, "");
    }
    const parsed = JSON.parse(cleaned) as { nodes?: unknown[]; edges?: unknown[] };
    if (!Array.isArray(parsed.nodes) || !Array.isArray(parsed.edges)) return null;

    const validNodes = (parsed.nodes as Array<{ agentId: string }>).filter((n) =>
      AGENT_IDS.includes(n.agentId)
    );
    if (validNodes.length === 0) return null;

    const validNodeIds = new Set(validNodes.map((n) => n.agentId));
    const validEdges = (parsed.edges as Array<{ source: string; target: string }>).filter(
      (e) => validNodeIds.has(e.source) && validNodeIds.has(e.target)
    );

    return { nodes: validNodes, edges: validEdges };
  } catch {
    return null;
  }
}
