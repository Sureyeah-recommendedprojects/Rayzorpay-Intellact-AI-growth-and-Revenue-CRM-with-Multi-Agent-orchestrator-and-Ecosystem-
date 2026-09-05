// ============================================================
// API Route: /api/chat
//
// Natural-language interface to RayzorFlow.
// Users can send text commands to:
//   • Run a specific agent with payment-operation parameters
//   • Execute the current canvas pipeline ("run my flow")
//   • Ask about agent capabilities       ("what agents do you have?")
//   • Build payment workflows on the canvas
//
// The LLM parses intent → dispatches to the matching agent
// endpoint → returns the result in a chat-friendly format.
// ============================================================

import { NextRequest, NextResponse } from "next/server";
import { AGENT_REGISTRY } from "@/data/agent-registry";
import { clampTimeout } from "@/lib/server-timeout";

export const maxDuration = 60;

// ── Shared LLM caller (Venice → Gemini fallback) ────────────────────────────

async function chatLLM(messages: { role: string; content: string }[], maxTokens = 1024): Promise<{ text: string; model: string }> {
    const veniceKey = process.env.VENICE_API_KEY;
    const geminiKey = process.env.GEMINI_API_KEY;

    // Venice first
    if (veniceKey) {
        try {
            const res = await fetch(
                `${process.env.VENICE_BASE_URL || "https://api.venice.ai/api/v1"}/chat/completions`,
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json", Authorization: `Bearer ${veniceKey}` },
                    body: JSON.stringify({ model: "llama-3.3-70b", messages, max_tokens: maxTokens, temperature: 0.2 }),
                    signal: AbortSignal.timeout(clampTimeout(30000)),
                },
            );
            if (res.ok) {
                const d = await res.json() as { choices?: { message?: { content?: string } }[] };
                return { text: d.choices?.[0]?.message?.content ?? "", model: "Agent X" };
            }
        } catch { /* fall through */ }
    }

    // Gemini free fallback
    if (geminiKey) {
        const res = await fetch("https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${geminiKey}` },
            body: JSON.stringify({ model: "gemini-2.0-flash", messages, max_tokens: maxTokens }),
            signal: AbortSignal.timeout(clampTimeout(30000)),
        });
        if (res.ok) {
            const d = await res.json() as { choices?: { message?: { content?: string } }[] };
            return { text: d.choices?.[0]?.message?.content ?? "", model: "Agent X" };
        }
    }

    throw new Error("No LLM configured — add GEMINI_API_KEY or VENICE_API_KEY");
}

// ── Build the agent catalogue for the system prompt ──────────────────────────

function buildAgentCatalogue(): string {
    return AGENT_REGISTRY.map((a) => {
        const params = a.parameters.map((p) => `${p.name}(${p.type}${p.required ? ",required" : ""}): ${p.description}`).join("; ");
        return `• ${a.id} [${a.category}/${a.sponsor}]: ${a.description}${params ? ` | Params: ${params}` : ""}`;
    }).join("\n");
}

const SYSTEM_PROMPT = `You are Agent X — the intelligent chat assistant for RayzorFlow, a Razorpay-focused payment-operations workflow builder.
You always refer to yourself as "Agent X". You help users interact with agents through natural language.

## Available Agents
${buildAgentCatalogue()}

## Your Capabilities
1. **Run an agent**: When the user wants to execute a payment-operation agent, respond with a JSON block to dispatch:
\`\`\`json
{"action":"run_agent","agentId":"<id>","params":{<paramKey>:<paramValue>}}
\`\`\`
2. **Run the pipeline**: When the user says "run flow", "execute pipeline", "start workflow", respond with:
\`\`\`json
{"action":"run_pipeline","globalParams":{<optional params>}}
\`\`\`
3. **Build a workflow on the canvas (REAL-TIME)**: When the user wants to create a payment, recovery, settlement, wallet, or payout workflow, respond with:
\`\`\`json
{"action":"build_flow","flowName":"<descriptive name>","agents":[{"id":"<agentId>"},{"id":"<agentId>"}],"connections":[[0,1],[1,2]]}
\`\`\`
Where \`agents\` lists agents from the catalogue (use exact IDs), and \`connections\` are [sourceIndex, targetIndex] pairs referencing indices in the agents array. Choose 2–8 agents that logically chain together. Briefly describe what the pipeline does before the JSON block.
4. **Add an agent to the canvas**: When the user wants to add a single agent to the existing canvas (e.g., "add a refund agent", "put a payout agent on the canvas"), respond with:
\`\`\`json
{"action":"add_agent","agentId":"<id>","connectFrom":"<existingAgentIdOnCanvas or omit>"}
\`\`\`
Include \`connectFrom\` with an agent ID if the user mentions connecting it to an existing agent.
5. **List agents**: When asked "what agents do you have?" or similar, give a concise categorized list.
6. **Explain**: When asked about a specific agent, explain its purpose, params, and sponsor.
7. **General questions**: Answer questions about payment operations and the available agents.

## Rules
- Always include the JSON block when dispatching an action. Put it in a fenced code block.
- Use the exact agent IDs from the catalogue.
- For INR amounts, extract numbers from the user's message.
- Never claim that a payment, refund, or payout has been sent; these agents prepare governed operations for merchant approval.
- Be concise but friendly. Use markdown formatting.
- When you run an agent, briefly explain what you're doing before the JSON block.
`;

