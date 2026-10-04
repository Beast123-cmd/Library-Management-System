"use client";

import { Bell, BookOpen, Clock, Loader2, TriangleAlert } from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import toast from "react-hot-toast";

type Preferences = {
  due_reminders: boolean;
  overdue_alerts: boolean;
  hold_ready_alerts: boolean;
};

const alerts: Array<{ key: keyof Preferences; title: string; description: string; icon: typeof Clock }> = [
  { key: "due_reminders", title: "Due date reminders", description: "Show reminders before your books are due.", icon: Clock },
  { key: "overdue_alerts", title: "Overdue alerts", description: "Show alerts when a loan becomes overdue.", icon: TriangleAlert },
  { key: "hold_ready_alerts", title: "Hold ready alerts", description: "Show alerts when a reserved book is ready to collect.", icon: BookOpen },
];

export default function ProfilePage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const { data: preferences, isLoading } = useQuery<Preferences>({
    queryKey: ["notification-preferences"],
    queryFn: () => api.get("/users/me/notification-preferences").then((response) => response.data),
  });

  const toggle = async (key: keyof Preferences) => {
    if (!preferences) return;
    try {
      const { data } = await api.patch<Preferences>("/users/me/notification-preferences", { [key]: !preferences[key] });
      queryClient.setQueryData(["notification-preferences"], data);
      toast.success("Alert preferences saved.");
    } catch {
      toast.error("Could not save alert preferences.");
    }
  };

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Profile & Alerts</h1>
        <p className="text-sm text-slate-400 mt-1">Control the library updates shown in your account.</p>
      </div>

      <div className="glass p-6 flex items-center gap-4">
        <div className="w-12 h-12 rounded-2xl bg-indigo-500/15 flex items-center justify-center text-indigo-300 font-bold text-lg">
          {user?.name?.[0]?.toUpperCase()}
        </div>
        <div>
          <p className="font-semibold text-white">{user?.name}</p>
          <p className="text-sm text-slate-400">{user?.email}</p>
        </div>
      </div>

      <div className="glass p-6">
        <div className="flex items-center gap-2">
          <Bell size={18} className="text-indigo-400" />
          <h2 className="font-semibold text-white">Library alerts</h2>
        </div>
        <div className="mt-4 divide-y divide-white/5">
          {isLoading ? <div className="py-8 flex justify-center"><Loader2 className="animate-spin text-indigo-400" /></div> : alerts.map(({ key, title, description, icon: Icon }) => (
            <div key={key} className="flex items-center justify-between gap-4 py-4 first:pt-0 last:pb-0">
              <div className="flex items-center gap-3">
                <Icon size={17} className="text-slate-400" />
                <div>
                  <p className="text-sm font-medium text-white">{title}</p>
                  <p className="text-xs text-slate-400 mt-0.5">{description}</p>
                </div>
              </div>
              <button type="button" role="switch" aria-checked={preferences?.[key] ?? false} onClick={() => toggle(key)}
                className={`relative w-11 h-6 rounded-full transition-colors ${preferences?.[key] ? "bg-indigo-600" : "bg-slate-700"}`}>
                <span className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${preferences?.[key] ? "translate-x-6" : "translate-x-1"}`} />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
