import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import {
  Send, Loader2, ArrowLeft, BookOpen, AlertTriangle, Check,
  Sparkles, Lightbulb, Users, Globe, Timer, ArrowRight,
  ShieldAlert, BookMarked,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import * as api from "@/lib/api";
import type { DeconstructResponse } from "@/lib/api";

type DeconPhase = "idle" | "analyzing" | "preview" | "creating" | "done" | "error";

interface SampleInput {
  id: number;
  content: string;
}

const SECTION_CONFIG: Array<{
  key: keyof NonNullable<DeconstructResponse["deconstruction"]>;
  label: string;
  icon: React.ElementType;
  color: string;
}> = [
  { key: "golden_chapters", label: "黄金三章", icon: BookMarked, color: "text-amber-500" },
  { key: "hooks", label: "爽点与钩子", icon: Sparkles, color: "text-pink-500" },
  { key: "character_patterns", label: "人设模式", icon: Users, color: "text-blue-500" },
  { key: "world_patterns", label: "世界观模式", icon: Globe, color: "text-emerald-500" },
  { key: "pacing", label: "叙事节奏", icon: Timer, color: "text-purple-500" },
  { key: "transferable_patterns", label: "可迁移模式", icon: Lightbulb, color: "text-primary" },
  { key: "red_flags", label: "红线警告", icon: ShieldAlert, color: "text-destructive" },
];

export function DeconstructPage() {
  const navigate = useNavigate();
  const [phase, setPhase] = useState<DeconPhase>("idle");
  const [bookTitle, setBookTitle] = useState("");
  const [samples, setSamples] = useState<SampleInput[]>([{ id: 1, content: "" }]);
  const [result, setResult] = useState<DeconstructResponse | null>(null);
  const [selectedPatterns, setSelectedPatterns] = useState<Set<string>>(new Set());
  const [fallbackNotice, setFallbackNotice] = useState(false);

  const createMutation = useMutation({
    mutationFn: api.createProject,
    onSuccess: (data) => {
      setPhase("done");
      toast.success("项目创建成功！");
      if (data.warnings?.length) {
        data.warnings.forEach((w) => toast.warning(w));
      }
      setTimeout(() => {
        navigate(`/projects/${data.id}/planning`);
      }, 800);
    },
    onError: (err) => {
      setPhase("error");
      toast.error(err instanceof Error ? err.message : "创建失败");
    },
  });

  const addSample = useCallback(() => {
    if (samples.length >= 3) {
      toast.info("最多支持 3 段样章");
      return;
    }
    setSamples((prev) => [...prev, { id: prev.length + 1, content: "" }]);
  }, [samples.length]);

  const removeSample = useCallback((id: number) => {
    setSamples((prev) => prev.filter((s) => s.id !== id));
  }, []);

  const updateSample = useCallback((id: number, content: string) => {
    setSamples((prev) => prev.map((s) => (s.id === id ? { ...s, content } : s)));
  }, []);

  const startDeconstruct = useCallback(async () => {
    const nonEmpty = samples.map((s) => s.content.trim()).filter(Boolean);
    if (!bookTitle.trim()) {
      toast.error("请输入参考书书名");
      return;
    }
    if (nonEmpty.length === 0) {
      toast.error("请至少粘贴一段样章");
      return;
    }

    setPhase("analyzing");
    setResult(null);
    setFallbackNotice(false);

    try {
      let lastResponse: DeconstructResponse | null = null;
      for await (const chunk of api.deconstructStream(bookTitle, nonEmpty)) {
        lastResponse = chunk;

        if (chunk.status === "error") {
          setPhase("error");
          toast.error(chunk.error || "拆解失败");
          return;
        }

        if (chunk.status === "done") {
          setResult(chunk);
          setPhase("preview");
          if (!chunk.deconstruction) {
            setFallbackNotice(true);
          }
          // Auto-select transferable patterns
          if (chunk.deconstruction?.transferable_patterns) {
            setSelectedPatterns(new Set(chunk.deconstruction.transferable_patterns));
          }
          return;
        }
      }

      if (lastResponse?.status === "done") {
        setResult(lastResponse);
        setPhase("preview");
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "连接失败";
      setPhase("error");
      toast.error(msg);
    }
  }, [bookTitle, samples]);

  const togglePattern = useCallback((pattern: string) => {
    setSelectedPatterns((prev) => {
      const next = new Set(prev);
      if (next.has(pattern)) {
        next.delete(pattern);
      } else {
        next.add(pattern);
      }
      return next;
    });
  }, []);

  const handleCreateProject = useCallback(() => {
    if (selectedPatterns.size === 0) {
      toast.error("请至少选择一个可迁移模式");
      return;
    }

    const decon = result?.deconstruction;
    const constraints = Array.from(selectedPatterns);
    const hooks = decon?.hooks?.slice(0, 2) || [];
    const worldHints = decon?.world_patterns?.slice(0, 2) || [];

    setPhase("creating");
    createMutation.mutate({
      title: `${bookTitle}·改写`,
      description: `基于《${bookTitle}》的模式改写，差异化创作`,
      genre: "未设定",
      hook: hooks[0] || "差异化卖点待完善",
      protagonist: { name: "主角" },
      world_building: { description: worldHints.join("；") || "" },
      constraints,
      target_words: 1000000,
      target_chapters: 500,
    });
  }, [selectedPatterns, result, bookTitle, createMutation]);

  return (
    <div className="min-h-[calc(100vh-4rem)] flex flex-col max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-3 border-b">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
          <ArrowLeft className="size-4" />
        </Button>
        <div className="flex-1">
          <h1 className="text-lg font-semibold flex items-center gap-2">
            <BookOpen className="size-5 text-primary" />
            参考书拆解
          </h1>
          <p className="text-xs text-muted-foreground">
            从参考书中提取可迁移模式，安全转化为原创项目输入
          </p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {phase === "idle" && (
          <div className="max-w-xl mx-auto space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <BookOpen className="size-4 text-primary" />
                  参考书信息
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">书名</label>
                  <Input
                    value={bookTitle}
                    onChange={(e) => setBookTitle(e.target.value)}
                    placeholder="输入参考书的名称"
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <BookMarked className="size-4 text-primary" />
                  样章文本
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  粘贴 1-3 段样章（每段约 500-3000 字），AI 将分析其结构模式。
                  <span className="text-destructive font-medium">不要粘贴整本书。只需关键片段。红线下不复制原作角色、地名和具体情节。</span>
                </p>
                {samples.map((sample, idx) => (
                  <div key={sample.id} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium">样章 {idx + 1}</label>
                      {samples.length > 1 && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeSample(sample.id)}
                        >
                          删除
                        </Button>
                      )}
                    </div>
                    <Textarea
                      value={sample.content}
                      onChange={(e) => updateSample(sample.id, e.target.value)}
                      placeholder={`粘贴第 ${idx + 1} 段样章文本...`}
                      rows={6}
                    />
                  </div>
                ))}
                {samples.length < 3 && (
                  <Button variant="outline" onClick={addSample} className="w-full">
                    + 添加样章
                  </Button>
                )}
              </CardContent>
            </Card>

            <Button onClick={startDeconstruct} className="w-full" disabled={!bookTitle.trim()}>
              <Sparkles className="size-4 mr-1" />
              开始拆解分析
            </Button>

            <div className="flex gap-3 text-xs text-muted-foreground">
              <div className="flex items-center gap-1">
                <ShieldAlert className="size-3 text-destructive" />
                仅提取模式，不写原作 canon
              </div>
              <div className="flex items-center gap-1">
                <Lightbulb className="size-3 text-primary" />
                差异化改写后确认写入
              </div>
            </div>
          </div>
        )}

        {phase === "analyzing" && (
          <div className="flex items-center justify-center min-h-[20rem]">
            <div className="text-center space-y-4">
              <Loader2 className="size-8 animate-spin mx-auto text-primary" />
              <p className="text-lg font-medium">正在分析参考书...</p>
              <p className="text-sm text-muted-foreground">
                AI 正在提取黄金三章、爽点、人设、世界观、叙事节奏等模式
              </p>
            </div>
          </div>
        )}

        {phase === "preview" && result?.deconstruction && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold">《{bookTitle}》拆解结果</h2>
                <p className="text-sm text-muted-foreground">
                  以下为可迁移模式分析，<span className="text-destructive font-medium">红线下禁止直接复制原作内容</span>
                </p>
              </div>
              {fallbackNotice && (
                <Badge variant="outline" className="text-amber-500">
                  <AlertTriangle className="size-3 mr-1" />
                  降级模式
                </Badge>
              )}
            </div>

            <Tabs defaultValue="transferable_patterns" className="w-full">
              <TabsList className="flex-wrap h-auto gap-1">
                {SECTION_CONFIG.filter((s) => {
                  const items = result.deconstruction?.[s.key];
                  return Array.isArray(items) && items.length > 0;
                }).map((s) => (
                  <TabsTrigger key={s.key} value={s.key} className="text-xs">
                    <s.icon className={`size-3 mr-1 ${s.color}`} />
                    {s.label}
                  </TabsTrigger>
                ))}
              </TabsList>

              {SECTION_CONFIG.map((s) => {
                const items = result.deconstruction?.[s.key];
                if (!Array.isArray(items) || items.length === 0) return null;
                const isRedFlag = s.key === "red_flags";
                const isTransferable = s.key === "transferable_patterns";

                return (
                  <TabsContent key={s.key} value={s.key} className="space-y-3">
                    <div className={`rounded-lg border p-4 ${isRedFlag ? "border-destructive/30 bg-destructive/5" : ""}`}>
                      <div className="flex items-center gap-2 mb-3">
                        <s.icon className={`size-4 ${s.color}`} />
                        <h3 className="font-medium">{s.label}</h3>
                        <Badge variant="secondary" className="text-xs">{items.length} 项</Badge>
                      </div>
                      <ul className="space-y-2">
                        {items.map((item, i) => (
                          <li
                            key={i}
                            className={`text-sm p-3 rounded-md flex items-start gap-2 ${
                              isRedFlag
                                ? "bg-destructive/10 text-destructive"
                                : isTransferable
                                ? selectedPatterns.has(item)
                                  ? "bg-primary/10 border border-primary/30 cursor-pointer"
                                  : "bg-muted hover:bg-muted/80 cursor-pointer border border-transparent"
                                : "bg-muted"
                            }`}
                            onClick={() => isTransferable && togglePattern(item)}
                          >
                            {isTransferable && (
                              <div className="mt-0.5 shrink-0">
                                {selectedPatterns.has(item) ? (
                                  <Check className="size-4 text-primary" />
                                ) : (
                                  <div className="size-4 rounded border border-muted-foreground/30" />
                                )}
                              </div>
                            )}
                            {isRedFlag && <ShieldAlert className="size-4 shrink-0 mt-0.5" />}
                            <span className="flex-1">{item}</span>
                          </li>
                        ))}
                      </ul>
                      {isTransferable && (
                        <p className="text-xs text-muted-foreground mt-2">
                          点击勾选要迁移到原创项目中的模式（已选 {selectedPatterns.size} 项）
                        </p>
                      )}
                    </div>                  </TabsContent>
                );
              })}
            </Tabs>

            <div className="flex items-center gap-3 p-4 rounded-lg border bg-amber-500/5 border-amber-500/20">
              <AlertTriangle className="size-5 text-amber-500 shrink-0" />
              <div className="text-sm">
                <p className="font-medium">差异化改写确认</p>
                <p className="text-muted-foreground">
                  以上分析仅提取可迁移的叙事模式和结构，不会写入原作的角色名、地名或具体情节。
                  确认后系统将基于勾选的模式生成原创 premise。
                </p>
              </div>
            </div>

            <div className="flex justify-end gap-3">
              <Button variant="outline" onClick={() => setPhase("idle")}>
                重新输入
              </Button>
              <Button
                onClick={() => navigate("/projects/new/chat")}
                variant="outline"
              >
                <ArrowRight className="size-4 mr-1" />
                去对话开书补充
              </Button>
              <Button
                onClick={handleCreateProject}
                disabled={selectedPatterns.size === 0 || createMutation.isPending}
              >
                {createMutation.isPending ? (
                  <>
                    <Loader2 className="size-4 mr-1 animate-spin" />
                    创建中...
                  </>
                ) : (
                  <>
                    <Check className="size-4 mr-1" />
                    确认并创建原创项目
                  </>
                )}
              </Button>
            </div>
          </div>
        )}

        {phase === "preview" && !result?.deconstruction && (
          <div className="text-center space-y-4">
            <AlertTriangle className="size-8 mx-auto text-amber-500" />
            <p>拆解完成，但未返回结构化数据。</p>
            <Button variant="outline" onClick={() => setPhase("idle")}>
              重新输入
            </Button>
          </div>
        )}

        {phase === "creating" && (
          <div className="flex items-center justify-center min-h-[20rem]">
            <div className="text-center space-y-4">
              <Loader2 className="size-8 animate-spin mx-auto text-primary" />
              <p className="text-lg font-medium">正在创建原创项目...</p>
              <p className="text-sm text-muted-foreground">
                基于可迁移模式生成原创设定
              </p>
            </div>
          </div>
        )}

        {phase === "done" && (
          <div className="flex items-center justify-center min-h-[20rem]">
            <div className="text-center space-y-4">
              <div className="w-12 h-12 rounded-full bg-green-500/10 flex items-center justify-center mx-auto">
                <Check className="size-6 text-green-500" />
              </div>
              <p className="text-lg font-medium">原创项目创建成功！</p>
              <p className="text-sm text-muted-foreground">正在跳转到规划中心...</p>
            </div>
          </div>
        )}

        {phase === "error" && (
          <div className="flex items-center justify-center min-h-[20rem]">
            <div className="text-center space-y-4">
              <AlertTriangle className="size-8 mx-auto text-destructive" />
              <p className="text-lg font-medium">分析失败</p>
              <Button variant="outline" onClick={() => setPhase("idle")}>
                重试
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
