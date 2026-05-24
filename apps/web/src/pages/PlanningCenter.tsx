import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft, Loader2, Sparkles, BookOpen, ListChecks,
  Layers, RotateCw, AlertTriangle, CheckCircle2, XCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Progress } from "@/components/ui/progress";
import { ProjectNav } from "@/components/layout/ProjectNav";
import * as api from "@/lib/api";
import { toast } from "sonner";
import { useState } from "react";

function MapIcon({ className }: { className?: string }) {
  return (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6" />
      <line x1="8" y1="2" x2="8" y2="18" />
      <line x1="16" y1="6" x2="16" y2="22" />
    </svg>
  );
}

export function PlanningCenter() {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();

  const [genre, setGenre] = useState("");
  const [hook, setHook] = useState("");
  const [protagonistName, setProtagonistName] = useState("");
  const [protagonistTraits, setProtagonistTraits] = useState("");
  const [worldBuilding, setWorldBuilding] = useState("");
  const [powerSystem, setPowerSystem] = useState("");

  const [volumeTitle, setVolumeTitle] = useState("");
  const [volumeSummary, setVolumeSummary] = useState("");
  const [chapterNum, setChapterNum] = useState(1);

  const [batchStart, setBatchStart] = useState(1);
  const [batchEnd, setBatchEnd] = useState(10);
  const [batchResults, setBatchResults] = useState<Array<{ chapter_num: number; success: boolean; data?: api.OutlineResponse; error?: string }>>([]);

  const [totalChapters, setTotalChapters] = useState(100);
  const [chaptersPerVolume, setChaptersPerVolume] = useState(50);
  const [volumePlanResult, setVolumePlanResult] = useState<api.VolumePlanResponse | null>(null);

  const [activeTab, setActiveTab] = useState("synopsis");

  const { data: project } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => api.getProject(projectId!),
    enabled: !!projectId,
  });

  const synopsisFromProject = project?.synopsis_json
    ? (() => { try { return JSON.parse(project.synopsis_json); } catch { return null; } })()
    : null;

  const synopsisMutation = useMutation({
    mutationFn: () =>
      api.generateSynopsis(projectId!, {
        genre,
        hook,
        protagonist: { name: protagonistName, traits: protagonistTraits },
        world_building: { description: worldBuilding },
        power_system: powerSystem,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
      toast.success("总纲已生成并保存");
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "生成失败"),
  });

  const outlineMutation = useMutation({
    mutationFn: () =>
      api.generateOutline(projectId!, {
        volume: { title: volumeTitle, summary: volumeSummary },
        chapter_num: chapterNum,
        synopsis: synopsisFromProject || {},
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chapters", projectId] });
      toast.success(`第${chapterNum}章章纲已生成`);
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "生成失败"),
  });

  const batchMutation = useMutation({
    mutationFn: () =>
      api.generateBatchOutlines(projectId!, {
        volume: { title: volumeTitle, summary: volumeSummary },
        start_chapter: batchStart,
        end_chapter: batchEnd,
        synopsis: synopsisFromProject || {},
      }),
    onSuccess: (data) => {
      setBatchResults(data.results);
      queryClient.invalidateQueries({ queryKey: ["chapters", projectId] });
      toast.success(`批量章纲完成: ${data.completed} 成功, ${data.failed} 失败`);
    },
    onError: (err) => {
      toast.error(err instanceof Error ? err.message : "批量生成失败");
    },
  });

  const volumePlanMutation = useMutation({
    mutationFn: () =>
      api.generateVolumePlan(projectId!, {
        synopsis: synopsisFromProject || {},
        total_chapters: totalChapters,
        chapters_per_volume: chaptersPerVolume,
      }),
    onSuccess: (data) => {
      setVolumePlanResult(data);
      queryClient.invalidateQueries({ queryKey: ["chapters", projectId] });
      toast.success(`卷纲规划完成: ${data.total_volumes} 卷`);
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "规划失败"),
  });

  return (
    <div>
      <div className="flex items-start justify-between mb-6">
        <div>
          <Link
            to={`/projects/${projectId}`}
            className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1 mb-2"
          >
            <ArrowLeft className="size-3" />
            返回项目
          </Link>
          <h1 className="font-serif text-2xl font-semibold">规划中心</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {project?.title || "加载中..."}
          </p>
        </div>
      </div>

      <ProjectNav projectId={projectId!} active="planning" className="mb-6" />

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="mb-6">
          <TabsTrigger value="synopsis" className="gap-1.5">
            <BookOpen className="size-4" />总纲
          </TabsTrigger>
          <TabsTrigger value="outline" className="gap-1.5">
            <ListChecks className="size-4" />章纲
          </TabsTrigger>
          <TabsTrigger value="batch" className="gap-1.5">
            <Layers className="size-4" />批量章纲
          </TabsTrigger>
          <TabsTrigger value="volume-plan" className="gap-1.5">
            <MapIcon className="size-4" />卷纲规划
          </TabsTrigger>
        </TabsList>

        {/* Synopsis Tab */}
        <TabsContent value="synopsis" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">总纲设定</CardTitle>
                <CardDescription>填写核心设定，AI 生成故事总纲</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="genre">题材</Label>
                  <Input id="genre" value={genre} onChange={(e) => setGenre(e.target.value)} placeholder="如：玄幻、都市、悬疑…" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="hook">核心卖点</Label>
                  <Textarea id="hook" value={hook} onChange={(e) => setHook(e.target.value)} placeholder="一句话概括故事的独特吸引力" rows={2} />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-2">
                    <Label htmlFor="pName">主角名</Label>
                    <Input id="pName" value={protagonistName} onChange={(e) => setProtagonistName(e.target.value)} placeholder="主角姓名" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="pTraits">主角特质</Label>
                    <Input id="pTraits" value={protagonistTraits} onChange={(e) => setProtagonistTraits(e.target.value)} placeholder="性格、背景…" />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="world">世界观</Label>
                  <Textarea id="world" value={worldBuilding} onChange={(e) => setWorldBuilding(e.target.value)} placeholder="世界背景、规则、设定…" rows={3} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="power">力量体系</Label>
                  <Input id="power" value={powerSystem} onChange={(e) => setPowerSystem(e.target.value)} placeholder="如：修仙境界、异能等级…" />
                </div>
                <Button
                  className="w-full"
                  onClick={() => synopsisMutation.mutate()}
                  disabled={synopsisMutation.isPending || !genre.trim()}
                >
                  {synopsisMutation.isPending ? (
                    <Loader2 className="size-4 mr-2 animate-spin" />
                  ) : (
                    <Sparkles className="size-4 mr-2" />
                  )}
                  生成总纲
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">总纲结果</CardTitle>
                <CardDescription>
                  {synopsisFromProject ? "已保存的总纲" : "生成后将在此展示"}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {synopsisMutation.isPending ? (
                  <div className="space-y-3">
                    <Skeleton className="h-5 w-48" />
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-2/3" />
                  </div>
                ) : synopsisFromProject ? (
                  <ScrollArea className="max-h-[400px]">
                    <div className="space-y-4">
                      {synopsisFromProject.title && (
                        <div>
                          <span className="text-xs text-muted-foreground">书名</span>
                          <p className="font-serif text-lg">{synopsisFromProject.title}</p>
                        </div>
                      )}
                      <div className="flex flex-wrap gap-2">
                        {synopsisFromProject.genre && <Badge variant="secondary">{synopsisFromProject.genre}</Badge>}
                        {synopsisFromProject.hook && <Badge variant="outline" className="max-w-xs truncate">{synopsisFromProject.hook}</Badge>}
                      </div>
                      {synopsisFromProject.synopsis && (
                        <div>
                          <span className="text-xs text-muted-foreground">故事概述</span>
                          <p className="text-sm mt-1 text-muted-foreground">{synopsisFromProject.synopsis}</p>
                        </div>
                      )}
                      {synopsisFromProject.volumes?.length > 0 && (
                        <div>
                          <span className="text-xs text-muted-foreground">卷纲结构</span>
                          <div className="space-y-2 mt-1">
                            {synopsisFromProject.volumes.map((v: Record<string, unknown>, i: number) => (
                              <div key={i} className="border border-border/40 rounded-md p-3">
                                <div className="flex items-center justify-between">
                                  <span className="font-medium text-sm">第{v.num as number}卷: {v.title as string}</span>
                                  <Badge variant="outline" className="text-xs">{v.target_chapters as number}章</Badge>
                                </div>
                                <p className="text-xs text-muted-foreground mt-1">{v.summary as string}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </ScrollArea>
                ) : (
                  <div className="text-center py-12 text-muted-foreground">
                    <BookOpen className="size-10 mx-auto mb-3 opacity-30" />
                    <p className="text-sm">尚未生成总纲</p>
                    <p className="text-xs mt-1">填写左侧表单后点击"生成总纲"</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Single Outline Tab */}
        <TabsContent value="outline" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">章纲生成</CardTitle>
                <CardDescription>为指定章节生成详细章纲</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-2">
                    <Label htmlFor="volTitle">卷标题</Label>
                    <Input id="volTitle" value={volumeTitle} onChange={(e) => setVolumeTitle(e.target.value)} placeholder="如：第一卷·觉醒" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="chNum">章节号</Label>
                    <Input id="chNum" type="number" min={1} value={chapterNum} onChange={(e) => setChapterNum(Number(e.target.value) || 1)} />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="volSummary">卷概要</Label>
                  <Textarea id="volSummary" value={volumeSummary} onChange={(e) => setVolumeSummary(e.target.value)} placeholder="本卷的主要剧情方向…" rows={2} />
                </div>
                <Button
                  className="w-full"
                  onClick={() => outlineMutation.mutate()}
                  disabled={outlineMutation.isPending}
                >
                  {outlineMutation.isPending ? (
                    <Loader2 className="size-4 mr-2 animate-spin" />
                  ) : (
                    <Sparkles className="size-4 mr-2" />
                  )}
                  生成第{chapterNum}章章纲
                </Button>
                {!synopsisFromProject && (
                  <p className="text-xs text-amber-400 flex items-center gap-1">
                    <AlertTriangle className="size-3" />
                    建议先生成总纲以获得更连贯的章纲
                  </p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">生成结果</CardTitle>
              </CardHeader>
              <CardContent>
                {outlineMutation.isPending ? (
                  <div className="space-y-3">
                    <Skeleton className="h-5 w-32" />
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-2/3" />
                  </div>
                ) : outlineMutation.data ? (
                  <ScrollArea className="max-h-[400px]">
                    <div className="space-y-3">
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary">第{outlineMutation.data.chapter_num}章</Badge>
                        <span className="font-medium">{outlineMutation.data.title}</span>
                        <Badge variant="outline" className="text-xs">{outlineMutation.data.target_words}字</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">{outlineMutation.data.outline}</p>
                      {outlineMutation.data.must_cover_nodes?.length > 0 && (
                        <div>
                          <span className="text-xs font-medium">必须覆盖节点</span>
                          <ul className="mt-1 space-y-1">
                            {outlineMutation.data.must_cover_nodes.map((n, i) => (
                              <li key={i} className="text-xs text-emerald-400 flex items-center gap-1">
                                <CheckCircle2 className="size-3" />{n}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {outlineMutation.data.forbidden_zones?.length > 0 && (
                        <div>
                          <span className="text-xs font-medium">禁区</span>
                          <ul className="mt-1 space-y-1">
                            {outlineMutation.data.forbidden_zones.map((z, i) => (
                              <li key={i} className="text-xs text-red-400 flex items-center gap-1">
                                <XCircle className="size-3" />{z}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {outlineMutation.data.key_characters?.length > 0 && (
                        <div>
                          <span className="text-xs font-medium">本章角色</span>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {outlineMutation.data.key_characters.map((c, i) => (
                              <Badge key={i} variant="outline" className="text-xs">
                                {c.name}: {c.role_in_chapter}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </ScrollArea>
                ) : (
                  <div className="text-center py-12 text-muted-foreground">
                    <ListChecks className="size-10 mx-auto mb-3 opacity-30" />
                    <p className="text-sm">尚未生成章纲</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Batch Outline Tab */}
        <TabsContent value="batch" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">批量章纲生成</CardTitle>
              <CardDescription>指定章节范围，按顺序逐章生成章纲。失败章节可单独重试。</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-3">
                <div className="space-y-2">
                  <Label htmlFor="batchStart">起始章节</Label>
                  <Input id="batchStart" type="number" min={1} value={batchStart} onChange={(e) => setBatchStart(Number(e.target.value) || 1)} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="batchEnd">结束章节</Label>
                  <Input id="batchEnd" type="number" min={1} value={batchEnd} onChange={(e) => setBatchEnd(Number(e.target.value) || 1)} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="batchVol">卷标题</Label>
                  <Input id="batchVol" value={volumeTitle} onChange={(e) => setVolumeTitle(e.target.value)} placeholder="如：第一卷" />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="batchVolSummary">卷概要</Label>
                <Textarea id="batchVolSummary" value={volumeSummary} onChange={(e) => setVolumeSummary(e.target.value)} placeholder="本卷剧情方向…" rows={2} />
              </div>
              <Button
                className="w-full"
                onClick={() => {
                  setBatchResults([]);
                  batchMutation.mutate();
                }}
                disabled={batchMutation.isPending || batchStart < 1 || batchEnd < batchStart}
              >
                {batchMutation.isPending ? (
                  <Loader2 className="size-4 mr-2 animate-spin" />
                ) : (
                  <Layers className="size-4 mr-2" />
                )}
                生成第{batchStart}–{batchEnd}章章纲（共{batchEnd - batchStart + 1}章）
              </Button>

              {(batchMutation.isPending || batchResults.length > 0) && (
                <div className="space-y-2 mt-4">
                  {batchMutation.isPending && (
                    <div className="space-y-1">
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>生成中...</span>
                      </div>
                      <Progress value={batchResults.length > 0 ? (batchResults.length / (batchEnd - batchStart + 1)) * 100 : 0} />
                    </div>
                  )}
                  <ScrollArea className="max-h-[300px]">
                    <div className="space-y-1">
                      {batchResults.map((r) => (
                        <div
                          key={r.chapter_num}
                          className={`flex items-center gap-2 text-sm p-2 rounded ${
                            r.success ? "bg-emerald-500/10" : "bg-red-500/10"
                          }`}
                        >
                          {r.success ? (
                            <CheckCircle2 className="size-4 text-emerald-400 shrink-0" />
                          ) : (
                            <XCircle className="size-4 text-red-400 shrink-0" />
                          )}
                          <span className="font-mono text-xs">第{r.chapter_num}章</span>
                          {r.success && r.data && (
                            <span className="truncate text-muted-foreground">{r.data.title}</span>
                          )}
                          {!r.success && (
                            <span className="text-xs text-red-400 truncate">{r.error}</span>
                          )}
                          {!r.success && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="ml-auto h-7 text-xs"
                              onClick={() => {
                                api.generateOutline(projectId!, {
                                  volume: { title: volumeTitle, summary: volumeSummary },
                                  chapter_num: r.chapter_num,
                                  synopsis: synopsisFromProject || {},
                                }).then(() => {
                                  toast.success(`第${r.chapter_num}章重试成功`);
                                  queryClient.invalidateQueries({ queryKey: ["chapters", projectId] });
                                }).catch((e) => toast.error(`重试失败: ${e.message}`));
                              }}
                            >
                              <RotateCw className="size-3 mr-1" />重试
                            </Button>
                          )}
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Volume Plan Tab */}
        <TabsContent value="volume-plan" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">滚动卷纲规划</CardTitle>
              <CardDescription>前 2 卷生成详细章纲，后续卷仅生成骨架（卷概要 + 目标章节数）</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label htmlFor="totalCh">总章节数</Label>
                  <Input id="totalCh" type="number" min={1} value={totalChapters} onChange={(e) => setTotalChapters(Number(e.target.value) || 1)} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="chPerVol">每卷章节数</Label>
                  <Input id="chPerVol" type="number" min={1} value={chaptersPerVolume} onChange={(e) => setChaptersPerVolume(Number(e.target.value) || 1)} />
                </div>
              </div>
              <Button
                className="w-full"
                onClick={() => volumePlanMutation.mutate()}
                disabled={volumePlanMutation.isPending || !synopsisFromProject}
              >
                {volumePlanMutation.isPending ? (
                  <Loader2 className="size-4 mr-2 animate-spin" />
                ) : (
                  <MapIcon className="size-4 mr-2" />
                )}
                生成卷纲规划
              </Button>
              {!synopsisFromProject && (
                <p className="text-xs text-amber-400 flex items-center gap-1">
                  <AlertTriangle className="size-3" />
                  请先生成总纲后再进行卷纲规划
                </p>
              )}

              {volumePlanResult && (
                <div className="space-y-3 mt-4">
                  <p className="text-sm text-muted-foreground">
                    共 {volumePlanResult.total_volumes} 卷（前 2 卷详细，后续骨架）
                  </p>
                  <ScrollArea className="max-h-[500px]">
                    <div className="space-y-3">
                      {volumePlanResult.volumes.map((vol) => (
                        <Card key={vol.num} className="border-border/40">
                          <CardHeader className="pb-2">
                            <div className="flex items-center justify-between">
                              <CardTitle className="text-base">
                                第{vol.num}卷: {vol.title}
                              </CardTitle>
                              <Badge variant={vol.num <= 2 ? "secondary" : "outline"}>
                                {vol.num <= 2 ? "详细" : "骨架"}
                              </Badge>
                            </div>
                            <CardDescription>{vol.summary}</CardDescription>
                            <p className="text-xs text-muted-foreground">{vol.target_chapters}章</p>
                          </CardHeader>
                          {vol.chapters && vol.chapters.length > 0 && (
                            <CardContent>
                              <div className="space-y-1.5 max-h-[200px] overflow-y-auto">
                                {vol.chapters.map((ch, i) => (
                                  <div key={i} className="flex items-center gap-2 text-xs p-1.5 rounded bg-muted/30">
                                    <span className="font-mono text-muted-foreground">
                                      Ch{ch.chapter_num}.
                                    </span>
                                    <span className="truncate">
                                      {ch.title || "无标题"}
                                    </span>
                                    <Badge variant="outline" className="text-[10px] ml-auto shrink-0">
                                      {ch.target_words}字
                                    </Badge>
                                  </div>
                                ))}
                              </div>
                            </CardContent>
                          )}
                        </Card>
                      ))}
                    </div>
                  </ScrollArea>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
