import { useState, useCallback, useRef, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft, Loader2, Plus, Save, Trash2, FileText,
  Sparkles, Play, PanelRightOpen, PanelRightClose,
  AlertTriangle, AlertCircle, Info, ChevronDown, ChevronUp,
  ExternalLink, ClipboardCheck, FlaskConical, Network,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import {
  Dialog, DialogContent, DialogDescription,
  DialogHeader, DialogTitle, DialogTrigger,
} from "@/components/ui/dialog";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { EmptyState } from "@/components/layout/EmptyState";
import { ProjectNav } from "@/components/layout/ProjectNav";
import * as api from "@/lib/api";
import { toast } from "sonner";

export function ChapterEditor() {
  const { projectId, chapterId } = useParams<{ projectId: string; chapterId: string }>();
  const queryClient = useQueryClient();

  const [content, setContent] = useState("");
  const [outline, setOutline] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [showOutline, setShowOutline] = useState(false);
  const [showReview, setShowReview] = useState(false);
  const [isNewChapterOpen, setIsNewChapterOpen] = useState(false);
  const [newChapterTitle, setNewChapterTitle] = useState("");
  const editorRef = useRef<HTMLTextAreaElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const [streamStatus, setStreamStatus] = useState<string | null>(null);

  const { data: project } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => api.getProject(projectId!),
    enabled: !!projectId,
  });

  const { data: chaptersData, isLoading: chaptersLoading } = useQuery({
    queryKey: ["chapters", projectId],
    queryFn: () => api.listChapters(projectId!),
    enabled: !!projectId,
  });

  const { data: chapter, isLoading: chapterLoading } = useQuery({
    queryKey: ["chapter", projectId, chapterId],
    queryFn: () => api.getChapter(projectId!, chapterId!),
    enabled: !!projectId && !!chapterId,
  });

  const { data: reviews, refetch: refetchReviews } = useQuery({
    queryKey: ["reviews", chapterId],
    queryFn: () => api.getReviews(chapterId!),
    enabled: !!chapterId,
  });

  const { data: llmSettings } = useQuery({
    queryKey: ["llmSettings"],
    queryFn: () => api.getLlmSettings(),
    staleTime: 5 * 60_000,
  });

  // Sync content/outline from chapter data (useEffect, not render body)
  useEffect(() => {
    if (chapter) {
      setContent(chapter.content ?? "");
      setOutline(chapter.outline ?? "");
    }
  }, [chapterId, chapter?.content, chapter?.outline]);

  const saveMutation = useMutation({
    mutationFn: (data: { content?: string; outline?: string }) =>
      api.updateChapter(projectId!, chapterId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chapter", projectId, chapterId] });
      toast.success("已保存");
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "保存失败"),
  });

  const pipelineMutation = useMutation({
    mutationFn: () => api.runPipeline(chapterId!, outline || chapter?.outline || chapter?.content || ""),
    onSuccess: (result) => {
      if (result.chapter_text) setContent(result.chapter_text);
      if (result.blocking_issues.length > 0) setShowReview(true);
      refetchReviews();
      queryClient.invalidateQueries({ queryKey: ["chapter", projectId, chapterId] });
      toast.success(
        result.success
          ? `流水线完成 (${result.blocking_issues.length} 个阻断问题)`
          : `流水线完成但有阻断问题`
      );
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "流水线执行失败"),
  });

  const createChapterMutation = useMutation({
    mutationFn: (title: string) =>
      api.createChapter(projectId!, {
        title,
        number: (chaptersData?.items?.length ?? 0) + 1,
        content: "",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chapters", projectId] });
      setIsNewChapterOpen(false);
      setNewChapterTitle("");
      toast.success("章节已创建");
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "创建失败"),
  });

  const deleteMutation = useMutation({
    mutationFn: () => api.deleteChapter(projectId!, chapterId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chapters", projectId] });
      toast.success("章节已删除");
      window.history.back();
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "删除失败"),
  });

  // SSE streaming generation
  const startStreaming = useCallback(() => {
    if (!chapterId || isGenerating) return;

    if (llmSettings && !llmSettings.api_key_masked) {
      toast.error("未配置 API Key，请先在设置页配置");
      return;
    }

    const draftOutline = (outline || chapter?.outline || "").trim();
    if (!draftOutline) {
      toast.error("请先填写章纲后再 AI 生成");
      setShowOutline(true);
      return;
    }

    eventSourceRef.current?.close();
    setIsGenerating(true);
    setStreamStatus("连接 AI 服务...");
    const abort = new AbortController();
    abortRef.current = abort;

    const url = api.streamDraftUrl(chapterId!, draftOutline);
    const es = new EventSource(url);
    eventSourceRef.current = es;
    let receivedContent = false;

    const finish = (errorMessage?: string) => {
      es.close();
      if (eventSourceRef.current === es) eventSourceRef.current = null;
      setIsGenerating(false);
      setStreamStatus(null);
      if (errorMessage) toast.error(errorMessage);
    };

    es.onmessage = (event) => {
      if (event.data === "[DONE]") {
        finish();
        toast.success("AI 生成完成");
        return;
      }
      try {
        const parsed = JSON.parse(event.data) as {
          type?: string;
          content?: string;
          message?: string;
        };

        if (parsed.type === "error") {
          finish(parsed.message || "AI 生成失败");
          return;
        }

        if (parsed.type === "status" && parsed.message) {
          setStreamStatus(parsed.message);
          return;
        }

        const chunk = parsed.type === "content" ? parsed.content : parsed.content;
        if (chunk) {
          if (!receivedContent) {
            receivedContent = true;
            setContent("");
            setStreamStatus(null);
          }
          setContent((prev) => prev + chunk);
          if (editorRef.current) {
            editorRef.current.scrollTop = editorRef.current.scrollHeight;
          }
        }
      } catch {
        // ignore parse errors
      }
    };

    es.onerror = () => {
      finish(receivedContent ? "SSE 连接中断" : "AI 生成连接失败，请检查 API Key 与网络");
    };

    abort.signal.addEventListener("abort", () => finish());
  }, [chapterId, outline, chapter, isGenerating, llmSettings]);

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort();
    eventSourceRef.current?.close();
    eventSourceRef.current = null;
    setIsGenerating(false);
    setStreamStatus(null);
  }, []);

  const handleSave = useCallback(() => {
    if (!chapterId || !chapter) return;
    const updates: { content?: string; outline?: string } = {};
    if (content !== (chapter.content ?? "")) updates.content = content;
    if (outline !== (chapter.outline ?? "")) updates.outline = outline;
    if (Object.keys(updates).length === 0) {
      toast.message("没有需要保存的更改");
      return;
    }
    saveMutation.mutate(updates);
  }, [content, outline, chapterId, chapter, saveMutation]);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "s") {
        e.preventDefault();
        handleSave();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [handleSave]);

  const chapters = chaptersData?.items ?? [];
  const blockingCount = reviews?.filter((r) => r.severity === "blocking" && !r.is_fixed).length ?? 0;

  if (!projectId) return null;

  const severityIcon = (s: string) => {
    switch (s) {
      case "blocking": return <AlertTriangle className="size-4 text-red-400 shrink-0" />;
      case "major": return <AlertCircle className="size-4 text-amber-400 shrink-0" />;
      default: return <Info className="size-4 text-muted-foreground shrink-0" />;
    }
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-0">
      {/* Chapter list sidebar — visible on xl+ (1280px), Sheet on smaller */}
      <aside className="w-56 border-r shrink-0 flex-col hidden xl:flex">
        <div className="p-3 border-b space-y-3">
          <Link
            to={`/projects/${projectId}`}
            className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1"
          >
            <ArrowLeft className="size-3" />
            {project?.title ?? "返回"}
          </Link>
          <ProjectNav projectId={projectId} className="flex-col items-stretch gap-1" />
        </div>
        <ScrollArea className="flex-1">
          <div className="p-2 space-y-1">
            {chaptersLoading ? (
              Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-8 w-full" />
              ))
            ) : chapters.length === 0 ? (
              <p className="text-xs text-muted-foreground p-2">暂无章节</p>
            ) : (
              chapters.map((ch) => (
                <Link
                  key={ch.id}
                  to={`/projects/${projectId}/chapters/${ch.id}`}
                  className={`block px-2 py-1.5 rounded text-sm transition-colors ${
                    ch.id === chapterId
                      ? "bg-amber-500/10 text-amber-400"
                      : "hover:bg-muted text-foreground"
                  }`}
                >
                  <span className="text-muted-foreground text-xs mr-1">
                    Ch{ch.number}.
                  </span>
                  {ch.title}
                </Link>
              ))
            )}
          </div>
        </ScrollArea>
        <div className="p-2 border-t">
          <Dialog open={isNewChapterOpen} onOpenChange={setIsNewChapterOpen}>
            <DialogTrigger
              render={
                <Button variant="ghost" size="sm" className="w-full justify-start">
                  <Plus className="size-3 mr-1" />
                  新建章节
                </Button>
              }
            />
            <DialogContent>
              <DialogHeader>
                <DialogTitle>新建章节</DialogTitle>
                <DialogDescription>第 {chapters.length + 1} 章</DialogDescription>
              </DialogHeader>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (newChapterTitle) createChapterMutation.mutate(newChapterTitle);
                }}
                className="space-y-4 mt-2"
              >
                <div className="space-y-2">
                  <Label htmlFor="chapterTitle">章节标题</Label>
                  <Input
                    id="chapterTitle"
                    value={newChapterTitle}
                    onChange={(e) => setNewChapterTitle(e.target.value)}
                    placeholder="输入章节标题"
                    required
                  />
                </div>
                <Button type="submit" className="w-full" disabled={createChapterMutation.isPending}>
                  {createChapterMutation.isPending && <Loader2 className="size-4 mr-2 animate-spin" />}
                  创建
                </Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </aside>

      {/* Editor area */}
      <div className="flex-1 flex flex-col min-w-0">
        {!chapterId ? (
          <EmptyState
            icon={FileText}
            title="选择一个章节"
            description="从左侧列表选择章节开始编辑，或创建新章节。"
            action={
              <Button onClick={() => setIsNewChapterOpen(true)}>
                <Plus className="size-4 mr-2" />
                新建章节
              </Button>
            }
          />
        ) : chapterLoading ? (
          <div className="p-6 space-y-4">
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-96 w-full" />
          </div>
        ) : chapter ? (
          <>
            {/* No-key warning */}
            {llmSettings && !llmSettings.api_key_masked && (
              <div className="flex items-center gap-3 mx-4 mt-3 p-3 rounded-lg bg-amber-500/10 border border-amber-500/30">
                <AlertTriangle className="size-5 text-amber-400 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-amber-400">未配置 API Key</p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    AI 写作和流水线需要 LLM API Key。请在设置页配置后使用。
                  </p>
                </div>
                <Link to="/settings" className="shrink-0">
                  <Button size="sm" variant="outline">去设置</Button>
                </Link>
              </div>
            )}
            {/* Toolbar */}
            <div className="flex items-center gap-3 px-4 py-2 border-b shrink-0 flex-wrap">
              {/* Mobile: chapter list Sheet trigger */}
              <Sheet>
                <SheetTrigger
                  render={
                    <Button variant="ghost" size="sm" className="xl:hidden">
                      <FileText className="size-4" />
                    </Button>
                  }
                />
                <SheetContent side="left" className="w-72">
                  <SheetHeader>
                    <SheetTitle>{project?.title ?? "章节列表"}</SheetTitle>
                  </SheetHeader>
                  <ScrollArea className="flex-1 -mx-4">
                    <div className="space-y-1 px-1">
                      {chaptersLoading ? (
                        Array.from({ length: 3 }).map((_, i) => (
                          <Skeleton key={i} className="h-8 w-full" />
                        ))
                      ) : chapters.length === 0 ? (
                        <p className="text-xs text-muted-foreground p-2">暂无章节</p>
                      ) : (
                        chapters.map((ch) => (
                          <Link
                            key={ch.id}
                            to={`/projects/${projectId}/chapters/${ch.id}`}
                            className={`block px-2 py-1.5 rounded text-sm transition-colors ${
                              ch.id === chapterId
                                ? "bg-amber-500/10 text-amber-400"
                                : "hover:bg-muted text-foreground"
                            }`}
                          >
                            <span className="text-muted-foreground text-xs mr-1">
                              Ch{ch.number}.
                            </span>
                            {ch.title}
                          </Link>
                        ))
                      )}
                    </div>
                  </ScrollArea>
                </SheetContent>
              </Sheet>

              <h2 className="font-serif text-lg font-semibold truncate flex-1 min-w-0">
                {chapter.title}
              </h2>
              <Badge variant="outline" className="text-xs">
                {chapter.word_count} 字
              </Badge>
              <Badge
                variant={chapter.status === "draft" ? "secondary" : "default"}
                className="text-xs"
              >
                {chapter.status === "draft" ? "草稿" : chapter.status === "accepted" ? "已通过" : chapter.status}
              </Badge>

              <Button size="sm" variant="ghost" onClick={() => setShowOutline(!showOutline)}>
                {showOutline ? <ChevronUp className="size-3 mr-1" /> : <ChevronDown className="size-3 mr-1" />}
                章纲
              </Button>

              {isGenerating ? (
                <Button size="sm" variant="destructive" onClick={stopStreaming}>
                  <Loader2 className="size-4 mr-1 animate-spin" />
                  停止生成
                </Button>
              ) : (
                <Button size="sm" variant="outline" onClick={startStreaming}>
                  <Sparkles className="size-4 mr-1" />
                  AI 生成
                </Button>
              )}

              {streamStatus && (
                <span className="text-xs text-amber-400/90 truncate max-w-[12rem]">
                  {streamStatus}
                </span>
              )}

              <Button
                size="sm"
                variant="default"
                onClick={() => pipelineMutation.mutate()}
                disabled={pipelineMutation.isPending}
              >
                {pipelineMutation.isPending ? (
                  <Loader2 className="size-4 mr-1 animate-spin" />
                ) : (
                  <Play className="size-4 mr-1" />
                )}
                流水线
              </Button>

              <Button size="sm" onClick={handleSave} disabled={saveMutation.isPending}>
                {saveMutation.isPending ? (
                  <Loader2 className="size-4 mr-1 animate-spin" />
                ) : (
                  <Save className="size-4 mr-1" />
                )}
                保存
              </Button>

              {blockingCount > 0 && (
                <Button size="sm" variant="destructive" onClick={() => setShowReview(!showReview)}>
                  <AlertTriangle className="size-4 mr-1" />
                  {blockingCount} 个阻断
                </Button>
              )}

              <Button
                variant="ghost" size="sm"
                onClick={() => setShowReview(!showReview)}
                className="text-xs"
              >
                {showReview ? <PanelRightClose className="size-4" /> : <PanelRightOpen className="size-4" />}
                {showReview ? "隐藏审查" : "审查"}
              </Button>

              <Link to={`/projects/${projectId}/reviews/${chapterId}`}>
                <Button variant="ghost" size="sm" className="text-xs" title="独立审查页">
                  <ClipboardCheck className="size-4 mr-1" />
                  审查页
                </Button>
              </Link>

              <Link to={`/projects/${projectId}/simulations`}>
                <Button variant="ghost" size="sm" className="text-xs hidden lg:inline-flex" title="推演中心">
                  <FlaskConical className="size-4 mr-1" />
                  推演
                </Button>
              </Link>

              <Link to={`/projects/${projectId}/graph`}>
                <Button variant="ghost" size="sm" className="text-xs hidden lg:inline-flex" title="关系图谱">
                  <Network className="size-4 mr-1" />
                  图谱
                </Button>
              </Link>

              <Button
                variant="ghost" size="icon"
                className="size-8 text-muted-foreground hover:text-destructive"
                onClick={() => {
                  if (confirm("确定删除此章节？")) deleteMutation.mutate();
                }}
              >
                <Trash2 className="size-4" />
              </Button>
            </div>

            {/* Outline input */}
            {showOutline && (
              <div className="px-4 py-3 border-b bg-muted/30">
                <Label className="text-xs mb-1 block">章纲</Label>
                <Textarea
                  value={outline}
                  onChange={(e) => setOutline(e.target.value)}
                  placeholder="输入章纲，用于指导 AI 写作和审查..."
                  className="font-mono text-xs h-20 resize-none"
                />
              </div>
            )}

            {/* Editor + Review Panel */}
            <div className="flex-1 flex min-h-0 relative">
              <textarea
                ref={editorRef}
                value={content}
                onChange={(e) => setContent(e.target.value)}
                className={`flex-1 resize-none p-6 bg-transparent text-foreground font-serif text-lg leading-relaxed outline-none placeholder:text-muted-foreground/40 ${isGenerating ? "border-r border-amber-500/20" : ""}`}
                placeholder="开始写作，或点击「AI 生成」由 WriterAgent 代写..."
                spellCheck={false}
                disabled={isGenerating}
              />

              {/* Review side panel — inline on xl+, overlay on smaller */}
              {showReview && (
                <aside className="xl:w-80 xl:static xl:border-l shrink-0 flex flex-col bg-muted/10 absolute inset-y-0 right-0 w-full sm:w-80 z-10 xl:z-auto">
                  <div className="p-3 border-b flex items-center justify-between">
                    <span className="text-sm font-medium">审查结果</span>
                    <div className="flex items-center gap-1">
                      <Link to={`/projects/${projectId}/reviews/${chapterId}`}>
                        <Button variant="ghost" size="icon" className="size-6" title="独立审查页面">
                          <ExternalLink className="size-3.5" />
                        </Button>
                      </Link>
                      <Button variant="ghost" size="icon" className="size-6" onClick={() => setShowReview(false)}>
                        <PanelRightClose className="size-4" />
                      </Button>
                    </div>
                  </div>
                  <ScrollArea className="flex-1">
                    <div className="p-3 space-y-3">
                      {reviews == null ? (
                        <p className="text-xs text-muted-foreground">暂无审查结果。运行流水线以获取审查报告。</p>
                      ) : reviews.length === 0 ? (
                        <p className="text-xs text-emerald-400">无问题，审查通过。</p>
                      ) : (
                        reviews.map((issue) => (
                          <div
                            key={issue.id}
                            className={`p-3 rounded-lg text-xs space-y-1.5 ${
                              issue.severity === "blocking"
                                ? "bg-red-500/10 border border-red-500/20"
                                : issue.severity === "major"
                                  ? "bg-amber-500/10 border border-amber-500/20"
                                  : "bg-muted/50 border border-border"
                            } ${issue.is_fixed ? "opacity-50" : ""}`}
                          >
                            <div className="flex items-center gap-2">
                              {severityIcon(issue.severity)}
                              <span className="font-medium text-foreground">{issue.title}</span>
                              <Badge variant="outline" className="text-[10px] ml-auto">
                                {issue.category}
                              </Badge>
                            </div>
                            <p className="text-muted-foreground">{issue.description}</p>
                            {issue.evidence && (
                              <blockquote className="border-l-2 border-muted-foreground/30 pl-2 italic text-muted-foreground/70">
                                {issue.evidence}
                              </blockquote>
                            )}
                            {issue.suggestion && (
                              <p className="text-amber-400/80">建议：{issue.suggestion}</p>
                            )}
                            {issue.is_fixed && <Badge className="text-[10px]">已修复</Badge>}
                          </div>
                        ))
                      )}
                    </div>
                  </ScrollArea>
                </aside>
              )}
            </div>
          </>
        ) : (
          <EmptyState title="章节未找到" description="此章节可能已被删除。" />
        )}
      </div>
    </div>
  );
}
