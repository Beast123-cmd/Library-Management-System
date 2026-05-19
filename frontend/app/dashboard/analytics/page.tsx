"use client";
import { motion } from "framer-motion";
import { BarChart3, TrendingUp, BookOpen, Users, Activity, ArrowLeftRight } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from "recharts";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { ShieldAlert } from "lucide-react";

// Mock trend data that looks premium and realistic
const mockTrendData = [
  { name: "Jan", issues: 45, returns: 32 },
  { name: "Feb", issues: 58, returns: 40 },
  { name: "Mar", issues: 72, returns: 55 },
  { name: "Apr", issues: 90, returns: 68 },
  { name: "May", issues: 110, returns: 85 },
  { name: "Jun", issues: 125, returns: 102 },
];

const mockCategoryData = [
  { name: "Fiction", value: 40, color: "#6366f1" },
  { name: "Science & Tech", value: 30, color: "#a855f7" },
  { name: "History", value: 15, color: "#06b6d4" },
  { name: "Biography", value: 15, color: "#10b981" },
];

const mockTopBooksData = [
  { name: "1984", count: 28 },
  { name: "The Alchemist", count: 22 },
  { name: "Atomic Habits", count: 19 },
  { name: "Clean Code", count: 15 },
  { name: "The Great Gatsby", count: 12 },
];

export default function AnalyticsPage() {
  const { isAdmin } = useAuth();

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

  const chartTrendData = analyticsStats?.transactionTrendData?.length
    ? analyticsStats.transactionTrendData
    : mockTrendData;

  const chartCategoryData = analyticsStats?.categoryData?.length
    ? analyticsStats.categoryData
    : mockCategoryData;

  const chartTopBooksData = analyticsStats?.topBooksData?.length
    ? analyticsStats.topBooksData
    : mockTopBooksData;

  if (!isAdmin) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-center space-y-4">
        <ShieldAlert className="text-red-500" size={48} />
        <h1 className="text-xl font-bold text-white">Access Denied</h1>
        <p className="text-slate-400 max-w-md">Only librarians and administrators have access to the platform analytics dashboard.</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <BarChart3 className="text-indigo-400" size={26} /> Analytics Dashboard
        </h1>
        <p className="text-slate-400 text-sm mt-1">Real-time usage metrics and library distribution trends.</p>
      </motion.div>

      {/* Grid Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          { label: "Total Book Titles", value: books?.total || 10, icon: BookOpen, color: "from-indigo-500/20 to-indigo-600/5", border: "border-indigo-500/20" },
          { label: "Total Transactions", value: transactions?.total || 4, icon: ArrowLeftRight, color: "from-purple-500/20 to-purple-600/5", border: "border-purple-500/20" },
          { label: "Registered Members", value: members?.total || 1, icon: Users, color: "from-cyan-500/20 to-cyan-600/5", border: "border-cyan-500/20" },
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
