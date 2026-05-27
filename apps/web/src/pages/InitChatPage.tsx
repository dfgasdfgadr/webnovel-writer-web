import { useState, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import {
  Send, Loader2, Bot, User, ArrowLeft, Sparkles, Check,
  BookOpen, AlertTriangle, BarChart3, Zap, Target,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { toast } from "sonner";
import * as api from "@/lib/api";
import type { InitChatMessage, InitChatResponse, InitScheme } from "@/lib/api";

type ChatPhase = "idle" | "chatting" | "schemes" | "creating" | "done" | "error";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  parsed?: InitChatResponse;
}

const FIELD_LABELS: Record<string, string> = {
  title: "书名",
  genre: "题材",
  hook: "核心卖点",
  protagonist_name: "主角名",
  world_building: "世界观",
  power_system: "力量体系",
  golden_finger: "金手指",
  constraints: "创意约束",
};

function ScoreBar({ label, score }: { label: string; score: number }) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-14 text-muted-foreground shrink-0">{label}</span>
      <Progress value={score} className="h-1.5 flex-1" />
      <span className="w-6 text-right font-medium">{score}</span>
    </div>
  );
}

function SchemeCard({
  scheme,
  index,
  selected,
  onSelect,
}: {
  scheme: InitScheme;
  index: number;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <Card
      className={`cursor-pointer transition-all hover:shadow-md ${
        selected ? "ring-2 ring-primary border-primary" : ""
      }`}
      onClick={onSelect}
    >
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">{scheme.name}</CardTitle>
          {selected && <Check className="size-4 text-primary" />}
        </div>
        <Badge variant="secondary" className="w-fit text-xs">
          {scheme.genre_focus}
        </Badge>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <div className="space-y-1">
          <p className="text-muted-foreground text-xs">卖点变体</p>
          <p className="line-clamp-2">{scheme.hook_variation}</p>
        </div>
        <div className="space-y-1">
          <p className="text-muted-foreground text-xs">力量演进</p>
          <p className="line-clamp-2">{scheme.power_evolution}</p>
        </div>
        <div className="space-y-1">
          <p className="text-muted-foreground text-xs">建议规模</p>
          <p>{scheme.target_scale}</p>
        </div>
        <div className="pt-2 border-t space-y-1.5">
          <ScoreBar label="创新性" score={scheme.scores.innovation} />
          <ScoreBar label="市场性" score={scheme.scores.marketability} />
          <ScoreBar label="一致性" score={scheme.scores.coherence} />
          <ScoreBar label="深度" score={scheme.scores.depth} />
          <ScoreBar label="可读性" score={scheme.scores.readability} />
        </div>
      </CardContent>
    </Card>
  );
}

