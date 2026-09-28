"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { 
  Users, 
  Search, 
  Shield, 
  MapPin, 
  CheckCircle, 
  XCircle, 
  ArrowLeft,
  RefreshCw,
  AlertCircle
} from "lucide-react";
import { useAuth } from "@/lib/auth/Context";
import { fetchUsers, updateUserRole } from "@/lib/api/auth";
import { User, UserRole } from "@/lib/types/auth";

export default function AdminUsersPage() {
  const { token, user: currentUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [roleFilter, setRoleFilter] = useState<string>("ALL");
  const [updatingUserId, setUpdatingUserId] = useState<string | null>(null);

  const loadUsers = async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const userList = await fetchUsers(token);
      setUsers(userList);
    } catch (err: any) {
      setError(err.message || "Failed to load users");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, [token]);

  const handleRoleChange = async (userId: string, newRole: UserRole) => {
    if (!token) return;
    setUpdatingUserId(userId);
    try {
      const updated = await updateUserRole(token, userId, newRole);
      setUsers(prev => prev.map(u => u.user_id === userId ? updated : u));
    } catch (err: any) {
      alert(err.message || "Failed to update role");
    } finally {
      setUpdatingUserId(null);
    }
  };

  const filteredUsers = users.filter(u => {
    const matchesSearch = 
      u.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      u.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (u.organization && u.organization.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesRole = roleFilter === "ALL" || u.role === roleFilter;

    return matchesSearch && matchesRole;
  });

  return (
    <div className="min-h-screen bg-[#F7F3EC] text-[#2C2C2C] flex flex-col font-sans">
      
      {/* Console Header */}
      <header className="bg-[#1A1A1A] text-[#FBF9F5] px-4 lg:px-8 py-3.5 flex items-center justify-between border-b border-white/10">
        <div className="flex items-center gap-3">
          <Link href="/admin" className="text-white/70 hover:text-white transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div className="w-8 h-8 rounded-lg bg-[#2D5016] flex items-center justify-center font-bold">
            <Users className="w-4 h-4 text-[#FBF9F5]" />
          </div>
          <div>
            <h1 className="font-display font-bold text-base text-white leading-none">
              User Management & Access Control
            </h1>
            <p className="text-[10px] text-[#8A8A8A]">SIH26012 Geospatial Role & Region Governance</p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs">
          <Link href="/admin/datasets" className="text-[#FBF9F5]/80 hover:text-white transition-colors">
            Datasets
          </Link>
          <Link href="/admin/regions" className="text-[#FBF9F5]/80 hover:text-white transition-colors">
            Regions
          </Link>
          <Link href="/admin/users" className="text-white font-semibold border-b border-[#2D5016]">
            Users
          </Link>
          <Link href="/app/map" className="px-3 py-1 bg-[#2D5016] text-white rounded font-medium text-xs hover:bg-[#3A6B1E] transition-colors">
            Exit Console
          </Link>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 lg:p-8 space-y-6">
        
        {/* Top Controls */}
        <div className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl p-6 shadow-panel space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="font-bold text-base text-[#2D5016]">
                Registered Platform Personnel ({filteredUsers.length})
              </h2>
              <p className="text-xs text-[#6B6B6B]">
                Manage role escalation, regional assignments, and user verification status.
              </p>
            </div>

            <button
              onClick={loadUsers}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#F7F3EC] border border-[#E8E0D0] hover:border-[#2D5016] rounded-lg text-xs font-semibold text-[#2C2C2C] transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              <span>Refresh</span>
            </button>
          </div>

          {/* Search & Filters */}
          <div className="flex flex-col sm:flex-row gap-3 pt-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-[#8A8A8A]" />
              <input
                type="text"
                placeholder="Search by officer name, email, or department..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-[#F7F3EC] border border-[#E8E0D0] rounded-lg pl-9 pr-3 py-2 text-xs text-[#2C2C2C] placeholder-[#8A8A8A] focus:outline-none focus:border-[#2D5016]"
              />
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-[#6B6B6B]">Role:</span>
              <select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
                className="bg-[#F7F3EC] border border-[#E8E0D0] rounded-lg px-3 py-2 text-xs font-semibold text-[#2C2C2C] focus:outline-none focus:border-[#2D5016]"
              >
                <option value="ALL">All Roles</option>
                <option value="ADMIN">ADMIN</option>
                <option value="REVIEWER">REVIEWER</option>
                <option value="SURVEYOR">SURVEYOR</option>
                <option value="PUBLIC">PUBLIC</option>
              </select>
            </div>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Users Table */}
        <div className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl shadow-panel overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left border-collapse">
              <thead>
                <tr className="bg-[#F7F3EC] border-b border-[#E8E0D0] text-[#8A8A8A] uppercase text-[10px]">
                  <th className="py-3 px-4">User Identity</th>
                  <th className="py-3 px-4">Organization</th>
                  <th className="py-3 px-4">Role</th>
                  <th className="py-3 px-4">Assigned Region</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#EDE8DE]">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-[#8A8A8A]">
                      Loading user directory...
                    </td>
                  </tr>
                ) : filteredUsers.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-[#8A8A8A]">
                      No users found matching query.
                    </td>
                  </tr>
                ) : (
                  filteredUsers.map((u) => (
                    <tr key={u.user_id} className="hover:bg-[#F7F3EC]/50 transition-colors">
                      <td className="py-3.5 px-4 font-medium">
                        <div className="font-bold text-[#2C2C2C]">{u.name}</div>
                        <div className="text-[11px] text-[#6B6B6B] font-mono">{u.email}</div>
                      </td>
                      <td className="py-3.5 px-4 text-[#6B6B6B]">
                        {u.organization || "Independent"}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded font-bold text-[10px] ${
                          u.role === "ADMIN" ? "bg-purple-100 text-purple-800 border border-purple-200" :
                          u.role === "REVIEWER" ? "bg-amber-100 text-amber-800 border border-amber-200" :
                          u.role === "SURVEYOR" ? "bg-emerald-100 text-emerald-800 border border-emerald-200" :
                          "bg-gray-100 text-gray-700 border border-gray-200"
                        }`}>
                          <Shield className="w-3 h-3" />
                          {u.role}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 font-mono text-[11px] text-[#2D5016]">
                        <div className="flex items-center gap-1">
                          <MapPin className="w-3.5 h-3.5 text-[#2D5016]" />
                          <span>{u.region_id || "Global (*)"}</span>
                        </div>
                      </td>
                      <td className="py-3.5 px-4">
                        {u.is_active ? (
                          <span className="inline-flex items-center gap-1 text-emerald-700 font-semibold text-[11px]">
                            <CheckCircle className="w-3.5 h-3.5" />
                            Active
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-red-600 font-semibold text-[11px]">
                            <XCircle className="w-3.5 h-3.5" />
                            Disabled
                          </span>
                        )}
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-2">
                          <select
                            disabled={updatingUserId === u.user_id || u.user_id === currentUser?.user_id}
                            value={u.role}
                            onChange={(e) => handleRoleChange(u.user_id, e.target.value as UserRole)}
                            className="bg-[#F7F3EC] border border-[#E8E0D0] rounded px-2 py-1 text-[11px] font-semibold text-[#2C2C2C] focus:outline-none focus:border-[#2D5016] disabled:opacity-50"
                          >
                            <option value="PUBLIC">Make PUBLIC</option>
                            <option value="SURVEYOR">Make SURVEYOR</option>
                            <option value="REVIEWER">Make REVIEWER</option>
                            <option value="ADMIN">Make ADMIN</option>
                          </select>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

      </main>

    </div>
  );
}
