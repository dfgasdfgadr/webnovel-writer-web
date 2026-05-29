import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { BookOpen, Plus, Loader2, MoreVertical, Archive, Trash2, Edit3, FolderOpen, Sparkles, FileArchive, Scissors, Download, Wand2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { EmptyState } from "@/components/layout/EmptyState";
import * as api from "@/lib/api";
import { toast } from "sonner";

export function ProjectHub() {
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isImportOpen, setIsImportOpen] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newGenre, setNewGenre] = useState("");
  const queryClient = useQueryClient();

  // Import state
  const [importPath, setImportPath] = useState("");
  const [scanResult, setScanResult] = useState<api.ImportScanResult | null>(null);
  const [isScanning, setIsScanning] = useState(false);

  // Edit state
  const [isZipOpen, setIsZipOpen] = useState(false);
  const [zipFile, setZipFile] = useState<File | null>(null);

  const [editProject, setEditProject] = useState<api.ProjectPublic | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editDesc, setEditDesc] = useState("");

  const { data, isLoading, isError } = useQuery({
    queryKey: ["projects"],
    queryFn: api.listProjects,
  });

  const createMutation = useMutation({
    mutationFn: api.createProject,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      setIsCreateOpen(false);
      setNewTitle("");
      setNewDesc("");
      setNewGenre("");
      if (data.warnings && data.warnings.length > 0) {
        toast.success("项目已创建");
        data.warnings.forEach((w) => toast.warning(w));
      } else {
        toast.success("项目已创建");
      }
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "创建失败"),
  });

  const deleteMutation = useMutation({
    mutationFn: api.deleteProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      toast.success("项目已删除");
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "删除失败"),
  });

  const importMutation = useMutation({
    mutationFn: (params: { sourcePath: string; title?: string }) =>
      api.executeImport(params.sourcePath, params.title),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      setIsImportOpen(false);
      setImportPath("");
      setScanResult(null);
      if (data.warnings && data.warnings.length > 0) {
        toast.success(`已导入：${data.title}`);
        data.warnings.forEach((w) => toast.warning(w));
      } else {
        toast.success(`已导入：${data.title}`);
      }
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "导入失败"),
  });

  const zipImportMut = useMutation({
    mutationFn: (file: File) => api.importZip(file),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      setIsZipOpen(false);
      setZipFile(null);
      toast.success(`已导入：${data.title}`);
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "导入失败"),
  });

  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) =>
      api.updateProject(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      setEditProject(null);
      toast.success("项目已更新");
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "更新失败"),
  });

  const archiveMut = useMutation({
    mutationFn: ({ id, archive }: { id: string; archive: boolean }) =>
      api.updateProject(id, { status: archive ? "archived" : "active" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      toast.success("项目状态已更新");
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "操作失败"),
  });

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate({ title: newTitle, description: newDesc || undefined, genre: newGenre || undefined });
  };

  const handleScan = async () => {
    if (!importPath.trim()) return;
    setIsScanning(true);
    setScanResult(null);
    try {
      const result = await api.scanImport(importPath.trim());
      setScanResult(result);
      if (!result.valid) {
        toast.error("目录无效：" + result.errors.join("; "));
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "扫描失败");
    } finally {
      setIsScanning(false);
    }
  };

  const handleImport = () => {
    if (!scanResult || !scanResult.valid) return;
    importMutation.mutate({ sourcePath: importPath.trim() });
  };

  const handleImportOpenChange = (open: boolean) => {
    setIsImportOpen(open);
    if (!open) {
      setImportPath("");
      setScanResult(null);
    }
  };

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="border-border/40">
            <CardHeader>
              <Skeleton className="h-6 w-3/4" />
              <Skeleton className="h-4 w-1/2 mt-2" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-2/3 mt-2" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <EmptyState
        title="加载失败"
        description="无法获取项目列表，请确认 API 服务是否正常运行。"
        action={
          <Button onClick={() => queryClient.invalidateQueries({ queryKey: ["projects"] })}>
            重试
          </Button>
        }
      />
    );
  }

  const projects = data?.items ?? [];

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-serif text-2xl font-semibold">我的项目</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {projects.length} 个项目
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <Link to="/projects/new">
            <Button className="gap-1.5 bg-primary hover:bg-primary/90">
              <Wand2 className="size-4" />
              AI 智能造书
            </Button>
          </Link>
          <Link to="/projects/new/chat">
            <Button variant="outline" className="gap-1.5" size="sm">
              <Sparkles className="size-4" />
              对话开书
            </Button>
          </Link>
          <Link to="/projects/new/wizard">
            <Button variant="outline" className="gap-1.5" size="sm">
              <BookOpen className="size-4" />
              静态向导
            </Button>
          </Link>
          <Link to="/projects/new/deconstruct">
            <Button variant="outline" className="gap-1.5" size="sm">
              <Scissors className="size-4" />
              拆书
            </Button>
          </Link>

          {/* Zip import dialog */}
          <Dialog open={isZipOpen} onOpenChange={(open) => { setIsZipOpen(open); if (!open) setZipFile(null); }}>
            <DialogTrigger
              render={
                <Button variant="outline" size="sm">
                  <FileArchive className="size-4 mr-1.5" />
                  导入 zip
                </Button>
              }
            />
            <DialogContent>
              <DialogHeader>
                <DialogTitle>从 zip 导入项目</DialogTitle>
                <DialogDescription>
                  上传包含 正文/ 设定集/ 大纲/ 目录的 zip 文件
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 mt-2">
                <Input
                  type="file"
                  accept=".zip"
                  onChange={(e) => setZipFile(e.target.files?.[0] ?? null)}
                />
                {zipFile && (
                  <p className="text-xs text-muted-foreground">
                    已选择：{zipFile.name} ({(zipFile.size / 1024).toFixed(1)} KB)
                  </p>
                )}
                <Button
                  className="w-full"
                  onClick={() => zipFile && zipImportMut.mutate(zipFile)}
                  disabled={!zipFile || zipImportMut.isPending}
                >
                  {zipImportMut.isPending && <Loader2 className="size-4 mr-2 animate-spin" />}
                  上传并导入
                </Button>
              </div>
            </DialogContent>
          </Dialog>

          {/* Import dialog */}
          <Dialog open={isImportOpen} onOpenChange={handleImportOpenChange}>
            <DialogTrigger
              render={
                <Button variant="outline">
                  <FolderOpen className="size-4 mr-2" />
                  导入项目
                </Button>
              }
            />
            <DialogContent>
              <DialogHeader>
                <DialogTitle>导入项目</DialogTitle>
                <DialogDescription>从本地目录导入已有的写作项目</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 mt-2">
                <div className="space-y-2">
                  <Label htmlFor="import-path">本地路径</Label>
                  <div className="flex gap-2">
                    <Input
                      id="import-path"
                      value={importPath}
                      onChange={(e) => setImportPath(e.target.value)}
                      placeholder="例：C:\Users\me\my-novel"
                    />
                    <Button
                      variant="secondary"
                      onClick={handleScan}
                      disabled={isScanning || !importPath.trim()}
                    >
                      {isScanning && <Loader2 className="size-4 mr-1 animate-spin" />}
                      扫描
                    </Button>
                  </div>
                </div>

                {scanResult && (
                  <div className="p-3 rounded-md border bg-muted/30 space-y-2">
                    <div className="flex items-center gap-2">
                      <Badge variant={scanResult.valid ? "default" : "destructive"}>
                        {scanResult.valid ? "有效" : "无效"}
                      </Badge>
                      <span className="text-sm font-medium">{scanResult.title}</span>
                    </div>
                    {scanResult.valid && (
                      <>
                        <div className="text-xs text-muted-foreground space-y-1">
                          <div>路径：{scanResult.source_path}</div>
                          <div>章节数：{scanResult.chapter_count}</div>
                          <div>设定文件数：{scanResult.settings_count}</div>
                          {scanResult.settings_preview.length > 0 && (
                            <div>设定预览：{scanResult.settings_preview.join("，")}</div>
                          )}
                        </div>
                        <Button
                          className="w-full"
                          onClick={handleImport}
                          disabled={importMutation.isPending}
                        >
                          {importMutation.isPending && <Loader2 className="size-4 mr-2 animate-spin" />}
                          导入项目
                        </Button>
                      </>
                    )}
                    {!scanResult.valid && scanResult.errors.length > 0 && (
                      <div className="text-xs text-destructive">
                        {scanResult.errors.map((e, i) => (
                          <div key={i}>- {e}</div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </DialogContent>
          </Dialog>

          {/* Edit dialog */}
          <Dialog open={!!editProject} onOpenChange={(open) => { if (!open) { setEditProject(null); setEditTitle(""); setEditDesc(""); } }}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>编辑项目</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 mt-2">
                <div className="space-y-2">
                  <Label htmlFor="edit-title">书名</Label>
                  <Input
                    id="edit-title"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="edit-desc">简介</Label>
                  <Input
                    id="edit-desc"
                    value={editDesc}
                    onChange={(e) => setEditDesc(e.target.value)}
                  />
                </div>
                <Button
                  className="w-full"
                  onClick={() => {
                    if (editProject) {
                      updateMut.mutate({
                        id: editProject.id,
                        data: { title: editTitle, description: editDesc },
                      });
                    }
                  }}
                  disabled={updateMut.isPending || !editTitle.trim()}
                >
                  {updateMut.isPending ? <Loader2 className="size-4 mr-2 animate-spin" /> : null}
                  保存
                </Button>
              </div>
            </DialogContent>
          </Dialog>

          {/* Create dialog */}
          <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <DialogTrigger
              render={
                <Button>
                  <Plus className="size-4 mr-2" />
                  新建项目
                </Button>
              }
            />
            <DialogContent>
              <DialogHeader>
                <DialogTitle>新建项目</DialogTitle>
                <DialogDescription>创建一本新书的写作项目</DialogDescription>
              </DialogHeader>
              <form onSubmit={handleCreate} className="space-y-4 mt-2">
                <div className="space-y-2">
                  <Label htmlFor="title">书名</Label>
                  <Input
                    id="title"
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    placeholder="给你的书起个名字"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="desc">简介（选填）</Label>
                  <Input
                    id="desc"
                    value={newDesc}
                    onChange={(e) => setNewDesc(e.target.value)}
                    placeholder="一句话简介"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="genre">题材（选填）</Label>
                  <Input
                    id="genre"
                    value={newGenre}
                    onChange={(e) => setNewGenre(e.target.value)}
                    placeholder="玄幻 / 都市 / 悬疑..."
                  />
                </div>
                <Button type="submit" className="w-full" disabled={createMutation.isPending}>
                  {createMutation.isPending && <Loader2 className="size-4 mr-2 animate-spin" />}
                  创建
                </Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {projects.length === 0 ? (
        <EmptyState
          icon={BookOpen}
          title="还没有项目"
          description="创建你的第一个写作项目，开始创作之旅。"
          action={
            <Button onClick={() => setIsCreateOpen(true)}>
              <Plus className="size-4 mr-2" />
              创建第一个项目
            </Button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((project) => (
            <Card
              key={project.id}
              className="border-border/40 hover:border-border-hover transition-colors group"
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <Link to={`/projects/${project.id}`} className="flex-1 min-w-0">
                    <CardTitle className="text-lg font-serif truncate hover:text-amber-400 transition-colors">
                      {project.title}
                    </CardTitle>
                  </Link>
                  <DropdownMenu>
                    <DropdownMenuTrigger
                      render={
                        <Button
                          variant="ghost"
                          size="icon"
                          className="size-8 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <MoreVertical className="size-4" />
                        </Button>
                      }
                    />
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => {
                        setEditProject(project);
                        setEditTitle(project.title);
                        setEditDesc(project.description || "");
                      }}>
                        <Edit3 className="size-4 mr-2" />
                        编辑
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => {
                        window.location.href = api.exportProjectUrl(project.id);
                      }}>
                        <Download className="size-4 mr-2" />
                        导出 zip
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() =>
                        archiveMut.mutate({
                          id: project.id,
                          archive: project.status !== "archived",
                        })
                      }>
                        <Archive className="size-4 mr-2" />
                        {project.status === "archived" ? "取消归档" : "归档"}
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => deleteMutation.mutate(project.id)}>
                        <Trash2 className="size-4 mr-2 text-destructive" />
                        删除
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
                <CardDescription className="text-xs">
                  创建于 {new Date(project.created_at).toLocaleDateString("zh-CN")}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {project.description && (
                  <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
                    {project.description}
                  </p>
                )}
                <div className="flex items-center gap-2 flex-wrap">
                  {project.genre && (
                    <Badge variant="secondary" className="text-xs">
                      {project.genre}
                    </Badge>
                  )}
                  {project.status === "archived" && (
                    <Badge variant="outline" className="text-xs">
                      <Archive className="size-3 mr-1" />
                      已归档
                    </Badge>
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
