import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Save, RotateCcw, Loader2, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import * as api from "@/lib/api";
import { useParams, useNavigate } from "react-router-dom";

const SCOPE_LABELS: Record<string, string> = {
  reader_pulse: "读者模拟",
  review: "审查",
  polish: "润色",
};

const SCOPE_DESCRIPTIONS: Record<string, string> = {
  reader_pulse: "ReaderPulseSim 的系统 prompt，控制读者模拟的评估维度与语气",
  review: "ReviewAgent 的系统 prompt，控制 7 维审查的严格度与侧重点",
  polish: "PolishAgent 的系统 prompt，控制 8 轴润色的风格偏好",
};

export function PromptWorkshop() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("reader_pulse");
  const [edits, setEdits] = useState<Record<string, string>>({});

  const { data, isLoading, isError } = useQuery({
    queryKey: ["projectPrompts", projectId],
    queryFn: () => api.getProjectPrompts(projectId!),
    enabled: !!projectId,
  });

  const saveMut = useMutation({
    mutationFn: ({ scope, key, content }: { scope: string; key: string; content: string }) =>
      api.updateProjectPrompt(projectId!, scope, key, content),
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({ queryKey: ["projectPrompts", projectId] });
      toast.success(`${SCOPE_LABELS[vars.scope] || vars.scope} prompt 已保存`);
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "保存失败"),
  });

  const resetMut = useMutation({
    mutationFn: ({ scope, key }: { scope: string; key: string }) =>
      api.resetProjectPrompt(projectId!, scope, key),
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({ queryKey: ["projectPrompts", projectId] });
      setEdits((prev) => {
        const next = { ...prev };
        delete next[`${vars.scope}/${vars.key}`];
        return next;
      });
      toast.success(`${SCOPE_LABELS[vars.scope] || vars.scope} prompt 已恢复默认`);
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "恢复失败"),
  });

  const prompts = data?.prompts ?? [];
  const currentPrompt = prompts.find((p) => p.scope === activeTab);
  const editKey = `${activeTab}/system_prompt`;
  const editValue = edits[editKey] ?? currentPrompt?.content ?? "";

  const handleSave = () => {
    saveMut.mutate({ scope: activeTab, key: "system_prompt", content: editValue });
  };

  const handleReset = () => {
    if (currentPrompt?.is_default) {
      toast.info("已经是默认值，无需恢复");
      return;
    }
    resetMut.mutate({ scope: activeTab, key: "system_prompt" });
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] flex flex-col max-w-4xl mx-auto">
      <div className="flex items-center gap-3 px-4 py-3 border-b">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
          <ArrowLeft className="size-4" />
        </Button>
        <div className="flex-1">
          <h1 className="text-lg font-semibold">Prompt 工坊</h1>
          <p className="text-xs text-muted-foreground">
            管理项目级 Agent 的 system prompt 覆盖
          </p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {isLoading && (
          <div className="space-y-4">
            <Skeleton className="h-10 w-64" />
            <Skeleton className="h-48 w-full" />
          </div>
        )}

        {isError && (
          <div className="text-center space-y-4 py-12">
            <p className="text-muted-foreground">加载失败</p>
            <Button variant="outline" onClick={() => queryClient.invalidateQueries({ queryKey: ["projectPrompts", projectId] })}>
              重试
            </Button>
          </div>
        )}

        {!isLoading && !isError && (
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="mb-4">
              {Object.entries(SCOPE_LABELS).map(([scope, label]) => (
                <TabsTrigger key={scope} value={scope} className="text-sm">
                  {label}
                </TabsTrigger>
              ))}
            </TabsList>

            {Object.keys(SCOPE_LABELS).map((scope) => (
              <TabsContent key={scope} value={scope} className="space-y-4">
                <Card>
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-base">
                        {SCOPE_LABELS[scope]} System Prompt
                      </CardTitle>
                      <Badge variant={currentPrompt?.is_default ? "secondary" : "default"} className="text-xs">
                        {currentPrompt?.is_default ? "默认" : "自定义"}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {SCOPE_DESCRIPTIONS[scope]}
                    </p>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <Textarea
                      value={editValue}
                      onChange={(e) => setEdits((prev) => ({ ...prev, [`${scope}/system_prompt`]: e.target.value }))}
                      rows={12}
                      className="font-mono text-xs"
                      placeholder="输入自定义 system prompt..."
                    />
                    <div className="flex justify-end gap-3">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleReset}
                        disabled={resetMut.isPending || currentPrompt?.is_default}
                      >
                        {resetMut.isPending ? (
                          <Loader2 className="size-4 mr-1 animate-spin" />
                        ) : (
                          <RotateCcw className="size-4 mr-1" />
                        )}
                        恢复默认
                      </Button>
                      <Button
                        size="sm"
                        onClick={handleSave}
                        disabled={saveMut.isPending || !editValue.trim()}
                      >
                        {saveMut.isPending ? (
                          <Loader2 className="size-4 mr-1 animate-spin" />
                        ) : (
                          <Save className="size-4 mr-1" />
                        )}
                        保存
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            ))}
          </Tabs>
        )}
      </div>
    </div>
  );
}
