"use client";

import Link from "next/link";
import { AlertTriangle, Bell, BookOpen, Clock, ShieldAlert } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

type Alert = { id: string; type: "overdue" | "due" | "hold"; title: string; message: string; action: string };
const icon = { overdue: AlertTriangle, due: Clock, hold: BookOpen };
const tone = { overdue: "text-red-300 bg-red-500/10", due: "text-amber-300 bg-amber-500/10", hold: "text-teal-300 bg-teal-500/10" };

export default function NotificationsPage() {
  const { isAdmin } = useAuth();
  const { data: alerts = [], isLoading } = useQuery<Alert[]>({ queryKey: ["library-notifications"], queryFn: () => api.get("/notifications/").then(response => response.data) });
  if (isAdmin) return <div className="flex min-h-[400px] flex-col items-center justify-center gap-4 text-center"><ShieldAlert className="text-slate-500" size={40} /><h1 className="text-xl font-bold text-white">Staff alerts are on the work queue</h1><p className="max-w-md text-sm text-slate-400">Use the dashboard’s circulation queue to manage due loans, overdue books, and pickup deadlines.</p><Link href="/dashboard" className="rounded-xl bg-indigo-500/15 px-4 py-2.5 text-sm font-semibold text-indigo-200">Open work queue</Link></div>;
  return <div className="mx-auto max-w-4xl space-y-6"><header><h1 className="flex items-center gap-2 text-2xl font-bold text-white"><Bell className="text-teal-300" /> Library alerts</h1><p className="mt-1 text-sm text-slate-400">Updates based on the alert preferences in your account settings.</p></header><section className="glass overflow-hidden">{isLoading ? <p className="p-12 text-center text-slate-400">Loading alerts…</p> : alerts.length === 0 ? <div className="p-12 text-center"><Bell className="mx-auto mb-3 text-teal-300" size={32} /><p className="font-semibold text-white">You are all caught up</p><p className="mt-1 text-sm text-slate-400">There are no due dates, overdue loans, or pickup reminders right now.</p></div> : <div className="divide-y divide-white/5">{alerts.map(alert => { const Icon = icon[alert.type]; return <Link key={alert.id} href={alert.action} className="flex items-center gap-4 p-5 transition-colors hover:bg-white/[0.03]"><span className={`rounded-xl p-3 ${tone[alert.type]}`}><Icon size={19} /></span><span className="min-w-0 flex-1"><span className="block font-semibold text-white">{alert.title}</span><span className="mt-1 block text-sm text-slate-400">{alert.message}</span></span><span className="text-sm text-teal-300">Open →</span></Link>; })}</div>}</section></div>;
}
