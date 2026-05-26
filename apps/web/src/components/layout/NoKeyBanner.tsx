import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, ExternalLink } from "lucide-react";
import { getLlmSettings } from "@/lib/api";

export function NoKeyBanner() {
  const { data, isLoading } = useQuery({
    queryKey: ["llmSettings"],
    queryFn: getLlmSettings,
    staleTime: 60_000,
  });

  if (isLoading || !data || data.api_key_masked) return null;

  return (
    <div className="flex items-center gap-3 px-4 py-2 bg-amber-500/10 border-b border-amber-500/20 text-sm">
      <AlertTriangle className="size-4 text-amber-400 shrink-0" />
      <span className="text-amber-300/80">
        尚未配置 LLM API Key，AI 功能将使用降级模式。
      </span>
      <a
        href="/settings"
        className="flex items-center gap-1 text-amber-400 hover:text-amber-300 transition-colors ml-auto"
      >
        前往配置
        <ExternalLink className="size-3" />
      </a>
    </div>
  );
}
