"use client";

// ============================================================
// RayzorFlow — Agent X Chat Panel
// Full-featured AI chat co-pilot:
//   • Venice.ai / Gemini LLM integration
//   • Progressive canvas flow building
//   • Agent execution via natural language
//   • Markdown rendering with code blocks
//   • Conversation history & quick actions
// ============================================================

import { useState, useRef, useEffect, useCallback } from "react";
import { X, Send, Bot, User, Loader2, Sparkles, Play, Terminal } from "lucide-react";
import { useFlowStore } from "@/store/flow-store";
import { AGENT_REGISTRY } from "@/data/agent-registry";
import { cn } from "@/lib/utils";

interface ChatMessage {
    id: string;
    role: "user" | "assistant";
    content: string;
    agentResult?: Record<string, unknown>;
    action?: string | null;
    agentId?: string | null;
    model?: string;
    timestamp: Date;
}

const QUICK_ACTIONS = [
    { label: "Build recovery flow", message: "Build a payment recovery flow with payment health, payment link, and customer support agents" },
    { label: "Build payout flow", message: "Create a RazorpayX wallet balance and controlled payout workflow" },
    { label: "Run my flow", message: "Run the pipeline on the canvas" },
    { label: "Recover a payment", message: "Build a payment recovery workflow for failed UPI checkouts" },
    { label: "Review settlements", message: "Build a settlement reconciliation and commerce insights workflow" },
];

