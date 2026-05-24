import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft, Loader2, User, MapPin, Sword, BookOpen,
  ChevronRight, AlertTriangle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { EmptyState } from "@/components/layout/EmptyState";
import { ProjectNav } from "@/components/layout/ProjectNav";
import * as api from "@/lib/api";
import type { GraphNode, GraphEdge, TimelineItem } from "@/lib/api";

const typeIcons: Record<string, React.ReactNode> = {
  character: <User className="size-4" />,
  location: <MapPin className="size-4" />,
  item: <Sword className="size-4" />,
  faction: <BookOpen className="size-4" />,
};

const typeColors: Record<string, string> = {
  character: "bg-blue-500/20 border-blue-500/40 text-blue-400",
  location: "bg-emerald-500/20 border-emerald-500/40 text-emerald-400",
  item: "bg-amber-500/20 border-amber-500/40 text-amber-400",
  faction: "bg-purple-500/20 border-purple-500/40 text-purple-400",
};

export function GraphView() {
  const { projectId } = useParams<{ projectId: string }>();
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  const { data: project } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => api.getProject(projectId!),
    enabled: !!projectId,
  });

  const { data: graph, isLoading } = useQuery({
    queryKey: ["graph", projectId],
    queryFn: () => api.getGraphData(projectId!),
    enabled: !!projectId,
  });

  const nodeMap = new Map(graph?.nodes.map((n) => [n.id, n]) || []);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (!graph || graph.nodes.length === 0) {
    return (
      <div>
        <div className="mb-4">
          <Link
            to="/"
            className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1 mb-2"
          >
            <ArrowLeft className="size-3" />
            项目列表
          </Link>
          <h1 className="font-serif text-2xl font-semibold">关系图谱</h1>
          {project && (
            <p className="text-sm text-muted-foreground mt-1">{project.title}</p>
          )}
        </div>
        <ProjectNav projectId={projectId!} active="graph" className="mb-6" />
        <EmptyState
          icon={BookOpen}
          title="暂无实体数据"
          description="从写作台运行 DataAgent 提取实体后，这里会显示角色、地点等关系图谱。"
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="mb-4">
        <Link
          to="/"
          className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1 mb-2"
        >
          <ArrowLeft className="size-3" />
          项目列表
        </Link>
        <h1 className="font-serif text-2xl font-semibold">关系图谱</h1>
        {project && (
          <p className="text-sm text-muted-foreground mt-1">{project.title}</p>
        )}
      </div>
      <ProjectNav projectId={projectId!} active="graph" className="mb-2" />

      <Tabs defaultValue="graph">
        <TabsList>
          <TabsTrigger value="graph">实体关系图</TabsTrigger>
          <TabsTrigger value="timeline">伏笔时间线</TabsTrigger>
        </TabsList>

        <TabsContent value="graph" className="mt-4">
          <div className="grid grid-cols-[1fr_300px] gap-4">
            {/* Graph canvas - SVG based */}
            <Card>
              <CardContent className="p-6">
                <div className="relative w-full min-h-[500px] bg-muted/30 rounded-lg overflow-hidden">
                  {/* SVG edges */}
                  <svg className="absolute inset-0 w-full h-full pointer-events-none">
                    {graph.edges.map((edge, i) => {
                      // Simple layout: nodes arranged in grid
                      const cols = Math.ceil(Math.sqrt(graph.nodes.length));
                      const sourceIdx = graph.nodes.findIndex((n) => n.id === edge.source);
                      const targetIdx = graph.nodes.findIndex((n) => n.id === edge.target);
                      if (sourceIdx < 0 || targetIdx < 0) return null;

                      const cellW = 100 / cols;
                      const cellH = 100 / cols;
                      const x1 = (sourceIdx % cols + 0.5) * cellW;
                      const y1 = (Math.floor(sourceIdx / cols) + 0.5) * cellH;
                      const x2 = (targetIdx % cols + 0.5) * cellW;
                      const y2 = (Math.floor(targetIdx / cols) + 0.5) * cellH;

                      return (
                        <g key={edge.id}>
                          <line
                            x1={`${x1}%`} y1={`${y1}%`}
                            x2={`${x2}%`} y2={`${y2}%`}
                            stroke="rgba(245, 158, 11, 0.4)"
                            strokeWidth={1.5}
                          />
                          <text
                            x={`${(x1 + x2) / 2}%`}
                            y={`${(y1 + y2) / 2}%`}
                            fill="rgba(245, 158, 11, 0.8)"
                            fontSize="11"
                            textAnchor="middle"
                            className="select-none"
                          >
                            {edge.label}
                          </text>
                        </g>
                      );
                    })}
                  </svg>

                  {/* Nodes */}
                  <div className="relative z-10 grid gap-3 p-4"
                    style={{
                      gridTemplateColumns: `repeat(${Math.ceil(Math.sqrt(graph.nodes.length))}, minmax(120px, 1fr))`,
                    }}
                  >
                    {graph.nodes.map((node) => (
                      <button
                        key={node.id}
                        onClick={() => setSelectedNode(node)}
                        className={`flex items-center gap-2 p-2.5 rounded-lg border text-sm transition-all hover:scale-105 cursor-pointer ${
                          typeColors[node.type] || "bg-muted border-border text-foreground"
                        } ${selectedNode?.id === node.id ? "ring-2 ring-amber-400" : ""}`}
                      >
                        {typeIcons[node.type] || <BookOpen className="size-4" />}
                        <span className="truncate font-medium">{node.name}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Detail panel */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">
                  {selectedNode ? selectedNode.name : "选择一个实体"}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {selectedNode ? (
                  <>
                    <Badge variant="outline">{selectedNode.type}</Badge>
                    {selectedNode.description && (
                      <p className="text-sm text-muted-foreground">
                        {selectedNode.description}
                      </p>
                    )}
                    <Separator />
                    <p className="text-xs text-muted-foreground">关联关系：</p>
                    {graph.edges
                      .filter(
                        (e) =>
                          e.source === selectedNode.id ||
                          e.target === selectedNode.id
                      )
                      .map((edge) => {
                        const other =
                          edge.source === selectedNode.id
                            ? nodeMap.get(edge.target)
                            : nodeMap.get(edge.source);
                        return (
                          <div
                            key={edge.id}
                            className="flex items-center gap-2 text-sm"
                          >
                            <ChevronRight className="size-3 text-muted-foreground" />
                            <span className="text-amber-400">{edge.label}</span>
                            <span className="text-muted-foreground">
                              {other?.name || "?"}
                            </span>
                          </div>
                        );
                      })}
                    {graph.edges.filter(
                      (e) =>
                        e.source === selectedNode.id ||
                        e.target === selectedNode.id
                    ).length === 0 && (
                      <p className="text-xs text-muted-foreground">无关联关系</p>
                    )}
                  </>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    点击左侧实体查看详情与关联关系
                  </p>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="timeline" className="mt-4">
          <Card>
            <CardContent className="p-6">
              {graph.timeline.length === 0 ? (
                <EmptyState
                  icon={AlertTriangle}
                  title="暂无伏笔"
                  description="从写作台运行 DataAgent 提取伏笔后，这里会显示伏笔时间线。"
                />
              ) : (
                <div className="space-y-0 relative pl-6">
                  {/* Timeline line */}
                  <div className="absolute left-2.5 top-2 bottom-2 w-px bg-border" />
                  {graph.timeline.map((item) => (
                    <div key={item.id} className="relative pb-6 last:pb-0">
                      {/* Timeline dot */}
                      <div
                        className={`absolute -left-[19px] top-1.5 size-3 rounded-full border-2 ${
                          item.status === "resolved"
                            ? "bg-emerald-500 border-emerald-500"
                            : item.status === "overdue"
                            ? "bg-red-500 border-red-500"
                            : "bg-amber-500 border-amber-500"
                        }`}
                      />
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium">{item.title}</span>
                          <Badge
                            variant="outline"
                            className={`text-xs ${
                              item.status === "resolved"
                                ? "text-emerald-400"
                                : item.status === "overdue"
                                ? "text-red-400"
                                : "text-amber-400"
                            }`}
                          >
                            {item.status === "resolved"
                              ? "已回收"
                              : item.status === "overdue"
                              ? "逾期"
                              : "待回收"}
                          </Badge>
                        </div>
                        <div className="flex gap-4 mt-1 text-xs text-muted-foreground">
                          {item.chapter_planted && (
                            <span>埋于第 {item.chapter_planted} 章</span>
                          )}
                          {item.chapter_resolved && (
                            <span>回收于第 {item.chapter_resolved} 章</span>
                          )}
                        </div>
                        {item.description && (
                          <p className="text-xs text-muted-foreground mt-1">
                            {item.description}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
