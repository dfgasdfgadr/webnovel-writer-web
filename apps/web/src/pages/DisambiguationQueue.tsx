import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Check, X, Filter, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { EmptyState } from "@/components/layout/EmptyState";
import { ProjectNav } from "@/components/layout/ProjectNav";
import * as api from "@/lib/api";

function confidenceColor(c: number): string {
  if (c >= 0.7) return "text-green-400";
  if (c >= 0.4) return "text-amber-400";
  return "text-red-400";
}

function confidenceBg(c: number): string {
  if (c >= 0.7) return "bg-green-500/10 border-green-500/20";
  if (c >= 0.4) return "bg-amber-500/10 border-amber-500/20";
  return "bg-red-500/10 border-red-500/20";
}

export function DisambiguationQueue() {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<string>("pending");

  const { data: project } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => api.getProject(projectId!),
    enabled: !!projectId,
  });

  const { data: itemsData, isLoading } = useQuery({
    queryKey: ["disambiguation", projectId, filter],
    queryFn: () => api.listDisambiguationItems(projectId!, filter === "all" ? undefined : filter),
    enabled: !!projectId,
  });

  const resolveMutation = useMutation({
    mutationFn: ({ itemId, status }: { itemId: string; status: string }) =>
      api.resolveDisambiguationItem(projectId!, itemId, {
        status,
        resolved_by: "user",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["disambiguation", projectId] });
    },
  });

  const items = itemsData?.items ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <Filter className="size-5 text-muted-foreground" />
          <h1 className="text-2xl font-serif font-semibold tracking-tight">
            消歧队列
          </h1>
        </div>
        {project && (
          <span className="text-sm text-muted-foreground">{project.title}</span>
        )}
      </div>

      {projectId && <ProjectNav projectId={projectId} className="mb-2" />}

      <Tabs value={filter} onValueChange={setFilter}>
        <TabsList>
          <TabsTrigger value="pending">
            待处理
          </TabsTrigger>
          <TabsTrigger value="accepted">已采纳</TabsTrigger>
          <TabsTrigger value="rejected">已驳回</TabsTrigger>
          <TabsTrigger value="all">全部</TabsTrigger>
        </TabsList>
      </Tabs>

      {isLoading ? (
        <div className="space-y-3">
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
        </div>
      ) : items.length === 0 ? (
        <EmptyState
          icon={Filter}
          title={filter === "pending" ? "无待处理项" : "无记录"}
          description="低置信度字段将在此展示供人工确认。运行写作流水线后，ContinuityAgent 和 DataAgent 会产生待确认项。"
        />
      ) : (
        <ScrollArea className="h-[calc(100vh-14rem)]">
          <div className="space-y-3 pr-2">
            {items.map((item) => {
              let alternatives: string[] = [];
              try {
                alternatives = JSON.parse(item.alternatives);
              } catch {}
              const isPending = item.status === "pending";

              return (
                <div
                  key={item.id}
                  className={`p-4 rounded-lg border ${confidenceBg(item.confidence)} ${!isPending ? "opacity-60" : ""}`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0 space-y-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge variant="outline" className="text-xs">
                          {item.field_name}
                        </Badge>
                        <Badge
                          variant="secondary"
                          className={`text-xs ${confidenceColor(item.confidence)}`}
                        >
                          <AlertTriangle className="size-3 mr-1" />
                          {(item.confidence * 100).toFixed(0)}%
                        </Badge>
                        {!isPending && (
                          <Badge variant={item.status === "accepted" ? "default" : "destructive"} className="text-xs">
                            {item.status === "accepted" ? "已采纳" : "已驳回"}
                          </Badge>
                        )}
                      </div>

                      <p className="text-sm">
                        <span className="text-muted-foreground">当前值：</span>
                        {item.current_value || "(空)"}
                      </p>

                      {item.suggestion && (
                        <p className="text-sm">
                          <span className="text-muted-foreground">建议：</span>
                          <span className="text-amber-400">{item.suggestion}</span>
                        </p>
                      )}

                      {alternatives.length > 0 && (
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-xs text-muted-foreground">备选：</span>
                          {alternatives.map((alt, i) => (
                            <Badge key={i} variant="outline" className="text-[10px]">
                              {alt}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>

                    {isPending && (
                      <div className="flex items-center gap-2 shrink-0">
                        <Button
                          size="sm"
                          variant="outline"
                          className="text-green-400 border-green-500/30 hover:bg-green-500/10"
                          onClick={() => resolveMutation.mutate({ itemId: item.id, status: "accepted" })}
                          disabled={resolveMutation.isPending}
                        >
                          <Check className="size-4 mr-1" />
                          采纳
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className="text-red-400 border-red-500/30 hover:bg-red-500/10"
                          onClick={() => resolveMutation.mutate({ itemId: item.id, status: "rejected" })}
                          disabled={resolveMutation.isPending}
                        >
                          <X className="size-4 mr-1" />
                          驳回
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </ScrollArea>
      )}
    </div>
  );
}
