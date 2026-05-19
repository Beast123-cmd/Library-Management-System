"use client";
import { motion, AnimatePresence } from "framer-motion";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { ArrowLeftRight, RotateCcw, Clock, Search, Filter, X, Check, AlertCircle, Calendar, ShieldCheck, HelpCircle, Loader2 } from "lucide-react";
import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import api from "@/lib/api";
import toast from "react-hot-toast";
import { useAuth } from "@/context/AuthContext";

export default function TransactionsPage() {
  const { isAdmin } = useAuth();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const PER_PAGE = 15;

  const handleSearch = (val: string) => {
    setSearch(val);
    clearTimeout((window as any)._txnSearchTimer);
    (window as any)._txnSearchTimer = setTimeout(() => {
      setDebouncedSearch(val);
      setPage(1);
    }, 200);
  };

  const handleStatusChange = (val: string) => {
    setStatusFilter(val);
    setPage(1);
  };

  const { data, isLoading, isFetching, refetch } = useQuery({
    queryKey: ["transactions", page, debouncedSearch, statusFilter],
    queryFn: () => {
      let url = `/transactions/?page=${page}&per_page=${PER_PAGE}`;
      if (debouncedSearch) url += `&search=${encodeURIComponent(debouncedSearch)}`;
      if (statusFilter) url += `&status=${statusFilter}`;
      return api.get(url).then(r => r.data);
    },
    placeholderData: keepPreviousData,
  });

  const [returnTxn, setReturnTxn] = useState<any>(null);
  const [returnStep, setReturnStep] = useState(1);
  const [fineAction, setFineAction] = useState<"paid" | "waived">("paid");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const calculateFineClient = (expectedReturnDateStr: string) => {
    const expected = new Date(expectedReturnDateStr);
    expected.setHours(0, 0, 0, 0);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    if (today <= expected) {
      return { overdueDays: 0, fine: 0 };
    }
    
    const diffTime = Math.abs(today.getTime() - expected.getTime());
    const overdueDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    let fine = 0;
    if (overdueDays <= 15) {
      fine = overdueDays * 5;
    } else {
      fine = (15 * 5) + ((overdueDays - 15) * 50);
    }
    return { overdueDays, fine };
  };

  const handleFinalizeReturn = async () => {
    if (!returnTxn) return;
    setIsSubmitting(true);
    try {
      await api.post(`/transactions/${returnTxn.id}/return`, {
        waive_fine: fineAction === "waived"
      });
      toast.success("Book returned successfully!");
      setReturnTxn(null);
      refetch();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Return failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStatusInfo = (txn: any) => {
    if (txn.status === "returned") {
      return { label: "Returned", badge: "bg-emerald-500/15 text-emerald-400" };
    }
    const isOverdue = new Date(txn.expected_return_date) < new Date();
    if (isOverdue) {
      return { label: "Overdue", badge: "bg-red-500/15 text-red-400 font-semibold animate-pulse" };
    }
    return { label: "Issued", badge: "bg-amber-500/15 text-amber-400" };
  };

  const totalPages = data ? Math.ceil(data.total / PER_PAGE) : 1;

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <ArrowLeftRight className="text-purple-400" size={26} /> Transactions
          </h1>
          <p className="text-slate-400 text-sm mt-1">{data?.total ?? "—"} total records</p>
        </div>
      </motion.div>

      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
          <input
            value={search}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="Search transactions by book title or member name..."
            className="w-full bg-white/5 border border-white/10 rounded-xl pl-12 pr-12 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/50 transition-all"
          />
          {isFetching && (
            <Loader2 className="absolute right-4 top-1/2 -translate-y-1/2 text-indigo-400 animate-spin" size={18} />
          )}
        </div>

        <div className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-xl px-3 py-1.5 min-w-[200px]">
          <Filter className="text-slate-500" size={16} />
          <select
            value={statusFilter}
            onChange={(e) => handleStatusChange(e.target.value)}
            className="bg-transparent border-none text-white focus:outline-none w-full text-sm py-1.5 cursor-pointer"
          >
            <option value="" className="bg-slate-900 text-slate-400">All Statuses</option>
            <option value="issued" className="bg-slate-900 text-white">Issued / Overdue</option>
            <option value="returned" className="bg-slate-900 text-white">Returned</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
        className="glass overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/5">
                {["ID", "Member", "Book", "Issued", "Expected Return", "Status", "Fine", ...(isAdmin ? ["Action"] : [])].map(h => (
                  <th key={h} className="text-left text-slate-400 text-xs font-semibold uppercase tracking-wider px-6 py-4">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                Array.from({ length: 8 }).map((_, i) => (
                  <tr key={i} className="border-b border-white/5">
                    {Array.from({ length: isAdmin ? 8 : 7 }).map((_, j) => (
                      <td key={j} className="px-6 py-4"><div className="h-4 bg-white/5 rounded animate-pulse w-3/4" /></td>
                    ))}
                  </tr>
                ))
              ) : data?.data?.length === 0 ? (
                <tr><td colSpan={isAdmin ? 8 : 7} className="px-6 py-16 text-center text-slate-500">No transactions found.</td></tr>
              ) : data?.data?.map((txn: any) => {
                const { label, badge } = getStatusInfo(txn);
                return (
                  <tr key={txn.id} className="border-b border-white/5 hover:bg-white/3 transition-colors group">
                    <td className="px-6 py-4 text-slate-500 text-sm">#{txn.id}</td>
                    <td className="px-6 py-4 text-slate-300 text-sm">{txn.user?.name ?? `User #${txn.user_id}`}</td>
                    <td className="px-6 py-4 text-white font-medium text-sm">{txn.book?.title ?? `Book #${txn.book_id}`}</td>
                    <td className="px-6 py-4 text-slate-400 text-sm">{txn.issue_date}</td>
                    <td className="px-6 py-4 text-sm">
                      <span className="flex items-center gap-1 text-slate-400">
                        <Clock size={13} /> {txn.expected_return_date}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-medium capitalize ${badge}`}>
                        {label}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm">
                      {txn.fine_amount > 0
                        ? <span className="text-red-400 font-medium">₹{txn.fine_amount}</span>
                        : <span className="text-slate-500">₹0</span>}
                    </td>
                    {isAdmin && (
                      <td className="px-6 py-4">
                        {txn.status === "issued" && (
                          <button onClick={() => {
                            setReturnTxn(txn);
                            setReturnStep(1);
                            setFineAction("paid");
                          }}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-indigo-400 border border-indigo-500/30 hover:bg-indigo-500/10 transition-all">
                            <RotateCcw size={13} /> Return
                          </button>
                        )}
                      </td>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-6 py-4 border-t border-white/5">
            <p className="text-slate-400 text-sm">Page {page} of {totalPages}</p>
            <div className="flex items-center gap-2">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
                className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 disabled:opacity-30 disabled:cursor-not-allowed transition-all">
                <ChevronLeft size={16} />
              </button>
              <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}
                className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 disabled:opacity-30 disabled:cursor-not-allowed transition-all">
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        )}
      </motion.div>

      {/* Return Book Wizard Modal */}
      <AnimatePresence>
        {returnTxn && (() => {
          const { overdueDays, fine } = calculateFineClient(returnTxn.expected_return_date);
          return (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
              <motion.div
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: 20 }}
                className="w-full max-w-lg glass border border-white/10 rounded-2xl overflow-hidden shadow-2xl bg-slate-900/95 text-white flex flex-col"
              >
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-white/5 bg-white/2">
                  <h3 className="font-bold text-lg flex items-center gap-2">
                    <RotateCcw className="text-indigo-400" size={18} />
                    Book Return Wizard
                  </h3>
                  <button
                    onClick={() => setReturnTxn(null)}
                    disabled={isSubmitting}
                    className="p-1 text-slate-400 hover:text-white rounded-lg hover:bg-white/5 transition-all"
                  >
                    <X size={18} />
                  </button>
                </div>

                {/* Steps Navigation Bar */}
                <div className="flex items-center justify-center gap-2 px-6 py-3 bg-white/2 border-b border-white/5 text-xs text-slate-400 select-none">
                  <span className={`px-2 py-0.5 rounded-full ${returnStep >= 1 ? "bg-indigo-500 text-white font-semibold" : "bg-white/5"}`}>1. Assessment</span>
                  <span className="w-8 h-px bg-white/10" />
                  <span className={`px-2 py-0.5 rounded-full ${returnStep >= 2 ? "bg-indigo-500 text-white font-semibold" : "bg-white/5"}`}>2. Fine Handling</span>
                  <span className="w-8 h-px bg-white/10" />
                  <span className={`px-2 py-0.5 rounded-full ${returnStep >= 3 ? "bg-indigo-500 text-white font-semibold" : "bg-white/5"}`}>3. Confirmation</span>
                </div>

                {/* Step Content */}
                <div className="p-6 space-y-4 flex-1">
                  {returnStep === 1 && (
                    <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} className="space-y-4">
                      <div className="bg-white/5 border border-white/5 p-4 rounded-xl space-y-2.5">
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-400">Book Title:</span>
                          <span className="text-white font-medium">{returnTxn.book?.title ?? `Book #${returnTxn.book_id}`}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-400">Borrower:</span>
                          <span className="text-white font-medium">{returnTxn.user?.name ?? `User #${returnTxn.user_id}`}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-400">Issue Date:</span>
                          <span className="text-slate-300">{returnTxn.issue_date}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-400">Expected Return:</span>
                          <span className="text-slate-300">{returnTxn.expected_return_date}</span>
                        </div>
                      </div>

                      {overdueDays > 0 ? (
                        <div className="bg-red-500/10 border border-red-500/20 p-4 rounded-xl flex items-start gap-3">
                          <AlertCircle className="text-red-400 shrink-0 mt-0.5" size={18} />
                          <div className="space-y-1">
                            <h4 className="text-red-400 font-semibold text-sm">Overdue Return Detected</h4>
                            <p className="text-slate-300 text-xs leading-relaxed">
                              This book is overdue by <strong className="text-white">{overdueDays} days</strong>. An automatic fine of <strong className="text-white">₹{fine}</strong> has been calculated.
                            </p>
                          </div>
                        </div>
                      ) : (
                        <div className="bg-emerald-500/10 border border-emerald-500/20 p-4 rounded-xl flex items-start gap-3">
                          <ShieldCheck className="text-emerald-400 shrink-0 mt-0.5" size={18} />
                          <div className="space-y-1">
                            <h4 className="text-emerald-400 font-semibold text-sm">On Time Return</h4>
                            <p className="text-slate-300 text-xs leading-relaxed">
                              No overdue days found. Zero fine generated. Ready for catalog check-in.
                            </p>
                          </div>
                        </div>
                      )}
                    </motion.div>
                  )}

                  {returnStep === 2 && (
                    <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} className="space-y-4">
                      <div className="text-center py-2">
                        <p className="text-slate-400 text-sm">Select how to settle the generated penalty:</p>
                        <h4 className="text-white text-3xl font-black mt-2">₹{fine} Fine</h4>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <button
                          type="button"
                          onClick={() => setFineAction("paid")}
                          className={`p-4 rounded-xl border text-left space-y-2 transition-all ${
                            fineAction === "paid"
                              ? "bg-indigo-600/10 border-indigo-500 text-white"
                              : "bg-white/5 border-white/10 text-slate-400 hover:bg-white/10"
                          }`}
                        >
                          <div className="w-8 h-8 rounded-lg bg-indigo-500/20 flex items-center justify-center text-indigo-400 font-bold">₹</div>
                          <div>
                            <h5 className="font-semibold text-sm text-white">Fine Paid</h5>
                            <p className="text-[11px] text-slate-400 mt-0.5">Payment collected successfully</p>
                          </div>
                        </button>

                        <button
                          type="button"
                          onClick={() => setFineAction("waived")}
                          className={`p-4 rounded-xl border text-left space-y-2 transition-all ${
                            fineAction === "waived"
                              ? "bg-amber-600/10 border-amber-500 text-white"
                              : "bg-white/5 border-white/10 text-slate-400 hover:bg-white/10"
                          }`}
                        >
                          <div className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center text-amber-400">
                            <Check size={16} />
                          </div>
                          <div>
                            <h5 className="font-semibold text-sm text-white">Waive Fine</h5>
                            <p className="text-[11px] text-slate-400 mt-0.5">Pardon / waive penalty</p>
                          </div>
                        </button>
                      </div>
                    </motion.div>
                  )}

                  {returnStep === 3 && (
                    <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} className="space-y-4">
                      <h4 className="text-sm font-semibold text-slate-300">Return Summary & Confirmation</h4>
                      <div className="bg-white/5 border border-white/5 rounded-xl p-4 space-y-3">
                        <div className="flex items-center gap-3 text-sm">
                          <span className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-xs">✓</span>
                          <span>Mark book <strong className="text-white">{returnTxn.book?.title}</strong> as returned.</span>
                        </div>
                        <div className="flex items-center gap-3 text-sm">
                          <span className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-xs">✓</span>
                          <span>Increment available copies in catalog (+1).</span>
                        </div>
                        <div className="flex items-center gap-3 text-sm">
                          <span className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-xs">✓</span>
                          {fine > 0 ? (
                            <span>
                              Fine of <strong className="text-white">₹{fine}</strong> marked as{" "}
                              <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                                fineAction === "waived" ? "bg-amber-500/20 text-amber-400" : "bg-indigo-500/20 text-indigo-400"
                              }`}>
                                {fineAction === "waived" ? "Waived" : "Paid"}
                              </span>
                            </span>
                          ) : (
                            <span>No outstanding fines to process.</span>
                          )}
                        </div>
                      </div>
                      <p className="text-slate-400 text-xs italic text-center">
                        Click "Finalize Return" to record the transaction and update the book stock.
                      </p>
                    </motion.div>
                  )}
                </div>

                {/* Footer Buttons */}
                <div className="flex items-center justify-between px-6 py-4 border-t border-white/5 bg-slate-950/20">
                  <button
                    onClick={() => setReturnTxn(null)}
                    disabled={isSubmitting}
                    className="px-4 py-2 text-sm font-medium text-slate-400 hover:text-white transition-all disabled:opacity-50"
                  >
                    Cancel
                  </button>
                  <div className="flex gap-2">
                    {returnStep > 1 && (
                      <button
                        onClick={() => {
                          if (returnStep === 3 && fine === 0) {
                            setReturnStep(1);
                          } else {
                            setReturnStep(p => p - 1);
                          }
                        }}
                        disabled={isSubmitting}
                        className="px-4 py-2 text-sm font-medium border border-white/10 rounded-xl hover:bg-white/5 transition-all disabled:opacity-50"
                      >
                        Back
                      </button>
                    )}
                    {returnStep === 1 && (
                      <button
                        onClick={() => {
                          if (fine > 0) {
                            setReturnStep(2);
                          } else {
                            setReturnStep(3);
                          }
                        }}
                        className="px-5 py-2 text-sm font-medium bg-indigo-600 hover:bg-indigo-500 rounded-xl transition-all shadow-lg shadow-indigo-600/20"
                      >
                        Continue
                      </button>
                    )}
                    {returnStep === 2 && (
                      <button
                        onClick={() => setReturnStep(3)}
                        className="px-5 py-2 text-sm font-medium bg-indigo-600 hover:bg-indigo-500 rounded-xl transition-all shadow-lg shadow-indigo-600/20"
                      >
                        Continue
                      </button>
                    )}
                    {returnStep === 3 && (
                      <button
                        onClick={handleFinalizeReturn}
                        disabled={isSubmitting}
                        className="px-5 py-2 text-sm font-medium bg-emerald-600 hover:bg-emerald-500 rounded-xl transition-all shadow-lg shadow-emerald-600/20 flex items-center gap-1.5 disabled:opacity-50"
                      >
                        {isSubmitting ? (
                          <>
                            <Loader2 className="animate-spin" size={14} />
                            Processing...
                          </>
                        ) : (
                          "Finalize Return"
                        )}
                      </button>
                    )}
                  </div>
                </div>
              </motion.div>
            </div>
          );
        })()}
      </AnimatePresence>
    </div>
  );
}
