import { useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft, AlertTriangle, AlertCircle, Info, CheckCircle,
  Loader2, Wand2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/layout/EmptyState";
import { ProjectNav } from "@/components/layout/ProjectNav";
import * as api from "@/lib/api";
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer,
} from "recharts";

function severityIcon(s: string) {
  switch (s) {
    case "blocking": return <AlertTriangle className="size-4 text-red-400 shrink-0" />;
    case "major": return <AlertCircle className="size-4 text-amber-400 shrink-0" />;
    default: return <Info className="size-4 text-muted-foreground shrink-0" />;
  }
}

const DIMENSION_KEYS = [
  { key: "consistency_score", label: "设定一致性" },
  { key: "timeline_score", label: "时间线" },
  { key: "coherence_score", label: "叙事连贯" },
  { key: "ooc_score", label: "角色OOC" },
  { key: "logic_score", label: "逻辑因果" },
  { key: "foreshadowing_score", label: "伏笔管理" },
  { key: "ai_flavor_score", label: "AI味" },
];

function metricsToRadarData(metrics: api.ReviewMetricPublic[] | undefined) {
  if (!metrics || metrics.length === 0) return [];
  const latest = metrics[0];
  return DIMENSION_KEYS.map(({ key, label }) => ({
    dimension: label,
    score: (latest as Record<string, unknown>)[key] as number ?? 0,
  }));
}

