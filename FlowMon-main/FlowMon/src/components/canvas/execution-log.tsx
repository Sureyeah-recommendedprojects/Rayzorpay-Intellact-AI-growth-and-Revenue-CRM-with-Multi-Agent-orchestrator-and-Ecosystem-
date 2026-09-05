"use client";

import { useRef, useEffect } from "react";
import { X, Trash2, Zap } from "lucide-react";
import { useFlowStore } from "@/store/flow-store";
import { cn, formatTimestamp } from "@/lib/utils";

const LEVEL_STYLES: Record<string, { bar: string; text: string; prefix: string }> = {
  info:    { bar: "bg-[#5a587a]", text: "text-[#9d9bbf]", prefix: "▸" },
  success: { bar: "bg-[#4ade80]", text: "text-[#4ade80]", prefix: "✓" },
  error:   { bar: "bg-[#f87171]", text: "text-[#f87171]", prefix: "✗" },
  warn:    { bar: "bg-[#fbbf24]", text: "text-[#fbbf24]", prefix: "⚠" },
};

export default function ExecutionLog() {
  const { executionLog, isLogVisible, toggleLog, clearLog } = useFlowStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isLogVisible) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [executionLog, isLogVisible]);

  if (!isLogVisible) return null;

  return (
    <div className="h-[200px] flex flex-col flex-shrink-0" style={{ background: "var(--bg-base)", borderTop: "1px solid #836EF918", fontFamily: "var(--font-jetbrains), monospace" }}>
      {/* Header */}
      <div className="flex items-center px-4 py-2 flex-shrink-0" style={{ borderBottom: "1px solid #836EF918" }}>
        <span className="text-[12px] font-medium" style={{ color: "var(--text-primary)" }}>Execution Log</span>
        <span className="ml-2 text-[10px] px-1.5 py-0.5 rounded" style={{ color: "var(--text-muted)", background: "var(--bg-surface)" }}>{executionLog.length}</span>
        <div className="flex-1" />
        <button onClick={clearLog} className="p-1 rounded transition-colors" style={{ color: "var(--text-muted)" }} title="Clear"><Trash2 size={12} /></button>
        <button onClick={toggleLog} className="p-1 rounded transition-colors ml-1" style={{ color: "var(--text-muted)" }} title="Close"><X size={14} /></button>
      </div>

      {/* Entries */}
      <div className="flex-1 overflow-y-auto text-[11px]">
        {executionLog.length === 0 ? (
          <div className="flex items-center justify-center h-full" style={{ color: "var(--text-muted)" }}>No log entries yet. Run a flow to see output.</div>
        ) : (
          executionLog.map((entry) => {
            const styles = LEVEL_STYLES[entry.level] ?? LEVEL_STYLES.info;
            const isGroupHeader = entry.groupIndex !== undefined && entry.message.includes("Parallel group");
            return (
              <div
                key={entry.id}
                className="flex items-start gap-0 transition-colors hover:bg-[#1a1a2e30]"
                style={{ borderBottom: "1px solid #836EF908", background: isGroupHeader ? "#1a1a2e" : undefined }}
              >
                <div className={cn("w-0.5 self-stretch flex-shrink-0", styles.bar)} />
                <span className="px-2 py-1.5 whitespace-nowrap flex-shrink-0 pt-[7px]" style={{ color: "var(--text-muted)" }}>{formatTimestamp(entry.timestamp)}</span>
                <span className={cn("px-1 py-1.5 flex-shrink-0 w-5 text-center pt-[7px]", styles.text)}>{styles.prefix}</span>
                {entry.groupIndex !== undefined && (
                  <span className="text-[9px] rounded px-1 py-0.5 mt-1.5 mr-1 flex-shrink-0 flex items-center gap-0.5" style={{ color: "var(--purple-primary)", background: "var(--purple-glow)" }}>
                    <Zap size={8} />G{entry.groupIndex + 1}
                  </span>
                )}
                <span className="py-1.5 pr-2 whitespace-nowrap flex-shrink-0 pt-[7px] max-w-[110px] truncate" style={{ color: "var(--text-code)" }}>{entry.agentName}</span>
                <span className={cn("py-1.5 pr-3 flex-1 pt-[7px] break-all", styles.text)}>{entry.message}</span>
              </div>
            );
          })
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
