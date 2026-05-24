import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import {
  Loader2, ArrowRight, ArrowLeft, BookOpen,
  Sparkles, User, Globe, Zap, Check,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { toast } from "sonner";
import * as api from "@/lib/api";

interface WizardData {
  genre: string;
  hook: string;
  protagonist: { name: string; traits: string };
  world_building: { description: string; key_locations: string };
  power_system: string;
}

const STEPS = [
  { key: "genre", label: "题材与卖点", icon: BookOpen },
  { key: "protagonist", label: "主角设定", icon: User },
  { key: "world", label: "世界观", icon: Globe },
  { key: "power", label: "力量体系", icon: Zap },
  { key: "review", label: "确认创建", icon: Check },
];

const KEY_FIELDS = ["genre", "hook", "protagonist"] as const;

function isStepComplete(data: WizardData, step: string): boolean {
  switch (step) {
    case "genre": return data.genre.trim().length > 0 && data.hook.trim().length > 0;
    case "protagonist": return data.protagonist.name.trim().length > 0;
    case "world": return data.world_building.description.trim().length > 0;
    case "power": return data.power_system.trim().length > 0;
    default: return true;
  }
}

function gateCheck(data: WizardData): string[] {
  const missing: string[] = [];
  if (!data.genre.trim()) missing.push("题材");
  if (!data.hook.trim()) missing.push("核心卖点");
  if (!data.protagonist.name.trim()) missing.push("主角名");
  return missing;
}

export function DeepInitWizard() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [data, setData] = useState<WizardData>({
    genre: "",
    hook: "",
    protagonist: { name: "", traits: "" },
    world_building: { description: "", key_locations: "" },
    power_system: "",
  });

  const createMutation = useMutation({
    mutationFn: async () => {
      const project = await api.createProject({ title: data.genre || "新项目", genre: data.genre, description: data.hook });
      return project;
    },
    onSuccess: (project) => {
      toast.success("项目创建成功，跳转到规划中心");
      navigate(`/projects/${project.id}/planning`);
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "创建失败"),
  });

  const update = (patch: Partial<WizardData>) => setData((d) => ({ ...d, ...patch }));

  const currentStep = STEPS[step];
  const progress = ((step + 1) / STEPS.length) * 100;

  const handleNext = () => {
    if (step === STEPS.length - 1) {
      const missing = gateCheck(data);
      if (missing.length > 0) {
        toast.error(`请填写必要信息：${missing.join("、")}`);
        return;
      }
      createMutation.mutate();
      return;
    }
    setStep((s) => s + 1);
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center p-4">
      <Card className="w-full max-w-lg">
        <CardHeader className="text-center">
          <CardTitle className="font-serif text-2xl flex items-center justify-center gap-2">
            <Sparkles className="size-6 text-amber-400" />
            新建项目向导
          </CardTitle>
          <CardDescription>分步填写核心设定，打造完整世界观</CardDescription>
          <Progress value={progress} className="mt-2 h-1.5" />
        </CardHeader>
        <CardContent className="space-y-6 min-h-[320px]">
          {/* Step indicator */}
          <div className="flex items-center justify-center gap-1">
            {STEPS.map((s, i) => (
              <div key={s.key} className="flex items-center">
                <Badge
                  variant={i === step ? "default" : i < step ? "secondary" : "outline"}
                  className={`text-xs ${i === step ? "bg-amber-500/15 text-amber-400 border-amber-500/30" : ""}`}
                >
                  {i + 1}
                </Badge>
                {i < STEPS.length - 1 && <div className="w-4 h-px bg-border mx-0.5" />}
              </div>
            ))}
          </div>

          {/* Step 1: Genre & Hook */}
          {step === 0 && (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="genre">题材 *</Label>
                <Input
                  id="genre"
                  value={data.genre}
                  onChange={(e) => update({ genre: e.target.value })}
                  placeholder="如：玄幻、都市、科幻、仙侠..."
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="hook">核心卖点 *</Label>
                <Textarea
                  id="hook"
                  value={data.hook}
                  onChange={(e) => update({ hook: e.target.value })}
                  placeholder="一句话描述故事最吸引人的地方..."
                  className="h-24 resize-none"
                />
              </div>
            </div>
          )}

          {/* Step 2: Protagonist */}
          {step === 1 && (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="protagName">主角名 *</Label>
                <Input
                  id="protagName"
                  value={data.protagonist.name}
                  onChange={(e) => update({ protagonist: { ...data.protagonist, name: e.target.value } })}
                  placeholder="主角姓名"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="protagTraits">主角特质</Label>
                <Textarea
                  id="protagTraits"
                  value={data.protagonist.traits}
                  onChange={(e) => update({ protagonist: { ...data.protagonist, traits: e.target.value } })}
                  placeholder="性格、能力、背景故事..."
                  className="h-24 resize-none"
                />
              </div>
            </div>
          )}

          {/* Step 3: World Building */}
          {step === 2 && (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="worldDesc">世界观描述 *</Label>
                <Textarea
                  id="worldDesc"
                  value={data.world_building.description}
                  onChange={(e) => update({ world_building: { ...data.world_building, description: e.target.value } })}
                  placeholder="世界背景、种族、势力格局..."
                  className="h-28 resize-none"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="locations">关键地点</Label>
                <Input
                  id="locations"
                  value={data.world_building.key_locations}
                  onChange={(e) => update({ world_building: { ...data.world_building, key_locations: e.target.value } })}
                  placeholder="重要地名，用逗号分隔"
                />
              </div>
            </div>
          )}

          {/* Step 4: Power System */}
          {step === 3 && (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="powerSys">力量体系描述</Label>
                <Textarea
                  id="powerSys"
                  value={data.power_system}
                  onChange={(e) => update({ power_system: e.target.value })}
                  placeholder="修炼等级、能力分类、力量来源..."
                  className="h-32 resize-none"
                />
                <p className="text-xs text-muted-foreground">可选，也可在规划中心细化</p>
              </div>
            </div>
          )}

          {/* Step 5: Review */}
          {step === 4 && (
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground mb-3">确认以下设定后创建项目并进入规划中心：</p>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between"><span className="text-muted-foreground">题材</span><span>{data.genre || <span className="text-red-400">未填写</span>}</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">卖点</span><span>{data.hook || <span className="text-red-400">未填写</span>}</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">主角</span><span>{data.protagonist.name || <span className="text-red-400">未填写</span>}</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">世界观</span><span>{data.world_building.description ? `${data.world_building.description.slice(0, 30)}...` : <span className="text-red-400">未填写</span>}</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">力量体系</span><span>{data.power_system || "未填写"}</span></div>
              </div>
              {gateCheck(data).length > 0 && (
                <p className="text-xs text-amber-400 mt-2">
                  仍有必填项未完成：{gateCheck(data).join("、")}
                </p>
              )}
            </div>
          )}
        </CardContent>

        <div className="flex items-center justify-between p-4 border-t">
          <Button
            variant="ghost"
            disabled={step === 0}
            onClick={() => setStep((s) => s - 1)}
          >
            <ArrowLeft className="size-4 mr-1" />
            上一步
          </Button>

          <span className="text-xs text-muted-foreground">
            {step + 1} / {STEPS.length}
          </span>

          <Button onClick={handleNext} disabled={createMutation.isPending}>
            {createMutation.isPending ? (
              <Loader2 className="size-4 mr-1 animate-spin" />
            ) : step === STEPS.length - 1 ? (
              <Check className="size-4 mr-1" />
            ) : (
              <ArrowRight className="size-4 mr-1" />
            )}
            {step === STEPS.length - 1 ? "创建项目" : "下一步"}
          </Button>
        </div>
      </Card>
    </div>
  );
}
