import { Outlet } from "react-router-dom";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "./AppSidebar";
import { ThemeToggle } from "./ThemeToggle";
import { CommandSearch } from "@/components/CommandSearch";
import { NoKeyBanner } from "./NoKeyBanner";

export function AppLayout() {
  return (
    <SidebarProvider>
      <AppSidebar />
      <main className="flex-1 flex flex-col min-h-screen">
        <NoKeyBanner />
        <header className="h-14 border-b flex items-center justify-between px-4 shrink-0">
          <div className="flex items-center gap-2">
            <SidebarTrigger />
          </div>
          <div className="flex items-center gap-3">
            <CommandSearch />
            <ThemeToggle />
          </div>
        </header>
        <div className="flex-1 p-6">
          <Outlet />
        </div>
      </main>
    </SidebarProvider>
  );
}
