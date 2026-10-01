"use client";
import { useState } from "react";
import axios from "axios";
import { Bookmark, Search, User as UserIcon, Book as BookIcon } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import toast from "react-hot-toast";

export default function HoldsPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const [searchTerm, setSearchTerm] = useState("");
  const [collectingId, setCollectingId] = useState<number | null>(null);

  const { data: holds, isLoading, refetch } = useQuery({
    queryKey: ["all-holds"],
    queryFn: () => api.get("/holds/all").then(r => r.data),
    enabled: isAdmin,
  });

  if (!isAdmin) {
    return (
      <div className="flex items-center justify-center h-[50vh]">
        <p className="text-slate-400">You do not have permission to view this page.</p>
      </div>
    );
  }

  const filteredHolds = holds?.filter((h: any) => 
    h.book?.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    h.user?.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    h.user?.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleCollect = async (hold: any) => {
    setCollectingId(hold.id);
    const due = new Date();
    due.setDate(due.getDate() + 7);
    const dueDate = `${due.getFullYear()}-${String(due.getMonth() + 1).padStart(2, "0")}-${String(due.getDate()).padStart(2, "0")}`;
    try {
      await api.post("/transactions/issue", {
        user_id: hold.user_id,
        book_id: hold.book_id,
        expected_return_date: dueDate,
      });
      toast.success("Book collected and issued for 7 days.");
      refetch();
    } catch (error: unknown) {
      toast.error(axios.isAxiosError(error) ? error.response?.data?.detail || "Could not issue this hold." : "Could not issue this hold.");
    } finally {
      setCollectingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <Bookmark className="text-indigo-500" />
            Holds & Pull List
          </h1>
          <p className="text-slate-400 mt-1">Manage member requests and prepare books for pickup.</p>
        </div>
      </div>

      {/* Controls */}
      <div className="glass p-4 rounded-2xl flex flex-col sm:flex-row gap-4 items-center justify-between border border-white/5">
        <div className="relative w-full sm:w-96">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
          <input
            type="text"
            placeholder="Search by book, member name, or email..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="w-full bg-slate-900/50 border border-white/10 rounded-xl py-2 pl-10 pr-4 text-sm text-white focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all"
          />
        </div>
      </div>

      {/* Holds Table */}
      <div className="glass rounded-2xl border border-white/5 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/10 bg-white/5 text-slate-300 text-sm font-semibold">
                <th className="p-4">Book</th>
                <th className="p-4">Member</th>
                <th className="p-4">Pickup Deadline</th>
                <th className="p-4">Status</th>
                <th className="p-4">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {isLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td className="p-4"><div className="h-4 bg-white/5 rounded w-3/4"></div></td>
                    <td className="p-4"><div className="h-4 bg-white/5 rounded w-1/2"></div></td>
                    <td className="p-4"><div className="h-4 bg-white/5 rounded w-24"></div></td>
                    <td className="p-4"><div className="h-4 bg-white/5 rounded w-16"></div></td>
                    <td className="p-4"><div className="h-4 bg-white/5 rounded w-24"></div></td>
                  </tr>
                ))
              ) : filteredHolds?.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-slate-400">
                    No holds found.
                  </td>
                </tr>
              ) : (
                filteredHolds?.map((hold: any) => (
                  <tr key={hold.id} className="hover:bg-white/5 transition-colors">
                    <td className="p-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-indigo-500/20 flex items-center justify-center shrink-0">
                          <BookIcon size={18} className="text-indigo-400" />
                        </div>
                        <div>
                          <p className="text-white font-medium text-sm">{hold.book?.title}</p>
                          <p className="text-slate-500 text-xs mt-0.5">{hold.book?.author}</p>
                        </div>
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-cyan-500/20 flex items-center justify-center shrink-0">
                          <UserIcon size={14} className="text-cyan-400" />
                        </div>
                        <div>
                          <p className="text-slate-200 text-sm">{hold.user?.name}</p>
                          <p className="text-slate-500 text-xs">{hold.user?.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="p-4">
                      <p className="text-slate-300 text-sm">
                        {hold.expiration_date ? new Date(hold.expiration_date).toLocaleDateString() : "—"}
                      </p>
                      <p className="text-slate-500 text-xs">
                        {hold.expiration_date ? new Date(hold.expiration_date).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : ""}
                      </p>
                    </td>
                    <td className="p-4">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-semibold capitalize border ${
                        hold.status === 'active' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                        hold.status === 'suspended' ? 'bg-slate-500/10 text-slate-400 border-slate-500/20' :
                        'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                      }`}>
                        {hold.status === "active" ? "Ready for pickup" : hold.status}
                      </span>
                    </td>
                    <td className="p-4">
                      <button onClick={() => handleCollect(hold)} disabled={collectingId !== null}
                        className="px-3 py-2 rounded-lg bg-indigo-600/20 text-indigo-300 text-xs font-semibold hover:bg-indigo-600/40 disabled:opacity-50">
                        {collectingId === hold.id ? "Issuing…" : "Mark Collected · 7-day loan"}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
