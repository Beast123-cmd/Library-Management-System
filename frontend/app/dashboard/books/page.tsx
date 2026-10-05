"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { useQuery, useQueryClient, keepPreviousData } from "@tanstack/react-query";
import { Search, Plus, BookOpen, Edit, Trash2, ChevronLeft, ChevronRight, ArrowLeftRight, Loader2, SlidersHorizontal, X, MapPin, Download, Upload, Grid2X2, List } from "lucide-react";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import toast from "react-hot-toast";

function localDateAfter(days: number) {
  const value = new Date();
  value.setDate(value.getDate() + days);
  return `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, "0")}-${String(value.getDate()).padStart(2, "0")}`;
}

export default function BooksPage() {
  const { isAdmin } = useAuth();
  const queryClient = useQueryClient();
  const importInputRef = useRef<HTMLInputElement>(null);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [category, setCategory] = useState("");
  const [language, setLanguage] = useState("");
  const [author, setAuthor] = useState("");
  const [publisher, setPublisher] = useState("");
  const [shelfLocation, setShelfLocation] = useState("");
  const [availableOnly, setAvailableOnly] = useState(false);
  const [sortBy, setSortBy] = useState("title");
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [page, setPage] = useState(1);
  const PER_PAGE = 24;

  useEffect(() => {
    const timer = window.setTimeout(() => { setDebouncedSearch(search); setPage(1); }, 300);
    return () => window.clearTimeout(timer);
  }, [search]);

  const { data, isLoading, isFetching, refetch } = useQuery({
    queryKey: ["books", debouncedSearch, category, language, author, publisher, shelfLocation, availableOnly, sortBy, page],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page), per_page: String(PER_PAGE) });
      if (debouncedSearch) params.set("search", debouncedSearch);
      if (category.trim()) params.set("category", category.trim());
      if (language.trim()) params.set("language", language.trim());
      if (author.trim()) params.set("author", author.trim());
      if (publisher.trim()) params.set("publisher", publisher.trim());
      if (shelfLocation.trim()) params.set("shelf_location", shelfLocation.trim());
      if (availableOnly) params.set("available_only", "true");
      params.set("sort_by", sortBy);
      return api.get(`/books/?${params}`).then(r => r.data);
    },
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  });
  const { data: filterOptions } = useQuery({
    queryKey: ["catalog-filter-options"],
    queryFn: () => api.get("/books/filter-options").then(r => r.data),
    staleTime: 5 * 60_000,
  });
  const [selectedBookForIssue, setSelectedBookForIssue] = useState<any>(null);
  const [selectedMemberId, setSelectedMemberId] = useState("");
  const [expectedReturnDate, setExpectedReturnDate] = useState(() => localDateAfter(14));
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isImporting, setIsImporting] = useState(false);

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
    const earliestReturnDate = localDateAfter(1);
    const latestReturnDate = localDateAfter(90);
    if (expectedReturnDate < earliestReturnDate || expectedReturnDate > latestReturnDate) {
      toast.error("Choose a return date between tomorrow and 90 days from now.");
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

  const exportCatalogue = async () => {
    try {
      const response = await api.get("/books/export", { responseType: "blob" });
      const url = URL.createObjectURL(response.data);
      const link = document.createElement("a");
      link.href = url; link.download = "library-catalogue.csv"; link.click();
      URL.revokeObjectURL(url);
    } catch { toast.error("Could not export the catalogue."); }
  };

  const importCatalogue = async (file?: File) => {
    if (!file) return;
    setIsImporting(true);
    try {
      const formData = new FormData(); formData.append("file", file);
      const response = await api.post("/books/import", formData, { headers: { "Content-Type": "multipart/form-data" } });
      const { created, skipped, errors } = response.data;
      toast.success(`${created} book${created === 1 ? "" : "s"} imported${skipped ? `, ${skipped} duplicate${skipped === 1 ? "" : "s"} skipped` : ""}.`);
      if (errors.length) toast.error(errors[0]);
      queryClient.invalidateQueries({ queryKey: ["books"] });
      queryClient.invalidateQueries({ queryKey: ["catalog-filter-options"] });
    } catch (error: any) { toast.error(error?.response?.data?.detail || "Could not import this CSV."); }
    finally { setIsImporting(false); if (importInputRef.current) importInputRef.current.value = ""; }
  };

  const totalPages = data ? Math.ceil(data.total / PER_PAGE) : 1;
  const activeFilters = [category, language, author, publisher, shelfLocation, availableOnly].filter(Boolean).length;
  const clearFilters = () => { setCategory(""); setLanguage(""); setAuthor(""); setPublisher(""); setShelfLocation(""); setAvailableOnly(false); setPage(1); };
  const goToPage = (nextPage: number) => {
    setPage(nextPage);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };
  const firstResult = data?.total ? (page - 1) * PER_PAGE + 1 : 0;
  const lastResult = data?.total ? Math.min(page * PER_PAGE, data.total) : 0;
  const pageNumbers = Array.from({ length: totalPages }, (_, index) => index + 1).filter(number => number === 1 || number === totalPages || Math.abs(number - page) <= 1);

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
        {isAdmin && (<div className="flex items-center gap-2">
          <input ref={importInputRef} onChange={event => importCatalogue(event.target.files?.[0])} type="file" accept=".csv,text/csv" className="hidden" />
          <button type="button" onClick={() => importInputRef.current?.click()} disabled={isImporting} className="hidden sm:inline-flex items-center gap-1.5 rounded-xl border border-white/10 px-3 py-2.5 text-xs font-semibold text-slate-300 hover:border-teal-400/30 hover:text-teal-200 disabled:opacity-50"><Upload size={15} /> {isImporting ? "Importing…" : "Import CSV"}</button>
          <button type="button" onClick={exportCatalogue} className="hidden sm:inline-flex items-center gap-1.5 rounded-xl border border-white/10 px-3 py-2.5 text-xs font-semibold text-slate-300 hover:border-teal-400/30 hover:text-teal-200"><Download size={15} /> Export</button>
          <a href="/dashboard/books/add">
            <motion.button whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
              className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl text-white text-sm font-medium shadow-lg shadow-indigo-500/20 hover:opacity-90 transition-opacity">
              <Plus size={16} /> Add Book
            </motion.button>
          </a></div>
        )}
      </motion.div>

      <section className="catalog-controls glass p-3 sm:p-4">
        <div className="flex flex-col gap-3 lg:flex-row">
          <div className="relative flex-1"><Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18} /><input aria-label="Search the catalogue" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search title, author, ISBN, or publisher" className="w-full bg-white/5 border border-white/10 rounded-xl pl-11 pr-11 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/50 transition-all" />{search && <button type="button" onClick={() => setSearch("")} className="absolute right-10 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white" aria-label="Clear search"><X size={16} /></button>}{isFetching && <Loader2 className="absolute right-4 top-1/2 -translate-y-1/2 text-indigo-400 animate-spin" size={18} />}</div>
          <div className="grid grid-cols-2 gap-2 sm:flex"><button type="button" onClick={() => setFiltersOpen(!filtersOpen)} className={`filter-trigger ${filtersOpen || activeFilters ? "filter-trigger-active" : ""}`}><SlidersHorizontal size={17} /> Filters{activeFilters > 0 && <span>{activeFilters}</span>}</button><select value={sortBy} onChange={e => { setSortBy(e.target.value); setPage(1); }} aria-label="Sort catalog" className="filter-select"><option value="title">Title A–Z</option><option value="newest">Recently added</option><option value="year_desc">Newest publication</option><option value="year_asc">Oldest publication</option><option value="availability">Most available</option></select><div className="catalog-view-switch" role="group" aria-label="Catalog layout"><button type="button" onClick={() => setViewMode("grid")} aria-label="Card view" aria-pressed={viewMode === "grid"} className={viewMode === "grid" ? "catalog-view-active" : ""}><Grid2X2 size={17} /><span>Cards</span></button><button type="button" onClick={() => setViewMode("list")} aria-label="List view" aria-pressed={viewMode === "list"} className={viewMode === "list" ? "catalog-view-active" : ""}><List size={18} /><span>List</span></button></div></div>
        </div>
        {filtersOpen && <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} className="mt-4 border-t border-white/5 pt-4"><div className="mb-3 flex items-center justify-between"><p className="text-sm font-medium text-white">Refine your results</p>{activeFilters > 0 && <button type="button" onClick={clearFilters} className="inline-flex items-center gap-1 text-xs text-teal-300 hover:text-white"><X size={13} /> Reset filters</button>}</div><div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3"><FilterSelect label="Category" value={category} options={filterOptions?.categories} onChange={value => { setCategory(value); setPage(1); }} /><FilterSelect label="Language" value={language} options={filterOptions?.languages} onChange={value => { setLanguage(value); setPage(1); }} /><FilterSelect label="Author" value={author} options={filterOptions?.authors} onChange={value => { setAuthor(value); setPage(1); }} /><FilterSelect label="Publisher" value={publisher} options={filterOptions?.publishers} onChange={value => { setPublisher(value); setPage(1); }} /><FilterSelect label="Shelf location" value={shelfLocation} options={filterOptions?.shelves} onChange={value => { setShelfLocation(value); setPage(1); }} /><button type="button" onClick={() => { setAvailableOnly(!availableOnly); setPage(1); }} className={`availability-filter ${availableOnly ? "availability-filter-active" : ""}`}><span className="availability-check">{availableOnly ? "✓" : ""}</span><span><b>Available now</b><small>Show books ready to borrow</small></span></button></div></motion.div>}
        {activeFilters > 0 && <div className="mt-3 flex flex-wrap items-center gap-2"><span className="catalog-filter-chip">{activeFilters} filter{activeFilters > 1 ? "s" : ""} applied</span><button type="button" onClick={clearFilters} className="inline-flex items-center gap-1 px-2 text-xs text-slate-400 hover:text-white"><X size={13} /> Clear all</button></div>}
      </section>

      <div className="flex items-center justify-between gap-3"><p className="text-sm text-slate-400">{data?.total ? <>Showing <span className="font-semibold text-white">{firstResult}–{lastResult}</span> of <span className="font-semibold text-white">{data.total}</span> titles</> : "Loading catalog…"}</p>{!filtersOpen && <button type="button" onClick={() => { setAvailableOnly(!availableOnly); setPage(1); }} className={`text-xs font-medium rounded-full px-3 py-1.5 border transition-colors ${availableOnly ? "bg-emerald-500/15 border-emerald-500/30 text-emerald-300" : "bg-white/5 border-white/10 text-slate-400 hover:text-white"}`}>Available now</button>}</div>

      <div className={viewMode === "grid" ? "catalog-grid" : "catalog-list"}>
        {isLoading ? Array.from({ length: 8 }).map((_, index) => <div key={index} className="catalog-card h-[21rem] animate-pulse"><div className="h-36 bg-white/5 rounded-xl" /></div>) : data?.data?.length === 0 ? <div className="catalog-empty"><BookOpen size={28} className="text-slate-500" /><p className="mt-3 text-white font-medium">No books match these filters.</p><button type="button" onClick={clearFilters} className="mt-3 text-sm text-indigo-400 hover:text-indigo-300">Clear catalog filters</button></div> : data?.data?.map((book: any, index: number) => <motion.article key={book.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: Math.min(index * 0.03, 0.2) }} className="catalog-card group">
          <div className="relative h-40 overflow-hidden rounded-xl bg-slate-800/50 border border-white/5">{book.cover_url ? <img src={book.cover_url} alt={book.title} className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105" /> : <div className="h-full w-full flex items-center justify-center"><BookOpen size={32} className="text-slate-500" /></div>}<span className={`absolute right-3 top-3 rounded-full border px-2.5 py-1 text-[11px] font-semibold backdrop-blur ${book.available_copies > 0 ? "bg-emerald-500/15 border-emerald-400/20 text-emerald-300" : "bg-red-500/15 border-red-400/20 text-red-300"}`}>{book.available_copies > 0 ? `${book.available_copies} available` : "Unavailable"}</span></div>
          <div className="mt-4 flex flex-1 flex-col"><div><h2 className="line-clamp-2 text-base font-semibold leading-5 text-white">{book.title}</h2><p className="mt-1 text-sm text-slate-400 line-clamp-1">{book.author}</p></div><div className="mt-3 flex flex-wrap gap-1.5">{[book.category, book.language].filter(Boolean).map((item: string) => <span key={item} className="catalog-meta">{item}</span>)}{book.shelf_location && <span className="catalog-meta inline-flex items-center gap-1"><MapPin size={11} />{book.shelf_location}</span>}</div><p className="mt-3 text-xs text-slate-500">{book.publish_year ? `Published ${book.publish_year}` : "Publication year unavailable"}{book.publisher ? ` · ${book.publisher}` : ""}</p><div className="mt-auto pt-4 flex items-center gap-2">{isAdmin ? <><button onClick={() => setSelectedBookForIssue(book)} disabled={book.available_copies < 1} className="catalog-card-action flex-1 disabled:opacity-40"><ArrowLeftRight size={15} /> Issue</button><Link href={`/dashboard/books/${book.id}/edit`} className="catalog-icon-action" aria-label={`Edit ${book.title}`}><Edit size={15} /></Link><button onClick={() => handleDelete(book.id, book.title)} className="catalog-icon-action hover:text-red-300" aria-label={`Delete ${book.title}`}><Trash2 size={15} /></button></> : <Link href={`/dashboard/books/${book.id}`} className="catalog-card-action w-full">View details</Link>}</div></div>
        </motion.article>)}</div>

      {totalPages > 1 && <nav className="catalog-pagination" aria-label="Catalog pages"><button onClick={() => goToPage(Math.max(1, page - 1))} disabled={page === 1} className="catalog-page-direction"><ChevronLeft size={17} /> <span>Previous</span></button><div className="flex items-center gap-1" aria-label={`Page ${page} of ${totalPages}`}>{pageNumbers.map((number, index) => <span key={number} className="flex items-center gap-1">{index > 0 && number - pageNumbers[index - 1] > 1 && <span className="catalog-page-gap">…</span>}<button onClick={() => goToPage(number)} className={`catalog-page-number ${page === number ? "catalog-page-current" : ""}`} aria-current={page === number ? "page" : undefined}>{number}</button></span>)}</div><button onClick={() => goToPage(Math.min(totalPages, page + 1))} disabled={page === totalPages} className="catalog-page-direction"><span>Next</span> <ChevronRight size={17} /></button></nav>}

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
                  {[7, 14, 21, 30].map((days) => (
                    <button
                      key={days}
                      type="button"
                      onClick={() => {
                        setExpectedReturnDate(localDateAfter(days));
                      }}
                      className={`flex-1 py-2 text-xs font-semibold border rounded-xl transition-all cursor-pointer ${expectedReturnDate === localDateAfter(days) ? "bg-indigo-600/30 border-indigo-400/60 text-white" : "bg-white/5 hover:bg-indigo-600/20 border-white/10 hover:border-indigo-500/50 text-indigo-300 hover:text-indigo-200"}`}
                    >
                      {days} Days
                    </button>
                  ))}
                </div>

                <input
                  type="date"
                  min={localDateAfter(1)}
                  max={localDateAfter(90)}
                  value={expectedReturnDate}
                  onChange={(e) => setExpectedReturnDate(e.target.value)}
                  className="w-full bg-slate-900 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500 transition-all"
                  required
                />
                <p className="text-[11px] text-slate-500">Choose a preset, or set a date within the next 90 days.</p>
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

    </div>
  );
}

function FilterSelect({ label, value, options = [], onChange }: { label: string; value: string; options?: string[]; onChange: (value: string) => void }) {
  return <label className="catalog-filter-field"><span>{label}</span><select value={value} onChange={event => onChange(event.target.value)}><option value="">All {label.toLowerCase()}s</option>{options.map(option => <option key={option} value={option}>{option}</option>)}</select></label>;
}