export function InitChatPage() {
  const navigate = useNavigate();
  const [phase, setPhase] = useState<ChatPhase>("idle");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [schemes, setSchemes] = useState<InitScheme[]>([]);
  const [selectedScheme, setSelectedScheme] = useState<number | null>(null);
  const [collectedFields, setCollectedFields] = useState<Set<string>>(new Set());
  const [fallbackNotice, setFallbackNotice] = useState(false);
  const abortRef = useRef(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, []);

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

  const startChat = useCallback(() => {
    setPhase("chatting");
    setMessages([
      {
        role: "assistant",
        content: "你好！我是你的网文创作助手。让我们一步步把你的创意变成可执行的作品设定。\n\n首先，请告诉我：",
        parsed: { status: "asking", question: "你的作品是什么题材？", missing_fields: ["genre"], hint: "" },
      },
    ]);
  }, []);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || isLoading) return;

      const userMsg: ChatMessage = { role: "user", content: text };
      setMessages((prev) => [...prev, userMsg]);
      setInput("");
      setIsLoading(true);
      abortRef.current = false;

      const history: InitChatMessage[] = messages
        .filter((m) => m.role === "user" || (m.role === "assistant" && m.parsed?.status === "asking"))
        .map((m) => ({ role: m.role, content: m.content }));
      history.push({ role: "user", content: text });

      try {
        let lastResponse: InitChatResponse | null = null;
        for await (const chunk of api.initChatStream(text, history)) {
          if (abortRef.current) break;
          lastResponse = chunk;

          if (chunk.status === "error") {
            setMessages((prev) => [
              ...prev,
              { role: "assistant", content: chunk.error || "发生错误", parsed: chunk },
            ]);
            setPhase("error");
            break;
          }

          if (chunk.status === "asking") {
            setMessages((prev) => [
              ...prev,
              {
                role: "assistant",
                content: chunk.question || "",
                parsed: chunk,
              },
            ]);
            if (chunk.missing_fields) {
              setCollectedFields((prev) => {
                const next = new Set(prev);
                // Mark all non-missing fields as collected
                Object.keys(FIELD_LABELS).forEach((f) => {
                  if (!chunk.missing_fields!.includes(f)) next.add(f);
                });
                return next;
              });
            }
          }

          if (chunk.status === "complete") {
            if (chunk.schemes && chunk.schemes.length > 0) {
              setSchemes(chunk.schemes);
              setPhase("schemes");
              setMessages((prev) => [
                ...prev,
                {
                  role: "assistant",
                  content: `太棒了！所有信息已收集完毕。我为你准备了 ${chunk.schemes.length} 套创意方案，请选择最符合你心意的一套：`,
                  parsed: chunk,
                },
              ]);
            } else {
              // Fallback: no schemes returned, try initSchemes API
              const premise = buildPremiseFromHistory(history);
              const schemeRes = await api.initSchemes(premise);
              if (schemeRes.schemes) {
                setSchemes(schemeRes.schemes);
                setPhase("schemes");
                setFallbackNotice(true);
              }
            }
            break;
          }
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : "连接失败";
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: `连接异常：${msg}`, parsed: { status: "error", error: msg } },
        ]);
        setPhase("error");
      } finally {
        setIsLoading(false);
        setTimeout(scrollToBottom, 100);
      }
    },
    [messages, isLoading, scrollToBottom]
  );

  const handleCreateProject = useCallback(() => {
    if (selectedScheme === null) {
      toast.error("请先选择一个方案");
      return;
    }

    const scheme = schemes[selectedScheme];
    const history = messages
      .filter((m) => m.role === "user")
      .map((m) => {
        try {
          return JSON.parse(m.content);
        } catch {
          return { raw: m.content };
        }
      });

    // Extract collected fields from history
    const premise: Record<string, unknown> = {};
    for (const h of history) {
      if (typeof h === "object" && h !== null) {
        Object.assign(premise, h);
      }
    }

    setPhase("creating");
    createMutation.mutate({
      title: (premise.title as string) || scheme.name,
      description: scheme.hook_variation,
      genre: (premise.genre as string) || scheme.genre_focus,
      hook: (premise.hook as string) || scheme.hook_variation,
      protagonist: {
        name: (premise.protagonist_name as string) || "主角",
      },
      world_building: {
        description: (premise.world_building as string) || "",
      },
      power_system: (premise.power_system as string) || scheme.power_evolution,
      golden_finger: (premise.golden_finger as string) || "",
      constraints: [scheme.genre_focus, scheme.hook_variation, scheme.power_evolution],
      target_words: 1000000,
      target_chapters: 500,
    });
  }, [selectedScheme, schemes, messages, createMutation]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  const completionRate = Math.round((collectedFields.size / 8) * 100);

  return (
    <div className="min-h-[calc(100vh-4rem)] flex flex-col max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-3 border-b">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
          <ArrowLeft className="size-4" />
        </Button>
        <div className="flex-1">
          <h1 className="text-lg font-semibold flex items-center gap-2">
            <Sparkles className="size-5 text-primary" />
            对话开书
          </h1>
          <p className="text-xs text-muted-foreground">
            通过自然对话，AI 助手帮你梳理创作思路
          </p>
        </div>
        {phase === "chatting" && (
          <div className="text-xs text-muted-foreground">
            采集进度
            <Progress value={completionRate} className="w-24 h-1.5 mt-1" />
          </div>
        )}
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {phase === "idle" && (
          <div className="flex-1 flex items-center justify-center p-8">
            <Card className="max-w-md w-full text-center">
              <CardHeader>
                <div className="mx-auto w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-3">
                  <Bot className="size-6 text-primary" />
                </div>
                <CardTitle>对话式开书</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  通过多轮对话，AI 助手会引导你逐步明确书名、题材、卖点、主角、世界观等关键信息，
                  最后生成 2-3 套创意约束方案供你选择。
                </p>
                <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                  <div className="flex items-center gap-1"><BookOpen className="size-3" /> 书名与题材</div>
                  <div className="flex items-center gap-1"><Zap className="size-3" /> 核心卖点</div>
                  <div className="flex items-center gap-1"><User className="size-3" /> 主角设定</div>
                  <div className="flex items-center gap-1"><Target className="size-3" /> 世界观与力量体系</div>
                </div>
                <Button onClick={startChat} className="w-full" data-testid="start-chat-btn">
                  <Sparkles className="size-4 mr-1" />
                  开始对话
                </Button>
                <Button variant="ghost" size="sm" className="w-full" onClick={() => navigate("/projects/new/wizard")}>
                  或使用静态向导快速创建
                </Button>
              </CardContent>
            </Card>
          </div>
        )}

        {(phase === "chatting" || phase === "error") && (
          <>
            {/* Messages */}
            <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  {msg.role === "assistant" && (
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                      <Bot className="size-4 text-primary" />
                    </div>
                  )}
                  <div
                    className={`max-w-[80%] rounded-lg px-4 py-2.5 text-sm ${
                      msg.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted"
                    }`}
                  >
                    {msg.parsed?.status === "error" ? (
                      <div className="flex items-start gap-2 text-destructive">
                        <AlertTriangle className="size-4 shrink-0 mt-0.5" />
                        <span>{msg.content}</span>
                      </div>
                    ) : (
                      <div className="whitespace-pre-wrap">{msg.content}</div>
                    )}
                    {msg.parsed?.hint && (
                      <p className="text-xs text-muted-foreground mt-2 border-t pt-2">
                        {msg.parsed.hint}
                      </p>
                    )}
                  </div>
                  {msg.role === "user" && (
                    <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center shrink-0">
                      <User className="size-4" />
                    </div>
                  )}
                </div>
              ))}
              {isLoading && (
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                    <Bot className="size-4 text-primary" />
                  </div>
                  <div className="bg-muted rounded-lg px-4 py-2.5">
                    <Loader2 className="size-4 animate-spin text-muted-foreground" />
                  </div>
                </div>
              )}
              {fallbackNotice && (
                <div className="flex justify-center">
                  <Badge variant="outline" className="text-xs text-amber-500">
                    <AlertTriangle className="size-3 mr-1" />
                    已使用本地降级方案生成
                  </Badge>
                </div>
              )}
            </div>

            {/* Input */}
            <div className="border-t p-4">
              <div className="flex gap-2">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="输入你的想法..."
                  disabled={isLoading}
                  className="flex-1"
                />
                <Button
                  size="icon"
                  aria-label="发送"
                  onClick={() => sendMessage(input)}
                  disabled={isLoading || !input.trim()}
                >
                  {isLoading ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : (
                    <Send className="size-4" />
                  )}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                按 Enter 发送，Shift+Enter 换行
              </p>
            </div>
          </>
        )}

        {phase === "schemes" && (
          <div className="flex-1 overflow-y-auto p-4">
            <div className="mb-4">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <BarChart3 className="size-5 text-primary" />
                创意约束方案
              </h2>
              <p className="text-sm text-muted-foreground">
                基于你的创作信息，AI 生成了以下方案。选择最符合你心意的一套：
              </p>
            </div>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {schemes.map((scheme, i) => (
                <SchemeCard
                  key={i}
                  scheme={scheme}
                  index={i}
                  selected={selectedScheme === i}
                  onSelect={() => setSelectedScheme(i)}
                />
              ))}
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <Button variant="outline" onClick={() => setPhase("chatting")}>
                返回对话
              </Button>
              <Button
                onClick={handleCreateProject}
                disabled={selectedScheme === null || createMutation.isPending}
              >
                {createMutation.isPending ? (
                  <>
                    <Loader2 className="size-4 mr-1 animate-spin" />
                    创建中...
                  </>
                ) : (
                  <>
                    <Check className="size-4 mr-1" />
                    确认创建项目
                  </>
                )}
              </Button>
            </div>
          </div>
        )}

        {phase === "creating" && (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center space-y-4">
              <Loader2 className="size-8 animate-spin mx-auto text-primary" />
              <p className="text-lg font-medium">正在创建项目...</p>
              <p className="text-sm text-muted-foreground">
                AI 正在生成设定集、总纲和故事系统
              </p>
            </div>
          </div>
        )}

        {phase === "done" && (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center space-y-4">
              <div className="w-12 h-12 rounded-full bg-green-500/10 flex items-center justify-center mx-auto">
                <Check className="size-6 text-green-500" />
              </div>
              <p className="text-lg font-medium">项目创建成功！</p>
              <p className="text-sm text-muted-foreground">正在跳转到规划中心...</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function buildPremiseFromHistory(history: InitChatMessage[]): Record<string, unknown> {
  const premise: Record<string, unknown> = {};
  for (const msg of history) {
    if (msg.role !== "user") continue;
    try {
      const data = JSON.parse(msg.content);
      Object.assign(premise, data);
    } catch {
      // not JSON, treat as raw text for last field
    }
  }
  return premise;
}
