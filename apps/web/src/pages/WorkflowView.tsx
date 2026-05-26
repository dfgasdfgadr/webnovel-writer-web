import { useQuery } from "@tanstack/react-query";
import { GitBranch, Zap } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { EmptyState } from "@/components/layout/EmptyState";
import * as api from "@/lib/api";

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
  custom: "自定义",
};

export function WorkflowView() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["workflows"],
    queryFn: api.listWorkflows,
  });

  const rules = data?.rules ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-serif text-2xl font-semibold">工作流规则</h1>
        <p className="text-sm text-muted-foreground mt-1">
          查看当前生效的工作流规则与触发条件
        </p>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      ) : isError ? (
        <EmptyState
          title="加载失败"
          description="无法获取工作流规则列表。"
        />
      ) : rules.length === 0 ? (
        <EmptyState
          icon={GitBranch}
          title="暂无工作流规则"
          description="工作流规则定义在引擎内置规则和插件 YAML 文件中。"
        />
      ) : (
        <div className="grid gap-4">
          {rules.map((rule) => (
            <Card key={rule.name} className={!rule.enabled ? "opacity-60" : ""}>
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <GitBranch className="size-4 text-amber-400" />
                    <CardTitle className="text-base">{rule.name}</CardTitle>
                    <Badge variant={rule.enabled ? "default" : "secondary"} className="text-[10px]">
                      {rule.enabled ? "启用" : "禁用"}
                    </Badge>
                  </div>
                  <Badge variant="outline" className="text-[10px]">
                    {TRIGGER_LABELS[rule.trigger] || rule.trigger}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-xs mb-3">
                  触发器：<code className="text-[11px] bg-muted px-1 rounded">{rule.trigger}</code>
                  {Object.keys(rule.condition).length > 0 && (
                    <span className="ml-2">
                      条件：<code className="text-[11px] bg-muted px-1 rounded">
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
          ))}
        </div>
      )}
    </div>
  );
}
