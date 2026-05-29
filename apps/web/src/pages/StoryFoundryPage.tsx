import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import {
  Send, Loader2, ArrowLeft, BookOpen, AlertTriangle, Check,
  Sparkles, Lightbulb, Users, Globe, Timer, ArrowRight,
  ShieldAlert, BookMarked, ChevronRight, Wand2, FileText,
  PenTool, CheckCircle2, AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import * as api from "@/lib/api";
import type { FoundryDeconstruction, QuestionSet } from "@/lib/api";

type FoundryStep =
  | "input"
  | "deconstructing"
  | "deconstruction"
  | "questions"
  | "composing"
  | "preview"
  | "creating"
  | "done"
  | "error";

interface SampleInput {
  id: number;
  content: string;
}

const STEPS: Array<{ key: FoundryStep; label: string }> = [
  { key: "input", label: "输入" },
  { key: "deconstructing", label: "拆书" },
  { key: "deconstruction", label: "分析" },
  { key: "questions", label: "选择" },
  { key: "composing", label: "生成" },
  { key: "preview", label: "预览" },
];

const SECTION_CONFIG: Array<{
  key: keyof FoundryDeconstruction;
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

function StepIndicator({ currentStep }: { currentStep: FoundryStep }) {
  const stepIndex = STEPS.findIndex((s) => s.key === currentStep);
  return (
    <div className="flex items-center gap-1 px-4 py-2 border-b overflow-x-auto">
      {STEPS.map((step, idx) => {
        const isActive = idx === stepIndex;
        const isPast = idx < stepIndex;
        return (
          <div key={step.key} className="flex items-center gap-1 shrink-0">
            <Badge
              variant={isActive ? "default" : isPast ? "secondary" : "outline"}
              className={`text-xs ${isActive ? "bg-primary" : ""}`}
            >
              {isPast ? <Check className="size-3 mr-0.5" /> : null}
              {step.label}
            </Badge>
            {idx < STEPS.length - 1 && (
              <ChevronRight className="size-3 text-muted-foreground" />
            )}
          </div>
        );
      })}
    </div>
  );
}

export function StoryFoundryPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState<FoundryStep>("input");
  const [bookTitle, setBookTitle] = useState("");
  const [samples, setSamples] = useState<SampleInput[]>([{ id: 1, content: "" }]);
  const [deconstruction, setDeconstruction] = useState<FoundryDeconstruction | null>(null);
  const [questionSets, setQuestionSets] = useState<QuestionSet[]>([]);
  const [selections, setSelections] = useState<Record<string, string>>({});
  const [composeResult, setComposeResult] = useState<api.FoundryComposeResponse | null>(null);
  const [customNotes, setCustomNotes] = useState("");
  const [fallbackNotice, setFallbackNotice] = useState(false);

  const deconstructMut = useMutation({
    mutationFn: api.foundryDeconstruct,
    onSuccess: (data) => {
      setDeconstruction(data.deconstruction);
      setFallbackNotice(data.fallback);
      setStep("deconstruction");
      // Auto-fetch questions
      fetchQuestions(data.deconstruction);
    },
    onError: (err) => {
      setStep("error");
      toast.error(err instanceof Error ? err.message : "拆书失败");
    },
  });

  const questionsMut = useMutation({
    mutationFn: api.foundryQuestions,
    onSuccess: (data) => {
      setQuestionSets(data.question_sets);
      if (data.fallback) setFallbackNotice(true);
    },
    onError: () => {
      // Fallback questions are baked into the API
      toast.error("问题生成失败");
    },
  });

  const composeMut = useMutation({
    mutationFn: api.foundryCompose,
    onSuccess: (data) => {
      setComposeResult(data);
      setFallbackNotice(data.fallback);
      setStep("preview");
    },
    onError: (err) => {
      setStep("error");
      toast.error(err instanceof Error ? err.message : "生成失败");
    },
  });

  const createMut = useMutation({
    mutationFn: (data: {
      title: string;
      premise: Record<string, unknown>;
      master_setting: Record<string, unknown>;
      synopsis: Record<string, unknown>;
      chapter_outlines: Array<Record<string, unknown>>;
    }) => api.createProject(data),
    onSuccess: (data) => {
      setStep("done");
      toast.success("项目创建成功！");
      setTimeout(() => {
        navigate(`/projects/${data.id}/planning`);
      }, 800);
    },
    onError: (err) => {
      setStep("error");
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

  const fetchQuestions = useCallback(
    (decon: FoundryDeconstruction) => {
      questionsMut.mutate({ deconstruction: decon });
    },
    [questionsMut]
  );

  const startDeconstruct = useCallback(() => {
    const nonEmpty = samples.map((s) => s.content.trim()).filter(Boolean);
    if (!bookTitle.trim()) {
      toast.error("请输入参考书书名");
      return;
    }
    if (nonEmpty.length === 0) {
      toast.error("请至少粘贴一段样章");
      return;
    }
    setStep("deconstructing");
    setDeconstruction(null);
    setFallbackNotice(false);
    deconstructMut.mutate({ book_title: bookTitle, sample_chapters: nonEmpty });
  }, [bookTitle, samples, deconstructMut]);

  const handleSelectOption = useCallback((questionId: string, optionId: string) => {
    setSelections((prev) => ({ ...prev, [questionId]: optionId }));
  }, []);

  const allQuestionsAnswered = questionSets.length > 0 && questionSets.every((q) => selections[q.id]);

  const startCompose = useCallback(() => {
    if (!allQuestionsAnswered) {
      toast.error("请回答所有选择题");
      return;
    }
    if (!deconstruction) return;
    setStep("composing");
    composeMut.mutate({
      book_title: bookTitle,
      deconstruction,
      selections,
      custom_notes: customNotes,
    });
  }, [allQuestionsAnswered, deconstruction, bookTitle, selections, customNotes, composeMut]);

  const handleCreateProject = useCallback(() => {
    if (!composeResult) return;
    setStep("creating");
    createMut.mutate({
      title: composeResult.premise.title as string || `${bookTitle}·改写`,
      premise: composeResult.premise,
      master_setting: composeResult.master_setting,
      synopsis: composeResult.synopsis,
      chapter_outlines: composeResult.first_volume_chapters.map((ch) => ({
        chapter_num: ch.chapter_num,
        title: ch.title,
        outline: ch.outline,
        must_cover_nodes: ch.must_cover_nodes,
        forbidden_zones: ch.forbidden_zones,
        key_characters: ch.key_characters,
        target_words: ch.target_words,
      })),
    });
  }, [composeResult, bookTitle, createMut]);

  const activeStepIndex = STEPS.findIndex((s) => s.key === step);

  return (
    <div className="min-h-[calc(100vh-4rem)] flex flex-col max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-3 border-b">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
          <ArrowLeft className="size-4" />
        </Button>
        <div className="flex-1">
          <h1 className="text-lg font-semibold flex items-center gap-2">
            <Wand2 className="size-5 text-primary" />
            AI 智能造书
          </h1>
          <p className="text-xs text-muted-foreground">
            从参考书提取模式，通过策略选择题生成完整原创设定
          </p>
        </div>
        {fallbackNotice && (
          <Badge variant="outline" className="text-amber-500 shrink-0">
            <AlertTriangle className="size-3 mr-1" />
            降级模式
          </Badge>
        )}
      </div>

      {/* Step Indicator */}
      {step !== "input" && step !== "error" && step !== "creating" && step !== "done" && (
        <StepIndicator currentStep={step} />
      )}

      <div className="flex-1 overflow-y-auto p-4">
        {/* ========== INPUT STEP ========== */}
        {step === "input" && (
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
                  粘贴 1-3 段样章（每段约 500-3000 字），AI 将分析其结构模式并生成策略选择题。
                  <span className="text-destructive font-medium">不要粘贴整本书。只需关键片段。红线下不复制原作角色、地名和具体情节。</span>
                </p>
                {samples.map((sample, idx) => (
                  <div key={sample.id} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium">样章 {idx + 1}</label>
                      {samples.length > 1 && (
                        <Button variant="ghost" size="sm" onClick={() => removeSample(sample.id)}>
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
              开始分析并生成选择题
            </Button>

            <div className="flex gap-3 text-xs text-muted-foreground">
              <div className="flex items-center gap-1">
                <ShieldAlert className="size-3 text-destructive" />
                仅提取模式，不写原作 canon
              </div>
              <div className="flex items-center gap-1">
                <Lightbulb className="size-3 text-primary" />
                差异化创作后一键生成
              </div>
            </div>
          </div>
        )}

        {/* ========== DECONSTRUCTING ========== */}
        {step === "deconstructing" && (
          <div className="flex items-center justify-center min-h-[20rem]">
            <div className="text-center space-y-4">
              <Loader2 className="size-8 animate-spin mx-auto text-primary" />
              <p className="text-lg font-medium">正在分析参考书...</p>
              <p className="text-sm text-muted-foreground">
                AI 正在提取黄金三章、爽点、人设、世界观、叙事节奏等模式
              </p>
              {questionsMut.isPending && (
                <p className="text-sm text-muted-foreground">
                  <Loader2 className="size-3 inline animate-spin mr-1" />
                  正在生成策略选择题...
                </p>
              )}
            </div>
          </div>
        )}

        {/* ========== DECONSTRUCTION ========== */}
        {step === "deconstruction" && deconstruction && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold">《{bookTitle}》拆解结果</h2>
                <p className="text-sm text-muted-foreground">
                  以下为可迁移模式分析，<span className="text-destructive font-medium">红线下禁止直接复制原作内容</span>
                </p>
              </div>
            </div>

            <Tabs defaultValue="transferable_patterns" className="w-full">
              <TabsList className="flex-wrap h-auto gap-1">
                {SECTION_CONFIG.filter((s) => {
                  const items = deconstruction[s.key];
                  return Array.isArray(items) && items.length > 0;
                }).map((s) => (
                  <TabsTrigger key={s.key} value={s.key} className="text-xs">
                    <s.icon className={`size-3 mr-1 ${s.color}`} />
                    {s.label}
                  </TabsTrigger>
                ))}
              </TabsList>

              {SECTION_CONFIG.map((s) => {
                const items = deconstruction[s.key];
                if (!Array.isArray(items) || items.length === 0) return null;
                const isRedFlag = s.key === "red_flags";

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
                                : "bg-muted"
                            }`}
                          >
                            {isRedFlag && <ShieldAlert className="size-4 shrink-0 mt-0.5" />}
                            <span className="flex-1">{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </TabsContent>
                );
              })}
            </Tabs>

            <div className="flex justify-end gap-3">
              <Button variant="outline" onClick={() => setStep("input")}>
                重新输入
              </Button>
              <Button
                onClick={() => setStep("questions")}
                disabled={questionSets.length === 0}
              >
                <ArrowRight className="size-4 mr-1" />
                下一步：策略选择
                {questionSets.length > 0 && (
                  <Badge variant="secondary" className="ml-2 text-xs">
                    {questionSets.length} 题
                  </Badge>
                )}
              </Button>
            </div>
          </div>
        )}

        {/* ========== QUESTIONS ========== */}
        {step === "questions" && (
          <div className="max-w-2xl mx-auto space-y-6">
            <div>
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <PenTool className="size-5 text-primary" />
                创作策略选择
              </h2>
              <p className="text-sm text-muted-foreground">
                基于拆书分析，选择与参考书差异化但保留可迁移模式的创作方向
              </p>
            </div>

            {questionSets.map((q, qIdx) => (
              <Card key={q.id} className={selections[q.id] ? "border-primary/30" : ""}>
                <CardHeader className="pb-3">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-xs">
                      {qIdx + 1}/{questionSets.length}
                    </Badge>
                    <CardTitle className="text-base">{q.title}</CardTitle>
                    {selections[q.id] && (
                      <CheckCircle2 className="size-4 text-green-500 ml-auto" />
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground">{q.description}</p>
                </CardHeader>
                <CardContent className="space-y-2">
                  {q.options.map((opt) => {
                    const isSelected = selections[q.id] === opt.id;
                    return (
                      <div
                        key={opt.id}
                        onClick={() => handleSelectOption(q.id, opt.id)}
                        className={`p-3 rounded-md border cursor-pointer transition-colors ${
                          isSelected
                            ? "bg-primary/10 border-primary/50"
                            : "bg-muted/30 border-transparent hover:bg-muted/60"
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <div className="mt-0.5 shrink-0">
                            <div
                              className={`size-4 rounded-full border-2 flex items-center justify-center ${
                                isSelected ? "border-primary" : "border-muted-foreground/30"
                              }`}
                            >
                              {isSelected && <div className="size-2 rounded-full bg-primary" />}
                            </div>
                          </div>
                          <div className="flex-1">
                            <p className="font-medium text-sm">{opt.label}</p>
                            <p className="text-xs text-muted-foreground mt-0.5">
                              {opt.description}
                            </p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </CardContent>
              </Card>
            ))}

            {/* Custom notes */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <FileText className="size-4 text-primary" />
                  补充备注（选填）
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Textarea
                  value={customNotes}
                  onChange={(e) => setCustomNotes(e.target.value)}
                  placeholder="任何额外的创作要求，例如：希望主角是女性、世界观偏科幻、不要有后宫情节..."
                  rows={3}
                />
              </CardContent>
            </Card>

            <div className="flex justify-end gap-3">
              <Button variant="outline" onClick={() => setStep("deconstruction")}>
                返回
              </Button>
              <Button
                onClick={startCompose}
                disabled={!allQuestionsAnswered || composeMut.isPending}
              >
                {composeMut.isPending ? (
                  <>
                    <Loader2 className="size-4 mr-1 animate-spin" />
                    生成中...
                  </>
                ) : (
                  <>
                    <Wand2 className="size-4 mr-1" />
                    生成完整设定
                  </>
                )}
              </Button>
            </div>
          </div>
        )}

        {/* ========== COMPOSING ========== */}
        {step === "composing" && (
          <div className="flex items-center justify-center min-h-[20rem]">
            <div className="text-center space-y-4">
              <Loader2 className="size-8 animate-spin mx-auto text-primary" />
              <p className="text-lg font-medium">正在生成原创设定...</p>
              <p className="text-sm text-muted-foreground">
                AI 正在基于你的选择组合生成 premise、世界观、总纲和章纲
              </p>
            </div>
          </div>
        )}

        {/* ========== PREVIEW ========== */}
        {step === "preview" && composeResult && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold">设定预览</h2>
                <p className="text-sm text-muted-foreground">
                  确认以下设定后创建项目
                </p>
              </div>
              {composeResult.fallback && (
                <Badge variant="outline" className="text-amber-500">
                  <AlertTriangle className="size-3 mr-1" />
                  降级模式
                </Badge>
              )}
            </div>

            {/* Premise */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <BookOpen className="size-4 text-primary" />
                  前提设定
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div><span className="font-medium">书名：</span>{(composeResult.premise.title as string) || "未命名"}</div>
                <div><span className="font-medium">题材：</span>{(composeResult.premise.genre as string) || "未设定"}</div>
                <div><span className="font-medium">卖点：</span>{(composeResult.premise.hook as string) || "未设定"}</div>
                <div><span className="font-medium">目标字数：</span>{(composeResult.premise.target_words as number) || 0} 字</div>
                <div><span className="font-medium">目标章数：</span>{(composeResult.premise.target_chapters as number) || 0} 章</div>
              </CardContent>
            </Card>

            {/* Synopsis */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <FileText className="size-4 text-primary" />
                  故事总纲
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <p className="text-muted-foreground leading-relaxed">
                  {(composeResult.synopsis.synopsis as string) || "暂无概述"}
                </p>
                {Array.isArray(composeResult.synopsis.volumes) && composeResult.synopsis.volumes.length > 0 && (
                  <div className="space-y-1">
                    <p className="font-medium">分卷规划：</p>
                    {composeResult.synopsis.volumes.map((vol: Record<string, unknown>, i: number) => (
                      <div key={i} className="text-muted-foreground">
                        第{vol.num}卷 {vol.title}：{vol.summary}（{vol.target_chapters}章）
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Chapter Outlines */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <BookMarked className="size-4 text-primary" />
                  第一卷章纲
                  <Badge variant="secondary" className="text-xs ml-auto">
                    {composeResult.first_volume_chapters.length} 章
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="max-h-80 overflow-y-auto space-y-2">
                  {composeResult.first_volume_chapters.map((ch) => (
                    <div key={ch.chapter_num} className="p-3 rounded-md bg-muted/30 text-sm">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium">第{ch.chapter_num}章</span>
                        <span>{ch.title}</span>
                        <Badge variant="outline" className="text-xs ml-auto">
                          {ch.target_words} 字
                        </Badge>
                      </div>
                      <p className="text-muted-foreground text-xs line-clamp-2">{ch.outline}</p>
                      {ch.must_cover_nodes.length > 0 && (
                        <div className="flex gap-1 flex-wrap mt-1">
                          {ch.must_cover_nodes.map((node, i) => (
                            <Badge key={i} variant="secondary" className="text-[10px]">
                              {node}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <div className="flex justify-end gap-3">
              <Button variant="outline" onClick={() => setStep("questions")}>
                返回修改
              </Button>
              <Button
                onClick={handleCreateProject}
                disabled={createMut.isPending}
              >
                {createMut.isPending ? (
                  <>
                    <Loader2 className="size-4 mr-1 animate-spin" />
                    创建中...
                  </>
                ) : (
                  <>
                    <Check className="size-4 mr-1" />
                    确认并创建项目
                  </>
                )}
              </Button>
            </div>
          </div>
        )}

        {/* ========== CREATING ========== */}
        {step === "creating" && (
          <div className="flex items-center justify-center min-h-[20rem]">
            <div className="text-center space-y-4">
              <Loader2 className="size-8 animate-spin mx-auto text-primary" />
              <p className="text-lg font-medium">正在创建项目...</p>
              <p className="text-sm text-muted-foreground">
                写入数据库、生成 story-system 契约文件
              </p>
            </div>
          </div>
        )}

        {/* ========== DONE ========== */}
        {step === "done" && (
          <div className="flex items-center justify-center min-h-[20rem]">
            <div className="text-center space-y-4">
              <div className="w-12 h-12 rounded-full bg-green-500/10 flex items-center justify-center mx-auto">
                <Check className="size-6 text-green-500" />
              </div>
              <p className="text-lg font-medium">项目创建成功！</p>
              <p className="text-sm text-muted-foreground">正在跳转到规划中心...</p>
            </div>
          </div>
        )}

        {/* ========== ERROR ========== */}
        {step === "error" && (
          <div className="flex items-center justify-center min-h-[20rem]">
            <div className="text-center space-y-4">
              <AlertCircle className="size-8 mx-auto text-destructive" />
              <p className="text-lg font-medium">处理失败</p>
              <div className="flex justify-center gap-3">
                <Button variant="outline" onClick={() => setStep("input")}>
                  重新开始
                </Button>
                <Button variant="outline" onClick={() => navigate("/")}>
                  返回项目中心
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
