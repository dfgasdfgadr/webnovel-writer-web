import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  GitBranch, Zap, History, Shield, CheckCircle, AlertTriangle,
  Clock, XCircle, Loader2, ChevronDown,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import {
  Card, CardContent, CardHeader, CardTitle, CardDescription,
} from "@/components/ui/card";
import { EmptyState } from "@/components/layout/EmptyState";
import * as api from "@/lib/api";
import { toast } from "sonner";

interface WorkflowRule {
  name: string;
  trigger: string;
  enabled: boolean;
  actions: Array<{ name: string; type: string; config: Record<string, unknown> }>;
  condition: Record<string, unknown>;
}

const TRIGGER_LABELS: Record<string, string> = {
  onChapterAccepted: "章节通过后",
  onProjectCreate: "项目创建后",
};

const ACTION_TYPE_LABELS: Record<string, string> = {
  sim: "推演",
  notify: "通知",
  git_backup: "Git 备份",
  custom: "自定义",
};

const STATUS_ICONS: Record<string, React.ElementType> = {
  completed: CheckCircle,
  no_changes: Clock,
  error: XCircle,
  skipped: AlertTriangle,
  never_run: Clock,
};

const STATUS_COLORS: Record<string, string> = {
  completed: "text-green-500",
  no_changes: "text-amber-500",
  error: "text-destructive",
  skipped: "text-muted-foreground",
  never_run: "text-muted-foreground",
};

