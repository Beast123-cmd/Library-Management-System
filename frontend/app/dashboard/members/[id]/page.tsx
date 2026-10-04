"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, BookOpen, CalendarDays, CircleDollarSign, Mail, UserRound } from "lucide-react";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export default function MemberProfilePage() {
  const { id } = useParams<{ id: string }>();
  const { isAdmin } = useAuth();
  const { data, isLoading } = useQuery({ queryKey: ["member-profile", id], queryFn: () => api.get(`/users/${id}/profile`).then(response => response.data), enabled: isAdmin });
  if (!isAdmin) return <div className="glass p-8 text-center text-slate-400">Only library staff can access member profiles.</div>;
  if (isLoading) return <div className="glass min-h-[30rem] animate-pulse" />;
  if (!data) return <div className="glass p-8 text-center text-slate-400">Member profile unavailable.</div>;
  const { member, summary, transactions } = data;
  return <div className="mx-auto max-w-5xl space-y-7"><Link href="/dashboard/members" className="inline-flex items-center gap-2 text-sm font-medium text-slate-400 hover:text-teal-200"><ArrowLeft size={16} /> Back to members</Link><section className="glass p-6 sm:p-8"><div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between"><div className="flex items-center gap-4"><div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-teal-500/15 text-2xl font-bold text-teal-200">{member.name.slice(0, 1).toUpperCase()}</div><div><h1 className="text-2xl font-bold text-white">{member.name}</h1><p className="mt-1 text-slate-400">@{member.username}</p><p className="mt-1 flex items-center gap-1.5 text-sm text-slate-400"><Mail size={14} /> {member.email}</p></div></div><span className={`w-fit rounded-full px-3 py-1.5 text-sm font-semibold ${member.is_active ? "bg-emerald-500/15 text-emerald-300" : "bg-red-500/15 text-red-300"}`}>{member.is_active ? "Active account" : "Suspended account"}</span></div><div className="mt-7 grid gap-3 sm:grid-cols-3"><Metric icon={BookOpen} label="Loans recorded" value={summary.total_loans} /><Metric icon={CalendarDays} label="Active loans" value={summary.active_loans} /><Metric icon={CircleDollarSign} label="Recent fines" value={`₹${summary.recent_fines.toFixed(2)}`} /></div></section><section className="glass overflow-hidden"><div className="border-b border-white/5 p-5"><h2 className="font-semibold text-white">Recent lending history</h2><p className="mt-1 text-sm text-slate-400">Latest 20 circulation records for this member.</p></div>{transactions.length ? <div className="divide-y divide-white/5">{transactions.map((transaction: any) => <div key={transaction.id} className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between"><div><p className="font-medium text-white">{transaction.title}</p><p className="mt-1 text-sm text-slate-400">Issued {formatDate(transaction.issue_date)} · Due {formatDate(transaction.expected_return_date)}</p></div><div className="flex items-center gap-3"><span className="rounded-full bg-white/5 px-2.5 py-1 text-xs capitalize text-slate-300">{transaction.status.replaceAll("_", " ")}</span>{transaction.fine_amount > 0 && <span className="text-sm text-amber-300">₹{transaction.fine_amount.toFixed(2)}</span>}</div></div>)}</div> : <div className="p-10 text-center text-slate-400"><UserRound className="mx-auto mb-3" /> No lending activity yet.</div>}</section></div>;
}

function Metric({ icon: Icon, label, value }: { icon: typeof BookOpen; label: string; value: string | number }) {
  return <div className="rounded-xl border border-white/5 bg-white/[.025] p-4"><Icon className="text-teal-300" size={18} /><p className="mt-4 text-2xl font-bold text-white">{value}</p><p className="mt-1 text-sm text-slate-400">{label}</p></div>;
}

function formatDate(value: string) { return new Date(`${value}T00:00:00`).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" }); }
