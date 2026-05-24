import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft, AlertTriangle, AlertCircle, Info, CheckCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { EmptyState } from "@/components/layout/EmptyState";
import { ProjectNav } from "@/components/layout/ProjectNav";
import * as api from "@/lib/api";

function severityIcon(s: string) {
  switch (s) {
    case "blocking": return <AlertTriangle className="size-4 text-red-400 shrink-0" />;
    case "major": return <AlertCircle className="size-4 text-amber-400 shrink-0" />;
    default: return <Info className="size-4 text-muted-foreground shrink-0" />;
  }
}

export function ReviewPage() {
  const { projectId, chapterId } = useParams<{ projectId: string; chapterId: string }>();

  const { data: project } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => api.getProject(projectId!),
    enabled: !!projectId,
  });

  const { data: chapter, isLoading: chapterLoading } = useQuery({
    queryKey: ["chapter", projectId, chapterId],
    queryFn: () => api.getChapter(projectId!, chapterId!),
    enabled: !!projectId && !!chapterId,
  });

  const { data: reviews, isLoading: reviewsLoading } = useQuery({
    queryKey: ["reviews", chapterId],
    queryFn: () => api.getReviews(chapterId!),
    enabled: !!chapterId,
  });

  const blockingCount = reviews?.filter((r) => r.severity === "blocking" && !r.is_fixed).length ?? 0;
  const majorCount = reviews?.filter((r) => r.severity === "major" && !r.is_fixed).length ?? 0;
  const minorCount = reviews?.filter((r) => r.severity === "minor" && !r.is_fixed).length ?? 0;
  const totalCount = reviews?.length ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex items-start gap-4 flex-wrap">
        <Link to={`/projects/${projectId}/chapters/${chapterId}`}>
          <Button variant="ghost" size="sm">
            <ArrowLeft className="size-4 mr-1" />
            返回写作台
          </Button>
        </Link>
        <div className="flex-1 min-w-0">
          <h1 className="text-2xl font-serif font-semibold tracking-tight">
            审查中心
          </h1>
          <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
            {project && <span>{project.title}</span>}
            {chapter && (
              <>
                <Separator orientation="vertical" className="h-3" />
                <span>{chapter.title}</span>
              </>
            )}
          </div>
        </div>
      </div>
      {projectId && <ProjectNav projectId={projectId} className="mb-2" />}

      {chapterLoading || reviewsLoading ? (
        <div className="space-y-3">
          <Skeleton className="h-12 w-64" />
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      ) : !reviews || reviews.length === 0 ? (
        <EmptyState
          icon={CheckCircle}
          title="暂无审查问题"
          description="运行写作流水线以获取审查报告。审查结果会展示在此页面中。"
        />
      ) : (
        <>
          {/* Summary bar */}
          <div className="flex items-center gap-4 p-4 rounded-lg bg-muted/30 border">
            <div className="flex items-center gap-1.5">
              <AlertTriangle className="size-4 text-red-400" />
              <span className="text-sm font-medium">{blockingCount}</span>
              <span className="text-xs text-muted-foreground">阻断</span>
            </div>
            <div className="flex items-center gap-1.5">
              <AlertCircle className="size-4 text-amber-400" />
              <span className="text-sm font-medium">{majorCount}</span>
              <span className="text-xs text-muted-foreground">严重</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Info className="size-4 text-muted-foreground" />
              <span className="text-sm font-medium">{minorCount}</span>
              <span className="text-xs text-muted-foreground">轻微</span>
            </div>
            <Badge variant="outline" className="ml-auto text-xs">
              共 {totalCount} 项
            </Badge>
          </div>

          {/* Issues list */}
          <ScrollArea className="h-[calc(100vh-16rem)]">
            <div className="space-y-4 pr-2">
              {reviews.map((issue) => (
                <div
                  key={issue.id}
                  className={`p-4 rounded-lg border ${
                    issue.severity === "blocking"
                      ? "bg-red-500/10 border-red-500/20"
                      : issue.severity === "major"
                        ? "bg-amber-500/10 border-amber-500/20"
                        : "bg-muted/30 border-border"
                  } ${issue.is_fixed ? "opacity-50" : ""}`}
                >
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5">{severityIcon(issue.severity)}</div>
                    <div className="flex-1 min-w-0 space-y-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="font-medium text-sm">{issue.title}</h3>
                        <Badge variant="outline" className="text-[10px]">
                          {issue.category}
                        </Badge>
                        <Badge
                          variant={issue.severity === "blocking" ? "destructive" : issue.severity === "major" ? "default" : "secondary"}
                          className="text-[10px]"
                        >
                          {issue.severity === "blocking" ? "阻断" : issue.severity === "major" ? "严重" : "轻微"}
                        </Badge>
                        {issue.is_fixed && (
                          <Badge variant="outline" className="text-[10px]">
                            <CheckCircle className="size-3 mr-1" />
                            已修复
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">{issue.description}</p>
                      {issue.evidence && (
                        <blockquote className="border-l-2 border-muted-foreground/30 pl-3 text-sm italic text-muted-foreground/70">
                          {issue.evidence}
                        </blockquote>
                      )}
                      {issue.suggestion && (
                        <div className="p-2 rounded bg-amber-500/5 border border-amber-500/10 text-sm">
                          <span className="font-medium text-amber-400">建议：</span>
                          <span className="text-muted-foreground">{issue.suggestion}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </>
      )}
    </div>
  );
}
