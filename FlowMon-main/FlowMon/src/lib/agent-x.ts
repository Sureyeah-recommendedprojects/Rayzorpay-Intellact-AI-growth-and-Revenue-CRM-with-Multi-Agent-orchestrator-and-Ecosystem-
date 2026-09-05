// ============================================================
// RayzorFlow — Agent X NL Intent Parser
// Venice.ai (primary) + Gemini (fallback) for NL → pipeline.
// ============================================================

import { AGENT_REGISTRY } from "@/data/agent-registry";

const AGENT_IDS = AGENT_REGISTRY.map((a) => a.id);

export function buildAgentXSystemPrompt(): string {
  return `You are RayzorFlow's payment-operations pipeline builder. Given a user request, return ONLY a valid JSON object with this shape:
{
  "nodes": [
    { "agentId": "payment-health-agent", "position": { "x": 100, "y": 200 } }
  ],
  "edges": [
    { "source": "payment-health-agent", "target": "payment-link-agent" }
  ]
}
Only use agentIds from this list: ${JSON.stringify(AGENT_IDS)}.
Place nodes in a left-to-right layout. x increases by 280 per step. y should be around 200 for single paths, stagger vertically for parallel branches.
Return nothing except the JSON object. No markdown, no explanation, no code fences.`;
}

export interface AgentXParsedPipeline {
  nodes: Array<{ agentId: string; position: { x: number; y: number } }>;
  edges: Array<{ source: string; target: string }>;
}

export function parseAgentXResponse(raw: string): AgentXParsedPipeline | null {
  try {
    // Strip markdown fences if present
    let cleaned = raw.trim();
    if (cleaned.startsWith("```")) {
      cleaned = cleaned.replace(/^```(?:json)?\s*/, "").replace(/\s*```$/, "");
    }
    const parsed = JSON.parse(cleaned) as AgentXParsedPipeline;

    if (!Array.isArray(parsed.nodes) || !Array.isArray(parsed.edges)) {
      return null;
    }

    // Validate agent IDs
    const validNodes = parsed.nodes.filter((n) =>
      AGENT_IDS.includes(n.agentId)
    );

    if (validNodes.length === 0) return null;

    const validNodeIds = new Set(validNodes.map((n) => n.agentId));
    const validEdges = parsed.edges.filter(
      (e) => validNodeIds.has(e.source) && validNodeIds.has(e.target)
    );

    return { nodes: validNodes, edges: validEdges };
  } catch {
    return null;
  }
}
