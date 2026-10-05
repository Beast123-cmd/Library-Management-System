"use client";

import { useMemo, useState } from "react";
import { ClipboardCheck, Search, ShieldAlert } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import toast from "react-hot-toast";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

type Copy = { id: number; title: string; author: string; shelf_location?: string | null; accession_number: string; copy_number: number; status: string };
const statusClass: Record<string, string> = { available: "bg-emerald-500/15 text-emerald-300", issued: "bg-amber-500/15 text-amber-300", on_hold_shelf: "bg-indigo-500/15 text-indigo-300", damaged: "bg-rose-500/15 text-rose-300", missing: "bg-red-500/15 text-red-300", withdrawn: "bg-slate-500/15 text-slate-300" };

export default function InventoryPage() {
  const { isAdmin } = useAuth();
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [updating, setUpdating] = useState<number | null>(null);
  const { data: copies = [], isLoading, refetch } = useQuery<Copy[]>({ queryKey: ["copy-audit"], queryFn: () => api.get("/books/copies/audit").then(response => response.data), enabled: isAdmin });
  const filtered = useMemo(() => copies.filter(copy => (filter === "all" || copy.status === filter) && `${copy.title} ${copy.author} ${copy.accession_number}`.toLowerCase().includes(search.toLowerCase())), [copies, filter, search]);
  const updateStatus = async (copy: Copy, status: string) => {
    if (status === copy.status) return;
    const note = status === "available" ? "Reconciled during inventory audit" : window.prompt(`Reason for marking this copy ${status.replaceAll("_", " ")}:`)?.trim();
    if (status !== "available" && !note) return;
    setUpdating(copy.id);
    try { await api.patch(`/books/copies/${copy.id}/status`, { status, note }); toast.success("Inventory status updated."); refetch(); } catch (error: any) { toast.error(error.response?.data?.detail || "Could not update this copy."); } finally { setUpdating(null); }
  };
  if (!isAdmin) return <div className="flex min-h-[400px] flex-col items-center justify-center gap-4"><ShieldAlert className="text-red-500" size={48} /><h1 className="text-xl font-bold text-white">Access denied</h1></div>;
  return <div className="space-y-6"><div><h1 className="flex items-center gap-2 text-2xl font-bold text-white"><ClipboardCheck className="text-teal-300" /> Inventory audit</h1><p className="mt-1 text-sm text-slate-400">Reconcile each physical copy and keep circulation availability accurate.</p></div><div className="glass flex flex-col gap-3 p-4 sm:flex-row"><label className="relative flex-1"><Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} /><input value={search} onChange={event => setSearch(event.target.value)} placeholder="Search title, author, or accession" className="w-full rounded-xl border border-white/10 bg-white/5 py-2.5 pl-10 pr-3 text-sm text-white outline-none focus:border-teal-300/60" /></label><select value={filter} onChange={event => setFilter(event.target.value)} className="rounded-xl border border-white/10 bg-[#102326] px-3 py-2.5 text-sm text-white outline-none"><option value="all">All statuses</option>{["available", "issued", "on_hold_shelf", "damaged", "missing", "withdrawn"].map(status => <option key={status} value={status}>{status.replaceAll("_", " ")}</option>)}</select></div><div className="glass overflow-hidden"><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="border-b border-white/5 text-xs uppercase tracking-wide text-slate-500"><tr><th className="px-5 py-4">Copy</th><th className="px-5 py-4">Shelf</th><th className="px-5 py-4">Status</th><th className="px-5 py-4">Audit action</th></tr></thead><tbody className="divide-y divide-white/5">{isLoading ? <tr><td colSpan={4} className="p-10 text-center text-slate-400">Loading physical copies…</td></tr> : filtered.length === 0 ? <tr><td colSpan={4} className="p-10 text-center text-slate-400">No copies match this audit view.</td></tr> : filtered.map(copy => <tr key={copy.id} className="hover:bg-white/[0.025]"><td className="px-5 py-4"><p className="font-medium text-white">{copy.title}</p><p className="mt-1 text-xs text-slate-400">{copy.author} · {copy.accession_number}</p></td><td className="px-5 py-4 text-slate-300">{copy.shelf_location || "—"}</td><td className="px-5 py-4"><span className={`rounded-full px-2.5 py-1 text-xs font-semibold capitalize ${statusClass[copy.status] || statusClass.withdrawn}`}>{copy.status.replaceAll("_", " ")}</span></td><td className="px-5 py-4"><select disabled={updating === copy.id || ["issued", "on_hold_shelf"].includes(copy.status)} value={copy.status} onChange={event => updateStatus(copy, event.target.value)} className="rounded-lg border border-white/10 bg-[#102326] px-2 py-2 text-xs text-white outline-none disabled:opacity-50"><option value="available">Available / reconciled</option><option value="damaged">Damaged</option><option value="missing">Missing</option><option value="withdrawn">Withdrawn</option></select></td></tr>)}</tbody></table></div></div></div>;
}
