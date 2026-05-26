import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Plus, Trash2, Loader2, Sparkles, BookOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/layout/EmptyState";
import { ProjectNav } from "@/components/layout/ProjectNav";
import * as api from "@/lib/api";
import { toast } from "sonner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from "@/components/ui/dialog";

export function SummariesPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("chapter");
  const [showCreate, setShowCreate] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [formTitle, setFormTitle] = useState("");
  const [formContent, setFormContent] = useState("");
  const [formScope, setFormScope] = useState("");

  const { data: summaries, isLoading } = useQuery({
    queryKey: ["summaries", projectId, activeTab],
    queryFn: () => api.listSummaries(projectId!, activeTab),
    enabled: !!projectId,
  });

  const { data: project } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => api.getProject(projectId!),
    enabled: !!projectId,
  });

  const createMut = useMutation({
    mutationFn: (data: api.SummaryCreateRequest) => api.createSummary(projectId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["summaries", projectId] });
      setShowCreate(false);
      resetForm();
      toast.success("摘要已创建");
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "创建失败"),
  });

  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: string; data: api.SummaryUpdateRequest }) =>
      api.updateSummary(projectId!, id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["summaries", projectId] });
      setEditId(null);
      resetForm();
      toast.success("摘要已更新");
    },
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => api.deleteSummary(projectId!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["summaries", projectId] });
      toast.success("摘要已删除");
    },
  });

  const genMut = useMutation({
    mutationFn: (level: string) =>
      api.generateSummary(projectId!, {
        level,
        scope_label: level === "volume" ? "卷摘要" : "弧摘要",
      }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["summaries", projectId] });
      toast.success(`${activeTab === "volume" ? "卷" : "弧"}摘要已生成`, {
        description: `关键事件: ${data.key_events?.length || 0} 项`,
      });
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "生成失败，请检查 LLM 配置"),
  });

  const resetForm = () => {
    setFormTitle("");
    setFormContent("");
    setFormScope("");
  };

  const handleEdit = (s: api.SummaryPublic) => {
    setEditId(s.id);
    setFormTitle(s.title || "");
    setFormContent(s.content || "");
    setFormScope(s.scope_label || "");
  };

  const handleSave = () => {
    if (editId) {
      updateMut.mutate({ id: editId, data: { title: formTitle, content: formContent } });
    } else {
      if (!formScope.trim()) return;
      createMut.mutate({
        level: activeTab as "volume" | "arc" | "chapter",
        scope_label: formScope.trim(),
        title: formTitle,
        content: formContent,
      });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 flex-wrap">
        <Link to={`/projects/${projectId}`}>
          <Button variant="ghost" size="sm">
            <ArrowLeft className="size-4 mr-1" />
            返回
          </Button>
        </Link>
        <h1 className="text-2xl font-serif font-semibold tracking-tight">三级摘要</h1>
        {project && <span className="text-sm text-muted-foreground">{project.title}</span>}
      </div>
      {projectId && <ProjectNav projectId={projectId} active="summaries" />}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <div className="flex items-center justify-between mb-4">
          <TabsList>
            <TabsTrigger value="chapter">章</TabsTrigger>
            <TabsTrigger value="arc">故事弧</TabsTrigger>
            <TabsTrigger value="volume">卷</TabsTrigger>
          </TabsList>
          <div className="flex gap-2">
            {(activeTab === "volume" || activeTab === "arc") && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => genMut.mutate(activeTab)}
                disabled={genMut.isPending}
              >
                {genMut.isPending ? (
                  <Loader2 className="size-3.5 mr-1 animate-spin" />
                ) : (
                  <Sparkles className="size-3.5 mr-1" />
                )}
                AI 生成
              </Button>
            )}
            <Button size="sm" variant="outline" onClick={() => { setEditId(null); resetForm(); setShowCreate(true); }}>
              <Plus className="size-3.5 mr-1" />
              新建摘要
            </Button>
          </div>
        </div>

        {["chapter", "arc", "volume"].map((level) => (
          <TabsContent key={level} value={level}>
            {isLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => <Skeleton key={i} className="h-24" />)}
              </div>
            ) : !summaries || summaries.length === 0 ? (
              <EmptyState
                icon={BookOpen}
                title={`暂无${level === "volume" ? "卷" : level === "arc" ? "弧" : "章"}摘要`}
                description={level !== "chapter" ? "可点击「AI 生成」自动生成" : "添加章级摘要以构建聚合层级"}
              />
            ) : (
              <div className="space-y-3">
                {summaries.map((s) => (
                  <Card key={s.id} className="group">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm flex items-center justify-between">
                        <span>{s.title || s.scope_label}</span>
                        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 text-xs"
                            onClick={() => handleEdit(s)}
                          >
                            编辑
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="size-7"
                            onClick={() => deleteMut.mutate(s.id)}
                          >
                            <Trash2 className="size-3.5 text-muted-foreground hover:text-red-400" />
                          </Button>
                        </div>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-xs text-muted-foreground whitespace-pre-wrap line-clamp-6">
                        {s.content}
                      </p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>
        ))}
      </Tabs>

      <Dialog open={showCreate || editId !== null} onOpenChange={(open) => { if (!open) { setShowCreate(false); setEditId(null); resetForm(); } }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editId ? "编辑摘要" : "新建摘要"}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {!editId && (
              <div className="space-y-2">
                <Label htmlFor="sum-scope">范围标签</Label>
                <Input
                  id="sum-scope"
                  value={formScope}
                  onChange={(e) => setFormScope(e.target.value)}
                  placeholder="如：第一卷、第一章、序幕弧"
                />
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="sum-title">标题</Label>
              <Input
                id="sum-title"
                value={formTitle}
                onChange={(e) => setFormTitle(e.target.value)}
                placeholder="摘要标题"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="sum-content">内容</Label>
              <Textarea
                id="sum-content"
                value={formContent}
                onChange={(e) => setFormContent(e.target.value)}
                placeholder="摘要内容"
                className="h-40 resize-none"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => { setShowCreate(false); setEditId(null); resetForm(); }}>取消</Button>
            <Button onClick={handleSave} disabled={(!editId && !formScope.trim()) || createMut.isPending || updateMut.isPending}>
              {(createMut.isPending || updateMut.isPending) ? <Loader2 className="size-4 animate-spin" /> : "保存"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
