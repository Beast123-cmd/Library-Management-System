"use client";
import { useState } from "react";
import { motion } from "framer-motion";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { Users, Search, Shield, ShieldAlert, CheckCircle, XCircle, ChevronLeft, ChevronRight, Plus, Edit, Trash2, Loader2 } from "lucide-react";
import api from "@/lib/api";
import toast from "react-hot-toast";
import { useAuth } from "@/context/AuthContext";

export default function MembersPage() {
  const { isAdmin } = useAuth();
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [page, setPage] = useState(1);
  const PER_PAGE = 15;

  // Add / Edit form states
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [addForm, setAddForm] = useState({ name: "", email: "", username: "", password: "" });

  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editForm, setEditForm] = useState({ id: 0, name: "", email: "", username: "", password: "" });

  // Debounce search
  const handleSearch = (val: string) => {
    setSearch(val);
    clearTimeout((window as any)._membersSearchTimer);
    (window as any)._membersSearchTimer = setTimeout(() => {
      setDebouncedSearch(val);
      setPage(1);
    }, 200);
  };

  const { data, isLoading, isFetching, refetch } = useQuery({
    queryKey: ["members", debouncedSearch, page],
    queryFn: () => api.get(`/users/?page=${page}&per_page=${PER_PAGE}&search=${debouncedSearch}`).then(r => r.data),
    enabled: isAdmin, // Only admins can fetch members list
    placeholderData: keepPreviousData,
  });

  const handleToggleActive = async (userId: number, currentStatus: boolean, name: string) => {
    const action = currentStatus ? "deactivate" : "activate";
    if (!confirm(`Are you sure you want to ${action} ${name}'s account?`)) return;
    try {
      await api.patch(`/users/${userId}/toggle-active`);
      toast.success(`Account ${currentStatus ? "deactivated" : "activated"} successfully!`);
      refetch();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Action failed.");
    }
  };

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post("/users/", addForm);
      toast.success("Member account created successfully!");
      setIsAddModalOpen(false);
      setAddForm({ name: "", email: "", username: "", password: "" });
      refetch();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Failed to create member.");
    }
  };

  const handleEditMember = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload: any = {
        name: editForm.name,
        email: editForm.email,
        username: editForm.username,
      };
      if (editForm.password) {
        payload.password = editForm.password;
      }
      await api.put(`/users/${editForm.id}`, payload);
      toast.success("Member profile updated successfully!");
      setIsEditModalOpen(false);
      refetch();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Failed to update member.");
    }
  };

  const handleDeleteMember = async (userId: number, name: string) => {
    if (!confirm(`Are you sure you want to permanently delete member "${name}"?`)) return;
    try {
      await api.delete(`/users/${userId}`);
      toast.success(`Member "${name}" deleted successfully.`);
      refetch();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Failed to delete member.");
    }
  };

  const openEditModal = (member: any) => {
    setEditForm({
      id: member.id,
      name: member.name,
      email: member.email,
      username: member.username,
      password: "", // Keep password blank unless changing
    });
    setIsEditModalOpen(true);
  };

  if (!isAdmin) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-center space-y-4">
        <ShieldAlert className="text-red-500" size={48} />
        <h1 className="text-xl font-bold text-white">Access Denied</h1>
        <p className="text-slate-400 max-w-md">Only librarians and administrators have access to the member management portal.</p>
      </div>
    );
  }

  const totalPages = data ? Math.ceil(data.total / PER_PAGE) : 1;

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Users className="text-indigo-400" size={26} /> Member Management
          </h1>
          <p className="text-slate-400 text-sm mt-1">{data?.total ?? "—"} total registered members</p>
        </div>
        <motion.button
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          onClick={() => setIsAddModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl text-white text-sm font-medium shadow-lg shadow-indigo-500/20 hover:opacity-90 transition-opacity"
        >
          <Plus size={16} /> Add Member
        </motion.button>
      </motion.div>

      {/* Search bar */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
        <input
          value={search}
          onChange={(e) => handleSearch(e.target.value)}
          placeholder="Search members by name or email..."
          className="w-full bg-white/5 border border-white/10 rounded-xl pl-12 pr-12 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/50 transition-all"
        />
        {isFetching && (
          <Loader2 className="absolute right-4 top-1/2 -translate-y-1/2 text-indigo-400 animate-spin" size={18} />
        )}
      </div>

      {/* Table */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
        className="glass overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/5">
                {["Name", "Username", "Email", "Status", "Actions"].map(h => (
                  <th key={h} className="text-left text-slate-400 text-xs font-semibold uppercase tracking-wider px-6 py-4">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                Array.from({ length: 8 }).map((_, i) => (
                  <tr key={i} className="border-b border-white/5">
                    {Array.from({ length: 5 }).map((_, j) => (
                      <td key={j} className="px-6 py-4">
                        <div className="h-4 bg-white/5 rounded animate-pulse" style={{ width: `${60 + Math.random() * 30}%` }} />
                      </td>
                    ))}
                  </tr>
                ))
              ) : data?.data?.length === 0 ? (
                <tr><td colSpan={5} className="px-6 py-16 text-center text-slate-500">No members found.</td></tr>
              ) : data?.data?.map((member: any) => (
                <motion.tr key={member.id}
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                  className="border-b border-white/5 hover:bg-white/3 transition-colors group"
                >
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-indigo-500/10 flex items-center justify-center text-indigo-400 font-bold text-sm">
                        {member.name.charAt(0).toUpperCase()}
                      </div>
                      <span className="text-white font-medium">{member.name}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-slate-300">@{member.username}</td>
                  <td className="px-6 py-4 text-slate-400">{member.email}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
                      member.is_active
                        ? "bg-emerald-500/15 text-emerald-400"
                        : "bg-red-500/15 text-red-400"
                    }`}>
                      {member.is_active ? <CheckCircle size={12} /> : <XCircle size={12} />}
                      {member.is_active ? "Active" : "Suspended"}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleToggleActive(member.id, member.is_active, member.name)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                          member.is_active
                            ? "border-red-500/30 text-red-400 hover:bg-red-500/10"
                            : "border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10"
                        }`}
                      >
                        {member.is_active ? "Deactivate" : "Activate"}
                      </button>
                      
                      <div className="flex items-center gap-1.5">
                        <button
                          onClick={() => openEditModal(member)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-400 hover:bg-indigo-500/10 transition-all"
                          title="Edit Profile"
                        >
                          <Edit size={15} />
                        </button>
                        <button
                          onClick={() => handleDeleteMember(member.id, member.name)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-all"
                          title="Delete Permanently"
                        >
                          <Trash2 size={15} />
                        </button>
                      </div>
                    </div>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-6 py-4 border-t border-white/5">
            <p className="text-slate-400 text-sm">Page {page} of {totalPages}</p>
            <div className="flex items-center gap-2">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
                className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 disabled:opacity-30 disabled:cursor-not-allowed transition-all">
                <ChevronLeft size={16} />
              </button>
              <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}
                className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 disabled:opacity-30 disabled:cursor-not-allowed transition-all">
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        )}
      </motion.div>

      {/* Add Member Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="w-full max-w-md bg-slate-900 border border-white/10 rounded-2xl p-6 space-y-6"
          >
            <div>
              <h3 className="text-xl font-bold text-white flex items-center gap-2">
                <Users className="text-indigo-400" size={20} /> Add New Member
              </h3>
              <p className="text-slate-400 text-sm mt-1">Register a new reader account in the library system.</p>
            </div>

            <form onSubmit={handleAddMember} className="space-y-4">
              <div className="space-y-1">
                <label className="text-slate-300 text-xs font-semibold uppercase tracking-wider block">Full Name</label>
                <input
                  type="text"
                  required
                  value={addForm.name}
                  onChange={(e) => setAddForm({ ...addForm, name: e.target.value })}
                  placeholder="e.g. Aayush Angal"
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-all text-sm"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-300 text-xs font-semibold uppercase tracking-wider block">Username</label>
                <input
                  type="text"
                  required
                  value={addForm.username}
                  onChange={(e) => setAddForm({ ...addForm, username: e.target.value })}
                  placeholder="e.g. aayush123"
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-all text-sm"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-300 text-xs font-semibold uppercase tracking-wider block">Email Address</label>
                <input
                  type="email"
                  required
                  value={addForm.email}
                  onChange={(e) => setAddForm({ ...addForm, email: e.target.value })}
                  placeholder="e.g. aayush@example.com"
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-all text-sm"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-300 text-xs font-semibold uppercase tracking-wider block">Temporary Password</label>
                <input
                  type="password"
                  required
                  value={addForm.password}
                  onChange={(e) => setAddForm({ ...addForm, password: e.target.value })}
                  placeholder="Minimum 6 characters"
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-all text-sm"
                />
              </div>

              <div className="flex items-center gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  className="flex-1 px-4 py-2.5 bg-white/5 hover:bg-white/10 text-white rounded-xl text-sm font-semibold transition-all"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-semibold shadow-lg shadow-indigo-500/20 transition-all"
                >
                  Create Member
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}

      {/* Edit Member Modal */}
      {isEditModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="w-full max-w-md bg-slate-900 border border-white/10 rounded-2xl p-6 space-y-6"
          >
            <div>
              <h3 className="text-xl font-bold text-white flex items-center gap-2">
                <Edit className="text-indigo-400" size={20} /> Edit Member Profile
              </h3>
              <p className="text-slate-400 text-sm mt-1">Modify account settings and parameters for this member.</p>
            </div>

            <form onSubmit={handleEditMember} className="space-y-4">
              <div className="space-y-1">
                <label className="text-slate-300 text-xs font-semibold uppercase tracking-wider block">Full Name</label>
                <input
                  type="text"
                  required
                  value={editForm.name}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                  placeholder="e.g. Aayush Angal"
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-all text-sm"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-300 text-xs font-semibold uppercase tracking-wider block">Username</label>
                <input
                  type="text"
                  required
                  value={editForm.username}
                  onChange={(e) => setEditForm({ ...editForm, username: e.target.value })}
                  placeholder="e.g. aayush123"
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-all text-sm"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-300 text-xs font-semibold uppercase tracking-wider block">Email Address</label>
                <input
                  type="email"
                  required
                  value={editForm.email}
                  onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                  placeholder="e.g. aayush@example.com"
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-all text-sm"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-300 text-xs font-semibold uppercase tracking-wider block">New Password</label>
                <input
                  type="password"
                  value={editForm.password}
                  onChange={(e) => setEditForm({ ...editForm, password: e.target.value })}
                  placeholder="Leave blank to keep unchanged"
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-all text-sm"
                />
              </div>

              <div className="flex items-center gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsEditModalOpen(false)}
                  className="flex-1 px-4 py-2.5 bg-white/5 hover:bg-white/10 text-white rounded-xl text-sm font-semibold transition-all"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-semibold shadow-lg shadow-indigo-500/20 transition-all"
                >
                  Save Changes
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </div>
  );
}
