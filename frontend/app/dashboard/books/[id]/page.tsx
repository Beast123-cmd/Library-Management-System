"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, BookOpen, CalendarDays, CheckCircle2, MapPin, Pencil, Tag, Users } from "lucide-react";
import toast from "react-hot-toast";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export default function BookDetailsPage() {
  const { id } = useParams<{ id: string }>();
  const { isAdmin } = useAuth();
  const queryClient = useQueryClient();
  const { data: book, isLoading } = useQuery({ queryKey: ["book", id], queryFn: () => api.get(`/books/${id}`).then(response => response.data) });
  const { data: holds = [] } = useQuery({ queryKey: ["member-holds"], queryFn: () => api.get("/holds/my-holds").then(response => response.data), enabled: !isAdmin });
  const { data: similar } = useQuery({ queryKey: ["similar-books", book?.category, book?.id], queryFn: () => api.get(`/books/?category=${encodeURIComponent(book.category)}&per_page=4`).then(response => response.data), enabled: !!book?.category });

  if (isLoading) return <div className="glass min-h-[32rem] animate-pulse" />;
  if (!book) return <div className="glass p-8 text-center text-slate-400">This book could not be found.</div>;

  const reserve = async () => {
    try {
      await api.post(`/holds/${book.id}`);
      toast.success("Book reserved for 12 hours. Please collect it from the library.");
      queryClient.invalidateQueries({ queryKey: ["book", id] });
      queryClient.invalidateQueries({ queryKey: ["books"] });
      queryClient.invalidateQueries({ queryKey: ["member-holds"] });
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || "Could not reserve this book.");
    }
  };

  return <div className="mx-auto max-w-5xl space-y-7">
    <Link href="/dashboard/books" className="inline-flex items-center gap-2 text-sm font-medium text-slate-400 hover:text-teal-200"><ArrowLeft size={16} /> Back to catalogue</Link>
    <section className="glass overflow-hidden p-5 sm:p-8"><div className="grid gap-7 md:grid-cols-[13rem_1fr]">
      <div className="overflow-hidden rounded-2xl border border-white/10 bg-slate-900/50 shadow-xl">{book.cover_url ? <img src={book.cover_url} alt={book.title} className="aspect-[3/4] h-full w-full object-cover" /> : <div className="flex aspect-[3/4] items-center justify-center"><BookOpen className="text-slate-500" size={48} /></div>}</div>
      <div><div className="flex flex-wrap items-center gap-2"><span className="catalog-meta">{book.category || "General"}</span><span className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${book.available_copies > 0 ? "border-emerald-400/20 bg-emerald-500/15 text-emerald-300" : "border-red-400/20 bg-red-500/15 text-red-300"}`}>{book.available_copies > 0 ? `${book.available_copies} available now` : "All copies are checked out"}</span></div><h1 className="mt-4 text-3xl font-bold tracking-tight text-white sm:text-4xl">{book.title}</h1><p className="mt-2 text-lg text-teal-200">by {book.author}</p><div className="mt-6 grid gap-3 text-sm text-slate-300 sm:grid-cols-2"><Detail icon={CalendarDays} label="Published" value={book.publish_year || "Not listed"} /><Detail icon={Tag} label="Publisher" value={book.publisher || "Not listed"} /><Detail icon={BookOpen} label="Language" value={book.language || "Not listed"} /><Detail icon={MapPin} label="Find it at" value={book.shelf_location || "Ask library staff"} /></div><div className="mt-7 flex flex-wrap gap-3">{isAdmin ? <Link href={`/dashboard/books/${book.id}/edit`} className="brand-button"><Pencil size={16} /> Edit inventory</Link> : <button onClick={reserve} disabled={book.available_copies < 1 || holds.length > 0} className="brand-button disabled:cursor-not-allowed disabled:opacity-45"><CheckCircle2 size={16} /> {holds.length > 0 ? "You already have a hold" : "Reserve for pickup"}</button>}<span className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-4 py-2.5 text-sm text-slate-400"><Users size={16} /> {book.total_copies} total copies</span></div></div>
    </div></section>
    <section className="glass p-5 sm:p-7"><h2 className="text-lg font-semibold text-white">About this book</h2><p className="mt-3 max-w-3xl whitespace-pre-line leading-7 text-slate-300">{book.description || "A library copy ready to discover. Ask staff for more information about this title."}</p></section>
    {similar?.data?.length > 1 && <section><div className="mb-3 flex items-center justify-between"><h2 className="text-lg font-semibold text-white">More in {book.category}</h2><Link href={`/dashboard/books?category=${encodeURIComponent(book.category)}`} className="text-sm text-teal-300 hover:text-white">Browse category</Link></div><div className="grid gap-3 sm:grid-cols-3">{similar.data.filter((item: any) => item.id !== book.id).slice(0, 3).map((item: any) => <Link key={item.id} href={`/dashboard/books/${item.id}`} className="catalog-card min-h-0 p-4"><p className="font-semibold text-white">{item.title}</p><p className="mt-1 text-sm text-slate-400">{item.author}</p></Link>)}</div></section>}
  </div>;
}

function Detail({ icon: Icon, label, value }: { icon: typeof BookOpen; label: string; value: string | number }) {
  return <div className="flex items-center gap-2"><Icon size={16} className="text-teal-300" /><span className="text-slate-500">{label}</span><span>{value}</span></div>;
}
