import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Plus, FileText, Trash2, Edit3, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent } from "@/components/ui/card";
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
import { useState } from "react";

export function ProjectDetail() {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();

  const [isNewChapterOpen, setIsNewChapterOpen] = useState(false);
  const [newChapterTitle, setNewChapterTitle] = useState("");

  const { data: project, isLoading: projectLoading } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => api.getProject(projectId!),
    enabled: !!projectId,
  });

  const { data: chaptersData, isLoading: chaptersLoading } = useQuery({
    queryKey: ["chapters", projectId],
    queryFn: () => api.listChapters(projectId!),
    enabled: !!projectId,
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

  const deleteChapterMutation = useMutation({
    mutationFn: (chapterId: string) => api.deleteChapter(projectId!, chapterId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chapters", projectId] });
      toast.success("章节已删除");
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "删除失败"),
  });

  if (projectLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-48" />
        <div className="space-y-2 mt-6">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <EmptyState
        title="项目未找到"
        description="此项目可能已被删除。"
        action={
          <Link to="/">
            <Button variant="outline">
              <ArrowLeft className="size-4 mr-2" />
              返回项目列表
            </Button>
          </Link>
        }
      />
    );
  }

  const chapters = chaptersData?.items ?? [];

  return (
    <div>
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <Link
            to="/"
            className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1 mb-2"
          >
            <ArrowLeft className="size-3" />
            项目列表
          </Link>
          <h1 className="font-serif text-2xl font-semibold">{project.title}</h1>
          <div className="flex items-center gap-2 mt-2">
            {project.genre && (
              <Badge variant="secondary" className="text-xs">{project.genre}</Badge>
            )}
            <Badge variant="outline" className="text-xs">
              {project.status === "active" ? "进行中" : "已归档"}
            </Badge>
            <span className="text-xs text-muted-foreground">
              {chapters.length} 章
            </span>
          </div>
          {project.description && (
            <p className="text-sm text-muted-foreground mt-3 max-w-prose">
              {project.description}
            </p>
          )}
        </div>
        <Dialog open={isNewChapterOpen} onOpenChange={setIsNewChapterOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="size-4 mr-2" />
              新建章节
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>新建章节</DialogTitle>
              <DialogDescription>
                {project.title} · 第 {chapters.length + 1} 章
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

      {/* Chapters */}
      {chaptersLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      ) : chapters.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="还没有章节"
          description="创建第一个章节开始写作。"
          action={
            <Button onClick={() => setIsNewChapterOpen(true)}>
              <Plus className="size-4 mr-2" />
              新建章节
            </Button>
          }
        />
      ) : (
        <div className="space-y-2">
          {chapters.map((ch) => (
            <Card
              key={ch.id}
              className="border-border/40 hover:border-border-hover transition-colors"
            >
              <CardContent className="p-4 flex items-center justify-between">
                <Link
                  to={`/projects/${projectId}/chapters/${ch.id}`}
                  className="flex-1 min-w-0 flex items-center gap-3 hover:text-amber-400 transition-colors"
                >
                  <span className="text-sm text-muted-foreground font-mono">
                    Ch{ch.number}.
                  </span>
                  <span className="font-medium truncate">{ch.title}</span>
                  <Badge variant="outline" className="text-xs shrink-0">
                    {ch.word_count} 字
                  </Badge>
                </Link>
                <Button
                  variant="ghost"
                  size="icon"
                  className="size-8 text-muted-foreground hover:text-destructive ml-2 shrink-0"
                  onClick={() => {
                    if (confirm("确定删除此章节？")) deleteChapterMutation.mutate(ch.id);
                  }}
                >
                  <Trash2 className="size-4" />
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
