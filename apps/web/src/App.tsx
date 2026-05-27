import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "next-themes";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "@/components/ui/sonner";
import { useAuthStore } from "@/stores/auth";
import { useEffect } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { LoginPage } from "@/pages/LoginPage";
import { ProjectHub } from "@/pages/ProjectHub";
import { ProjectDetail } from "@/pages/ProjectDetail";
import { ChapterEditor } from "@/pages/ChapterEditor";
import { SettingsPage } from "@/pages/SettingsPage";
import { GraphView } from "@/pages/GraphView";
import { SimulationCenter } from "@/pages/SimulationCenter";
import { ReviewPage } from "@/pages/ReviewPage";
import { PlanningCenter } from "@/pages/PlanningCenter";
import { DeepInitWizard } from "@/pages/DeepInitWizard";
import { InitChatPage } from "@/pages/InitChatPage";
import { DisambiguationQueue } from "@/pages/DisambiguationQueue";
import { CardsPage } from "@/pages/CardsPage";
import { SummariesPage } from "@/pages/SummariesPage";
import { PluginManager } from "@/pages/PluginManager";
import { WorkflowView } from "@/pages/WorkflowView";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
    },
  },
});

function AuthGuard({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const isLoading = useAuthStore((s) => s.isLoading);
  const checkAuth = useAuthStore((s) => s.checkAuth);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--color-page)]">
        <div className="animate-pulse text-muted-foreground">加载中...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

export default function App() {
  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false}>
      <TooltipProvider>
        <QueryClientProvider client={queryClient}>
          <BrowserRouter>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route
                element={
                  <AuthGuard>
                    <AppLayout />
                  </AuthGuard>
                }
              >
                <Route path="/" element={<ProjectHub />} />
                <Route path="/projects/new/wizard" element={<DeepInitWizard />} />
                <Route path="/projects/new/chat" element={<InitChatPage />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path="/settings/plugins" element={<PluginManager />} />
                <Route path="/settings/workflows" element={<WorkflowView />} />
                <Route path="/projects/:projectId" element={<ProjectDetail />} />
                <Route path="/projects/:projectId/planning" element={<PlanningCenter />} />
                <Route path="/projects/:projectId/cards" element={<CardsPage />} />
                <Route path="/projects/:projectId/summaries" element={<SummariesPage />} />
                <Route path="/projects/:projectId/graph" element={<GraphView />} />
                <Route path="/projects/:projectId/simulations" element={<SimulationCenter />} />
                <Route path="/projects/:projectId/disambiguation" element={<DisambiguationQueue />} />
                <Route
                  path="/projects/:projectId/chapters/:chapterId"
                  element={<ChapterEditor />}
                />
                <Route
                  path="/projects/:projectId/reviews/:chapterId"
                  element={<ReviewPage />}
                />
              </Route>
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrowserRouter>
          <Toaster richColors theme="dark" />
        </QueryClientProvider>
      </TooltipProvider>
    </ThemeProvider>
  );
}
