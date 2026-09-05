"use client";

import { useCallback, useEffect } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  BackgroundVariant,
  useReactFlow,
  type NodeTypes,
} from "@xyflow/react";
import { useFlowStore } from "@/store/flow-store";
import AgentNode from "./agent-node";
import type { CanvasNodeData, AgentDefinition } from "@/types";
import type { Node } from "@xyflow/react";

const NODE_TYPES: NodeTypes = { agentNode: AgentNode };

function EmptyCanvasState({ onLoadDemo }: { onLoadDemo: () => void }) {
  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none z-10">
      <div className="pointer-events-auto flex flex-col items-center gap-5 max-w-xs text-center">
        <div className="w-14 h-14 rounded-[10px] flex items-center justify-center" style={{ background: "var(--bg-surface)", border: "1px solid var(--purple-border)" }}>
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#836EF9" strokeWidth="1.5" strokeLinecap="round">
            <path d="M12 2L2 7l10 5 10-5-10-5z" /><path d="M2 17l10 5 10-5" /><path d="M2 12l10 5 10-5" />
          </svg>
        </div>
        <div>
          <p className="text-[14px] font-medium mb-1" style={{ color: "var(--text-primary)", fontFamily: "var(--font-jetbrains), monospace" }}>Start building your flow</p>
          <p className="text-[12px] leading-relaxed" style={{ color: "var(--text-muted)", fontFamily: "var(--font-jetbrains), monospace" }}>
            Drag agents from the sidebar, wire them together, then hit <span style={{ color: "var(--purple-primary)" }}>Run Flow</span>.
            <br />Independent nodes execute in <span style={{ color: "var(--purple-primary)" }}>parallel</span>.
          </p>
        </div>
        <button
          onClick={onLoadDemo}
          className="flex items-center gap-2 px-5 py-2.5 rounded-md text-[12px] font-medium transition-colors"
          style={{ background: "var(--purple-glow)", border: "1px solid var(--purple-border)", color: "var(--purple-primary)", fontFamily: "var(--font-jetbrains), monospace" }}
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect width="18" height="7" x="3" y="3" rx="1" /><rect width="9" height="7" x="3" y="14" rx="1" /><rect width="5" height="7" x="16" y="14" rx="1" /></svg>
          Load commerce demo flow
        </button>
      </div>
    </div>
  );
}

export default function FlowCanvas() {
  const { nodes, edges, onNodesChange, onEdgesChange, onConnect, selectNode, addAgentToCanvas, loadDemoFlow, loadAutoSave, runFlow, stopFlow } = useFlowStore();
  const { screenToFlowPosition } = useReactFlow();

  useEffect(() => { loadAutoSave(); }, [loadAutoSave]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      if (e.key === "r" || e.key === "R") { e.preventDefault(); runFlow(); }
      else if (e.key === "Escape") { stopFlow(); }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [runFlow, stopFlow]);

  const handleDragOver = useCallback((event: React.DragEvent) => { event.preventDefault(); event.dataTransfer.dropEffect = "move"; }, []);

  const handleDrop = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    const agentJson = event.dataTransfer.getData("agent");
    if (!agentJson) return;
    try {
      const agent = JSON.parse(agentJson) as AgentDefinition;
      const position = screenToFlowPosition({ x: event.clientX, y: event.clientY });
      addAgentToCanvas(agent, position);
    } catch { /* ignore */ }
  }, [screenToFlowPosition, addAgentToCanvas]);

  const handleNodeClick = useCallback((_: React.MouseEvent, node: Node<CanvasNodeData>) => { selectNode(node.id); }, [selectNode]);
  const handlePaneClick = useCallback(() => { selectNode(null); }, [selectNode]);

  return (
    <div className="flex-1 h-full relative" style={{ background: "var(--bg-base)" }} onDragOver={handleDragOver} onDrop={handleDrop}>
      {nodes.length === 0 && <EmptyCanvasState onLoadDemo={loadDemoFlow} />}
      <ReactFlow
        nodes={nodes} edges={edges}
        onNodesChange={onNodesChange} onEdgesChange={onEdgesChange} onConnect={onConnect}
        onNodeClick={handleNodeClick} onPaneClick={handlePaneClick}
        nodeTypes={NODE_TYPES}
        fitView fitViewOptions={{ padding: 0.2 }}
        minZoom={0.3} maxZoom={2}
        defaultEdgeOptions={{ type: "smoothstep", style: { stroke: "#836EF9", strokeWidth: 1.5, opacity: 0.5 } }}
        proOptions={{ hideAttribution: true }}
      >
        <Background variant={BackgroundVariant.Dots} gap={24} size={2} color="#836EF908" />
        <Controls showInteractive={false} />
        <MiniMap nodeColor="#836EF9" maskColor="rgba(13,13,26,0.7)" />
      </ReactFlow>
    </div>
  );
}