export function WorkflowView() {
  const queryClient = useQueryClient();
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");

  const { data, isLoading, isError } = useQuery({
    queryKey: ["workflows"],
    queryFn: api.listWorkflows,
  });

  const { data: projectsData } = useQuery({
    queryKey: ["projects"],
    queryFn: api.listProjects,
  });

  const { data: backupStatus } = useQuery({
    queryKey: ["backup-status", selectedProjectId],
    queryFn: () => api.getBackupStatus(selectedProjectId),
    enabled: !!selectedProjectId,
  });

  const { data: historyData } = useQuery({
    queryKey: ["workflow-history", selectedProjectId],
    queryFn: () => api.getWorkflowHistory(selectedProjectId, 10),
    enabled: !!selectedProjectId,
  });

  const toggleMutation = useMutation({
    mutationFn: ({ name, enabled }: { name: string; enabled: boolean }) =>
      api.toggleWorkflowRule(name, enabled),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflows"] });
      toast.success("规则状态已更新");
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "更新失败"),
  });

  const rules = data?.rules ?? [];
  const projects = projectsData?.items ?? [];
  const runs = historyData?.runs ?? [];

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="font-serif text-2xl font-semibold">工作流规则</h1>
        <p className="text-sm text-muted-foreground mt-1">
          管理工作流规则的启停、查看执行历史和备份状态
        </p>
      </div>

      {/* Rules */}
      {isLoading ? (
        <div className="space-y-3">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      ) : isError ? (
        <EmptyState title="加载失败" description="无法获取工作流规则列表。" />
      ) : rules.length === 0 ? (
        <EmptyState
          icon={GitBranch}
          title="暂无工作流规则"
          description="工作流规则定义在引擎内置规则和插件 YAML 文件中。"
        />
      ) : (
        <div className="grid gap-4">
          {rules.map((rule) => (
            <WorkflowRuleCard
              key={rule.name}
              rule={rule}
              isToggling={toggleMutation.isPending}
              onToggle={(enabled) => toggleMutation.mutate({ name: rule.name, enabled })}
            />
          ))}
        </div>
      )}

      {/* Backup Status */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base flex items-center gap-2">
            <Shield className="size-4 text-primary" />
            备份状态
          </CardTitle>
          <CardDescription>
            查看项目的 Git 自动备份状态
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">选择项目</label>
            <div className="relative">
              <select
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(e.target.value)}
                className="w-full h-9 rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              >
                <option value="">请选择项目...</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.title}
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none" />
            </div>
          </div>

          {selectedProjectId && backupStatus && (
            <div className="rounded-lg border p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">自动备份</span>
                <Badge variant={backupStatus.enabled ? "default" : "secondary"}>
                  {backupStatus.enabled ? "已启用" : "已禁用"}
                </Badge>
              </div>
              <div className="flex items-center gap-3">
                {(() => {
                  const Icon = STATUS_ICONS[backupStatus.status] || Clock;
                  const color = STATUS_COLORS[backupStatus.status] || "text-muted-foreground";
                  return <Icon className={`size-5 ${color}`} />;
                })()}
                <div>
                  <p className="text-sm font-medium">
                    {backupStatus.status === "completed" && "备份成功"}
                    {backupStatus.status === "no_changes" && "无变更需备份"}
                    {backupStatus.status === "error" && "备份出错"}
                    {backupStatus.status === "skipped" && "已跳过"}
                    {backupStatus.status === "never_run" && "尚未执行"}
                    {backupStatus.status === "no_root_dir" && "无项目目录"}
                  </p>
                  {backupStatus.last_run && (
                    <p className="text-xs text-muted-foreground">
                      最近执行：{new Date(backupStatus.last_run).toLocaleString("zh-CN")}
                      {backupStatus.chapter_num !== undefined && ` · 章节 ${backupStatus.chapter_num}`}
                    </p>
                  )}
                  {backupStatus.reason && (
                    <p className="text-xs text-muted-foreground mt-1">
                      原因：{backupStatus.reason}
                    </p>
                  )}
                </div>
              </div>
              {backupStatus.total_runs !== undefined && (
                <p className="text-xs text-muted-foreground">
                  累计执行 {backupStatus.total_runs} 次
                </p>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Execution History */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base flex items-center gap-2">
            <History className="size-4 text-primary" />
            执行历史
          </CardTitle>
          <CardDescription>
            最近的工作流触发记录
          </CardDescription>
        </CardHeader>
        <CardContent>
          {!selectedProjectId ? (
            <p className="text-sm text-muted-foreground">请先选择项目</p>
          ) : !historyData ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" />
              加载中...
            </div>
          ) : runs.length === 0 ? (
            <EmptyState
              icon={History}
              title="暂无执行记录"
              description="该项目的章节通过后触发工作流时，将在此显示记录。"
              className="py-6"
            />
          ) : (
            <div className="space-y-2">
              {runs.map((run, i) => {
                const Icon = STATUS_ICONS[run.status] || Clock;
                const color = STATUS_COLORS[run.status] || "text-muted-foreground";
                return (
                  <div
                    key={i}
                    className="flex items-start gap-3 p-3 rounded-md bg-muted/30 text-sm"
                  >
                    <Icon className={`size-4 mt-0.5 ${color}`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-medium">{run.action}</span>
                        <Badge variant="outline" className="text-[10px]">
                          {run.status}
                        </Badge>
                        {run.chapter_num !== undefined && (
                          <Badge variant="secondary" className="text-[10px]">
                            章节 {run.chapter_num}
                          </Badge>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        {new Date(run.timestamp).toLocaleString("zh-CN")}
                      </p>
                      {run.reason && (
                        <p className="text-xs text-muted-foreground mt-1">
                          {run.reason}
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function WorkflowRuleCard({
  rule,
  isToggling,
  onToggle,
}: {
  rule: WorkflowRule;
  isToggling: boolean;
  onToggle: (enabled: boolean) => void;
}) {
  return (
    <Card className={!rule.enabled ? "opacity-60" : ""}>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2 flex-wrap">
            <GitBranch className="size-4 text-amber-400" />
            <CardTitle className="text-base">{rule.name}</CardTitle>
            <Badge variant={rule.enabled ? "default" : "secondary"} className="text-[10px]">
              {rule.enabled ? "启用" : "禁用"}
            </Badge>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-[10px]">
              {TRIGGER_LABELS[rule.trigger] || rule.trigger}
            </Badge>
            <Switch
              checked={rule.enabled}
              disabled={isToggling}
              onCheckedChange={onToggle}
              aria-label={`${rule.enabled ? "禁用" : "启用"} ${rule.name}`}
            />
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <CardDescription className="text-xs mb-3">
          触发器：
          <code className="text-[11px] bg-muted px-1 rounded">{rule.trigger}</code>
          {Object.keys(rule.condition).length > 0 && (
            <span className="ml-2">
              条件：
              <code className="text-[11px] bg-muted px-1 rounded">
                {JSON.stringify(rule.condition)}
              </code>
            </span>
          )}
        </CardDescription>

        {rule.actions.length > 0 && (
          <div className="space-y-2">
            <span className="text-xs font-medium text-muted-foreground">动作列表</span>
            {rule.actions.map((action) => (
              <div
                key={action.name}
                className="flex items-start gap-2 p-2 rounded bg-muted/30 border text-sm"
              >
                <Zap className="size-3.5 text-amber-400 mt-0.5 shrink-0" />
                <div className="min-w-0">
                  <span className="font-medium text-xs">{action.name}</span>
                  <Badge variant="outline" className="text-[10px] ml-1.5">
                    {ACTION_TYPE_LABELS[action.type] || action.type}
                  </Badge>
                  {Object.keys(action.config).length > 0 && (
                    <pre className="text-[10px] text-muted-foreground mt-1 whitespace-pre-wrap">
                      {JSON.stringify(action.config, null, 2)}
                    </pre>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
