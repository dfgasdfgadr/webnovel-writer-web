import { useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Loader2,
  Plus,
  Save,
  Trash2,
  FileText,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { EmptyState } from "@/components/layout/EmptyState";
import * as api from "@/lib/api";
import { toast } from "sonner";

export function ChapterEditor() {
  const { projectId, chapterId } = useParams<{ projectId: string; chapterId: string }>();
  const queryClient = useQueryClient();

  const [content, setContent] = useState("");
  const [isNewChapterOpen, setIsNewChapterOpen] = useState(false);
  const [newChapterTitle, setNewChapterTitle] = useState("");

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

  // Sync content when chapter loads
  if (chapter && content === "" && chapterId) {
    setContent(chapter.content);
  }

  const saveMutation = useMutation({
    mutationFn: (newContent: string) =>
      api.updateChapter(projectId!, chapterId!, { content: newContent }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chapter", projectId, chapterId] });
      toast.success("已保存");
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "保存失败"),
  });

  const createChapterMutation = useMutation({
    mutationFn: (title: string) =>
      api.createChapter(projectId!, {
        title,
        number: (chaptersData?.items?.length ?? 0) + 1,
        content: "",
      }),
    onSuccess: (newChapter) => {
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

  const handleSave = useCallback(() => {
    if (chapterId && content !== chapter?.content) {
      saveMutation.mutate(content);
    }
  }, [content, chapterId, chapter?.content, saveMutation]);

  // Keyboard shortcut: Ctrl+S
  useState(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "s") {
        e.preventDefault();
        handleSave();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  });

  const chapters = chaptersData?.items ?? [];

  if (!projectId) return null;

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-0">
      {/* Chapter list sidebar */}
      <aside className="w-56 border-r shrink-0 flex flex-col">
        <div className="p-3 border-b flex items-center justify-between">
          <Link
            to={`/projects/${projectId}`}
            className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1"
          >
            <ArrowLeft className="size-3" />
            {project?.title ?? "返回"}
          </Link>
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
                <DialogDescription>
                  第 {chapters.length + 1} 章
                </DialogDescription>
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
            {/* Toolbar */}
            <div className="flex items-center gap-3 px-4 py-2 border-b shrink-0">
              <h2 className="font-serif text-lg font-semibold truncate flex-1">
                {chapter.title}
              </h2>
              <Badge variant="outline" className="text-xs">
                {chapter.word_count} 字
              </Badge>
              <Badge
                variant={chapter.status === "draft" ? "secondary" : "default"}
                className="text-xs"
              >
                {chapter.status === "draft" ? "草稿" : chapter.status}
              </Badge>
              <Button
                size="sm"
                onClick={handleSave}
                disabled={saveMutation.isPending}
              >
                {saveMutation.isPending ? (
                  <Loader2 className="size-4 mr-1 animate-spin" />
                ) : (
                  <Save className="size-4 mr-1" />
                )}
                保存
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="size-8 text-muted-foreground hover:text-destructive"
                onClick={() => {
                  if (confirm("确定删除此章节？")) deleteMutation.mutate();
                }}
              >
                <Trash2 className="size-4" />
              </Button>
            </div>

            {/* Editor */}
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              className="flex-1 w-full resize-none p-6 bg-transparent text-foreground font-serif text-lg leading-relaxed outline-none placeholder:text-muted-foreground/40"
              placeholder="开始写作..."
              spellCheck={false}
            />
          </>
        ) : (
          <EmptyState
            title="章节未找到"
            description="此章节可能已被删除。"
          />
        )}
      </div>
    </div>
  );
}
