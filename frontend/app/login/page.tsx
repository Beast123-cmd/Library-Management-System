"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowLeft, BookOpen, Eye, EyeOff, Lock, Loader2, ShieldCheck, UserRound } from "lucide-react";
import toast from "react-hot-toast";
import { useAuth } from "@/context/AuthContext";

function Field({ label, icon: Icon, children }: { label: string; icon: typeof Lock; children: React.ReactNode }) {
  return <label className="block"><span className="mb-2 block text-sm font-medium text-slate-200">{label}</span><span className="relative block"><Icon className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" size={17} />{children}</span></label>;
}

export default function LoginPage() {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!username || !password) return toast.error("Enter your username and password.");
    setLoading(true);
    try { await login(username, password); toast.success("Welcome back."); }
    catch (error: any) { toast.error(error?.response?.data?.detail || "Those details did not match an account."); }
    finally { setLoading(false); }
  };

  return <main className="auth-shell min-h-screen">
    <Link href="/" className="auth-back"><ArrowLeft size={16} /> Back to home</Link>
    <div className="auth-grid">
      <section className="auth-intro"><Link href="/" className="flex items-center gap-2.5 text-white font-semibold"><span className="brand-mark"><BookOpen size={19} /></span> Library Desk</Link><div className="mt-auto mb-auto"><p className="eyebrow">Your library, organized</p><h1 className="mt-5 text-4xl sm:text-5xl font-bold tracking-[-0.04em] leading-tight text-white">Welcome back to your reading space.</h1><p className="mt-5 max-w-md text-slate-300 leading-7">Pick up where you left off: manage your loans, find your next book, and keep every visit on track.</p><div className="mt-8 space-y-3 text-sm text-slate-300"><p className="flex items-center gap-3"><ShieldCheck size={17} className="text-teal-200" /> Your account and circulation data stay protected.</p><p className="flex items-center gap-3"><BookOpen size={17} className="text-teal-200" /> Every loan is tied to an individual library copy.</p></div></div></section>
      <motion.section initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} className="auth-card"><div><p className="text-sm font-medium text-teal-200">Sign in</p><h2 className="mt-2 text-3xl font-bold tracking-tight text-white">Good to see you.</h2><p className="mt-2 text-sm text-slate-400">Use the username and password from your library account.</p></div><form onSubmit={submit} className="mt-8 space-y-5"><Field label="Username" icon={UserRound}><input value={username} onChange={e => setUsername(e.target.value)} autoComplete="username" placeholder="Your username" className="input-control" /></Field><Field label="Password" icon={Lock}><input type={showPassword ? "text" : "password"} value={password} onChange={e => setPassword(e.target.value)} autoComplete="current-password" placeholder="Your password" className="input-control pr-12" /><button type="button" aria-label={showPassword ? "Hide password" : "Show password"} onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-teal-200">{showPassword ? <EyeOff size={18} /> : <Eye size={18} />}</button></Field><button disabled={loading} className="brand-button w-full justify-center py-3.5 disabled:opacity-60">{loading && <Loader2 size={17} className="animate-spin" />}{loading ? "Signing in…" : "Sign in"}</button></form><p className="mt-7 text-sm text-slate-400">New to the library? <Link href="/signup" className="font-medium text-teal-200 hover:text-teal-100">Create an account</Link></p></motion.section>
    </div>
  </main>;
}
