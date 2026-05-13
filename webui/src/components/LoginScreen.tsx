import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { registerUser, validateUser } from "@/lib/bootstrap";
import type { UserRole } from "@/lib/types";

interface RoleOption {
  role: UserRole;
  icon: string;
  labelKey: string;
  descKey: string;
}

const ROLES: RoleOption[] = [
  { role: "student", icon: "📚", labelKey: "login.role.student", descKey: "login.role.student.desc" },
  { role: "teacher", icon: "👨‍🏫", labelKey: "login.role.teacher", descKey: "login.role.teacher.desc" },
  { role: "researcher", icon: "🔬", labelKey: "login.role.researcher", descKey: "login.role.researcher.desc" },
];

type AuthMode = "login" | "register";

interface LoginScreenProps {
  onLogin: (role: UserRole, userId: string) => void;
}

export function LoginScreen({ onLogin }: LoginScreenProps) {
  const { t } = useTranslation();
  const [mode, setMode] = useState<AuthMode>("login");
  const [selectedRole, setSelectedRole] = useState<UserRole | null>(null);
  const [userId, setUserId] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    const trimmed = userId.trim();
    if (!selectedRole) {
      setError(t("login.error.selectRole"));
      return;
    }
    if (!trimmed) {
      setError(t("login.error.enterName"));
      return;
    }
    if (trimmed.length > 64) {
      setError(t("login.error.nameTooLong"));
      return;
    }

    setError("");
    setLoading(true);

    try {
      if (mode === "register") {
        const res = await registerUser("", selectedRole, trimmed);
        if (!res.ok) {
          if (res.error === "User already exists") {
            setError(t("login.error.userExists"));
          } else {
            setError(t("login.error.serverError"));
          }
          return;
        }
      } else {
        const res = await validateUser("", selectedRole, trimmed);
        if (!res.ok) {
          if (res.error === "User not found") {
            setError(t("login.error.userNotFound"));
          } else {
            setError(t("login.error.serverError"));
          }
          return;
        }
      }
      onLogin(selectedRole, trimmed);
    } catch {
      setError(t("login.error.networkError"));
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      void handleSubmit();
    }
  };

  const toggleMode = () => {
    setMode(mode === "login" ? "register" : "login");
    setError("");
  };

  return (
    <div className="flex h-full w-full items-center justify-center px-4">
      <div className="flex w-full max-w-md flex-col items-center gap-6 animate-in fade-in-0 duration-300">
        {/* Header */}
        <div className="flex flex-col items-center gap-2">
          <img
            src="/brand/nanobot_icon.png"
            alt=""
            className="h-12 w-12 select-none"
            aria-hidden
            draggable={false}
          />
          <h1 className="text-xl font-semibold">{t("login.title")}</h1>
          <p className="text-sm text-muted-foreground">{t("login.subtitle")}</p>
        </div>

        {/* Role selection */}
        <div className="w-full space-y-2">
          <label className="text-sm font-medium">{t("login.selectRole")}</label>
          <div className="grid grid-cols-3 gap-3">
            {ROLES.map((opt) => (
              <button
                key={opt.role}
                type="button"
                onClick={() => {
                  setSelectedRole(opt.role);
                  setError("");
                }}
                className={[
                  "flex flex-col items-center gap-1.5 rounded-lg border-2 p-3 transition-all",
                  "hover:border-primary/50 hover:bg-accent",
                  selectedRole === opt.role
                    ? "border-primary bg-primary/5 shadow-sm"
                    : "border-border",
                ].join(" ")}
              >
                <span className="text-2xl">{opt.icon}</span>
                <span className="text-sm font-medium">{t(opt.labelKey)}</span>
                <span className="text-center text-xs text-muted-foreground leading-tight">
                  {t(opt.descKey)}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* User ID input */}
        <div className="w-full space-y-2">
          <label className="text-sm font-medium">{t("login.userId")}</label>
          <Input
            placeholder={t("login.userId.placeholder")}
            value={userId}
            onChange={(e) => {
              setUserId(e.target.value);
              setError("");
            }}
            onKeyDown={handleKeyDown}
            autoFocus
          />
        </div>

        {/* Error */}
        {error && (
          <p className="text-sm text-destructive">{error}</p>
        )}

        {/* Submit */}
        <Button
          className="w-full"
          size="lg"
          onClick={() => void handleSubmit()}
          disabled={!selectedRole || !userId.trim() || loading}
        >
          {loading
            ? "..."
            : mode === "login"
              ? t("login.submitLogin")
              : t("login.submitRegister")}
        </Button>

        {/* Mode toggle */}
        <button
          type="button"
          onClick={toggleMode}
          className="text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          {mode === "login"
            ? t("login.switchToRegister")
            : t("login.switchToLogin")}
        </button>
      </div>
    </div>
  );
}
