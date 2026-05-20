"use client";
import { useState } from "react";
import { motion } from "framer-motion";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { Search, Plus, BookOpen, Edit, Trash2, ChevronLeft, ChevronRight, ArrowLeftRight, AlertCircle, Loader2 } from "lucide-react";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import toast from "react-hot-toast";

export default function BooksPage() {
  const { isAdmin } = useAuth();
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [page, setPage] = useState(1);
  const PER_PAGE = 15;

  // Debounce search - reduced to 200ms for snappier feel
  const handleSearch = (val: string) => {
    setSearch(val);
    clearTimeout((window as any)._searchTimer);
    (window as any)._searchTimer = setTimeout(() => { setDebouncedSearch(val); setPage(1); }, 200);
  };

  const { data, isLoading, isFetching, refetch } = useQuery({
    queryKey: ["books", debouncedSearch, page],
    queryFn: () => api.get(`/books/?page=${page}&per_page=${PER_PAGE}&search=${debouncedSearch}`).then(r => r.data),
    placeholderData: keepPreviousData,
  });

  const [selectedBookForIssue, setSelectedBookForIssue] = useState<any>(null);
  const [selectedMemberId, setSelectedMemberId] = useState("");
  const [expectedReturnDate, setExpectedReturnDate] = useState(() => {
    return new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split("T")[0];
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [selectedBookForDetails, setSelectedBookForDetails] = useState<any>(null);
  const [bookDescription, setBookDescription] = useState<string | null>(null);
  const [isFetchingDescription, setIsFetchingDescription] = useState(false);

  const handleViewDetails = async (book: any) => {
    setSelectedBookForDetails(book);
    setBookDescription(null);
    if (book.isbn) {
      setIsFetchingDescription(true);
      try {
        const res = await fetch(`https://www.googleapis.com/books/v1/volumes?q=isbn:${book.isbn}`);
        const apiData = await res.json();
        if (apiData.items && apiData.items.length > 0) {
          setBookDescription(apiData.items[0].volumeInfo.description || "No description available for this book.");
        } else {
          setBookDescription("No description found for this ISBN.");
        }
      } catch (e) {
        setBookDescription("Failed to load description.");
      } finally {
        setIsFetchingDescription(false);
      }
    } else {
      setBookDescription("This book does not have an ISBN recorded.");
    }
  };

  // Query all members for the checkout dropdown
  const { data: membersData } = useQuery({
    queryKey: ["all-members-dropdown"],
    queryFn: () => api.get("/users/?per_page=500").then(r => r.data),
    enabled: isAdmin && !!selectedBookForIssue,
  });

  const handleIssueBook = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedMemberId) {
      toast.error("Please select a member.");
      return;
    }
    const today = new Date().toISOString().split("T")[0];
    if (expectedReturnDate < today) {
      toast.error("Return date cannot be in the past.");
      return;
    }
    setIsSubmitting(true);
    try {
      await api.post("/transactions/issue", {
        user_id: parseInt(selectedMemberId),
        book_id: selectedBookForIssue.id,
        expected_return_date: expectedReturnDate,
      });
      toast.success(`"${selectedBookForIssue.title}" successfully issued!`);
      setSelectedBookForIssue(null);
      setSelectedMemberId("");
      refetch();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Failed to issue book.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (id: number, title: string) => {
    if (!confirm(`Delete "${title}"?`)) return;
    try {
      await api.delete(`/books/${id}`);
      toast.success("Book deleted.");
      refetch();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Failed to delete.");
    }
  };

  const totalPages = data ? Math.ceil(data.total / PER_PAGE) : 1;

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <BookOpen className="text-indigo-400" size={26} /> Book Catalog
          </h1>
          <p className="text-slate-400 text-sm mt-1">{data?.total ?? "—"} total books</p>
        </div>
        {isAdmin && (
          <a href="/dashboard/books/add">
            <motion.button whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
              className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl text-white text-sm font-medium shadow-lg shadow-indigo-500/20 hover:opacity-90 transition-opacity">
              <Plus size={16} /> Add Book
            </motion.button>
          </a>
        )}
      </motion.div>

      {/* Search bar */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
        <input
          value={search}
          onChange={(e) => handleSearch(e.target.value)}
          placeholder="Search by title, author, or ISBN..."
          className="w-full bg-white/5 border border-white/10 rounded-xl pl-12 pr-12 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/50 transition-all"
        />
        {isFetching && (
          <Loader2 className="absolute right-4 top-1/2 -translate-y-1/2 text-indigo-400 animate-spin" size={18} />
        )}
      </div>

      {/* Table */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
        className="glass overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/5">
                {["Title", "Author", "Year", "Copies", "Available", "Actions"].map(h => (
                  <th key={h} className="text-left text-slate-400 text-xs font-semibold uppercase tracking-wider px-6 py-4">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                Array.from({ length: 8 }).map((_, i) => (
                  <tr key={i} className="border-b border-white/5">
                    {Array.from({ length: 6 }).map((_, j) => (
                      <td key={j} className="px-6 py-4">
                        <div className="h-4 bg-white/5 rounded animate-pulse" style={{ width: `${60 + Math.random() * 30}%` }} />
                      </td>
                    ))}
                  </tr>
                ))
              ) : data?.data?.length === 0 ? (
                <tr><td colSpan={6} className="px-6 py-16 text-center text-slate-500">No books found.</td></tr>
              ) : data?.data?.map((book: any) => {


                return (
                  <motion.tr key={book.id}
                    initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                    className="border-b border-white/5 hover:bg-white/3 transition-colors group"
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        {book.cover_url ? (
                          /* eslint-disable-next-line @next/next/no-img-element */
                          <img src={book.cover_url} alt={book.title} className="w-10 h-14 object-cover rounded border border-white/10 shadow-sm" />
                        ) : (
                          <div className="w-10 h-14 bg-slate-800/50 border border-white/5 flex items-center justify-center rounded shadow-sm">
                            <BookOpen size={16} className="text-slate-500" />
                          </div>
                        )}
                        <span className="text-white font-medium">{book.title}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-slate-300">{book.author}</td>
                    <td className="px-6 py-4 text-slate-400">{book.publish_year ?? "—"}</td>
                    <td className="px-6 py-4 text-slate-300">{book.total_copies}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${
                        book.available_copies > 0
                          ? "bg-emerald-500/15 text-emerald-400"
                          : "bg-red-500/15 text-red-400"
                      }`}>
                        {book.available_copies}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {isAdmin ? (
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => setSelectedBookForIssue(book)}
                            disabled={book.available_copies < 1}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/10 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                            title="Issue Book"
                          >
                            <ArrowLeftRight size={15} />
                          </button>
                          <a href={`/dashboard/books/${book.id}/edit`}>
                            <button className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-400 hover:bg-indigo-500/10 transition-all" title="Edit">
                              <Edit size={15} />
                            </button>
                          </a>
                          <button onClick={() => handleDelete(book.id, book.title)}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-all" title="Delete">
                            <Trash2 size={15} />
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => handleViewDetails(book)}
                          className="px-3 py-1.5 bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 rounded-lg text-xs font-semibold hover:bg-indigo-500/30 transition-all"
                        >
                          View Details
                        </button>
                      )}
                    </td>
                  </motion.tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
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

      {/* Issue Book Modal */}
      {selectedBookForIssue && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="w-full max-w-md bg-slate-900 border border-white/10 rounded-2xl p-6 space-y-6"
          >
            <div>
              <h3 className="text-xl font-bold text-white">Issue Book</h3>
              <p className="text-slate-400 text-sm mt-1">
                Checkout &ldquo;<span className="text-indigo-300 font-semibold">{selectedBookForIssue.title}</span>&rdquo; to a member.
              </p>
            </div>

            <form onSubmit={handleIssueBook} className="space-y-4">
              <div className="space-y-2">
                <label className="text-slate-300 text-xs font-semibold uppercase tracking-wider block">Select Member</label>
                <select
                  value={selectedMemberId}
                  onChange={(e) => setSelectedMemberId(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500 transition-all"
                  required
                >
                  <option value="" className="bg-slate-900 text-slate-500">Choose a member...</option>
                  {membersData?.data?.map((m: any) => (
                    <option key={m.id} value={m.id} className="bg-slate-900 text-white">
                      {m.name} ({m.username})
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-slate-300 text-xs font-semibold uppercase tracking-wider block">Expected Return Date</label>
                  <span className="text-[10px] text-indigo-400 font-medium">Quick Select:</span>
                </div>
                
                <div className="flex gap-2 mb-2">
                  {[7, 14, 30].map((days) => (
                    <button
                      key={days}
                      type="button"
                      onClick={() => {
                        const d = new Date();
                        d.setDate(d.getDate() + days);
                        setExpectedReturnDate(d.toISOString().split("T")[0]);
                      }}
                      className="flex-1 py-2 text-xs font-semibold bg-white/5 hover:bg-indigo-600/20 border border-white/10 hover:border-indigo-500/50 rounded-xl text-indigo-300 hover:text-indigo-200 transition-all cursor-pointer"
                    >
                      {days} Days
                    </button>
                  ))}
                </div>

                <input
                  type="date"
                  min={new Date().toISOString().split("T")[0]}
                  value={expectedReturnDate}
                  onChange={(e) => setExpectedReturnDate(e.target.value)}
                  className="w-full bg-slate-900 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500 transition-all"
                  required
                />
              </div>

              <div className="flex items-center gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedBookForIssue(null)}
                  disabled={isSubmitting}
                  className="flex-1 px-4 py-3 bg-white/5 hover:bg-white/10 text-white rounded-xl text-sm font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex-1 px-4 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-semibold shadow-lg shadow-indigo-500/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {isSubmitting ? (
                    <>
                      <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Issuing...
                    </>
                  ) : (
                    "Confirm Issue"
                  )}
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}

      {/* View Details Modal for Members */}
      {selectedBookForDetails && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="w-full max-w-lg bg-slate-900 border border-white/10 rounded-2xl overflow-hidden shadow-2xl"
          >
            <div className="p-6">
              <div className="flex gap-5">
                {selectedBookForDetails.cover_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={selectedBookForDetails.cover_url} alt={selectedBookForDetails.title} className="w-28 h-40 object-cover rounded shadow-md border border-white/10" />
                ) : (
                  <div className="w-28 h-40 bg-slate-800/50 border border-white/5 flex items-center justify-center rounded shadow-md">
                    <BookOpen size={28} className="text-slate-500" />
                  </div>
                )}
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-white leading-tight">{selectedBookForDetails.title}</h3>
                  <p className="text-indigo-400 font-medium text-sm mt-1">{selectedBookForDetails.author}</p>
                  <div className="flex flex-col gap-2 mt-3">
                    <span className="inline-flex w-fit px-2 py-1 bg-white/5 border border-white/10 rounded text-xs text-slate-300">
                      Published: {selectedBookForDetails.publish_year || "Unknown"}
                    </span>
                    <span className="inline-flex w-fit px-2 py-1 bg-white/5 border border-white/10 rounded text-xs text-slate-300">
                      ISBN: {selectedBookForDetails.isbn || "N/A"}
                    </span>
                    <span className={`inline-flex w-fit px-2 py-1 border rounded text-xs font-semibold ${selectedBookForDetails.available_copies > 0 ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400" : "bg-red-500/10 border-red-500/20 text-red-400"}`}>
                      {selectedBookForDetails.available_copies > 0 ? `${selectedBookForDetails.available_copies} Copies Available` : "Out of Stock"}
                    </span>
                  </div>
                </div>
              </div>
              
              <div className="mt-6 space-y-2">
                <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">About this Book</h4>
                <div className="bg-white/5 border border-white/10 rounded-xl p-4 text-sm text-slate-300 leading-relaxed max-h-48 overflow-y-auto custom-scrollbar">
                  {isFetchingDescription ? (
                    <div className="flex items-center gap-2 text-indigo-400 justify-center py-4">
                      <Loader2 className="animate-spin" size={16} /> Fetching description...
                    </div>
                  ) : (
                    <p className="whitespace-pre-line">{bookDescription}</p>
                  )}
                </div>
              </div>
            </div>
            
            <div className="p-4 border-t border-white/10 bg-slate-950/50 flex justify-end">
              <button
                onClick={() => setSelectedBookForDetails(null)}
                className="px-5 py-2.5 text-sm font-semibold text-white bg-white/10 hover:bg-white/20 rounded-xl transition-all"
              >
                Close
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
