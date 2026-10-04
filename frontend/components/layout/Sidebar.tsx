"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  LayoutDashboard, BookOpen, ArrowLeftRight,
  Users, BarChart3, LogOut, BookMarked, ChevronLeft, ChevronRight, Sun, Moon, Bookmark, Settings, Menu, X
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";
import { cn } from "@/lib/utils";
import { useState } from "react";

const navItems = [
  { href: "/dashboard",              label: "Dashboard",     icon: LayoutDashboard },
  { href: "/dashboard/books",        label: "Books",         icon: BookOpen },
  { href: "/dashboard/transactions", label: "Transactions",  icon: ArrowLeftRight },
  { href: "/dashboard/holds",        label: "Holds & Pull List", icon: Bookmark, adminOnly: true },
  { href: "/dashboard/members",      label: "Members",       icon: Users, adminOnly: true },
  { href: "/dashboard/analytics",    label: "Analytics",     icon: BarChart3, adminOnly: true },
  { href: "/dashboard/profile",      label: "Account & Settings", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout, isAdmin } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const items = navItems.filter(i => !i.adminOnly || isAdmin);

  return (
    <>
    <motion.aside
      animate={{ width: collapsed ? 72 : 240 }}
      transition={{ duration: 0.3, ease: "easeInOut" }}
      className="relative hidden md:flex flex-col h-screen shrink-0 overflow-hidden"
      style={{ background: "var(--sidebar-bg)", borderRight: "1px solid var(--border)" }}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-6 border-b border-white/5">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shrink-0 shadow-lg shadow-emerald-950/30">
          <BookMarked size={18} className="text-white" />
        </div>
        {!collapsed && (
          <motion.span
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
            className="font-bold text-white text-sm tracking-wide"
          >
            Library Desk
          </motion.span>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 px-2 space-y-1">
        {items.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link key={href} href={href}>
              <motion.div
                whileHover={{ x: 4 }}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all cursor-pointer",
                  active
                    ? "bg-indigo-600/20 text-indigo-400 border border-indigo-500/20"
                    : "text-slate-400 hover:text-white hover:bg-white/5"
                )}
              >
                <Icon size={18} className="shrink-0" />
                {!collapsed && (
                  <motion.span
                    initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
                    className="text-sm font-medium"
                  >
                    {!isAdmin && href === "/dashboard/transactions" ? "My Loans" : label}
                  </motion.span>
                )}
              </motion.div>
            </Link>
          );
        })}
      </nav>

      {/* User + Toggle + Logout */}
      <div className="border-t border-white/5 p-3">
        {!collapsed && user && (
          <div className="flex items-center gap-3 px-2 py-2 mb-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white text-xs font-bold shrink-0">
              {user.name[0].toUpperCase()}
            </div>
            <div className="overflow-hidden">
              <p className="text-white text-xs font-semibold truncate">{user.name}</p>
              <p className="text-slate-500 text-xs capitalize">{user.role}</p>
            </div>
          </div>
        )}
        
        <button
          onClick={toggleTheme}
          className={cn(
            "flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-slate-400 hover:text-indigo-400 hover:bg-indigo-500/10 transition-all mb-1.5",
          )}
        >
          {theme === "dark" ? (
            <Sun size={18} className="shrink-0 text-amber-400" />
          ) : (
            <Moon size={18} className="shrink-0 text-indigo-500" />
          )}
          {!collapsed && (
            <span className="text-sm font-medium">
              {theme === "dark" ? "Light Mode" : "Dark Mode"}
            </span>
          )}
        </button>

        <button
          onClick={logout}
          className={cn(
            "flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-all",
          )}
        >
          <LogOut size={18} className="shrink-0" />
          {!collapsed && <span className="text-sm font-medium">Logout</span>}
        </button>
      </div>

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="absolute -right-3 top-8 w-6 h-6 rounded-full bg-indigo-600 border border-white/10 flex items-center justify-center text-white hover:bg-indigo-500 transition-colors z-10"
      >
        {collapsed ? <ChevronRight size={12} /> : <ChevronLeft size={12} />}
      </button>
    </motion.aside>

    <div className="md:hidden fixed inset-x-0 top-0 z-40 flex h-16 items-center justify-between border-b border-white/10 bg-[var(--sidebar-bg)]/95 px-4 backdrop-blur-xl">
      <Link href="/dashboard" className="flex items-center gap-2 text-sm font-semibold text-white"><span className="brand-mark"><BookMarked size={17} /></span> Library Desk</Link>
      <button onClick={() => setMobileOpen(true)} aria-label="Open navigation" className="rounded-xl border border-white/10 bg-white/5 p-2 text-slate-200"><Menu size={20} /></button>
    </div>
    {mobileOpen && <div className="md:hidden fixed inset-0 z-50 bg-[#061014]/80 backdrop-blur-sm" onClick={() => setMobileOpen(false)}>
      <motion.aside initial={{ x: -280 }} animate={{ x: 0 }} exit={{ x: -280 }} transition={{ type: "spring", damping: 25, stiffness: 260 }} onClick={event => event.stopPropagation()} className="flex h-full w-[min(85vw,19rem)] flex-col border-r border-white/10 bg-[var(--sidebar-bg)] p-3 shadow-2xl">
        <div className="flex items-center justify-between px-2 py-2"><span className="flex items-center gap-2 text-sm font-semibold text-white"><span className="brand-mark"><BookMarked size={17} /></span> Library Desk</span><button onClick={() => setMobileOpen(false)} aria-label="Close navigation" className="rounded-lg p-2 text-slate-400 hover:bg-white/5 hover:text-white"><X size={19} /></button></div>
        <nav className="mt-5 flex-1 space-y-1">{items.map(({ href, label, icon: Icon }) => { const active = pathname === href || pathname.startsWith(href + "/"); return <Link key={href} href={href} onClick={() => setMobileOpen(false)} className={cn("flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium", active ? "bg-indigo-600/20 text-indigo-300 border border-indigo-500/20" : "text-slate-400 hover:bg-white/5 hover:text-white")}><Icon size={18} />{!isAdmin && href === "/dashboard/transactions" ? "My Loans" : label}</Link>; })}</nav>
        {user && <div className="border-t border-white/10 pt-3"><div className="flex items-center gap-3 px-2 pb-3"><div className="w-9 h-9 rounded-full bg-indigo-500/15 text-indigo-300 flex items-center justify-center font-bold">{user.name[0].toUpperCase()}</div><div><p className="text-sm font-medium text-white">{user.name}</p><p className="text-xs capitalize text-slate-500">{user.role}</p></div></div><button onClick={toggleTheme} className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-slate-400 hover:bg-white/5">{theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}{theme === "dark" ? "Use light mode" : "Use dark mode"}</button><button onClick={logout} className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-slate-400 hover:bg-red-500/10 hover:text-red-300"><LogOut size={18} />Sign out</button></div>}
      </motion.aside>
    </div>}
    </>
  );
}
