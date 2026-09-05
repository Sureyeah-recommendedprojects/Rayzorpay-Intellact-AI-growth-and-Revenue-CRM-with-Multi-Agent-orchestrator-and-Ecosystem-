"use client";

import Image from "next/image";import { Play, Square, Download, Upload, Trash2, LayoutTemplate, Save, Bot } from "lucide-react";
import { useFlowStore } from "@/store/flow-store";
import { cn } from "@/lib/utils";

export default function Toolbar() {
  const {
    flowName, flowStatus, nodes,
    setFlowName, stopFlow, exportFlow, clearCanvas, loadDemoFlow,
    toggleLog, isLogVisible, isAgentXOpen, setAgentXOpen,
    setPipelineTriggerOpen,
  } = useFlowStore();

  const isRunning = flowStatus === "running";
  const openSaveModal = () => { window.dispatchEvent(new CustomEvent("rayzorflow:open-save-modal")); };
  const handleImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) { const reader = new FileReader(); reader.onload = (re) => { useFlowStore.getState().importFlow(re.target?.result as string); }; reader.readAsText(file); }
    e.target.value = "";
  };

  const handleRunClick = () => {
    if (nodes.length === 0) return;
    setPipelineTriggerOpen(true);
  };

  const btnBase = "flex items-center gap-1.5 px-2.5 py-1.5 text-[11px] rounded-md transition-colors";
  const btnIdle = "hover:bg-[#1a1a2e]";

  return (
    <div className="h-12 flex items-center px-4 gap-2 flex-shrink-0" style={{ background: "var(--bg-surface)", borderBottom: "1px solid #836EF918", fontFamily: "var(--font-jetbrains), monospace" }}>
      {/* Brand */}
      <div className="flex items-center gap-2 mr-3">
        <Image src="/images/logo.png" alt="RayzorFlow Logo" width={24} height={24} className="rounded-md" />
        <span className="font-heading text-[10px]" style={{ color: "var(--purple-primary)" }}>RAYZORFLOW</span>
      </div>
      <div className="w-px h-5" style={{ background: "var(--purple-border)" }} />

      {/* Flow name */}
      <input type="text" value={flowName} onChange={(e) => setFlowName(e.target.value)}
        className="bg-transparent text-[12px] outline-none w-36 placeholder:opacity-40"
        style={{ color: "var(--text-secondary)", fontFamily: "var(--font-jetbrains), monospace" }}
        placeholder="Flow name…" />

      <div className="flex-1" />

      <span className="text-[10px] hidden sm:inline" style={{ color: "var(--text-muted)" }}>{nodes.length} node{nodes.length !== 1 ? "s" : ""}</span>
      <div className="w-px h-5 hidden sm:block" style={{ background: "var(--purple-border)" }} />

      <button onClick={loadDemoFlow} title="Demo" className={cn(btnBase, btnIdle)} style={{ color: "var(--text-secondary)" }}><LayoutTemplate size={13} /><span className="hidden sm:inline">Demo</span></button>
      <button onClick={clearCanvas} title="Clear" className={cn(btnBase, "hover:!text-[#f87171]", btnIdle)} style={{ color: "var(--text-secondary)" }}><Trash2 size={13} /></button>

      <label className={cn(btnBase, btnIdle, "cursor-pointer")} style={{ color: "var(--text-secondary)" }} title="Import">
        <Upload size={13} /><span className="hidden sm:inline">Import</span>
        <input type="file" accept=".json" className="hidden" onChange={handleImport} />
      </label>

      <button onClick={exportFlow} title="Export" className={cn(btnBase, btnIdle)} style={{ color: "var(--text-secondary)" }}><Download size={13} /><span className="hidden sm:inline">Export</span></button>
      <button onClick={openSaveModal} title="Save" className={cn(btnBase, btnIdle)} style={{ color: "var(--text-secondary)" }}><Save size={13} /><span className="hidden sm:inline">Save</span></button>

      <div className="w-px h-5" style={{ background: "var(--purple-border)" }} />

      <button onClick={toggleLog} className={cn(btnBase, isLogVisible ? "bg-[#836EF915]" : btnIdle)} style={{ color: isLogVisible ? "var(--purple-primary)" : "var(--text-secondary)" }}>Logs</button>

      <button onClick={() => setAgentXOpen(!isAgentXOpen)} className={cn(btnBase, isAgentXOpen ? "bg-[#836EF915]" : btnIdle)} style={{ color: isAgentXOpen ? "var(--purple-primary)" : "var(--text-secondary)" }}><Bot size={13} /><span className="hidden sm:inline">Agent X</span></button>

      <div className="w-px h-5" style={{ background: "var(--purple-border)" }} />

      {isRunning ? (
        <button onClick={stopFlow} className="flex items-center gap-2 px-4 py-1.5 text-[12px] font-semibold rounded-md transition-colors" style={{ background: "var(--red-error)", color: "white" }}><Square size={12} /> Stop</button>
      ) : (
        <button onClick={handleRunClick} disabled={nodes.length === 0}
          className="flex items-center gap-2 px-4 py-1.5 text-[12px] font-semibold rounded-md transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
          style={{ background: nodes.length === 0 ? "var(--bg-elevated)" : "var(--purple-primary)", color: nodes.length === 0 ? "var(--text-muted)" : "var(--bg-base)" }}>
          <Play size={12} /> Run Flow
        </button>
      )}

      <div className="flex items-center gap-1.5 ml-1">
        <div className={cn("w-2 h-2 rounded-full",
          flowStatus === "idle" && "bg-[#5a587a]",
          flowStatus === "running" && "bg-[#836EF9] animate-pulse",
          flowStatus === "completed" && "bg-[#4ade80]",
          flowStatus === "error" && "bg-[#f87171]"
        )} />
        <span className="text-[10px] capitalize hidden sm:inline" style={{ color: "var(--text-muted)" }}>{flowStatus}</span>
      </div>
    </div>
  );
}
