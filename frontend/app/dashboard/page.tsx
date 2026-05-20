"use client";
import { motion } from "framer-motion";
import { BookOpen, Users, ArrowLeftRight, AlertCircle, DollarSign, AlertTriangle, Clock, TrendingUp, Bookmark } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import TransactionsPage from "./transactions/page";

const cardVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number) => ({ opacity: 1, y: 0, transition: { delay: i * 0.1, duration: 0.5 } }),
};

function StatCard({ icon: Icon, label, value, color, index }: any) {
  return (
    <motion.div
      custom={index} variants={cardVariants} initial="hidden" animate="visible"
      whileHover={{ scale: 1.02, translateY: -2 }}
      className="glass p-6 flex items-center gap-4 cursor-default"
    >
      <div className={`w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 ${color}`}>
        <Icon size={22} className="text-white" />
      </div>
      <div>
        <p className="text-slate-400 text-sm">{label}</p>
        <p className="text-white text-2xl font-bold mt-0.5">
          {value ?? <span className="text-slate-600 animate-pulse">—</span>}
        </p>
      </div>
    </motion.div>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  const { data: stats, isLoading } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: () => api.get("/dashboard/stats").then(r => r.data),
    enabled: isAdmin,
  });

  if (user && !isAdmin) {
    return <TransactionsPage />;
  }

  const kpis = stats?.kpis;

  const statCards = [
    { icon: BookOpen,        label: "Total Books",       value: kpis?.total_books,        color: "bg-indigo-600" },
    { icon: Users,           label: "Total Members",     value: kpis?.total_members,      color: "bg-cyan-600" },
    { icon: ArrowLeftRight,  label: "Active Loans",      value: kpis?.active_loans,      color: "bg-purple-600" },
    { icon: DollarSign,      label: "Total Fines",       value: kpis?.total_fines !== undefined ? `₹${kpis.total_fines.toFixed(2)}` : undefined, color: "bg-emerald-600" },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-bold text-white">
          Good {new Date().getHours() < 12 ? "morning" : "afternoon"},{" "}
          <span className="gradient-text">{user?.name?.split(" ")[0]} 👋</span>
        </h1>
        <p className="text-slate-400 mt-1">Here&apos;s what&apos;s happening in your library today.</p>
      </motion.div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {statCards.map((s, i) => <StatCard key={s.label} {...s} index={i} />)}
      </div>

      {/* Low Stock Warning Banner for Admin */}
      {isAdmin && stats?.low_stock_books?.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }}
          className="border border-amber-500/20 bg-amber-500/10 rounded-2xl p-4 flex gap-3 items-start"
        >
          <AlertTriangle className="text-amber-400 shrink-0 mt-0.5" size={20} />
          <div>
            <h3 className="text-amber-400 font-semibold text-sm">Low Stock Alerts</h3>
            <p className="text-slate-300 text-xs mt-1">
              The following books are running low on available copies. Consider ordering more copies or checking return schedules:
            </p>
            <div className="flex flex-wrap gap-2 mt-3">
              {stats.low_stock_books.map((b: any) => (
                <div key={b.id} className="bg-black/40 text-xs px-2.5 py-1 rounded-lg border border-amber-500/10 text-amber-200">
                  <span className="font-semibold">{b.title}</span> ({b.available_copies}/{b.total_copies} left)
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      )}

      {/* Split section: Activity Feed & Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Activity Feed */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
          className="glass p-6 lg:col-span-2 space-y-4"
        >
          <h2 className="text-white font-semibold flex items-center gap-2">
            <Clock size={18} className="text-indigo-400" />
            Recent Activity Feed
          </h2>
          <div className="space-y-3 overflow-y-auto max-h-[350px] pr-2">
            {isLoading ? (
              Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-14 bg-white/5 rounded-xl animate-pulse" />
              ))
            ) : !stats?.recent_activity || stats.recent_activity.length === 0 ? (
              <p className="text-slate-500 text-sm py-8 text-center">No recent library transactions found.</p>
            ) : (
              stats.recent_activity.map((act: any) => (
                <div key={act.id} className="flex justify-between items-center bg-white/3 hover:bg-white/5 transition-colors p-3.5 rounded-xl border border-white/5">
                  <div>
                    <p className="text-white text-sm font-medium">
                      <span className="text-slate-300">{act.user_name}</span>{" "}
                      <span className={act.action === "issued" ? "text-amber-400" : "text-emerald-400"}>
                        {act.action === "issued" ? "borrowed" : "returned"}
                      </span>{" "}
                      <span className="text-indigo-300 font-semibold">{act.book_title}</span>
                    </p>
                    <p className="text-slate-500 text-xs mt-1">Transaction ID: #{act.id}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-slate-400 text-xs">{new Date(act.date).toLocaleDateString()}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </motion.div>

        {/* Quick Actions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
          className="glass p-6 flex flex-col justify-between"
        >
          <div>
            <h2 className="text-white font-semibold mb-4 flex items-center gap-2">
              <AlertCircle size={18} className="text-indigo-400" />
              Quick Operations
            </h2>
            <p className="text-slate-400 text-xs mb-6">
              Use these shortcuts to navigate directly to management screens or view key metrics.
            </p>
          </div>
          <div className="grid grid-cols-1 gap-3">
            {[
              { label: "Browse Catalog",   href: "/dashboard/books",        color: "from-indigo-600/80 to-indigo-700/80 hover:from-indigo-600 hover:to-indigo-700" },
              { label: "Book Loans & Returns", href: "/dashboard/transactions",  color: "from-purple-600/80 to-purple-700/80 hover:from-purple-600 hover:to-purple-700" },
              { label: "Member Directory",   href: "/dashboard/members",       color: "from-cyan-600/80 to-cyan-700/80 hover:from-cyan-600 hover:to-cyan-700" },
              { label: "Analytics & Trends",      href: "/dashboard/analytics",     color: "from-emerald-600/80 to-emerald-700/80 hover:from-emerald-600 hover:to-emerald-700" },
            ].map(({ label, href, color }) => (
              <a key={label} href={href}
                className={`bg-gradient-to-r ${color} rounded-xl py-3.5 px-4 text-white text-sm font-semibold text-center shadow-lg transition-all transform hover:-translate-y-0.5`}>
                {label}
              </a>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Analytics Widgets (Admin Only) */}
      {isAdmin && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Member Activity Rankings */}
          <motion.div
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }}
            className="glass p-6 space-y-4"
          >
            <h2 className="text-white font-semibold flex items-center gap-2">
              <TrendingUp size={18} className="text-indigo-400" />
              Most Active Readers (Member Activity)
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-white/5 text-slate-400 text-xs font-semibold uppercase tracking-wider">
                    <th className="pb-3">Member</th>
                    <th className="pb-3">Username</th>
                    <th className="pb-3 text-right">Transactions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {!stats?.member_rankings || stats.member_rankings.length === 0 ? (
                    <tr>
                      <td colSpan={3} className="py-8 text-center text-slate-500 text-sm">
                        No activity rankings available yet.
                      </td>
                    </tr>
                  ) : (
                    stats.member_rankings.map((member: any, idx: number) => (
                      <tr key={member.username} className="hover:bg-white/3 transition-colors">
                        <td className="py-3.5 flex items-center gap-2.5">
                          <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${
                            idx === 0 ? "bg-amber-500/20 text-amber-400" :
                            idx === 1 ? "bg-slate-400/20 text-slate-300" :
                            idx === 2 ? "bg-amber-700/20 text-amber-600" :
                            "bg-white/5 text-slate-400"
                          }`}>
                            {idx + 1}
                          </span>
                          <span className="text-white text-sm font-medium">{member.name}</span>
                        </td>
                        <td className="py-3.5 text-slate-400 text-sm">@{member.username}</td>
                        <td className="py-3.5 text-indigo-400 font-bold text-sm text-right">{member.count} borrow actions</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </motion.div>

          {/* Current Books Issued to Members */}
          <motion.div
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}
            className="glass p-6 space-y-4"
          >
            <h2 className="text-white font-semibold flex items-center gap-2">
              <Bookmark size={18} className="text-indigo-400" />
              Top Book Holders (Current Active Loans)
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-white/5 text-slate-400 text-xs font-semibold uppercase tracking-wider">
                    <th className="pb-3">Member</th>
                    <th className="pb-3">Username</th>
                    <th className="pb-3 text-right">Holding</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {!stats?.active_loans_by_member || stats.active_loans_by_member.length === 0 ? (
                    <tr>
                      <td colSpan={3} className="py-8 text-center text-slate-500 text-sm">
                        No active loans currently held by members.
                      </td>
                    </tr>
                  ) : (
                    stats.active_loans_by_member.map((member: any, idx: number) => (
                      <tr key={member.username} className="hover:bg-white/3 transition-colors">
                        <td className="py-3.5 flex items-center gap-2.5">
                          <span className="w-5 h-5 rounded-full flex items-center justify-center text-xs font-semibold bg-white/5 text-slate-400">
                            {idx + 1}
                          </span>
                          <span className="text-white text-sm font-medium">{member.name}</span>
                        </td>
                        <td className="py-3.5 text-slate-400 text-sm">@{member.username}</td>
                        <td className="py-3.5 text-emerald-400 font-bold text-sm text-right">{member.count} books checked out</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
