"use client";

import { useEffect, useState } from "react";
import { api, User } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { RequireAdmin } from "@/components/auth/RequireRole";

export default function AdminPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [pending, setPending] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<Record<number, boolean>>({});

  useEffect(() => {
    loadUsers();
  }, []);

  async function loadUsers() {
    setLoading(true);
    try {
      const [all, pend] = await Promise.all([
        api.listUsers(),
        api.listPendingUsers(),
      ]);
      setUsers(all);
      setPending(pend);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function approveUser(userId: number, isActive: boolean) {
    setActionLoading({ ...actionLoading, [userId]: true });
    try {
      await api.approveUser(userId, isActive);
      await loadUsers();
    } catch (err) {
      alert(String(err));
    } finally {
      setActionLoading({ ...actionLoading, [userId]: false });
    }
  }

  const roleBadge = (role: string) => {
    const colors: Record<string, string> = {
      admin: "bg-purple-100 text-purple-800",
      officer: "bg-blue-100 text-blue-800",
      bidder: "bg-green-100 text-green-800",
    };
    return <Badge variant="secondary" className={colors[role] || "bg-slate-100 text-slate-800"}>{role}</Badge>;
  };

  return (
    <RequireAdmin>
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">Admin Panel</h1>

        {/* Pending Approvals */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center justify-between">
              Pending Approvals ({pending.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
              </div>
            ) : pending.length === 0 ? (
              <p className="text-slate-500 text-sm">No pending approvals</p>
            ) : (
              <div className="space-y-3">
                {pending.map((u) => (
                  <div key={u.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <p className="font-medium">{u.full_name || u.email}</p>
                      <p className="text-sm text-slate-500">{u.email} · {u.organization_id} · {roleBadge(u.role)}</p>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        className="bg-emerald-600 hover:bg-emerald-700"
                        onClick={() => approveUser(u.id, true)}
                        disabled={actionLoading[u.id]}
                      >
                        Approve
                      </Button>
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => approveUser(u.id, false)}
                        disabled={actionLoading[u.id]}
                      >
                        Reject
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* All Users */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">All Users ({users.length})</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
              </div>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {users.map((u) => (
                  <div key={u.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <p className="font-medium">{u.full_name || u.email}</p>
                      <p className="text-sm text-slate-500">{u.email} · Org: {u.organization_id} · {roleBadge(u.role)} · {u.is_active ? "Active" : "Inactive"}</p>
                    </div>
                    {!u.is_active && (
                      <Button
                        size="sm"
                        className="bg-emerald-600 hover:bg-emerald-700"
                        onClick={() => approveUser(u.id, true)}
                        disabled={actionLoading[u.id]}
                      >
                        Activate
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </RequireAdmin>
  );
}