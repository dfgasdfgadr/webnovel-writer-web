import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Search, Loader2, FileText, Layers } from "lucide-react";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import * as api from "@/lib/api";
import { useAuthStore } from "@/stores/auth";

export function CommandSearch() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const navigate = useNavigate();
  const isAuth = useAuthStore((s) => s.isAuthenticated);

  // Get current project from URL
  const pathParts = window.location.pathname.split("/");
  const projectIndex = pathParts.indexOf("projects");
  const projectId = projectIndex >= 0 && pathParts.length > projectIndex + 1
    ? pathParts[projectIndex + 1]
    : null;

  const { data: results, isLoading } = useQuery({
    queryKey: ["search", projectId, query],
    queryFn: () => api.searchProject(projectId!, query, "all"),
    enabled: !!projectId && query.length > 1,
  });

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if ((e.key === "k" && (e.metaKey || e.ctrlKey)) || e.key === "/") {
        e.preventDefault();
        if (isAuth) setOpen((o) => !o);
      }
    };
    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, [isAuth]);

  const handleSelect = useCallback((docId: string, meta: Record<string, unknown>) => {
    setOpen(false);
    setQuery("");
    if (projectId && meta.entity_type) {
      // Navigate to relevant section
      navigate(`/projects/${projectId}/cards`);
    } else if (projectId) {
      navigate(`/projects/${projectId}`);
    }
  }, [projectId, navigate]);

  if (!isAuth) return null;

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="hidden lg:flex items-center gap-2 px-3 py-1.5 text-sm text-muted-foreground border rounded-md bg-muted/30 hover:bg-muted/60 transition-colors"
      >
        <Search className="size-3.5" />
        <span>搜索...</span>
        <kbd className="ml-auto text-[10px] text-muted-foreground/50">Ctrl+K</kbd>
      </button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-lg p-0 gap-0">
          <DialogHeader className="p-4 pb-0">
            <DialogTitle className="sr-only">项目搜索</DialogTitle>
          </DialogHeader>
          <div className="flex items-center border-b px-4 pb-3">
            <Search className="size-4 text-muted-foreground mr-2 shrink-0" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={projectId ? "搜索项目内实体与卡片..." : "打开项目后可用 Cmd+K 搜索"}
              className="border-0 p-0 h-auto text-sm focus-visible:ring-0 focus-visible:ring-offset-0 shadow-none"
              autoFocus
            />
          </div>
          {projectId && query.length > 1 && (
            <ScrollArea className="max-h-64">
              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="size-5 animate-spin text-muted-foreground" />
                </div>
              ) : results && results.length > 0 ? (
                <div className="py-2">
                  {results.map((r) => (
                    <button
                      key={r.doc_id}
                      className="flex items-start gap-3 w-full px-4 py-2.5 text-left hover:bg-amber-500/10 transition-colors"
                      onClick={() => handleSelect(r.doc_id, r.meta)}
                    >
                      {r.meta.entity_type ? (
                        <Layers className="size-4 text-muted-foreground mt-0.5 shrink-0" />
                      ) : (
                        <FileText className="size-4 text-muted-foreground mt-0.5 shrink-0" />
                      )}
                      <div className="min-w-0">
                        <div className="text-sm font-medium truncate">{r.title}</div>
                        <div className="text-xs text-muted-foreground truncate">{r.content.slice(0, 100)}</div>
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="py-8 text-center text-sm text-muted-foreground">
                  无搜索结果
                </div>
              )}
            </ScrollArea>
          )}
          {!projectId && (
            <div className="py-8 text-center text-sm text-muted-foreground">
              请先进入项目后使用搜索功能
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