function renderMarkdown(text: string) {
    // Minimal markdown: bold, code blocks, inline code, line breaks
    return text
        .split(/```(\w*)\n([\s\S]*?)```/g)
        .map((part, i) => {
            if (i % 3 === 2) {
                // Code block content
                return (
                    <pre
                        key={i}
                        className="rounded-md px-3 py-2 text-[11px] overflow-x-auto my-2 font-mono whitespace-pre-wrap break-all"
                        style={{
                            background: "var(--bg-base)",
                            border: "1px solid var(--purple-border)",
                            color: "var(--text-code)",
                        }}
                    >
                        {part}
                    </pre>
                );
            }
            if (i % 3 === 1) return null; // language identifier
            // Regular text: process bold, inline code, newlines
            return (
                <span key={i}>
                    {part.split("\n").map((line, li) => (
                        <span key={li}>
                            {li > 0 && <br />}
                            {line.split(/(\*\*.*?\*\*|`[^`]+`)/g).map((seg, si) => {
                                if (seg.startsWith("**") && seg.endsWith("**"))
                                    return <strong key={si} style={{ color: "var(--text-primary)", fontWeight: 600 }}>{seg.slice(2, -2)}</strong>;
                                if (seg.startsWith("`") && seg.endsWith("`"))
                                    return <code key={si} style={{ background: "var(--bg-base)", color: "var(--purple-primary)", padding: "1px 4px", borderRadius: 3, fontSize: "11px" }}>{seg.slice(1, -1)}</code>;
                                return <span key={si}>{seg}</span>;
                            })}
                        </span>
                    ))}
                </span>
            );
        });
}

export default function AgentXPanel() {
    const {
        isAgentXOpen,
        setAgentXOpen,
        runFlow,
        clearCanvas,
        addAgentToCanvas,
        onConnect,
        setFlowName,
        updateNodeParameter,
    } = useFlowStore();

    const [messages, setMessages] = useState<ChatMessage[]>([
        {
            id: "welcome",
            role: "assistant",
            content:
                "👋 **Hey! I'm Agent X — your RayzorFlow co-pilot.**\n\nYou can tell me what to do in plain English — compose commerce agents, run a governed workflow, inspect payment operations, or **build flows on the canvas in real-time**.\n\nTry one of the quick actions below, or just type!",
            timestamp: new Date(),
        },
    ]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const bottomRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    useEffect(() => {
        if (isAgentXOpen) inputRef.current?.focus();
    }, [isAgentXOpen]);

    const conversationHistory = messages
        .filter((m) => m.id !== "welcome")
        .map((m) => ({ role: m.role, content: m.content }));

    /* ── Build flow on canvas progressively (real-time) ─────────── */
    const buildFlowOnCanvas = useCallback(
        async (flowData: {
            flowName: string;
            agents: { id: string; params?: Record<string, string> }[];
            connections: [number, number][];
        }) => {
            clearCanvas();
            setFlowName(flowData.flowName);

            const buildMsgId = `build-${Date.now()}`;
            const nodeIds: string[] = [];

            const updateBuildMsg = (content: string) => {
                setMessages((prev) => {
                    const idx = prev.findIndex((m) => m.id === buildMsgId);
                    if (idx >= 0) {
                        const updated = [...prev];
                        updated[idx] = { ...updated[idx], content };
                        return updated;
                    }
                    return [
                        ...prev,
                        { id: buildMsgId, role: "assistant" as const, content, timestamp: new Date() },
                    ];
                });
            };

            for (let i = 0; i < flowData.agents.length; i++) {
                const agentSpec = flowData.agents[i];
                const agentDef = AGENT_REGISTRY.find((a) => a.id === agentSpec.id);
                if (!agentDef) continue;

                const done = nodeIds
                    .map((_, j) => {
                        const d = AGENT_REGISTRY.find((a) => a.id === flowData.agents[j].id);
                        return `✅ ${d?.name ?? flowData.agents[j].id}`;
                    })
                    .join("\n");

                updateBuildMsg(
                    `🔨 **Building "${flowData.flowName}"**\n\n${done}${done ? "\n" : ""}⏳ Adding **${agentDef.name}**…`,
                );

                // Layout: up to 4 columns, then wrap to next row
                const cols = Math.min(flowData.agents.length, 4);
                const row = Math.floor(i / cols);
                const col = i % cols;
                addAgentToCanvas(agentDef, { x: 100 + col * 280, y: 150 + row * 220 });

                // Apply custom params if specified
                if (agentSpec.params) {
                    const latestNodes = useFlowStore.getState().nodes;
                    const newNode = latestNodes[latestNodes.length - 1];
                    for (const [key, value] of Object.entries(agentSpec.params)) {
                        updateNodeParameter(newNode.id, key, value);
                    }
                }

                const latestNodes = useFlowStore.getState().nodes;
                nodeIds.push(latestNodes[latestNodes.length - 1].id);
                await new Promise<void>((r) => setTimeout(r, 500));
            }

            // Wire up connections with a short delay between each
            for (const [fromIdx, toIdx] of flowData.connections) {
                if (nodeIds[fromIdx] && nodeIds[toIdx]) {
                    onConnect({
                        source: nodeIds[fromIdx],
                        target: nodeIds[toIdx],
                        sourceHandle: null,
                        targetHandle: null,
                    });
                    await new Promise<void>((r) => setTimeout(r, 250));
                }
            }

            const names = flowData.agents
                .map((a) => {
                    const d = AGENT_REGISTRY.find((d2) => d2.id === a.id);
                    return `✅ ${d?.name ?? a.id}`;
                })
                .join("\n");

            updateBuildMsg(
                `🎉 **Pipeline "${flowData.flowName}" ready!**\n\n${names}\n\n🔗 ${flowData.connections.length} connection(s) made.\n\nSay **"run the pipeline"** or click **Run Flow** to execute.`,
            );
        },
        [clearCanvas, setFlowName, addAgentToCanvas, updateNodeParameter, onConnect],
    );

    const sendMessage = useCallback(
        async (text: string) => {
            const trimmed = text.trim();
            if (!trimmed || isLoading) return;

            const userMsg: ChatMessage = {
                id: `user-${Date.now()}`,
                role: "user",
                content: trimmed,
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, userMsg]);
            setInput("");
            setIsLoading(true);

            try {
                const res = await fetch("/api/chat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        message: trimmed,
                        conversationHistory,
                    }),
                });

                const data = await res.json() as {
                    reply?: string;
                    error?: string;
                    action?: string;
                    agentId?: string;
                    agentResult?: Record<string, unknown>;
                    model?: string;
                    flowData?: {
                        flowName: string;
                        agents: { id: string; params?: Record<string, string> }[];
                        connections: [number, number][];
                    };
                    connectFrom?: string;
                };

                // Handle run_pipeline action from the LLM
                if (data.action === "run_pipeline") {
                    runFlow();
                }

                // Handle build_flow — progressive canvas building in real-time
                if (data.action === "build_flow" && data.flowData) {
                    const buildReplyMsg: ChatMessage = {
                        id: `assistant-${Date.now()}`,
                        role: "assistant",
                        content: data.reply || "Building your workflow…",
                        action: data.action,
                        model: data.model,
                        timestamp: new Date(),
                    };
                    setMessages((prev) => [...prev, buildReplyMsg]);
                    await buildFlowOnCanvas(data.flowData);
                    return; // finally block handles setIsLoading(false)
                }

                // Handle add_agent — add single agent to existing canvas
                if (data.action === "add_agent" && data.agentId) {
                    const agentDef = AGENT_REGISTRY.find((a) => a.id === data.agentId);
                    if (agentDef) {
                        const storeState = useFlowStore.getState();
                        const existingNodes = storeState.nodes;
                        const maxX = existingNodes.length > 0
                            ? Math.max(...existingNodes.map((n) => n.position.x))
                            : -180;
                        const avgY = existingNodes.length > 0
                            ? existingNodes.reduce((s, n) => s + n.position.y, 0) / existingNodes.length
                            : 200;
                        addAgentToCanvas(agentDef, { x: maxX + 280, y: avgY });

                        if (data.connectFrom) {
                            const updatedNodes = useFlowStore.getState().nodes;
                            const newNode = updatedNodes[updatedNodes.length - 1];
                            const sourceNode = updatedNodes.find(
                                (n) => n.data.agentId === data.connectFrom,
                            );
                            if (sourceNode && newNode) {
                                onConnect({
                                    source: sourceNode.id,
                                    target: newNode.id,
                                    sourceHandle: null,
                                    targetHandle: null,
                                });
                            }
                        }
                    }
                }

                const assistantMsg: ChatMessage = {
                    id: `assistant-${Date.now()}`,
                    role: "assistant",
                    content: data.reply || data.error || "No response.",
                    agentResult: data.agentResult ?? undefined,
                    action: data.action,
                    agentId: data.agentId,
                    model: data.model,
                    timestamp: new Date(),
                };
                setMessages((prev) => [...prev, assistantMsg]);
            } catch (err) {
                setMessages((prev) => [
                    ...prev,
                    {
                        id: `error-${Date.now()}`,
                        role: "assistant",
                        content: `⚠️ ${err instanceof Error ? err.message : "Connection failed"}`,
                        timestamp: new Date(),
                    },
                ]);
            } finally {
                setIsLoading(false);
            }
        },
        [isLoading, conversationHistory, runFlow, buildFlowOnCanvas, addAgentToCanvas, onConnect],
    );

    if (!isAgentXOpen) return null;

    return (
        <div
            className="fixed bottom-4 right-4 z-50 flex flex-col overflow-hidden"
            style={{
                width: 420,
                height: 620,
                background: "var(--bg-surface)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-xl)",
                boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.5)",
            }}
        >
            {/* ── Header ── */}
            <div
                className="flex items-center px-4 py-3 flex-shrink-0"
                style={{ borderBottom: "1px solid var(--border-subtle)" }}
            >
                <div className="flex items-center gap-2.5 flex-1">
                    <div
                        className="flex items-center justify-center"
                        style={{
                            width: 28,
                            height: 28,
                            borderRadius: 8,
                            background: "var(--purple-glow)",
                            border: "1px solid var(--purple-border)",
                        }}
                    >
                        <Sparkles size={13} style={{ color: "var(--purple-primary)" }} />
                    </div>
                    <div>
                        <p style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)", margin: 0 }}>Agent X</p>
                        <p style={{ fontSize: 10, color: "var(--text-muted)", margin: 0 }}>Your AI co-pilot for commerce workflows</p>
                    </div>
                </div>
                <button
                    onClick={() => setAgentXOpen(false)}
                    className="p-1 rounded transition-colors"
                    style={{ color: "var(--text-muted)" }}
                >
                    <X size={15} />
                </button>
            </div>

            {/* ── Messages ── */}
            <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4">
                {messages.map((msg) => (
                    <div
                        key={msg.id}
                        className={cn(
                            "flex gap-2.5",
                            msg.role === "user" ? "justify-end" : "justify-start",
                        )}
                    >
                        {msg.role === "assistant" && (
                            <div
                                className="flex items-center justify-center flex-shrink-0 mt-0.5"
                                style={{
                                    width: 24,
                                    height: 24,
                                    borderRadius: "50%",
                                    background: "var(--purple-glow)",
                                    border: "1px solid var(--purple-border)",
                                }}
                            >
                                <Bot size={12} style={{ color: "var(--purple-primary)" }} />
                            </div>
                        )}
                        <div
                            className="max-w-[85%] px-3 py-2.5 text-[12px] leading-relaxed"
                            style={{
                                borderRadius: msg.role === "user" ? "12px 12px 4px 12px" : "12px 12px 12px 4px",
                                background: msg.role === "user"
                                    ? "var(--purple-primary)"
                                    : "var(--bg-elevated)",
                                color: msg.role === "user"
                                    ? "#fff"
                                    : "var(--text-secondary)",
                                border: msg.role === "user"
                                    ? "none"
                                    : "1px solid var(--border-subtle)",
                            }}
                        >
                            {msg.role === "assistant" ? (
                                <div className="space-y-1">{renderMarkdown(msg.content)}</div>
                            ) : (
                                msg.content
                            )}
                            {/* Action badge */}
                            {msg.agentId && (
                                <div
                                    className="flex items-center gap-1.5 mt-2 pt-2"
                                    style={{ borderTop: "1px solid var(--border-subtle)" }}
                                >
                                    <Terminal size={10} style={{ color: "var(--green-live)" }} />
                                    <span style={{ fontSize: 10, color: "var(--green-live)", fontFamily: "var(--font-code)" }}>{msg.agentId}</span>
                                </div>
                            )}
                            {/* Model badge */}
                            {msg.model && (
                                <div style={{ fontSize: 9, color: "var(--purple-primary)", opacity: 0.6, marginTop: 4, textAlign: "right", fontWeight: 500 }}>Agent X</div>
                            )}
                        </div>
                        {msg.role === "user" && (
                            <div
                                className="flex items-center justify-center flex-shrink-0 mt-0.5"
                                style={{
                                    width: 24,
                                    height: 24,
                                    borderRadius: "50%",
                                    background: "rgba(139, 92, 246, 0.15)",
                                    border: "1px solid rgba(139, 92, 246, 0.3)",
                                }}
                            >
                                <User size={12} style={{ color: "var(--purple-primary)" }} />
                            </div>
                        )}
                    </div>
                ))}

                {isLoading && (
                    <div className="flex items-center gap-2">
                        <div
                            className="flex items-center justify-center flex-shrink-0"
                            style={{
                                width: 24,
                                height: 24,
                                borderRadius: "50%",
                                background: "var(--purple-glow)",
                                border: "1px solid var(--purple-border)",
                            }}
                        >
                            <Bot size={12} style={{ color: "var(--purple-primary)" }} />
                        </div>
                        <div
                            className="flex items-center gap-2 px-3 py-2 rounded-lg"
                            style={{
                                background: "var(--bg-elevated)",
                                border: "1px solid var(--border-subtle)",
                            }}
                        >
                            <Loader2 size={12} className="animate-spin" style={{ color: "var(--purple-primary)" }} />
                            <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Thinking…</span>
                        </div>
                    </div>
                )}
                <div ref={bottomRef} />
            </div>

            {/* ── Quick actions ── */}
            {messages.length <= 2 && (
                <div className="px-4 pb-2 flex flex-wrap gap-1.5">
                    {QUICK_ACTIONS.map((qa) => (
                        <button
                            key={qa.label}
                            onClick={() => sendMessage(qa.message)}
                            disabled={isLoading}
                            className="flex items-center gap-1.5 px-2.5 py-1.5 text-[11px] rounded-md transition-colors"
                            style={{
                                background: "var(--bg-elevated)",
                                border: "1px solid var(--border-subtle)",
                                color: "var(--text-muted)",
                            }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.borderColor = "var(--purple-border)";
                                e.currentTarget.style.color = "var(--text-secondary)";
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.borderColor = "var(--border-subtle)";
                                e.currentTarget.style.color = "var(--text-muted)";
                            }}
                        >
                            <Play size={9} />
                            {qa.label}
                        </button>
                    ))}
                </div>
            )}

            {/* ── Input ── */}
            <div
                className="px-4 py-3 flex-shrink-0"
                style={{ borderTop: "1px solid var(--border-subtle)" }}
            >
                <div className="flex gap-2">
                    <input
                        ref={inputRef}
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === "Enter" && !e.shiftKey) {
                                e.preventDefault();
                                sendMessage(input);
                            }
                        }}
                        placeholder="Tell your agents what to do…"
                        disabled={isLoading}
                        className="flex-1 px-3 py-2 text-[12px] rounded-md outline-none transition-colors"
                        style={{
                            background: "var(--bg-base)",
                            border: "1px solid var(--border-subtle)",
                            color: "var(--text-primary)",
                            fontFamily: "var(--font-body), sans-serif",
                        }}
                        onFocus={(e) => { e.currentTarget.style.borderColor = "var(--purple-border)"; }}
                        onBlur={(e) => { e.currentTarget.style.borderColor = "var(--border-subtle)"; }}
                    />
                    <button
                        onClick={() => sendMessage(input)}
                        disabled={isLoading || !input.trim()}
                        className="p-2 rounded-md transition-colors flex-shrink-0"
                        style={{
                            background: !input.trim() || isLoading ? "var(--bg-elevated)" : "var(--purple-primary)",
                            color: !input.trim() || isLoading ? "var(--text-muted)" : "#fff",
                            cursor: !input.trim() || isLoading ? "not-allowed" : "pointer",
                        }}
                    >
                        <Send size={14} />
                    </button>
                </div>
            </div>
        </div>
    );
}