function metricsToTimelineData(metrics: api.ReviewMetricPublic[] | undefined) {
  if (!metrics || metrics.length === 0) return [];
  return [...metrics].reverse().map((m) => ({
    time: new Date(m.created_at).toLocaleDateString("zh-CN", { month: "short", day: "numeric" }),
    consistency: m.consistency_score,
    timeline: m.timeline_score,
    coherence: m.coherence_score,
    ooc: m.ooc_score,
    logic: m.logic_score,
    foreshadowing: m.foreshadowing_score,
    aiFlavor: m.ai_flavor_score,
  }));
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

  const { data: metrics } = useQuery({
    queryKey: ["reviewMetrics", chapterId],
    queryFn: () => api.getReviewMetrics(chapterId!),
    enabled: !!chapterId,
  });

  const queryClient = useQueryClient();
  const [isPolishing, setIsPolishing] = useState(false);
  const [polishProgress, setPolishProgress] = useState<{ index: number; total: number; issueTitle: string } | null>(null);
  const [polishDiffs, setPolishDiffs] = useState<Array<{ issueId: string; issueTitle: string; summary: string; diffs: Array<{ before: string; after: string; axis: string }> }>>([]);
  const [polishError, setPolishError] = useState<string | null>(null);

  const handleFixAll = useCallback(() => {
    if (!chapterId) return;
    setIsPolishing(true);
    setPolishDiffs([]);
    setPolishProgress(null);

    const url = api.streamPolishUrl(chapterId);
    const eventSource = new EventSource(url);

    eventSource.addEventListener("start", (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      setPolishProgress({ index: 0, total: data.total_issues, issueTitle: "" });
    });

    eventSource.addEventListener("issue_done", (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      setPolishProgress({ index: data.index, total: data.index, issueTitle: data.issue_title });
      setPolishDiffs((prev) => [...prev, {
        issueId: data.issue_id,
        issueTitle: data.issue_title,
        summary: data.summary,
        diffs: data.diff || [],
      }]);
    });

    eventSource.addEventListener("issue_error", (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      setPolishDiffs((prev) => [...prev, {
        issueId: data.issue_id,
        issueTitle: `错误: ${data.error}`,
        summary: "",
        diffs: [],
      }]);
    });

    eventSource.addEventListener("done", () => {
      setIsPolishing(false);
      eventSource.close();
      queryClient.invalidateQueries({ queryKey: ["reviews", chapterId] });
      queryClient.invalidateQueries({ queryKey: ["chapter", projectId, chapterId] });
    });

    eventSource.onerror = () => {
      setIsPolishing(false);
      setPolishError("SSE 连接中断，请检查 API 服务是否运行");
      eventSource.close();
    };
  }, [chapterId, projectId, queryClient]);

  const blockingCount = reviews?.filter((r) => r.severity === "blocking" && !r.is_fixed).length ?? 0;
  const majorCount = reviews?.filter((r) => r.severity === "major" && !r.is_fixed).length ?? 0;
  const minorCount = reviews?.filter((r) => r.severity === "minor" && !r.is_fixed).length ?? 0;
  const totalCount = reviews?.length ?? 0;
  const unfixedCount = reviews?.filter((r) => !r.is_fixed).length ?? 0;

  const radarData = metricsToRadarData(metrics);
  const timelineData = metricsToTimelineData(metrics);
  const hasMetrics = radarData.length > 0;
  const hasTimeline = timelineData.length > 1;

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
            <Badge variant="outline" className="text-xs">
              共 {totalCount} 项
            </Badge>
            {unfixedCount > 0 && (
              <Button
                size="sm"
                variant="outline"
                className="ml-auto gap-1.5"
                onClick={handleFixAll}
                disabled={isPolishing}
              >
                {isPolishing ? (
                  <>
                    <Loader2 className="size-3.5 animate-spin" />
                    {polishProgress ? `修复中 ${polishProgress.index}` : "修复中..."}
                  </>
                ) : (
                  <>
                    <Wand2 className="size-3.5" />
                    一键修复 ({unfixedCount})
                  </>
                )}
              </Button>
            )}
            {polishError && (
              <span className="text-xs text-red-400 ml-2">{polishError}</span>
            )}
          </div>

          {/* Metrics charts */}
          {hasMetrics && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">7 维评分雷达图</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <RadarChart data={radarData}>
                      <PolarGrid stroke="hsl(var(--border))" />
                      <PolarAngleAxis
                        dataKey="dimension"
                        tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                      />
                      <PolarRadiusAxis
                        angle={30}
                        domain={[0, 100]}
                        tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }}
                      />
                      <Radar
                        name="评分"
                        dataKey="score"
                        stroke="hsl(45 93% 47%)"
                        fill="hsl(45 93% 47%)"
                        fillOpacity={0.2}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {hasTimeline ? (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">评分趋势</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={timelineData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                        <XAxis dataKey="time" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }} />
                        <YAxis domain={[0, 100]} tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }} />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "hsl(var(--background))",
                            border: "1px solid hsl(var(--border))",
                            borderRadius: "0.5rem",
                            fontSize: "0.75rem",
                          }}
                        />
                        <Legend wrapperStyle={{ fontSize: "0.7rem" }} />
                        <Line type="monotone" dataKey="aiFlavor" name="AI味" stroke="#ef4444" strokeWidth={2} dot={false} />
                        <Line type="monotone" dataKey="consistency" name="一致性" stroke="#22c55e" strokeWidth={2} dot={false} />
                        <Line type="monotone" dataKey="coherence" name="连贯性" stroke="#3b82f6" strokeWidth={2} dot={false} />
                        <Line type="monotone" dataKey="logic" name="逻辑" stroke="#8b5cf6" strokeWidth={2} dot={false} />
                        <Line type="monotone" dataKey="ooc" name="OOC" stroke="#f59e0b" strokeWidth={2} dot={false} />
                        <Line type="monotone" dataKey="timeline" name="时间线" stroke="#06b6d4" strokeWidth={2} dot={false} />
                        <Line type="monotone" dataKey="foreshadowing" name="伏笔" stroke="#ec4899" strokeWidth={2} dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              ) : (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">各维度详情</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {radarData.map((item) => (
                        <div key={item.dimension} className="flex items-center gap-2">
                          <span className="text-xs text-muted-foreground w-20 shrink-0">{item.dimension}</span>
                          <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                            <div
                              className="h-full bg-amber-500 rounded-full transition-all"
                              style={{ width: `${item.score}%` }}
                            />
                          </div>
                          <span className="text-xs font-mono w-8 text-right">{item.score}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}

          {/* Polish diff preview */}
          {polishDiffs.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-sm font-medium">润色差异预览</h3>
              {polishDiffs.map((pd) => (
                <div key={pd.issueId} className="p-4 rounded-lg border bg-muted/20">
                  <p className="text-sm font-medium mb-2">{pd.issueTitle}</p>
                  {pd.summary && (
                    <p className="text-xs text-muted-foreground mb-3">{pd.summary}</p>
                  )}
                  <div className="space-y-2">
                    {pd.diffs.map((d, di) => (
                      <div key={di} className="text-xs space-y-1">
                        <span className="text-muted-foreground">轴：{d.axis}</span>
                        <div className="grid grid-cols-1 gap-1">
                          <div className="p-2 rounded bg-red-500/10 border border-red-500/20">
                            <span className="text-red-400 font-medium">- </span>
                            <span className="line-through text-muted-foreground">{d.before}</span>
                          </div>
                          <div className="p-2 rounded bg-emerald-500/10 border border-emerald-500/20">
                            <span className="text-emerald-400 font-medium">+ </span>
                            <span>{d.after}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

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
