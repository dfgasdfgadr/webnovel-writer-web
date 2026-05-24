import { Link, useLocation } from "react-router-dom";
import { FileText, FlaskConical, Network } from "lucide-react";
import { cn } from "@/lib/utils";

export type ProjectNavTab = "chapters" | "simulations" | "graph";

interface ProjectNavProps {
  projectId: string;
  active?: ProjectNavTab;
  className?: string;
}

const tabs: Array<{
  id: ProjectNavTab;
  label: string;
  suffix: string;
  icon: typeof FileText;
}> = [
  { id: "chapters", label: "章节", suffix: "", icon: FileText },
  { id: "simulations", label: "推演中心", suffix: "/simulations", icon: FlaskConical },
  { id: "graph", label: "关系图谱", suffix: "/graph", icon: Network },
];

export function resolveProjectNavTab(pathname: string): ProjectNavTab {
  if (pathname.includes("/simulations")) return "simulations";
  if (pathname.includes("/graph")) return "graph";
  return "chapters";
}

export function ProjectNav({ projectId, active, className }: ProjectNavProps) {
  const location = useLocation();
  const current = active ?? resolveProjectNavTab(location.pathname);

  return (
    <nav
      className={cn("flex flex-wrap gap-2", className)}
      aria-label="项目导航"
    >
      {tabs.map((tab) => {
        const isActive = current === tab.id;
        const Icon = tab.icon;
        return (
          <Link
            key={tab.id}
            to={`/projects/${projectId}${tab.suffix}`}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm transition-colors",
              isActive
                ? "bg-amber-500/15 text-amber-400 border border-amber-500/30"
                : "text-muted-foreground hover:text-foreground hover:bg-muted/60 border border-transparent"
            )}
            aria-current={isActive ? "page" : undefined}
          >
            <Icon className="size-4 shrink-0" />
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
}
