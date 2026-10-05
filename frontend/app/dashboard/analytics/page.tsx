"use client";
import { motion } from "framer-motion";
import { BarChart3, TrendingUp, BookOpen, Users, Activity, ArrowLeftRight, Download, AlertTriangle, CircleDollarSign, PackageCheck } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from "recharts";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export default function AnalyticsPage() {
  const { isAdmin } = useAuth();

  const downloadReport = async (path: string, filename: string) => {
    try {
      const response = await api.get(path, { responseType: "blob" });
      const url = URL.createObjectURL(response.data);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      link.click();
      URL.revokeObjectURL(url);
    } catch {
      window.alert("The report could not be downloaded. Please try again.");
    }
  };

  const exportReport = () => downloadReport("/analytics/export", "library-analytics-report.csv");

  // Queries to show actual counts on stats cards
  const { data: books } = useQuery({
    queryKey: ["books-count"],
    queryFn: () => api.get("/books/?per_page=1").then(r => r.data),
    enabled: isAdmin,
  });

  const { data: transactions } = useQuery({
    queryKey: ["txn-count"],
    queryFn: () => api.get("/transactions/?per_page=1").then(r => r.data),
    enabled: isAdmin,
  });

  const { data: members } = useQuery({
    queryKey: ["members-count"],
    queryFn: () => api.get("/users/?per_page=1").then(r => r.data),
    enabled: isAdmin,
  });

  const { data: analyticsStats } = useQuery({
    queryKey: ["analytics-stats"],
    queryFn: () => api.get("/analytics/stats").then(r => r.data),
    enabled: isAdmin,
  });

  const chartTrendData = analyticsStats?.transactionTrendData || [];
  const chartCategoryData = analyticsStats?.categoryData || [];
  const chartTopBooksData = analyticsStats?.topBooksData || [];

  if (!isAdmin) {
    return <MemberAnalytics />;
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div><h1 className="text-2xl font-bold text-white flex items-center gap-2"><BarChart3 className="text-indigo-400" size={26} /> Analytics Dashboard</h1><p className="text-slate-400 text-sm mt-1">Circulation, catalogue composition, and member activity in one operational view.</p></div>
        <button type="button" onClick={exportReport} className="inline-flex w-fit items-center gap-2 rounded-xl border border-teal-400/25 bg-teal-500/10 px-4 py-2.5 text-sm font-semibold text-teal-200 transition-colors hover:bg-teal-500/20"><Download size={16} /> Download CSV report</button>
      </motion.div>

      {/* Grid Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          { label: "Total Book Titles", value: books?.total ?? "—", icon: BookOpen, color: "from-indigo-500/20 to-indigo-600/5", border: "border-indigo-500/20" },
          { label: "Total Transactions", value: transactions?.total ?? "—", icon: ArrowLeftRight, color: "from-purple-500/20 to-purple-600/5", border: "border-purple-500/20" },
          { label: "Registered Members", value: members?.total ?? "—", icon: Users, color: "from-cyan-500/20 to-cyan-600/5", border: "border-cyan-500/20" },
        ].map((item, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
            className={`glass border ${item.border} p-6 flex items-center justify-between bg-gradient-to-br ${item.color}`}
          >
            <div>
              <p className="text-slate-400 text-sm font-medium">{item.label}</p>
              <h3 className="text-white text-3xl font-extrabold mt-1">{item.value}</h3>
            </div>
            <div className="p-3 bg-white/5 rounded-2xl text-white">
              <item.icon size={24} />
            </div>
          </motion.div>
        ))}
      </div>

      <section className="glass p-5 sm:p-6">
        <div className="mb-5"><h2 className="text-base font-semibold text-white">Operational reports</h2><p className="mt-1 text-sm text-slate-400">Download the lists staff need for follow-up, payment collection, and shelf checks.</p></div>
        <div className="grid gap-3 md:grid-cols-3">
          {[
            { label: "Overdue loans", detail: "Members and expected fines", icon: AlertTriangle, path: "/analytics/export/overdue", file: "library-overdue-report.csv", tone: "text-amber-300" },
            { label: "Fine ledger", detail: "Assessed, paid, and outstanding", icon: CircleDollarSign, path: "/analytics/export/fines", file: "library-fines-report.csv", tone: "text-rose-300" },
            { label: "Inventory availability", detail: "Copies and shelf locations", icon: PackageCheck, path: "/analytics/export/inventory", file: "library-inventory-report.csv", tone: "text-teal-300" },
          ].map(({ label, detail, icon: Icon, path, file, tone }) => (
            <button key={label} type="button" onClick={() => downloadReport(path, file)} className="group flex items-center gap-3 rounded-xl border border-white/8 bg-white/[0.025] p-4 text-left transition-colors hover:border-teal-300/25 hover:bg-white/[0.06]">
              <span className={`rounded-xl bg-white/5 p-2.5 ${tone}`}><Icon size={18} /></span><span className="min-w-0 flex-1"><span className="block font-semibold text-white">{label}</span><span className="mt-0.5 block text-xs text-slate-400">{detail}</span></span><Download size={16} className="text-slate-500 transition-colors group-hover:text-teal-200" />
            </button>
          ))}
        </div>
      </section>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Transaction Flow (Area Chart) */}
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          className="glass p-6 space-y-4"
        >
          <div className="flex items-center gap-2">
            <TrendingUp size={18} className="text-indigo-400" />
            <h2 className="text-white font-semibold">Transaction Activity Flow</h2>
          </div>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartTrendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorIssues" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorReturns" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#a855f7" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#a855f7" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} tickLine={false} />
                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} />
                <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "12px", color: "#fff" }} />
                <Area type="monotone" dataKey="issues" stroke="#6366f1" strokeWidth={2} fillOpacity={1} fill="url(#colorIssues)" name="Issues" />
                <Area type="monotone" dataKey="returns" stroke="#a855f7" strokeWidth={2} fillOpacity={1} fill="url(#colorReturns)" name="Returns" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Book Categories (Pie Chart) */}
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="glass p-6 space-y-4"
        >
          <div className="flex items-center gap-2">
            <Activity size={18} className="text-purple-400" />
            <h2 className="text-white font-semibold">Book Genre Distribution</h2>
          </div>
          <div className="h-72 flex flex-col sm:flex-row items-center justify-around">
            <div className="w-48 h-48">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={chartCategoryData} cx="50%" cy="50%" innerRadius={55} outerRadius={75} paddingAngle={4} dataKey="value">
                    {chartCategoryData.map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "12px" }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="space-y-2 mt-4 sm:mt-0">
              {chartCategoryData.map((c: any, idx: number) => (
                <div key={idx} className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full" style={{ backgroundColor: c.color }} />
                  <span className="text-slate-300 text-xs font-medium">{c.name} ({c.value}%)</span>
                </div>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Top Circulated Books (Bar Chart) */}
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="glass p-6 space-y-4 lg:col-span-2"
        >
          <div className="flex items-center gap-2">
            <BookOpen size={18} className="text-cyan-400" />
            <h2 className="text-white font-semibold">Top Circulated Books</h2>
          </div>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartTopBooksData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} tickLine={false} />
                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} />
                <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "12px" }} />
                <Bar dataKey="count" fill="url(#colorIssues)" radius={[8, 8, 0, 0]} name="Issues">
                  {chartTopBooksData.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={index % 2 === 0 ? "#6366f1" : "#06b6d4"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

function MemberAnalytics() {
  const { data: transactions, isLoading } = useQuery({
    queryKey: ["member-reading-insights"],
    queryFn: () => api.get("/transactions/?page=1&per_page=100").then(response => response.data),
  });
  const loans = transactions?.data || [];
  const active = loans.filter((loan: any) => loan.status === "issued" || loan.status === "overdue");
  const returned = loans.filter((loan: any) => loan.status === "returned");
  const totalFines = loans.reduce((total: number, loan: any) => total + Number(loan.fine_amount || 0), 0);
  const categoryCounts = loans.reduce((counts: Record<string, number>, loan: any) => {
    const category = loan.book?.category || "Other";
    counts[category] = (counts[category] || 0) + 1;
    return counts;
  }, {});
  const chartData = Object.entries(categoryCounts).map(([name, count]) => ({ name, count }));

  return <div className="space-y-8"><header><h1 className="flex items-center gap-2 text-2xl font-bold text-white"><BarChart3 className="text-indigo-400" size={26} /> My reading insights</h1><p className="mt-1 text-sm text-slate-400">Your loans, reading history, and borrowing patterns.</p></header><div className="grid gap-4 sm:grid-cols-3"><Insight label="Books borrowed" value={isLoading ? "—" : loans.length} icon={BookOpen} tone="text-indigo-200" /><Insight label="Active loans" value={isLoading ? "—" : active.length} icon={ArrowLeftRight} tone="text-amber-300" /><Insight label="Fines recorded" value={isLoading ? "—" : `₹${totalFines.toFixed(2)}`} icon={Activity} tone="text-rose-300" /></div><section className="glass p-5 sm:p-6"><div className="mb-5"><h2 className="font-semibold text-white">Your reading categories</h2><p className="mt-1 text-sm text-slate-400">Based on books you have borrowed.</p></div>{chartData.length ? <div className="h-64"><ResponsiveContainer width="100%" height="100%"><BarChart data={chartData}><CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" /><XAxis dataKey="name" stroke="#94a3b8" fontSize={11} tickLine={false} /><YAxis allowDecimals={false} stroke="#94a3b8" fontSize={11} tickLine={false} /><Tooltip contentStyle={{ background: "#1e293b", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "12px" }} /><Bar dataKey="count" fill="#6366f1" radius={[8, 8, 0, 0]} name="Books" /></BarChart></ResponsiveContainer></div> : <p className="py-12 text-center text-sm text-slate-400">Borrow a book to start seeing your reading insights.</p>}</section><section className="glass p-5 sm:p-6"><div className="mb-4 flex items-center justify-between"><h2 className="font-semibold text-white">Reading activity</h2><span className="text-sm text-slate-400">{returned.length} returned</span></div><div className="divide-y divide-white/5">{active.length ? active.map((loan: any) => <div key={loan.id} className="flex items-center justify-between py-3 first:pt-0"><div><p className="text-sm font-medium text-white">{loan.book?.title || "Library book"}</p><p className="mt-1 text-xs text-slate-400">Due {loan.expected_return_date}</p></div><span className="rounded-full bg-amber-500/15 px-2.5 py-1 text-xs font-semibold text-amber-300">On loan</span></div>) : <p className="py-5 text-sm text-slate-400">No books are currently on loan.</p>}</div></section></div>;
}

function Insight({ label, value, icon: Icon, tone }: { label: string; value: string | number; icon: typeof BookOpen; tone: string }) {
  return <div className="glass flex items-center justify-between p-5"><div><p className="text-sm text-slate-400">{label}</p><p className={`mt-2 text-2xl font-bold ${tone}`}>{value}</p></div><Icon className="text-slate-500" size={22} /></div>;
}
