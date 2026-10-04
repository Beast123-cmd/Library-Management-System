"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, BookOpen, CheckCircle2, Clock3, Library, ShieldCheck, Users } from "lucide-react";

const steps = [
  ["1", "Find a title", "Search by title, author, shelf, category, or language."],
  ["2", "Reserve or borrow", "Place a hold or let staff issue the exact physical copy."],
  ["3", "Stay on track", "See due dates, renew once, and keep return receipts in one place."],
];

export default function Home() {
  return <main className="marketing-shell min-h-screen overflow-hidden">
    <div className="absolute inset-x-0 top-0 h-[36rem] bg-[radial-gradient(circle_at_72%_18%,rgba(45,212,191,0.18),transparent_30rem)] pointer-events-none" />
    <nav className="relative max-w-7xl mx-auto px-5 sm:px-8 py-5 flex items-center justify-between">
      <Link href="/" className="flex items-center gap-2.5 text-white font-semibold tracking-tight"><span className="brand-mark"><Library size={19} /></span> Library Desk</Link>
      <div className="flex items-center gap-2 sm:gap-3"><Link href="/login" className="secondary-button text-sm px-3.5 py-2">Sign in</Link><Link href="/signup" className="brand-button text-sm px-3.5 py-2">Create account</Link></div>
    </nav>
    <section className="relative max-w-7xl mx-auto px-5 sm:px-8 pt-14 sm:pt-24 pb-20 grid lg:grid-cols-[1.08fr_.92fr] gap-12 items-center">
      <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.55 }}>
        <p className="eyebrow"><span className="w-1.5 h-1.5 rounded-full bg-emerald-300" /> Library operations, made clear</p>
        <h1 className="mt-5 text-4xl sm:text-5xl lg:text-6xl font-bold tracking-[-0.045em] leading-[1.03] text-white max-w-3xl">A calmer way to run your library.</h1>
        <p className="mt-6 max-w-xl text-lg leading-8 text-slate-300">Library Desk helps members find and reserve books while giving staff a focused view of loans, pickups, copies, and day-to-day work.</p>
        <div className="mt-8 flex flex-col sm:flex-row gap-3"><Link href="/signup" className="brand-button justify-center py-3.5 px-5">Create a member account <ArrowRight size={17} /></Link><Link href="/login" className="secondary-button justify-center py-3.5 px-5">Sign in to Library Desk</Link></div>
        <div className="mt-8 flex flex-wrap gap-x-5 gap-y-2 text-sm text-slate-400"><span className="flex items-center gap-2"><CheckCircle2 size={16} className="text-emerald-300" /> Physical-copy tracking</span><span className="flex items-center gap-2"><CheckCircle2 size={16} className="text-emerald-300" /> Clear hold deadlines</span></div>
      </motion.div>
      <motion.div initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.12, duration: 0.55 }} className="hero-console">
        <div className="flex items-center justify-between border-b border-white/10 pb-4"><div><p className="text-xs uppercase tracking-[0.16em] text-teal-200">Today at the desk</p><p className="text-white font-semibold mt-1">Your circulation snapshot</p></div><span className="status-pill status-live">Live</span></div>
        <div className="grid grid-cols-3 gap-3 mt-5"><Metric icon={Clock3} value="03" label="Due today" /><Metric icon={BookOpen} value="12" label="Active loans" /><Metric icon={Users} value="04" label="Ready pickups" /></div>
        <div className="mt-5 rounded-2xl bg-black/15 border border-white/8 p-4"><div className="flex items-center justify-between"><div><p className="font-medium text-white text-sm">The Pragmatic Programmer</p><p className="text-xs text-slate-400 mt-1">Reserved for Aayush · Shelf A-12</p></div><span className="status-pill status-ready">Ready</span></div><div className="h-px bg-white/8 my-4" /><div className="flex items-center justify-between text-xs"><span className="text-slate-400">Pickup deadline</span><span className="font-medium text-amber-200">Today, 6:00 PM</span></div></div>
      </motion.div>
    </section>
    <section className="relative border-y border-white/8 bg-black/10"><div className="max-w-7xl mx-auto px-5 sm:px-8 py-16"><div className="max-w-2xl"><p className="eyebrow">How it works</p><h2 className="mt-4 text-3xl sm:text-4xl font-bold tracking-tight text-white">Everything needed for a smooth visit.</h2></div><div className="mt-10 grid md:grid-cols-3 gap-4">{steps.map(([number, title, description], index) => <motion.article key={title} initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: 0.35 }} transition={{ delay: index * 0.08 }} className="feature-card"><span className="step-number">{number}</span><h3 className="mt-7 text-lg font-semibold text-white">{title}</h3><p className="mt-2 text-sm leading-6 text-slate-400">{description}</p></motion.article>)}</div></div></section>
    <section className="relative max-w-7xl mx-auto px-5 sm:px-8 py-20"><div className="grid md:grid-cols-2 gap-5"><Audience icon={BookOpen} title="For members" text="Browse the catalog, reserve one available book, see loan dates, renew eligible books, and keep alerts in your settings." action="Explore your library" href="/signup" /><Audience icon={ShieldCheck} title="For staff" text="Manage members and copies, process issues and returns, and start every day with a focused circulation queue." action="Open staff sign in" href="/login" /></div><div className="mt-16 text-center"><p className="text-slate-400">Ready to make library visits easier?</p><Link href="/signup" className="brand-button mt-4 inline-flex px-5 py-3">Get started <ArrowRight size={17} /></Link></div></section>
  </main>;
}

function Metric({ icon: Icon, value, label }: { icon: typeof Clock3; value: string; label: string }) { return <div className="rounded-xl bg-white/5 border border-white/8 p-3"><Icon size={16} className="text-teal-200" /><p className="mt-4 text-xl font-bold text-white">{value}</p><p className="text-[11px] text-slate-400 mt-1">{label}</p></div>; }
function Audience({ icon: Icon, title, text, action, href }: { icon: typeof BookOpen; title: string; text: string; action: string; href: string }) { return <article className="feature-card"><Icon className="text-teal-200" size={22} /><h3 className="mt-5 text-xl font-semibold text-white">{title}</h3><p className="mt-3 text-sm leading-6 text-slate-400">{text}</p><Link href={href} className="mt-6 inline-flex items-center gap-2 text-sm font-medium text-teal-200 hover:text-teal-100">{action} <ArrowRight size={15} /></Link></article>; }
