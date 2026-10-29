import React, { useState, useEffect, useCallback } from 'react';
import {
  UserPlus,
  Search,
  RotateCcw,
  Edit3,
  Trash2,
  Power,
  X,
  AlertCircle,
  CheckCircle2,
  Key,
  UserCheck,
  Save,
} from 'lucide-react';
import { api } from '../../utils/api';

const BRANCHES = ['IT', 'CSE', 'ECE', 'EE', 'ME'];

const overlayStyle = {
  position: 'fixed',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  backgroundColor: 'rgba(0, 0, 0, 0.65)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 1000,
  padding: '1rem',
};

const thStyle = {
  padding: '0.875rem 1rem',
  textAlign: 'left',
  fontWeight: 600,
  fontSize: '0.78rem',
  color: 'var(--text-muted)',
  textTransform: 'uppercase',
  letterSpacing: '0.05em',
};

const tdStyle = {
  padding: '0.875rem 1rem',
  verticalAlign: 'middle',
};

export default function TeacherManagement() {
  const [teachers, setTeachers] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);

  // Filters
  const [search, setSearch] = useState('');
  const [branchFilter, setBranchFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // Alerts
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Create Modal
  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({
    name: '',
    email: '',
    phone: '',
    teacher_id: '',
    branch: 'IT',
  });
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState('');

  // Edit Modal
  const [editTarget, setEditTarget] = useState(null);
  const [editForm, setEditForm] = useState({
    name: '',
    email: '',
    phone: '',
    teacher_id: '',
    branch: '',
  });
  const [editLoading, setEditLoading] = useState(false);
  const [editError, setEditError] = useState('');

  // Password Reset Modal
  const [resetTarget, setResetTarget] = useState(null);
  const [resetLoading, setResetLoading] = useState(false);

  // Status Toggle Modal
  const [statusTarget, setStatusTarget] = useState(null);
  const [statusLoading, setStatusLoading] = useState(false);
  const [statusError, setStatusError] = useState('');

  // Delete Modal
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const loadTeachers = useCallback(async (pageNum = 1) => {
    setLoading(true);
    setError('');
    try {
      let url = `/api/admin/users/teachers?page=${pageNum}&limit=15`;
      if (branchFilter) url += `&branch=${encodeURIComponent(branchFilter)}`;
      if (statusFilter) url += `&status=${encodeURIComponent(statusFilter)}`;
      if (search) url += `&q=${encodeURIComponent(search)}`;

      const res = await api.get(url);
      if (res.ok) {
        const data = await res.json();
        setTeachers(data.items);
        setTotal(data.total);
        setPage(data.page);
        setTotalPages(data.total_pages);
      } else {
        const err = await res.json();
        setError(err.detail || 'Failed to load teachers.');
      }
    } catch {
      setError('Failed to connect to server.');
    }
    setLoading(false);
  }, [branchFilter, statusFilter, search]);

  useEffect(() => {
    let ignore = false;
    const fetchInitial = async () => {
      try {
        let url = `/api/admin/users/teachers?page=1&limit=15`;
        if (branchFilter) url += `&branch=${encodeURIComponent(branchFilter)}`;
        if (statusFilter) url += `&status=${encodeURIComponent(statusFilter)}`;
        if (search) url += `&q=${encodeURIComponent(search)}`;

        const res = await api.get(url);
        if (!ignore) {
          if (res.ok) {
            const data = await res.json();
            setTeachers(data.items);
            setTotal(data.total);
            setPage(data.page);
            setTotalPages(data.total_pages);
          } else {
            const err = await res.json();
            setError(err.detail || 'Failed to load teachers.');
          }
          setLoading(false);
        }
      } catch {
        if (!ignore) {
          setError('Failed to connect to server.');
          setLoading(false);
        }
      }
    };
    fetchInitial();
    return () => {
      ignore = true;
    };
  }, [branchFilter, statusFilter, search]);

  // Create Teacher
  const handleCreate = async (e) => {
    e.preventDefault();
    setCreateLoading(true);
    setCreateError('');
    try {
      const res = await api.post('/api/admin/users/teachers', {
        name: createForm.name.trim(),
        email: createForm.email.trim(),
        phone: createForm.phone.trim() || undefined,
        teacher_id: createForm.teacher_id.trim() || undefined,
        branch: createForm.branch || undefined,
      });
      if (res.ok) {
        setShowCreate(false);
        setCreateForm({
          name: '',
          email: '',
          phone: '',
          teacher_id: '',
          branch: 'IT',
        });
        setSuccess('Teacher account created successfully with default password assigned.');
        loadTeachers(1);
        setTimeout(() => setSuccess(''), 4000);
      } else {
        const err = await res.json();
        setCreateError(err.detail || 'Failed to create teacher.');
      }
    } catch {
      setCreateError('Failed to connect to server.');
    }
    setCreateLoading(false);
  };

  // Open Edit
  const handleOpenEdit = (tea) => {
    setEditTarget(tea);
    setEditError('');
    setEditForm({
      name: tea.name || '',
      email: tea.email || '',
      phone: tea.phone || '',
      teacher_id: tea.teacher_id || '',
      branch: tea.branch || 'IT',
    });
  };

  // Save Edit
  const handleSaveEdit = async (e) => {
    e.preventDefault();
    if (!editTarget) return;
    setEditLoading(true);
    setEditError('');

    const payload = {};
    if (editForm.name.trim() !== editTarget.name) payload.name = editForm.name.trim();
    if (editForm.email.trim() !== editTarget.email) payload.email = editForm.email.trim();
    if (editForm.phone.trim() !== (editTarget.phone || '')) payload.phone = editForm.phone.trim();
    if (editForm.teacher_id.trim() !== (editTarget.teacher_id || '')) payload.teacher_id = editForm.teacher_id.trim();
    if (editForm.branch !== (editTarget.branch || '')) payload.branch = editForm.branch;

    try {
      const res = await api.patch(`/api/users/${editTarget.id}`, payload);
      if (res.ok) {
        setEditTarget(null);
        setSuccess(`Teacher '${editForm.name}' updated successfully.`);
        loadTeachers(page);
        setTimeout(() => setSuccess(''), 4000);
      } else {
        const err = await res.json();
        setEditError(err.detail || 'Failed to update teacher.');
      }
    } catch {
      setEditError('Failed to connect to server.');
    }
    setEditLoading(false);
  };

  // Reset Password
  const handleResetPassword = async () => {
    if (!resetTarget) return;
    setResetLoading(true);
    try {
      const res = await api.post(`/api/admin/users/${resetTarget.id}/reset-password`, {});
      if (res.ok) {
        setResetTarget(null);
        setSuccess(`Password reset for ${resetTarget.name}. They will be required to change it on next login.`);
        setTimeout(() => setSuccess(''), 4000);
      } else {
        const err = await res.json();
        setError(err.detail || 'Failed to reset password.');
      }
    } catch {
      setError('Failed to connect to server.');
    }
    setResetLoading(false);
  };

  // Toggle Status
  const handleToggleStatus = async () => {
    if (!statusTarget) return;
    setStatusLoading(true);
    setStatusError('');
    try {
      const newStatus = !statusTarget.is_verified;
      const res = await api.patch(`/api/admin/users/${statusTarget.id}/status`, {
        is_verified: newStatus,
      });
      if (res.ok) {
        const actionLabel = newStatus ? 'activated' : 'deactivated';
        setStatusTarget(null);
        setSuccess(`Teacher ${statusTarget.name} has been ${actionLabel}.`);
        loadTeachers(page);
        setTimeout(() => setSuccess(''), 4000);
      } else {
        const err = await res.json();
        setStatusError(err.detail || 'Failed to change teacher status.');
      }
    } catch (err) {
      setStatusError(err.message || 'Failed to connect to server.');
    }
    setStatusLoading(false);
  };

  // Delete Teacher
  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleteLoading(true);
    try {
      const res = await api.delete(`/api/users/${deleteTarget.id}`);
      if (res.ok) {
        const deletedName = deleteTarget.name;
        setDeleteTarget(null);
        setSuccess(`Teacher '${deletedName}' has been permanently deleted.`);
        loadTeachers(page);
        setTimeout(() => setSuccess(''), 4000);
      } else {
        const err = await res.json();
        setError(err.detail || 'Failed to delete teacher.');
      }
    } catch {
      setError('Failed to connect to server.');
    }
    setDeleteLoading(false);
  };

  return (
    <div style={{ width: '100%' }}>
      {/* Header & Primary Action */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.65rem', fontWeight: 800, margin: '0 0 0.25rem 0' }}>Teacher Management</h2>
          <p className="text-muted" style={{ margin: 0, fontSize: '0.9rem' }}>
            Manage teacher accounts ({total} total faculty members)
          </p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => { setShowCreate(true); setCreateError(''); }}
          style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.65rem 1.25rem', fontWeight: 600 }}
        >
          <UserPlus size={17} /> Create Teacher
        </button>
      </div>

      {/* Alerts */}
      {success && (
        <div className="alert alert-success" style={{ marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <CheckCircle2 size={18} /> {success}
        </div>
      )}
      {error && (
        <div className="alert alert-danger" style={{ marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <AlertCircle size={18} /> {error}
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="card" style={{ padding: '1rem 1.25rem', marginBottom: '1.25rem', width: '100%', boxSizing: 'border-box', display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
        {/* Search */}
        <div style={{ position: 'relative', flex: '1 1 240px' }}>
          <Search size={16} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', pointerEvents: 'none' }} />
          <input
            type="text"
            className="form-input"
            placeholder="Search name, employee ID, email..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && loadTeachers(1)}
            style={{ paddingLeft: '2.25rem', fontSize: '0.875rem' }}
          />
        </div>

        {/* Branch Filter */}
        <select
          className="form-select"
          value={branchFilter}
          onChange={e => setBranchFilter(e.target.value)}
          style={{ width: 'auto', minWidth: '140px', fontSize: '0.875rem' }}
        >
          <option value="">All Departments</option>
          {BRANCHES.map(b => <option key={b} value={b}>{b}</option>)}
        </select>

        {/* Status Filter */}
        <select
          className="form-select"
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          style={{ width: 'auto', minWidth: '120px', fontSize: '0.875rem' }}
        >
          <option value="">All Status</option>
          <option value="active">Active</option>
          <option value="inactive">Deactivated</option>
        </select>

        <button className="btn btn-primary" onClick={() => loadTeachers(1)} style={{ padding: '0.5rem 1rem', fontSize: '0.875rem' }}>
          <Search size={14} /> Search
        </button>
      </div>

      {/* Teacher Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden', width: '100%', boxSizing: 'border-box' }}>
        {loading ? (
          <div style={{ padding: '3.5rem', textAlign: 'center' }}>
            <div className="spinner" style={{ width: '28px', height: '28px', margin: '0 auto 0.75rem' }} />
            <p className="text-muted" style={{ margin: 0 }}>Loading teachers...</p>
          </div>
        ) : teachers.length === 0 ? (
          <div style={{ padding: '3.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            <UserCheck size={36} style={{ margin: '0 auto 0.75rem', opacity: 0.4, display: 'block' }} />
            <p style={{ margin: 0 }}>No teachers found matching your search or filters.</p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto', width: '100%' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', backgroundColor: 'var(--surface-subtle)' }}>
                  <th style={{ ...thStyle, width: '24%' }}>Name</th>
                  <th style={{ ...thStyle, width: '18%' }}>Employee ID</th>
                  <th style={{ ...thStyle, width: '24%' }}>Email</th>
                  <th style={{ ...thStyle, width: '14%' }}>Department</th>
                  <th style={{ ...thStyle, width: '10%' }}>Status</th>
                  <th style={{ ...thStyle, width: '10%', textAlign: 'center' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {teachers.map(tea => (
                  <tr key={tea.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td style={tdStyle}>
                      <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>{tea.name}</div>
                      {tea.phone && <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{tea.phone}</div>}
                    </td>
                    <td style={tdStyle}>
                      <span style={{ fontSize: '0.825rem', fontFamily: 'monospace', fontWeight: 600 }}>
                        {tea.teacher_id || '–'}
                      </span>
                    </td>
                    <td style={tdStyle}>
                      <span style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>{tea.email}</span>
                    </td>
                    <td style={tdStyle}>
                      <span className="badge badge-primary" style={{ fontSize: '0.75rem' }}>
                        {tea.branch || '–'}
                      </span>
                    </td>
                    <td style={tdStyle}>
                      <span
                        className={`badge ${tea.is_verified ? 'badge-primary' : 'badge-danger'}`}
                        style={{ fontSize: '0.725rem' }}
                      >
                        {tea.is_verified ? 'Active' : 'Deactivated'}
                      </span>
                    </td>
                    <td style={{ ...tdStyle, textAlign: 'center' }}>
                      <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.45rem', justifyContent: 'center' }}>
                        {/* Edit */}
                        <div className="admin-action-btn-wrap">
                          <button
                            type="button"
                            className="admin-action-icon-btn edit"
                            onClick={() => handleOpenEdit(tea)}
                            aria-label="Edit teacher"
                            title="Edit Teacher"
                          >
                            <Edit3 size={15} />
                          </button>
                          <span className="admin-action-tooltip">Edit Teacher</span>
                        </div>

                        {/* Reset Password */}
                        <div className="admin-action-btn-wrap">
                          <button
                            type="button"
                            className="admin-action-icon-btn reset"
                            onClick={() => setResetTarget(tea)}
                            aria-label="Reset password"
                            title="Reset Password"
                          >
                            <RotateCcw size={15} />
                          </button>
                          <span className="admin-action-tooltip">Reset Password</span>
                        </div>

                        {/* Activate / Deactivate */}
                        <div className="admin-action-btn-wrap">
                          <button
                            type="button"
                            className={`admin-action-icon-btn ${tea.is_verified ? 'deactivate' : 'activate'}`}
                            onClick={() => { setStatusTarget(tea); setStatusError(''); }}
                            aria-label={tea.is_verified ? 'Deactivate teacher' : 'Activate teacher'}
                            title={tea.is_verified ? 'Deactivate Teacher' : 'Activate Teacher'}
                          >
                            <Power size={14} />
                          </button>
                          <span className="admin-action-tooltip">{tea.is_verified ? 'Deactivate Teacher' : 'Activate Teacher'}</span>
                        </div>

                        {/* Delete */}
                        <div className="admin-action-btn-wrap">
                          <button
                            type="button"
                            className="admin-action-icon-btn delete"
                            onClick={() => setDeleteTarget(tea)}
                            aria-label="Delete teacher"
                            title="Delete Teacher"
                          >
                            <Trash2 size={15} />
                          </button>
                          <span className="admin-action-tooltip">Delete Teacher</span>
                        </div>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div style={{ padding: '0.85rem 1.25rem', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="text-muted" style={{ fontSize: '0.825rem' }}>Page {page} of {totalPages}</span>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button className="btn btn-outline" disabled={page <= 1} onClick={() => loadTeachers(page - 1)} style={{ padding: '0.35rem 0.85rem', fontSize: '0.8rem' }}>Previous</button>
              <button className="btn btn-outline" disabled={page >= totalPages} onClick={() => loadTeachers(page + 1)} style={{ padding: '0.35rem 0.85rem', fontSize: '0.8rem' }}>Next</button>
            </div>
          </div>
        )}
      </div>

      {/* ── Create Teacher Modal ── */}
      {showCreate && (
        <div style={overlayStyle} onClick={() => setShowCreate(false)}>
          <div className="card glass-panel" style={{ maxWidth: '520px', width: '100%', padding: '2rem', maxHeight: '88vh', overflowY: 'auto' }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <div style={{ width: '34px', height: '34px', borderRadius: 'var(--radius-md)', background: 'rgba(16, 185, 129, 0.1)', color: '#10b981', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <UserCheck size={18} />
                </div>
                <h3 style={{ fontWeight: 700, margin: 0, fontSize: '1.2rem' }}>Create Teacher</h3>
              </div>
              <button type="button" onClick={() => setShowCreate(false)} style={{ color: 'var(--text-muted)', cursor: 'pointer', padding: '0.25rem', background: 'none', border: 'none' }}><X size={20} /></button>
            </div>

            {createError && (
              <div className="alert alert-danger" style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <AlertCircle size={16} /> {createError}
              </div>
            )}

            <form onSubmit={handleCreate}>
              <div className="form-group"><label className="form-label">Full Name *</label><input type="text" className="form-input" required placeholder="e.g. Dr. Alan Turing" value={createForm.name} onChange={e => setCreateForm({ ...createForm, name: e.target.value })} /></div>
              <div className="form-group"><label className="form-label">Email Address *</label><input type="email" className="form-input" required placeholder="alan.turing@university.edu" value={createForm.email} onChange={e => setCreateForm({ ...createForm, email: e.target.value })} /></div>
              <div className="form-group"><label className="form-label">Phone Number</label><input type="tel" className="form-input" placeholder="9876543210" value={createForm.phone} onChange={e => setCreateForm({ ...createForm, phone: e.target.value })} /></div>

              <div style={{ padding: '1rem', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', marginBottom: '1.25rem', background: 'var(--surface-subtle)' }}>
                <h4 style={{ fontSize: '0.875rem', fontWeight: 700, marginBottom: '0.75rem', color: '#10b981' }}>Department Details</h4>
                <div className="form-group"><label className="form-label">Employee / Teacher ID</label><input type="text" className="form-input" placeholder="e.g. FAC-IT-042" value={createForm.teacher_id} onChange={e => setCreateForm({ ...createForm, teacher_id: e.target.value })} /></div>
                <div className="form-group" style={{ marginBottom: 0 }}><label className="form-label">Department / Branch</label>
                  <select className="form-select" value={createForm.branch} onChange={e => setCreateForm({ ...createForm, branch: e.target.value })}>
                    {BRANCHES.map(b => <option key={b} value={b}>{b}</option>)}
                  </select>
                </div>
              </div>

              <div style={{ padding: '0.75rem', borderRadius: 'var(--radius-md)', background: 'var(--primary-light)', marginBottom: '1.25rem', fontSize: '0.825rem', color: 'var(--primary-color)' }}>
                <strong>Note:</strong> Default password will be assigned. The teacher must change it on their first login.
              </div>

              <button type="submit" className="btn btn-primary w-full" disabled={createLoading} style={{ padding: '0.75rem', fontWeight: 600 }}>
                {createLoading ? (<><div className="spinner spinner-white" style={{ width: '16px', height: '16px' }} /> Creating...</>) : (<><UserPlus size={16} /> Create Teacher</>)}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* ── Edit Teacher Modal ── */}
      {editTarget && (
        <div style={overlayStyle} onClick={() => setEditTarget(null)}>
          <div className="card glass-panel" style={{ maxWidth: '520px', width: '100%', padding: '2rem', maxHeight: '88vh', overflowY: 'auto' }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <div style={{ width: '34px', height: '34px', borderRadius: 'var(--radius-md)', background: 'rgba(16, 185, 129, 0.1)', color: '#10b981', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Edit3 size={17} />
                </div>
                <h3 style={{ fontWeight: 700, margin: 0, fontSize: '1.2rem' }}>Edit Teacher</h3>
              </div>
              <button type="button" onClick={() => setEditTarget(null)} style={{ color: 'var(--text-muted)', cursor: 'pointer', padding: '0.25rem', background: 'none', border: 'none' }}><X size={20} /></button>
            </div>

            {editError && (
              <div className="alert alert-danger" style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <AlertCircle size={16} /> {editError}
              </div>
            )}

            <form onSubmit={handleSaveEdit}>
              <div className="form-group"><label className="form-label">Full Name *</label><input type="text" className="form-input" required value={editForm.name} onChange={e => setEditForm({ ...editForm, name: e.target.value })} /></div>
              <div className="form-group"><label className="form-label">Email Address *</label><input type="email" className="form-input" required value={editForm.email} onChange={e => setEditForm({ ...editForm, email: e.target.value })} /></div>
              <div className="form-group"><label className="form-label">Phone Number</label><input type="tel" className="form-input" value={editForm.phone} onChange={e => setEditForm({ ...editForm, phone: e.target.value })} /></div>

              <div style={{ padding: '1rem', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', marginBottom: '1.25rem', background: 'var(--surface-subtle)' }}>
                <h4 style={{ fontSize: '0.875rem', fontWeight: 700, marginBottom: '0.75rem', color: '#10b981' }}>Department Details</h4>
                <div className="form-group"><label className="form-label">Employee / Teacher ID</label><input type="text" className="form-input" value={editForm.teacher_id} onChange={e => setEditForm({ ...editForm, teacher_id: e.target.value })} /></div>
                <div className="form-group" style={{ marginBottom: 0 }}><label className="form-label">Department / Branch</label>
                  <select className="form-select" value={editForm.branch} onChange={e => setEditForm({ ...editForm, branch: e.target.value })}>
                    {BRANCHES.map(b => <option key={b} value={b}>{b}</option>)}
                  </select>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
                <button type="button" className="btn btn-outline" style={{ flex: 1, padding: '0.7rem' }} onClick={() => setEditTarget(null)}>Cancel</button>
                <button type="submit" className="btn btn-primary" style={{ flex: 1, padding: '0.7rem' }} disabled={editLoading}>
                  {editLoading ? (<><div className="spinner spinner-white" style={{ width: '16px', height: '16px' }} /> Saving...</>) : (<><Save size={16} /> Save Changes</>)}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Reset Password Confirmation Modal ── */}
      {resetTarget && (
        <div style={overlayStyle} onClick={() => setResetTarget(null)}>
          <div className="card glass-panel" style={{ maxWidth: '440px', width: '100%', padding: '2rem' }} onClick={e => e.stopPropagation()}>
            <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
              <div style={{ width: '56px', height: '56px', borderRadius: '50%', background: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem' }}>
                <Key size={28} />
              </div>
              <h3 style={{ fontWeight: 700, marginBottom: '0.5rem' }}>Reset Password</h3>
              <p className="text-muted" style={{ fontSize: '0.9rem' }}>
                Are you sure you want to reset the password for teacher <strong style={{ color: 'var(--text-main)' }}>{resetTarget.name}</strong> ({resetTarget.email})?
              </p>
              <p className="text-muted" style={{ fontSize: '0.825rem' }}>
                The password will be reset to default. They will be required to change it on next login.
              </p>
            </div>
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button className="btn btn-outline" style={{ flex: 1, padding: '0.65rem' }} onClick={() => setResetTarget(null)}>Cancel</button>
              <button className="btn btn-primary" style={{ flex: 1, padding: '0.65rem', background: '#f59e0b', borderColor: '#f59e0b' }} onClick={handleResetPassword} disabled={resetLoading}>
                {resetLoading ? (<><div className="spinner spinner-white" style={{ width: '14px', height: '14px' }} /> Resetting...</>) : (<><RotateCcw size={14} /> Reset Password</>)}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Status Toggle Confirmation Modal ── */}
      {statusTarget && (
        <div style={overlayStyle} onClick={() => setStatusTarget(null)}>
          <div className="card glass-panel" style={{ maxWidth: '440px', width: '100%', padding: '2rem' }} onClick={e => e.stopPropagation()}>
            <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
              <div style={{
                width: '56px', height: '56px', borderRadius: '50%',
                background: statusTarget.is_verified ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)',
                color: statusTarget.is_verified ? 'var(--danger-color)' : 'var(--success-color)',
                display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem',
              }}>
                <Power size={28} />
              </div>
              <h3 style={{ fontWeight: 700, marginBottom: '0.5rem' }}>
                {statusTarget.is_verified ? 'Deactivate Teacher Account' : 'Activate Teacher Account'}
              </h3>
              <p className="text-muted" style={{ fontSize: '0.9rem' }}>
                Are you sure you want to {statusTarget.is_verified ? 'deactivate' : 'activate'} <strong style={{ color: 'var(--text-main)' }}>{statusTarget.name}</strong>?
              </p>
              {statusTarget.is_verified && (
                <p style={{ fontSize: '0.8rem', color: 'var(--danger-color)', marginTop: '0.5rem' }}>
                  Deactivating will immediately revoke all active sessions and block login until reactivated.
                </p>
              )}
            </div>

            {statusError && (
              <div className="alert alert-danger" style={{ marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <AlertCircle size={16} /> {statusError}
              </div>
            )}
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button className="btn btn-outline" style={{ flex: 1, padding: '0.65rem' }} onClick={() => setStatusTarget(null)}>Cancel</button>
              <button
                className={`btn ${statusTarget.is_verified ? 'btn-danger' : 'btn-primary'}`}
                style={{ flex: 1, padding: '0.65rem' }}
                onClick={handleToggleStatus}
                disabled={statusLoading}
              >
                {statusLoading ? (<><div className="spinner spinner-white" style={{ width: '14px', height: '14px' }} /> Processing...</>) : (statusTarget.is_verified ? 'Deactivate' : 'Activate')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Delete Confirmation Modal ── */}
      {deleteTarget && (
        <div style={overlayStyle} onClick={() => setDeleteTarget(null)}>
          <div className="card glass-panel" style={{ maxWidth: '440px', width: '100%', padding: '2rem' }} onClick={e => e.stopPropagation()}>
            <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
              <div style={{ width: '56px', height: '56px', borderRadius: '50%', background: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger-color)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem' }}>
                <Trash2 size={28} />
              </div>
              <h3 style={{ fontWeight: 700, marginBottom: '0.5rem' }}>Delete Teacher Account</h3>
              <p className="text-muted" style={{ fontSize: '0.9rem' }}>
                Are you sure you want to permanently delete <strong style={{ color: 'var(--text-main)' }}>{deleteTarget.name}</strong> ({deleteTarget.email})?
              </p>
              <p style={{ fontSize: '0.8rem', color: 'var(--danger-color)', marginTop: '0.5rem', fontWeight: 500 }}>
                All teacher records and active sessions will be permanently purged. This action cannot be undone.
              </p>
            </div>
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button className="btn btn-outline" style={{ flex: 1, padding: '0.65rem' }} onClick={() => setDeleteTarget(null)}>Cancel</button>
              <button className="btn btn-danger" style={{ flex: 1, padding: '0.65rem' }} onClick={handleDelete} disabled={deleteLoading}>
                {deleteLoading ? (<><div className="spinner spinner-white" style={{ width: '14px', height: '14px' }} /> Deleting...</>) : (<><Trash2 size={14} /> Delete Teacher</>)}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
