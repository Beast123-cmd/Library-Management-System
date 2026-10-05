"use client";

import { useMemo, useState } from "react";
import axios from "axios";
import { CircleDollarSign, Download, Search, ShieldAlert } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import toast from "react-hot-toast";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

type FineRecord = {
  transaction_id: number;
  member_name: string;
  book_title: string;
  assessed_amount: number;
  paid_amount: number;
  outstanding_amount: number;
  paid_at?: string | null;
  note?: string | null;
};

export default function FinesPage() {
  const { isAdmin } = useAuth();
  const [search, setSearch] = useState("");
  const [amounts, setAmounts] = useState<Record<number, string>>({});
  const [notes, setNotes] = useState<Record<number, string>>({});
  const [savingId, setSavingId] = useState<number | null>(null);
  const { data: records = [], isLoading, refetch } = useQuery<FineRecord[]>({
    queryKey: ["fine-records"], queryFn: () => api.get("/transactions/fines").then(response => response.data), enabled: isAdmin,
  });

  const filtered = useMemo(() => records.filter(record => `${record.member_name} ${record.book_title}`.toLowerCase().includes(search.toLowerCase())), [records, search]);
  const outstanding = records.reduce((total, record) => total + record.outstanding_amount, 0);
  const collected = records.reduce((total, record) => total + record.paid_amount, 0);

  const recordPayment = async (record: FineRecord) => {
    const amount = Number(amounts[record.transaction_id] || record.outstanding_amount);
    if (!Number.isFinite(amount) || amount <= 0 || amount > record.outstanding_amount) {
      toast.error(`Enter an amount up to ₹${record.outstanding_amount.toFixed(2)}.`);
      return;
    }
    setSavingId(record.transaction_id);
    try {
      await api.post(`/transactions/${record.transaction_id}/fine-payment`, { amount, note: notes[record.transaction_id] || undefined });
      toast.success("Payment recorded.");
      setAmounts(current => ({ ...current, [record.transaction_id]: "" }));
      setNotes(current => ({ ...current, [record.transaction_id]: "" }));
      refetch();
    } catch (error) {
      toast.error(axios.isAxiosError(error) ? error.response?.data?.detail || "Could not record payment." : "Could not record payment.");
    } finally {
      setSavingId(null);
    }
  };

  const downloadLedger = async () => {
    const response = await api.get("/analytics/export/fines", { responseType: "blob" });
    const url = URL.createObjectURL(response.data);
    const link = document.createElement("a");
    link.href = url; link.download = "library-fines-report.csv"; link.click(); URL.revokeObjectURL(url);
  };

  if (!isAdmin) return <div className="flex min-h-[400px] flex-col items-center justify-center space-y-4 text-center"><ShieldAlert className="text-red-500" size={48} /><h1 className="text-xl font-bold text-white">Access denied</h1><p className="max-w-md text-slate-400">Only library staff can manage payments.</p></div>;

  return <div className="space-y-6">
    <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><h1 className="flex items-center gap-2 text-2xl font-bold text-white"><CircleDollarSign className="text-teal-300" /> Fine management</h1><p className="mt-1 text-sm text-slate-400">Record partial or full payments and keep outstanding balances visible.</p></div><button onClick={downloadLedger} className="inline-flex w-fit items-center gap-2 rounded-xl border border-teal-400/25 bg-teal-500/10 px-4 py-2.5 text-sm font-semibold text-teal-200 hover:bg-teal-500/20"><Download size={16} /> Download ledger</button></div>
    <div className="grid gap-4 sm:grid-cols-3"><Metric label="Fine records" value={records.length} tone="text-indigo-200" /><Metric label="Collected" value={`₹${collected.toFixed(2)}`} tone="text-emerald-300" /><Metric label="Outstanding" value={`₹${outstanding.toFixed(2)}`} tone="text-amber-300" /></div>
    <div className="glass overflow-hidden"><div className="border-b border-white/5 p-4"><label className="relative block max-w-md"><Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} /><input value={search} onChange={event => setSearch(event.target.value)} placeholder="Search member or book" className="w-full rounded-xl border border-white/10 bg-white/5 py-2.5 pl-10 pr-3 text-sm text-white outline-none focus:border-teal-300/60" /></label></div><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="border-b border-white/5 text-xs uppercase tracking-wide text-slate-500"><tr><th className="px-5 py-4">Member / book</th><th className="px-5 py-4">Fine</th><th className="px-5 py-4">Paid</th><th className="px-5 py-4">Payment</th></tr></thead><tbody className="divide-y divide-white/5">{isLoading ? <tr><td colSpan={4} className="p-10 text-center text-slate-400">Loading fine records…</td></tr> : filtered.length === 0 ? <tr><td colSpan={4} className="p-10 text-center text-slate-400">No fine records found.</td></tr> : filtered.map(record => <tr key={record.transaction_id} className="align-top hover:bg-white/[0.025]"><td className="px-5 py-4"><p className="font-medium text-white">{record.member_name}</p><p className="mt-1 text-xs text-slate-400">{record.book_title} · Loan #{record.transaction_id}</p>{record.note && <p className="mt-2 text-xs text-slate-500">Last note: {record.note}</p>}</td><td className="px-5 py-4 text-slate-200">₹{record.assessed_amount.toFixed(2)}</td><td className="px-5 py-4"><p className="text-emerald-300">₹{record.paid_amount.toFixed(2)}</p><p className="mt-1 text-xs text-amber-300">Due ₹{record.outstanding_amount.toFixed(2)}</p></td><td className="min-w-[19rem] px-5 py-4">{record.outstanding_amount === 0 ? <span className="rounded-full bg-emerald-500/15 px-2.5 py-1 text-xs font-semibold text-emerald-300">Paid in full</span> : <div className="flex flex-col gap-2 sm:flex-row"><input type="number" min="0.01" max={record.outstanding_amount} step="0.01" value={amounts[record.transaction_id] ?? ""} onChange={event => setAmounts(current => ({ ...current, [record.transaction_id]: event.target.value }))} placeholder={`₹${record.outstanding_amount.toFixed(2)}`} className="w-24 rounded-lg border border-white/10 bg-white/5 px-2 py-2 text-white outline-none focus:border-teal-300/60" /><input value={notes[record.transaction_id] ?? ""} onChange={event => setNotes(current => ({ ...current, [record.transaction_id]: event.target.value }))} placeholder="Optional note" className="min-w-0 flex-1 rounded-lg border border-white/10 bg-white/5 px-2 py-2 text-white outline-none focus:border-teal-300/60" /><button disabled={savingId === record.transaction_id} onClick={() => recordPayment(record)} className="rounded-lg bg-teal-500/15 px-3 py-2 text-xs font-semibold text-teal-200 hover:bg-teal-500/25 disabled:opacity-50">{savingId === record.transaction_id ? "Saving…" : "Record"}</button></div>}</td></tr>)}</tbody></table></div></div>
  </div>;
}

function Metric({ label, value, tone }: { label: string; value: string | number; tone: string }) { return <div className="glass p-5"><p className="text-sm text-slate-400">{label}</p><p className={`mt-2 text-2xl font-bold ${tone}`}>{value}</p></div>; }