// ── Parse LLM response for action JSON blocks ───────────────────────────────

interface ChatAction {
    action: string;
    agentId?: string;
    params?: Record<string, string>;
    globalParams?: Record<string, string>;
    // build_flow
    flowName?: string;
    agents?: { id: string; params?: Record<string, string> }[];
    connections?: [number, number][];
    // add_agent
    connectFrom?: string;
}

function extractAction(text: string): ChatAction | null {
    // Look for ```json ... ``` blocks
    const jsonBlockMatch = text.match(/```json\s*\n?([\s\S]*?)```/);
    if (jsonBlockMatch) {
        try {
            return JSON.parse(jsonBlockMatch[1].trim()) as ChatAction;
        } catch { /* not valid json */ }
    }
    // Also try to find raw JSON objects
    const rawJsonMatch = text.match(/\{[\s\S]*?"action"\s*:\s*"[^"]+[\s\S]*?\}/);
    if (rawJsonMatch) {
        try {
            return JSON.parse(rawJsonMatch[0]) as ChatAction;
        } catch { /* ignore */ }
    }
    return null;
}

// ── Execute an agent by calling its API ──────────────────────────────────────

async function executeAgent(agentId: string, params: Record<string, string>): Promise<Record<string, unknown>> {
    const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";
    const res = await fetch(`${baseUrl}/api/agents/${agentId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(params),
        signal: AbortSignal.timeout(clampTimeout(30000)),
    });
    if (!res.ok) {
        const text = await res.text();
        throw new Error(`Agent ${agentId} returned ${res.status}: ${text.slice(0, 200)}`);
    }
    return await res.json() as Record<string, unknown>;
}

// ── Main POST handler ────────────────────────────────────────────────────────

export async function POST(request: NextRequest) {
    const startTime = Date.now();
    try {
        const body = await request.json() as {
            message: string;
            conversationHistory?: { role: string; content: string }[];
        };

        const userMessage = body.message?.trim();
        if (!userMessage) {
            return NextResponse.json({ error: "Empty message" }, { status: 400 });
        }

        // Build conversation with history
        const messages: { role: string; content: string }[] = [
            { role: "system", content: SYSTEM_PROMPT },
            ...(body.conversationHistory ?? []).slice(-20), // keep last 20 messages for context
            { role: "user", content: userMessage },
        ];

        // Get LLM response
        const llmResult = await chatLLM(messages);
        let responseText = llmResult.text;

        // Check if the LLM wants to dispatch an action
        const action = extractAction(responseText);
        let agentResult: Record<string, unknown> | null = null;

        if (action?.action === "run_agent" && action.agentId) {
            try {
                agentResult = await executeAgent(action.agentId, action.params ?? {});
                // Append result summary to the response
                const resultJson = JSON.stringify(agentResult, null, 2);
                const truncatedResult = resultJson.length > 2000 ? resultJson.slice(0, 2000) + "\n..." : resultJson;
                responseText += `\n\n**Agent Result:**\n\`\`\`json\n${truncatedResult}\n\`\`\``;
            } catch (err) {
                const errMsg = err instanceof Error ? err.message : "Agent execution failed";
                responseText += `\n\n⚠️ **Agent Error:** ${errMsg}`;
            }
        }

        return NextResponse.json({
            reply: responseText,
            action: action?.action ?? null,
            agentId: action?.agentId ?? null,
            agentResult,
            flowData: action?.action === "build_flow" ? {
                flowName: action?.flowName ?? "New Pipeline",
                agents: action?.agents ?? [],
                connections: action?.connections ?? [],
            } : undefined,
            connectFrom: action?.connectFrom ?? null,
            model: llmResult.model,
            executionTimeMs: Date.now() - startTime,
        });
    } catch (err) {
        const errMsg = err instanceof Error ? err.message : "Chat failed";
        return NextResponse.json({ error: errMsg, executionTimeMs: Date.now() - startTime }, { status: 500 });
    }
}
