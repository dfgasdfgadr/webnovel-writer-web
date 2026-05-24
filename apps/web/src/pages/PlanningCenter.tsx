import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ProjectNav } from "@/components/layout/ProjectNav";
import { EmptyState } from "@/components/layout/EmptyState";
import * as api from "@/lib/api";

export function PlanningCenter() {
  const { projectId } = useParams<{ projectId: string }>();

  const { data: project, isLoading } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => api.getProject(projectId!),
    enabled: !!projectId,
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-6 w-32" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="mb-4">
        <Link
          to="/"
          className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1 mb-2"
        >
          <ArrowLeft className="size-3" />
          项目列表
        </Link>
        <h1 className="font-serif text-2xl font-semibold">规划中心</h1>
        {project && (
          <p className="text-sm text-muted-foreground mt-1">{project.title}</p>
        )}
      </div>
      <ProjectNav projectId={projectId!} active="planning" className="mb-2" />

      <EmptyState
        icon={Loader2}
        title="规划中心 (WIP)"
        description="总纲/章纲/批量生成功能开发中..."
      />
    </div>
  );
}
