// ============================================================
// RayzorFlow — Negotiate API Route
// AI-powered inter-agent parameter negotiation via Venice.ai
// ============================================================

import { NextRequest, NextResponse } from "next/server";
import { clampTimeout } from "@/lib/server-timeout";

const NEGOTIATE_TIMEOUT = clampTimeout(30000);

async function handleNegotiate(req: NextRequest) {
  const body = await req.json();
  const {
    initiatorAgentId,
    initiatorAgentName,
    receiverAgentId,
    receiverAgentName,
    initiatorParams,
    receiverParams,
    negotiationGoal,
  } = body;

  const apiKey = process.env.VENICE_API_KEY;
  if (!apiKey) {
    // Fallback: generate a deterministic negotiation without LLM
    return NextResponse.json({
      agreed: true,
      confidence: 0.85,
      summary: `Parameter alignment between ${initiatorAgentName} and ${receiverAgentName}: outputs from ${initiatorAgentName} will be mapped to ${receiverAgentName}'s input parameters automatically via AMP protocol.`,
      agentAMessage: `I'll provide my outputs in a structured format. Key fields: ${Object.keys(initiatorParams || {}).join(", ")}.`,
      agentBMessage: `Acknowledged. I can accept inputs for: ${Object.keys(receiverParams || {}).join(", ")}. Let's align on data format.`,
      suggestedMapping: Object.keys(receiverParams || {}).reduce((acc: Record<string, string>, key: string) => {
        acc[key] = key;
        return acc;
      }, {}),
    });
  }

  try {
    const systemPrompt = `You are an AI mediator for agent parameter negotiation in RayzorFlow, a payment-operations orchestrator.

Two agents need to align their parameters for optimal data handoff in a pipeline:

INITIATOR: ${initiatorAgentName} (${initiatorAgentId})
Parameters: ${JSON.stringify(initiatorParams)}

RECEIVER: ${receiverAgentName} (${receiverAgentId})
Parameters: ${JSON.stringify(receiverParams)}

GOAL: ${negotiationGoal}

Respond with a JSON object:
{
  "agreed": true/false,
  "confidence": 0.0-1.0,
  "summary": "Brief description of the agreement",
  "agentAMessage": "What the initiator agent says",
  "agentBMessage": "What the receiver agent responds",
  "suggestedMapping": { "receiverParam": "initiatorOutputField" }
}`;

    const response = await fetch("https://api.venice.ai/api/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: "llama-3.3-70b",
        messages: [
          { role: "system", content: systemPrompt },
          { role: "user", content: `Negotiate parameter alignment between these two agents. Produce actionable mapping.` },
        ],
        max_tokens: 512,
        temperature: 0.3,
      }),
    });

    if (!response.ok) {
      throw new Error(`Venice API error: ${response.status}`);
    }

    const data = await response.json();
    const content = data.choices?.[0]?.message?.content ?? "";

    // Try to parse JSON from the response
    const jsonMatch = content.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      const result = JSON.parse(jsonMatch[0]);
      return NextResponse.json(result);
    }

    // Fallback if Venice doesn't return proper JSON
    return NextResponse.json({
      agreed: true,
      confidence: 0.7,
      summary: content.slice(0, 200),
      agentAMessage: `Proposing alignment based on my output schema.`,
      agentBMessage: `Accepted. Will map incoming data accordingly.`,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Negotiation failed";
    return NextResponse.json({
      agreed: false,
      confidence: 0,
      summary: `Negotiation error: ${message}`,
      agentAMessage: "Unable to complete negotiation.",
      agentBMessage: "Negotiation not reached.",
    });
  }
}

export async function POST(req: NextRequest) {
  return handleNegotiate(req);
}
