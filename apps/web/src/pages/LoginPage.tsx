import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { BookOpen, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuthStore } from "@/stores/auth";
import { toast } from "sonner";

export function LoginPage() {
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const login = useAuthStore((s) => s.login);
  const register = useAuthStore((s) => s.register);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      if (isRegister) {
        await register(username, password, displayName || undefined);
        toast.success("注册成功！");
      } else {
        await login(username, password);
        toast.success("登录成功！");
      }
      navigate("/");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "操作失败");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--color-page)] p-4">
      <Card className="w-full max-w-md border-border/40 shadow-elevated">
        <CardHeader className="text-center space-y-2">
          <div className="mx-auto mb-2">
            <BookOpen className="size-10 text-amber-400" />
          </div>
          <CardTitle className="font-serif text-2xl">NovelCraft</CardTitle>
          <CardDescription>
            {isRegister ? "创建你的创作账号" : "登录你的写作工作台"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">用户名</Label>
              <Input
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="输入用户名"
                required
                minLength={3}
              />
            </div>

            {isRegister && (
              <div className="space-y-2">
                <Label htmlFor="displayName">显示名称（选填）</Label>
                <Input
                  id="displayName"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder="你的笔名"
                />
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="password">密码</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={isRegister ? "至少 6 位密码" : "输入密码"}
                required
                minLength={6}
              />
            </div>

            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting && <Loader2 className="size-4 mr-2 animate-spin" />}
              {isRegister ? "注册" : "登录"}
            </Button>
          </form>

          <div className="mt-4 text-center text-sm text-muted-foreground">
            {isRegister ? "已有账号？" : "还没有账号？"}
            <button
              type="button"
              onClick={() => setIsRegister(!isRegister)}
              className="ml-1 text-amber-400 hover:text-amber-300 transition-colors"
            >
              {isRegister ? "登录" : "注册"}
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
