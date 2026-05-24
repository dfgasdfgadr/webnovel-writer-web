import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft, Play, Loader2, CheckCircle, XCircle,
  AlertTriangle, RefreshCw, FlaskConical, GitBranch,
  Clock, ChevronRight, ClipboardCheck,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { EmptyState } from "@/components/layout/EmptyState";
import { ProjectNav } from "@/components/layout/ProjectNav";
import { toast } from "sonner";
import * as api from "@/lib/api";

interface SimJob {
  id: string;
  project_id: string;
  mode: string;
  status: string;
  progress: number;
  mirofish_available: boolean;
  report: Record<string, unknown> | null;
  steps: Array<{ step: string; status: string; description: string }> | null;
  error_message: string | null;
  created_at: string;
}

function requestSimulations<T>(path: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem("token");
  return fetch(`/api/v1/simulations${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options?.headers || {}),
    },
  }).then(async (res) => {
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Request failed");
    return data as T;
  });
}

export function SimulationCenter() {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();

  const [mode, setMode] = useState<"pre_chapter" | "branch_explore">("pre_chapter");
  const [simBrief, setSimBrief] = useState("");
  const [selectedSim, setSelectedSim] = useState<string | null>(null);

  const { data: project } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => api.getProject(projectId!),
    enabled: !!projectId,
  });

  const { data: simJobs, isLoading } = useQuery({
    queryKey: ["simulations", projectId],
    queryFn: () => requestSimulations<SimJob[]>(`?project_id=${projectId}`),
    enabled: !!projectId,
  });

  const { data: simDetail } = useQuery({
    queryKey: ["simulation", selectedSim],
    queryFn: () => requestSimulations<SimJob>(`/${selectedSim}`),
    enabled: !!selectedSim,
  });

  const createSim = useMutation({
    mutationFn: () =>
      requestSimulations<SimJob>("", {
        method: "POST",
        body: JSON.stringify({
          project_id: projectId,
          mode,
          sim_brief: simBrief,
        }),
      }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["simulations", projectId] });
      setSelectedSim(data.id);
      setSimBrief("");
      if (data.mirofish_available) {
        toast.success("推演任务已提交");
      } else {
        toast.warning("MiroFish 不可用，推演已记录为失败。");
      }
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "创建失败"),
  });

  const modeLabel = (m: string) => (m === "pre_chapter" ? "写前推演" : "分支探索");
  const statusBadge = (status: string) => {
    const map: Record<string, { variant: "default" | "destructive" | "outline"; label: string }> = {
      pending: { variant: "outline", label: "等待中" },
      running: { variant: "default", label: "运行中" },
      completed: { variant: "default", label: "已完成" },
      failed: { variant: "destructive", label: "失败" },
    };
    const s = map[status] || { variant: "outline" as const, label: status };
    return <Badge variant={s.variant}>{s.label}</Badge>;
  };

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
        <h1 className="font-serif text-2xl font-semibold">推演中心</h1>
        {project && (
          <p className="text-sm text-muted-foreground mt-1">{project.title}</p>
        )}
      </div>
      <ProjectNav projectId={projectId!} active="simulations" className="mb-2" />

      <Tabs defaultValue="new">
        <TabsList>
          <TabsTrigger value="new">新建推演</TabsTrigger>
          <TabsTrigger value="history">
            推演历史
            {simJobs && simJobs.length > 0 && (
              <span className="ml-1.5 text-xs bg-muted rounded-full px-1.5 py-0.5">
                {simJobs.length}
              </span>
            )}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="new" className="mt-4">
          <div className="grid grid-cols-[1fr_360px] gap-4">
            <Card>
              <CardHeader>
                <CardTitle>新建推演任务</CardTitle>
                <CardDescription>
                  选择推演模式并描述你想模拟的剧情走向
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-4">
                  <button
                    onClick={() => setMode("pre_chapter")}
                    className={`flex-1 p-4 rounded-lg border-2 text-left transition-colors ${
                      mode === "pre_chapter"
                        ? "border-amber-400 bg-amber-500/10"
                        : "border-border hover:border-muted-foreground"
                    }`}
                  >
                    <FlaskConical className="size-5 mb-2 text-amber-400" />
                    <h3 className="font-medium text-sm">写前推演</h3>
                    <p className="text-xs text-muted-foreground mt-1">
                      写新章前模拟剧情发展，评估合理性与影响
                    </p>
                  </button>
                  <button
                    onClick={() => setMode("branch_explore")}
                    className={`flex-1 p-4 rounded-lg border-2 text-left transition-colors ${
                      mode === "branch_explore"
                        ? "border-amber-400 bg-amber-500/10"
                        : "border-border hover:border-muted-foreground"
                    }`}
                  >
                    <GitBranch className="size-5 mb-2 text-amber-400" />
                    <h3 className="font-medium text-sm">分支探索</h3>
                    <p className="text-xs text-muted-foreground mt-1">
                      对比不同分支走向的多角色推演
                    </p>
                  </button>
                </div>

                <div className="space-y-2">
                  <Label>推演需求</Label>
                  <Textarea
                    placeholder="用自然语言描述推演需求：&#10;例如：主角在第5章结束后有两条路可选——加入宗门或独自修炼。请模拟两条路线的后续影响..."
                    value={simBrief}
                    onChange={(e) => setSimBrief(e.target.value)}
                    rows={6}
                  />
                </div>

                <Button
                  className="w-full"
                  onClick={() => createSim.mutate()}
                  disabled={!simBrief.trim() || createSim.isPending}
                >
                  {createSim.isPending ? (
                    <Loader2 className="size-4 mr-2 animate-spin" />
                  ) : (
                    <Play className="size-4 mr-2" />
                  )}
                  开始推演
                </Button>
              </CardContent>
            </Card>

            {/* Result panel */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">推演报告</CardTitle>
              </CardHeader>
              <CardContent>
                {simDetail ? (
                  <ScrollArea className="h-[500px]">
                    <div className="space-y-4">
                      <div className="flex items-center gap-2">
                        {statusBadge(simDetail.status)}
                        <Badge variant="outline">{modeLabel(simDetail.mode)}</Badge>
                      </div>

                      {!simDetail.mirofish_available && (
                        <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 text-sm text-muted-foreground">
                          <AlertTriangle className="size-4 inline mr-1 text-amber-400" />
                          MiroFish 服务不可用。请确保 Docker 已启动。其余功能不受影响。
                        </div>
                      )}

                      {simDetail.error_message && (
                        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-sm text-red-400">
                          {simDetail.error_message}
                        </div>
                      )}

                      {simDetail.steps && simDetail.steps.length > 0 && (
                        <div className="space-y-2">
                          <h4 className="text-sm font-medium">推演步骤</h4>
                          {simDetail.steps.map((step, i) => (
                            <div key={i} className="flex items-start gap-2 text-sm">
                              {step.status === "completed" ? (
                                <CheckCircle className="size-4 text-emerald-400 mt-0.5 shrink-0" />
                              ) : step.status === "failed" ? (
                                <XCircle className="size-4 text-red-400 mt-0.5 shrink-0" />
                              ) : (
                                <Clock className="size-4 text-muted-foreground mt-0.5 shrink-0" />
                              )}
                              <div>
                                <span className="font-medium">{step.step}</span>
                                <p className="text-xs text-muted-foreground">{step.description}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}

                      {simDetail.report && (
                        <div className="space-y-2">
                          <Separator />
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-muted-foreground">推演报告</span>
                            <Button
                              size="sm"
                              variant="outline"
                              className="text-xs text-amber-400"
                              onClick={async () => {
                                try {
                                  const res = await requestSimulations<{ success: boolean }>(`/${selectedSim}/adopt`, { method: "POST" });
                                  if (res.success) toast.success("已采纳修订章纲");
                                } catch (err) {
                                  toast.error(err instanceof Error ? err.message : "采纳失败");
                                }
                              }}
                            >
                              <ClipboardCheck className="size-3 mr-1" />
                              采纳修订章纲
                            </Button>
                          </div>
                          <pre className="text-xs text-muted-foreground whitespace-pre-wrap font-mono">
                            {JSON.stringify(simDetail.report, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  </ScrollArea>
                ) : (
                  <EmptyState
                    icon={FlaskConical}
                    title="尚未创建推演"
                    description="创建推演任务后，报告将在此显示。"
                  />
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="history" className="mt-4">
          {isLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
            </div>
          ) : !simJobs || simJobs.length === 0 ? (
            <EmptyState
              icon={FlaskConical}
              title="暂无推演记录"
              description="创建推演任务后，历史记录将在此显示。"
            />
          ) : (
            <div className="space-y-3">
              {simJobs.map((job) => (
                <Card
                  key={job.id}
                  className={`cursor-pointer transition-colors hover:bg-muted/50 ${
                    selectedSim === job.id ? "ring-2 ring-amber-400" : ""
                  }`}
                  onClick={() => setSelectedSim(job.id)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {job.mode === "pre_chapter" ? (
                          <FlaskConical className="size-4 text-amber-400" />
                        ) : (
                          <GitBranch className="size-4 text-amber-400" />
                        )}
                        <div>
                          <p className="text-sm font-medium">{modeLabel(job.mode)}</p>
                          <p className="text-xs text-muted-foreground">
                            {new Date(job.created_at).toLocaleString()}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {statusBadge(job.status)}
                        <ChevronRight className="size-4 text-muted-foreground" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
