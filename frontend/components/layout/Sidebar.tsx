"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowLeftRight, BarChart3, BookMarked, BookOpen, ChevronLeft, ChevronRight, CircleDollarSign, ClipboardCheck, LayoutDashboard, Menu, Settings, Users, X, Bookmark, Send } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { cn } from "@/lib/utils";
import { useState } from "react";

const libraryNav = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/dashboard/books", label: "Catalog", icon: BookOpen },
  { href: "/dashboard/transactions", label: "Transactions", icon: ArrowLeftRight },
  { href: "/dashboard/requests", label: "Book requests", icon: Send },
  { href: "/dashboard/analytics", label: "Analytics", icon: BarChart3 },
];
const staffNav = [
  { href: "/dashboard/holds", label: "Holds & pickup", icon: Bookmark },
  { href: "/dashboard/inventory", label: "Inventory audit", icon: ClipboardCheck },
  { href: "/dashboard/fines", label: "Fines", icon: CircleDollarSign },
  { href: "/dashboard/members", label: "Members", icon: Users },
];

function NavLinks({ items, pathname, collapsed, close, member }: { items: typeof libraryNav; pathname: string; collapsed?: boolean; close?: () => void; member: boolean }) {
  return <div className="space-y-1">{items.map(({ href, label, icon: Icon }) => {
    const active = pathname === href || pathname.startsWith(`${href}/`);
    const resolvedLabel = member && href === "/dashboard/transactions" ? "My loans" : member && href === "/dashboard/analytics" ? "My insights" : label;
    return <Link key={href} href={href} onClick={close} title={collapsed ? resolvedLabel : undefined} className={cn("group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-colors", active ? "bg-indigo-600/20 text-indigo-200" : "text-slate-400 hover:bg-white/5 hover:text-white")}><Icon size={18} className="shrink-0" />{!collapsed && <span className="font-medium">{resolvedLabel}</span>}{active && <span className="absolute left-0 h-5 w-0.5 rounded-r-full bg-teal-300" />}</Link>;
  })}</div>;
}

export default function Sidebar() {
  const pathname = usePathname();
  const { user, isAdmin } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const member = !isAdmin;

  return <>
    <motion.aside animate={{ width: collapsed ? 80 : 264 }} transition={{ duration: 0.22, ease: "easeOut" }} className="relative hidden h-screen shrink-0 flex-col border-r border-white/5 bg-[#081619]/95 p-3 md:flex">
      <div className={cn("flex items-center py-2", collapsed ? "justify-center" : "justify-between px-1")}>
        <Link href="/dashboard" className="flex min-w-0 items-center gap-3"><span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-teal-500 to-emerald-700 text-white shadow-lg shadow-emerald-950/30"><BookMarked size={19} /></span>{!collapsed && <span className="min-w-0"><span className="block truncate text-[15px] font-bold tracking-tight text-white">Library Desk</span><span className="block text-[10px] font-semibold uppercase tracking-[0.16em] text-teal-300/70">Workspace</span></span>}</Link>
        {!collapsed && <button onClick={() => setCollapsed(true)} aria-label="Collapse navigation" className="rounded-lg p-2 text-slate-500 transition-colors hover:bg-white/5 hover:text-white"><ChevronLeft size={16} /></button>}
      </div>
      {collapsed && <button onClick={() => setCollapsed(false)} aria-label="Expand navigation" className="mx-auto mt-3 rounded-lg p-2 text-slate-500 transition-colors hover:bg-white/5 hover:text-white"><ChevronRight size={16} /></button>}
      <nav className="mt-8 flex-1 overflow-y-auto"><p className={cn("mb-2 px-3 text-[10px] font-bold tracking-[0.15em] text-slate-600", collapsed && "sr-only")}>LIBRARY</p><NavLinks items={libraryNav} pathname={pathname} collapsed={collapsed} member={member} />{isAdmin && <><p className={cn("mb-2 mt-7 px-3 text-[10px] font-bold tracking-[0.15em] text-slate-600", collapsed && "sr-only")}>MANAGE</p><NavLinks items={staffNav} pathname={pathname} collapsed={collapsed} member={member} /></>}</nav>
      {user && <Link href="/dashboard/profile" title={collapsed ? "Account & settings" : undefined} className={cn("group flex items-center gap-3 rounded-xl border border-white/5 bg-white/[0.025] p-2.5 transition-colors hover:border-teal-300/20 hover:bg-white/[0.06]", collapsed && "justify-center p-2")}><span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-teal-500/15 text-sm font-bold text-teal-200">{user.name[0].toUpperCase()}</span>{!collapsed && <span className="min-w-0"><span className="block truncate text-sm font-medium text-white">{user.name}</span><span className="block truncate text-xs capitalize text-slate-500">{isAdmin ? "Administrator" : "Member"}</span></span>}{!collapsed && <Settings size={16} className="ml-auto shrink-0 text-slate-500 group-hover:text-teal-200" />}</Link>}
    </motion.aside>

    <header className="fixed inset-x-0 top-0 z-40 flex h-16 items-center justify-between border-b border-white/10 bg-[#081619]/90 px-4 backdrop-blur-xl md:hidden"><Link href="/dashboard" className="flex items-center gap-2.5 text-sm font-semibold text-white"><span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-teal-500 to-emerald-700"><BookMarked size={16} /></span> Library Desk</Link><button onClick={() => setMobileOpen(true)} aria-label="Open navigation" className="rounded-xl border border-white/10 bg-white/5 p-2 text-slate-200"><Menu size={20} /></button></header>
    {mobileOpen && <div className="fixed inset-0 z-50 bg-[#02090b]/70 backdrop-blur-sm md:hidden" onClick={() => setMobileOpen(false)}><motion.aside initial={{ x: -300 }} animate={{ x: 0 }} exit={{ x: -300 }} transition={{ type: "spring", damping: 26, stiffness: 280 }} onClick={event => event.stopPropagation()} className="flex h-full w-[min(86vw,20rem)] flex-col border-r border-white/10 bg-[#081619] p-4 shadow-2xl"><div className="flex items-center justify-between"><Link href="/dashboard" onClick={() => setMobileOpen(false)} className="flex items-center gap-2.5 text-sm font-semibold text-white"><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-teal-500 to-emerald-700"><BookMarked size={17} /></span> Library Desk</Link><button onClick={() => setMobileOpen(false)} aria-label="Close navigation" className="rounded-lg p-2 text-slate-400 hover:bg-white/5 hover:text-white"><X size={19} /></button></div><nav className="mt-8 flex-1"><p className="mb-2 px-3 text-[10px] font-bold tracking-[0.15em] text-slate-600">LIBRARY</p><NavLinks items={libraryNav} pathname={pathname} close={() => setMobileOpen(false)} member={member} />{isAdmin && <><p className="mb-2 mt-7 px-3 text-[10px] font-bold tracking-[0.15em] text-slate-600">MANAGE</p><NavLinks items={staffNav} pathname={pathname} close={() => setMobileOpen(false)} member={member} /></>}</nav>{user && <Link href="/dashboard/profile" onClick={() => setMobileOpen(false)} className="flex items-center gap-3 rounded-xl border border-white/5 bg-white/[0.025] p-3"><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-teal-500/15 text-sm font-bold text-teal-200">{user.name[0].toUpperCase()}</span><span><span className="block text-sm font-medium text-white">{user.name}</span><span className="block text-xs text-slate-500">Account & settings</span></span><Settings size={16} className="ml-auto text-slate-500" /></Link>}</motion.aside></div>}
  </>;
}
