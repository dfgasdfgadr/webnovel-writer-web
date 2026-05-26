import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Plus, Trash2, Loader2, User, Sword, Scroll, Package } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/layout/EmptyState";
import { ProjectNav } from "@/components/layout/ProjectNav";
import * as api from "@/lib/api";
import { toast } from "sonner";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const CARD_TYPES = [
  { key: "character", label: "角色", icon: User },
  { key: "faction", label: "势力", icon: Sword },
  { key: "rule", label: "规则", icon: Scroll },
  { key: "item", label: "道具", icon: Package },
];

export function CardsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("character");
  const [showCreate, setShowCreate] = useState(false);
  const [newLabel, setNewLabel] = useState("");
  const [newContent, setNewContent] = useState("");

  const { data: cards, isLoading } = useQuery({
    queryKey: ["cards", projectId, activeTab],
    queryFn: () => api.listCards(projectId!, activeTab),
    enabled: !!projectId,
  });

  const { data: project } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => api.getProject(projectId!),
    enabled: !!projectId,
  });

  const createMut = useMutation({
    mutationFn: (data: api.CardCreate) => api.createCard(projectId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cards", projectId] });
      setShowCreate(false);
      setNewLabel("");
      setNewContent("");
      toast.success("卡片已创建");
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "创建失败"),
  });

  const deleteMut = useMutation({
    mutationFn: (cardId: string) => api.deleteCard(projectId!, cardId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cards", projectId] });
      toast.success("卡片已删除");
    },
  });

  const handleCreate = () => {
    if (!newLabel.trim()) return;
    createMut.mutate({
      card_type: activeTab,
      label: newLabel.trim(),
      content: { text: newContent.trim() },
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 flex-wrap">
        <Link to={`/projects/${projectId}`}>
          <Button variant="ghost" size="sm">
            <ArrowLeft className="size-4 mr-1" />
            返回
          </Button>
        </Link>
        <h1 className="text-2xl font-serif font-semibold tracking-tight">设定卡片</h1>
        {project && <span className="text-sm text-muted-foreground">{project.title}</span>}
      </div>
      {projectId && <ProjectNav projectId={projectId} active="cards" />}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <div className="flex items-center justify-between mb-4">
          <TabsList>
            {CARD_TYPES.map((ct) => {
              const Icon = ct.icon;
              return (
                <TabsTrigger key={ct.key} value={ct.key} className="gap-1.5">
                  <Icon className="size-3.5" />
                  {ct.label}
                </TabsTrigger>
              );
            })}
          </TabsList>
          <Button size="sm" variant="outline" onClick={() => setShowCreate(true)}>
            <Plus className="size-3.5 mr-1" />
            新建卡片
          </Button>
        </div>

        {CARD_TYPES.map((ct) => (
          <TabsContent key={ct.key} value={ct.key}>
            {isLoading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[1, 2, 3].map((i) => <Skeleton key={i} className="h-40" />)}
              </div>
            ) : !cards || cards.length === 0 ? (
              <EmptyState
                icon={ct.icon}
                title={`暂无${ct.label}卡片`}
                description={`点击上方「新建卡片」创建第一个${ct.label}卡片`}
              />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {cards.map((card) => (
                  <Card key={card.id} className="relative group">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm flex items-center justify-between">
                        {card.label}
                        <Button
                          variant="ghost"
                          size="icon"
                          className="size-6 opacity-0 group-hover:opacity-100 transition-opacity"
                          onClick={() => deleteMut.mutate(card.id)}
                        >
                          <Trash2 className="size-3.5 text-muted-foreground hover:text-red-400" />
                        </Button>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-xs text-muted-foreground whitespace-pre-wrap">
                        {typeof card.content === "object" && card.content
                          ? (card.content as Record<string, unknown>).text as string || JSON.stringify(card.content)
                          : String(card.content)}
                      </p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>
        ))}
      </Tabs>

      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>新建{CARD_TYPES.find((c) => c.key === activeTab)?.label}卡片</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="card-label">名称</Label>
              <Input
                id="card-label"
                value={newLabel}
                onChange={(e) => setNewLabel(e.target.value)}
                placeholder="卡片名称"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="card-content">描述</Label>
              <Textarea
                id="card-content"
                value={newContent}
                onChange={(e) => setNewContent(e.target.value)}
                placeholder="卡片描述内容"
                className="h-32 resize-none"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setShowCreate(false)}>取消</Button>
            <Button onClick={handleCreate} disabled={!newLabel.trim() || createMut.isPending}>
              {createMut.isPending ? <Loader2 className="size-4 animate-spin" /> : "创建"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
