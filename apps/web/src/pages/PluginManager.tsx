import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Puzzle, Loader2, Power, PowerOff, Download, RefreshCw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { EmptyState } from "@/components/layout/EmptyState";
import * as api from "@/lib/api";
import { toast } from "sonner";

export function PluginManager() {
  const queryClient = useQueryClient();
  const [toggling, setToggling] = useState<string | null>(null);
  const [loading, setLoading] = useState<string | null>(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["plugins"],
    queryFn: api.listPlugins,
  });

  const toggleMut = useMutation({
    mutationFn: ({ name, enabled }: { name: string; enabled: boolean }) =>
      api.togglePlugin(name, enabled),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["plugins"] });
      setToggling(null);
      toast.success("插件状态已更新");
    },
    onError: (err) => {
      setToggling(null);
      toast.error(err instanceof Error ? err.message : "操作失败");
    },
  });

  const loadMut = useMutation({
    mutationFn: (name: string) => api.loadPlugin(name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["plugins"] });
      setLoading(null);
      toast.success("插件已加载");
    },
    onError: (err) => {
      setLoading(null);
      toast.error(err instanceof Error ? err.message : "加载失败");
    },
  });

  const reloadMut = useMutation({
    mutationFn: api.reloadPlugins,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["plugins"] });
      toast.success(`已重新扫描，发现 ${data.discovered} 个插件`);
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "重新加载失败"),
  });

  const plugins = data?.plugins ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-serif text-2xl font-semibold">插件管理</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {data ? `${data.total} 个插件` : "加载中..."}
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => reloadMut.mutate()}
          disabled={reloadMut.isPending}
        >
          {reloadMut.isPending ? (
            <Loader2 className="size-4 mr-1.5 animate-spin" />
          ) : (
            <RefreshCw className="size-4 mr-1.5" />
          )}
          重新扫描
        </Button>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      ) : isError ? (
        <EmptyState
          title="加载失败"
          description="无法获取插件列表，请确认 API 服务是否正常运行。"
        />
      ) : plugins.length === 0 ? (
        <EmptyState
          icon={Puzzle}
          title="暂无插件"
          description="在 plugins/agents/ 目录下放置插件并包含 agent.yaml 配置后，点击重新扫描。"
        />
      ) : (
        <div className="grid gap-4">
          {plugins.map((plugin) => (
            <Card key={plugin.name} className={!plugin.enabled ? "opacity-60" : ""}>
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <Puzzle className="size-4 text-amber-400" />
                    <CardTitle className="text-base">{plugin.display_name}</CardTitle>
                    <Badge variant="outline" className="text-[10px]">
                      v{plugin.version}
                    </Badge>
                    {plugin.loaded && (
                      <Badge variant="default" className="text-[10px]">已加载</Badge>
                    )}
                    {!plugin.enabled && (
                      <Badge variant="secondary" className="text-[10px]">已禁用</Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setToggling(plugin.name);
                        toggleMut.mutate({ name: plugin.name, enabled: !plugin.enabled });
                      }}
                      disabled={toggling === plugin.name}
                    >
                      {toggling === plugin.name ? (
                        <Loader2 className="size-3.5 animate-spin" />
                      ) : plugin.enabled ? (
                        <PowerOff className="size-3.5" />
                      ) : (
                        <Power className="size-3.5" />
                      )}
                      <span className="ml-1 text-xs">
                        {plugin.enabled ? "禁用" : "启用"}
                      </span>
                    </Button>
                    {!plugin.loaded && plugin.enabled && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setLoading(plugin.name);
                          loadMut.mutate(plugin.name);
                        }}
                        disabled={loading === plugin.name}
                      >
                        {loading === plugin.name ? (
                          <Loader2 className="size-3.5 animate-spin" />
                        ) : (
                          <Download className="size-3.5" />
                        )}
                        <span className="ml-1 text-xs">加载</span>
                      </Button>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-xs">{plugin.description}</CardDescription>
                <div className="flex items-center gap-2 mt-2 flex-wrap">
                  <span className="text-[10px] text-muted-foreground">作者：{plugin.author}</span>
                  {plugin.triggers.length > 0 && (
                    <div className="flex items-center gap-1">
                      {plugin.triggers.map((t) => (
                        <Badge key={t} variant="outline" className="text-[10px]">{t}</Badge>
                      ))}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
