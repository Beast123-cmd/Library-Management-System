"use client";
import { useState } from "react";
import { motion } from "framer-motion";
import { BookOpen, ArrowLeft, Loader2, Search } from "lucide-react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import toast from "react-hot-toast";

export default function AddBookPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [fetchingMetadata, setFetchingMetadata] = useState(false);
  
  const [title, setTitle] = useState("");
  const [author, setAuthor] = useState("");
  const [isbn, setIsbn] = useState("");
  const [publishYear, setPublishYear] = useState<number | "">("");
  const [totalCopies, setTotalCopies] = useState<number>(1);
  const [coverUrl, setCoverUrl] = useState("");

  const handleAutoFill = async () => {
    const cleanIsbn = isbn.replace(/-/g, "").trim();
    if (!cleanIsbn) return toast.error("Please enter an ISBN first.");
    
    setFetchingMetadata(true);
    try {
      const res = await fetch(`https://openlibrary.org/api/books?bibkeys=ISBN:${cleanIsbn}&format=json&jscmd=data`);
      const data = await res.json();
      const bookData = data[`ISBN:${cleanIsbn}`];
      
      if (bookData) {
        if (bookData.title) setTitle(bookData.title);
        if (bookData.authors && bookData.authors.length > 0) {
          setAuthor(bookData.authors[0].name);
        }
        if (bookData.publish_date) {
          const yearMatch = bookData.publish_date.match(/\d{4}/);
          if (yearMatch) setPublishYear(parseInt(yearMatch[0]));
        }
        if (bookData.cover && bookData.cover.large) {
          setCoverUrl(bookData.cover.large);
        } else if (bookData.cover && bookData.cover.medium) {
          setCoverUrl(bookData.cover.medium);
        }
        toast.success("Auto-filled details from Open Library!");
      } else {
        toast.error("No book found for this ISBN.");
      }
    } catch (e) {
      toast.error("Failed to fetch book data.");
    } finally {
      setFetchingMetadata(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !author) {
      return toast.error("Title and Author are required.");
    }
    setLoading(true);
    try {
      await api.post("/books/", {
        title,
        author,
        isbn: isbn || null,
        publish_year: publishYear || null,
        total_copies: totalCopies,
        available_copies: totalCopies,
        cover_url: coverUrl || null,
      });
      toast.success("Book added successfully!");
      router.push("/dashboard/books");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Failed to add book.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Back Button */}
      <button onClick={() => router.back()}
        className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors">
        <ArrowLeft size={16} /> Back to Catalog
      </button>

      <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }}
        className="glass p-8">
        
        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 bg-indigo-500/10 rounded-xl text-indigo-400">
            <BookOpen size={24} />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Add New Book</h1>
            <p className="text-slate-400 text-sm">Enter the book details below to add it to the catalog</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">ISBN</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={isbn}
                  onChange={(e) => setIsbn(e.target.value)}
                  placeholder="e.g. 9780743273565"
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-all"
                />
                <button
                  type="button"
                  onClick={handleAutoFill}
                  disabled={fetchingMetadata}
                  className="flex items-center gap-2 px-4 py-2.5 bg-indigo-600/20 text-indigo-400 hover:bg-indigo-600/30 border border-indigo-500/30 rounded-xl font-medium text-sm transition-all disabled:opacity-50"
                  title="Auto-fill using ISBN"
                >
                  {fetchingMetadata ? <Loader2 className="animate-spin" size={16} /> : <Search size={16} />}
                  Fetch
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Publish Year</label>
              <input
                type="number"
                value={publishYear}
                onChange={(e) => setPublishYear(e.target.value ? parseInt(e.target.value) : "")}
                placeholder="e.g. 1925"
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-all"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Book Title *</label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. The Great Gatsby"
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-all"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Author Name *</label>
            <input
              type="text"
              required
              value={author}
              onChange={(e) => setAuthor(e.target.value)}
              placeholder="e.g. F. Scott Fitzgerald"
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-all"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Total Copies Available *</label>
              <input
                type="number"
                min="1"
                required
                value={totalCopies}
                onChange={(e) => setTotalCopies(Math.max(1, parseInt(e.target.value) || 1))}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-all"
              />
            </div>
            <div>
               <label className="block text-sm font-medium text-slate-300 mb-1">Cover Image URL</label>
               <input
                 type="url"
                 value={coverUrl}
                 onChange={(e) => setCoverUrl(e.target.value)}
                 placeholder="https://..."
                 className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-all"
               />
            </div>
          </div>

          {coverUrl && (
            <div className="pt-2">
               <p className="text-xs text-slate-400 mb-2">Cover Preview</p>
               {/* eslint-disable-next-line @next/next/no-img-element */}
               <img src={coverUrl} alt="Cover Preview" className="h-32 w-auto object-cover rounded-lg border border-white/10 shadow-lg" />
            </div>
          )}

          <div className="pt-4 flex items-center justify-end gap-3 border-t border-white/5 mt-6">
            <button
              type="button"
              onClick={() => router.back()}
              className="px-5 py-2.5 rounded-xl border border-white/10 text-slate-300 hover:bg-white/5 transition-colors font-medium text-sm"
            >
              Cancel
            </button>
            <motion.button
              type="submit"
              disabled={loading}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 text-white rounded-xl font-medium text-sm hover:bg-indigo-500 transition-colors shadow-lg shadow-indigo-600/20 disabled:opacity-50"
            >
              {loading ? <Loader2 className="animate-spin" size={16} /> : null}
              {loading ? "Adding..." : "Add Book"}
            </motion.button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}
