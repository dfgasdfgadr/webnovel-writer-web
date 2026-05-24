import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import {
  getLlmSettings,
  updateLlmSettings,
  testLlmConnection,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { Eye, EyeOff, CheckCircle, XCircle, Loader2 } from "lucide-react";

interface LlmFormValues {
  api_key: string;
  base_url: string;
  model: string;
}

export function SettingsPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [showKey, setShowKey] = useState(false);
  const [savedKeyMasked, setSavedKeyMasked] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);

  const form = useForm<LlmFormValues>({
    defaultValues: {
      api_key: "",
      base_url: "",
      model: "",
    },
  });

  useEffect(() => {
    loadSettings();
  }, []);

  async function loadSettings() {
    try {
      const data = await getLlmSettings();
      setSavedKeyMasked(data.api_key_masked);
      form.reset({
        api_key: "",
        base_url: data.base_url || "https://api.openai.com/v1",
        model: data.model || "gpt-4o",
      });
    } catch {
      setSavedKeyMasked(null);
    } finally {
      setLoading(false);
    }
  }

  async function onSubmit(values: LlmFormValues) {
    setSaving(true);
    try {
      const payload: Record<string, string> = {};
      if (values.api_key) payload.api_key = values.api_key;
      if (values.base_url) payload.base_url = values.base_url;
      if (values.model) payload.model = values.model;
      const updated = await updateLlmSettings(payload);
      setSavedKeyMasked(updated.api_key_masked ?? null);
      form.setValue("api_key", "");
      toast.success("LLM 设置已保存");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "保存失败");
    } finally {
      setSaving(false);
    }
  }

  async function handleTestConnection() {
    setTesting(true);
    setTestResult(null);
    try {
      const values = form.getValues();
      const payload: Record<string, string> = {};
      if (values.api_key) payload.api_key = values.api_key;
      if (values.base_url) payload.base_url = values.base_url;
      if (values.model) payload.model = values.model;
      const data = await testLlmConnection(payload);
      setTestResult({ success: data.success, message: data.message });
    } catch (e) {
      setTestResult({
        success: false,
        message: e instanceof Error ? e.message : "测试失败",
      });
    } finally {
      setTesting(false);
    }
  }

  const apiKeyValue = form.watch("api_key");

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-96" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-serif font-semibold tracking-tight">LLM 设置</h1>
        <p className="text-muted-foreground mt-1">
          配置你的大语言模型 API，用于 AI 写作、审查和推演。API Key 将加密存储，不会写入日志。
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>API 配置</CardTitle>
          <CardDescription>
            支持所有 OpenAI 兼容接口（如 DeepSeek、OpenRouter、通义千问等）
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="api_key">API Key</Label>
            <div className="relative">
              <Input
                id="api_key"
                type={showKey ? "text" : "password"}
                placeholder={savedKeyMasked ? `已配置 ${savedKeyMasked}` : "sk-..."}
                {...form.register("api_key")}
                className="pr-10 font-mono"
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                {showKey ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
              </button>
            </div>
            <p className="text-xs text-muted-foreground">
              留空则不更新已保存的 Key。在浏览器设置页配置的 Key 优先于 .env 全局配置。
            </p>
            {savedKeyMasked && !apiKeyValue && (
              <p className="text-xs text-emerald-400 flex items-center gap-1">
                <CheckCircle className="size-3.5 shrink-0" />
                已保存 Key：<span className="font-mono">{savedKeyMasked}</span>
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="base_url">Base URL</Label>
            <Input
              id="base_url"
              placeholder="https://api.openai.com/v1"
              {...form.register("base_url")}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="model">Model</Label>
            <Input
              id="model"
              placeholder="gpt-4o"
              {...form.register("model")}
            />
          </div>

          <Separator />

          <div className="flex items-center gap-4">
            <Button onClick={form.handleSubmit(onSubmit)} disabled={saving}>
              {saving && <Loader2 className="size-4 mr-2 animate-spin" />}
              保存设置
            </Button>
            <Button
              variant="outline"
              onClick={handleTestConnection}
              disabled={testing}
            >
              {testing && <Loader2 className="size-4 mr-2 animate-spin" />}
              测试连接
            </Button>
          </div>

          {testResult && (
            <div
              className={`flex items-start gap-3 p-4 rounded-lg border ${
                testResult.success
                  ? "bg-emerald-500/10 border-emerald-500/30"
                  : "bg-red-500/10 border-red-500/30"
              }`}
            >
              {testResult.success ? (
                <CheckCircle className="size-5 text-emerald-400 shrink-0 mt-0.5" />
              ) : (
                <XCircle className="size-5 text-red-400 shrink-0 mt-0.5" />
              )}
              <div>
                <p className={`text-sm font-medium ${testResult.success ? "text-emerald-400" : "text-red-400"}`}>
                  {testResult.success ? "连接成功" : "连接失败"}
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  {testResult.message}
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>优先级说明</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <p>LLM 配置优先级（从高到低）：</p>
          <ol className="list-decimal list-inside space-y-1 pl-2">
            <li><strong>用户设置</strong>（本页面配置的 API Key）</li>
            <li><strong>环境变量</strong>（.env 中的 LLM_API_KEY）</li>
            <li><strong>默认值</strong>（gpt-4o @ api.openai.com）</li>
          </ol>
        </CardContent>
      </Card>
    </div>
  );
}
