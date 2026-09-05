"use client";

import { useState, useEffect, useCallback } from "react";
import { X } from "lucide-react";
import { useFlowStore } from "@/store/flow-store";

export default function PipelineSaveModal() {
  const [isOpen, setIsOpen] = useState(false);
  const [name, setName] = useState("");
  const { nodes, edges, flowName } = useFlowStore();

  useEffect(() => {
    const handler = () => { setName(flowName); setIsOpen(true); };
    window.addEventListener("rayzorflow:open-save-modal", handler);
    return () => window.removeEventListener("rayzorflow:open-save-modal", handler);
  }, [flowName]);

  const handleSave = useCallback(() => {
    if (!name.trim() || nodes.length === 0) return;
    import("@/store/pipeline-store").then(({ usePipelineStore }) => {
      usePipelineStore.getState().savePipeline(name.trim(), nodes, edges);
      setIsOpen(false); setName("");
    });
  }, [name, nodes, edges]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center" style={{ background: "rgba(0,0,0,0.6)" }}>
      <div className="w-96 p-6 rounded-[10px]" style={{ background: "var(--bg-elevated)", border: "1px solid var(--purple-border)", fontFamily: "var(--font-jetbrains), monospace" }}>
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-[14px] font-semibold" style={{ color: "var(--text-primary)" }}>Save Pipeline</h2>
          <button onClick={() => setIsOpen(false)} style={{ color: "var(--text-muted)" }}><X size={16} /></button>
        </div>

        <div className="mb-4">
          <label className="text-[11px] mb-1.5 block" style={{ color: "var(--text-secondary)" }}>Pipeline Name</label>
          <input type="text" value={name} onChange={(e) => setName(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleSave()}
            className="w-full rounded-md px-3 py-2.5 text-[13px] outline-none transition-colors"
            style={{ background: "var(--bg-surface)", border: "1px solid var(--purple-border)", color: "var(--text-primary)", fontFamily: "var(--font-jetbrains), monospace" }}
            placeholder="My Payment Operations Flow" autoFocus />
        </div>

        <div className="text-[10px] mb-5" style={{ color: "var(--text-muted)" }}>{nodes.length} agent(s), {edges.length} connection(s) will be saved.</div>

        <div className="flex gap-2">
          <button onClick={() => setIsOpen(false)} className="flex-1 text-[12px] py-2.5 rounded-md transition-colors" style={{ color: "var(--text-secondary)", background: "var(--bg-surface)", border: "1px solid var(--purple-border)" }}>
            Cancel
          </button>
          <button onClick={handleSave} disabled={!name.trim() || nodes.length === 0}
            className="flex-1 text-[12px] font-semibold py-2.5 rounded-md transition-colors disabled:opacity-30"
            style={{ background: "var(--purple-primary)", color: "var(--bg-base)" }}>
            Save
          </button>
        </div>
      </div>
    </div>
  );
}
