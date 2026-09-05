import { cn } from "@/lib/utils";

export function Logo({ collapsed = false, className }: { collapsed?: boolean; className?: string }) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="brand-mark grid size-6 shrink-0 place-items-center rounded-md font-mono text-xs font-bold">I</div>
      {!collapsed ? (
        <span className="font-heading text-sm font-semibold tracking-tight">
          Intell<span className="text-primary">act</span>
        </span>
      ) : null}
    </div>
  );
}
