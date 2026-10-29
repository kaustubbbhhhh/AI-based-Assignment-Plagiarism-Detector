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
  GraduationCap,
  Save,
} from 'lucide-react';
import { api } from '../../utils/api';

const BRANCHES = ['IT', 'CSE', 'ECE', 'EE', 'ME'];
const SEMESTERS = [1, 2, 3, 4, 5, 6, 7, 8];

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

export default function StudentManagement() {
  const [students, setStudents] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);

  // Filters
  const [search, setSearch] = useState('');
  const [branchFilter, setBranchFilter] = useState('');
  const [semesterFilter, setSemesterFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // Alerts
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Modals
  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({
    name: '',
    email: '',
    phone: '',
    enrollment_no: '',
    branch: 'IT',
    semester: 4,
    section: '',
    session: '2024-2028',
  });
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState('');

  // Edit Modal
  const [editTarget, setEditTarget] = useState(null);
  const [editForm, setEditForm] = useState({
    name: '',
    email: '',
    phone: '',
    enrollment_no: '',
    branch: '',
    semester: '',
    section: '',
    session: '',
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

  const loadStudents = useCallback(async (pageNum = 1) => {
    setLoading(true);
    setError('');
    try {
      let url = `/api/admin/users/students?page=${pageNum}&limit=15`;
      if (branchFilter) url += `&branch=${encodeURIComponent(branchFilter)}`;
      if (semesterFilter) url += `&semester=${encodeURIComponent(semesterFilter)}`;
      if (statusFilter) url += `&status=${encodeURIComponent(statusFilter)}`;
      if (search) url += `&q=${encodeURIComponent(search)}`;

      const res = await api.get(url);
      if (res.ok) {
        const data = await res.json();
        setStudents(data.items);
        setTotal(data.total);
        setPage(data.page);
        setTotalPages(data.total_pages);
      } else {
        const err = await res.json();
        setError(err.detail || 'Failed to load students.');
      }
    } catch {
      setError('Failed to connect to server.');
    }
    setLoading(false);
  }, [branchFilter, semesterFilter, statusFilter, search]);

  useEffect(() => {
    let ignore = false;
    const fetchInitial = async () => {
      try {
        let url = `/api/admin/users/students?page=1&limit=15`;
        if (branchFilter) url += `&branch=${encodeURIComponent(branchFilter)}`;
        if (semesterFilter) url += `&semester=${encodeURIComponent(semesterFilter)}`;
        if (statusFilter) url += `&status=${encodeURIComponent(statusFilter)}`;
        if (search) url += `&q=${encodeURIComponent(search)}`;

        const res = await api.get(url);
        if (!ignore) {
          if (res.ok) {
            const data = await res.json();
            setStudents(data.items);
            setTotal(data.total);
            setPage(data.page);
            setTotalPages(data.total_pages);
          } else {
            const err = await res.json();
            setError(err.detail || 'Failed to load students.');
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
  }, [branchFilter, semesterFilter, statusFilter, search]);

  // Create Student
  const handleCreate = async (e) => {
    e.preventDefault();
    setCreateLoading(true);
    setCreateError('');
    try {
      const res = await api.post('/api/admin/users/students', {
        name: createForm.name.trim(),
        email: createForm.email.trim(),
        phone: createForm.phone.trim() || undefined,
        enrollment_no: createForm.enrollment_no.trim() || undefined,
        branch: createForm.branch || undefined,
        semester: createForm.semester ? parseInt(createForm.semester) : undefined,
        section: createForm.section.trim() || undefined,
        session: createForm.session.trim() || undefined,
      });
      if (res.ok) {
        setShowCreate(false);
        setCreateForm({
          name: '',
          email: '',
          phone: '',
          enrollment_no: '',
          branch: 'IT',
          semester: 4,
          section: '',
          session: '2024-2028',
        });
        setSuccess('Student created successfully with default password assigned.');
        loadStudents(1);
        setTimeout(() => setSuccess(''), 4000);
      } else {
        const err = await res.json();
        setCreateError(err.detail || 'Failed to create student.');
      }
    } catch {
      setCreateError('Failed to connect to server.');
    }
    setCreateLoading(false);
  };

  // Open Edit
  const handleOpenEdit = (stu) => {
    setEditTarget(stu);
    setEditError('');
    setEditForm({
      name: stu.name || '',
      email: stu.email || '',
      phone: stu.phone || '',
      enrollment_no: stu.enrollment_no || '',
      branch: stu.branch || 'IT',
      semester: stu.semester ? String(stu.semester) : '',
      section: stu.section || '',
      session: stu.session || '',
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
    if (editForm.enrollment_no.trim() !== (editTarget.enrollment_no || '')) payload.enrollment_no = editForm.enrollment_no.trim();
    if (editForm.branch !== (editTarget.branch || '')) payload.branch = editForm.branch;
    if (editForm.semester !== (editTarget.semester ? String(editTarget.semester) : '')) {
      payload.semester = editForm.semester ? parseInt(editForm.semester) : null;
    }
    if (editForm.section.trim() !== (editTarget.section || '')) payload.section = editForm.section.trim();
    if (editForm.session.trim() !== (editTarget.session || '')) payload.session = editForm.session.trim();

    try {
      const res = await api.patch(`/api/users/${editTarget.id}`, payload);
      if (res.ok) {
        setEditTarget(null);
        setSuccess(`Student '${editForm.name}' updated successfully.`);
        loadStudents(page);
        setTimeout(() => setSuccess(''), 4000);
      } else {
        const err = await res.json();
        setEditError(err.detail || 'Failed to update student.');
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
        setSuccess(`Student ${statusTarget.name} has been ${actionLabel}.`);
        loadStudents(page);
        setTimeout(() => setSuccess(''), 4000);
      } else {
        const err = await res.json();
        setStatusError(err.detail || 'Failed to change student status.');
      }
    } catch (err) {
      setStatusError(err.message || 'Failed to connect to server.');
    }
    setStatusLoading(false);
  };

  // Delete Student
  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleteLoading(true);
    try {
      const res = await api.delete(`/api/users/${deleteTarget.id}`);
      if (res.ok) {
        const deletedName = deleteTarget.name;
        setDeleteTarget(null);
        setSuccess(`Student '${deletedName}' has been permanently deleted.`);
        loadStudents(page);
        setTimeout(() => setSuccess(''), 4000);
      } else {
        const err = await res.json();
        setError(err.detail || 'Failed to delete student.');
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
          <h2 style={{ fontSize: '1.65rem', fontWeight: 800, margin: '0 0 0.25rem 0' }}>Student Management</h2>
          <p className="text-muted" style={{ margin: 0, fontSize: '0.9rem' }}>
            Manage student accounts ({total} total students enrolled)
          </p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => { setShowCreate(true); setCreateError(''); }}
          style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.65rem 1.25rem', fontWeight: 600 }}
        >
          <UserPlus size={17} /> Create Student
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
            placeholder="Search name, enrollment no, email..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && loadStudents(1)}
            style={{ paddingLeft: '2.25rem', fontSize: '0.875rem' }}
          />
        </div>

        {/* Branch Filter */}
        <select
          className="form-select"
          value={branchFilter}
          onChange={e => setBranchFilter(e.target.value)}
          style={{ width: 'auto', minWidth: '120px', fontSize: '0.875rem' }}
        >
          <option value="">All Branches</option>
          {BRANCHES.map(b => <option key={b} value={b}>{b}</option>)}
        </select>

        {/* Semester Filter */}
        <select
          className="form-select"
          value={semesterFilter}
          onChange={e => setSemesterFilter(e.target.value)}
          style={{ width: 'auto', minWidth: '130px', fontSize: '0.875rem' }}
        >
          <option value="">All Semesters</option>
          {SEMESTERS.map(s => <option key={s} value={s}>Semester {s}</option>)}
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

        <button className="btn btn-primary" onClick={() => loadStudents(1)} style={{ padding: '0.5rem 1rem', fontSize: '0.875rem' }}>
          <Search size={14} /> Search
        </button>
      </div>

      {/* Student Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden', width: '100%', boxSizing: 'border-box' }}>
        {loading ? (
          <div style={{ padding: '3.5rem', textAlign: 'center' }}>
            <div className="spinner" style={{ width: '28px', height: '28px', margin: '0 auto 0.75rem' }} />
            <p className="text-muted" style={{ margin: 0 }}>Loading students...</p>
          </div>
        ) : students.length === 0 ? (
          <div style={{ padding: '3.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            <GraduationCap size={36} style={{ margin: '0 auto 0.75rem', opacity: 0.4, display: 'block' }} />
            <p style={{ margin: 0 }}>No students found matching your search or filters.</p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto', width: '100%' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', backgroundColor: 'var(--surface-subtle)' }}>
                  <th style={{ ...thStyle, width: '22%' }}>Name</th>
                  <th style={{ ...thStyle, width: '18%' }}>Enrollment No</th>
                  <th style={{ ...thStyle, width: '22%' }}>Email</th>
                  <th style={{ ...thStyle, width: '10%' }}>Branch</th>
                  <th style={{ ...thStyle, width: '10%' }}>Semester</th>
                  <th style={{ ...thStyle, width: '8%' }}>Status</th>
                  <th style={{ ...thStyle, width: '10%', textAlign: 'center' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {students.map(stu => (
                  <tr key={stu.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td style={tdStyle}>
                      <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>{stu.name}</div>
                      {stu.phone && <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{stu.phone}</div>}
                    </td>
                    <td style={tdStyle}>
                      <span style={{ fontSize: '0.825rem', fontFamily: 'monospace', fontWeight: 600 }}>
                        {stu.enrollment_no || '–'}
                      </span>
                    </td>
                    <td style={tdStyle}>
                      <span style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>{stu.email}</span>
                    </td>
                    <td style={tdStyle}>
                      <span className="badge badge-accent" style={{ fontSize: '0.75rem' }}>
                        {stu.branch || '–'}
                      </span>
                    </td>
                    <td style={tdStyle}>
                      {stu.semester ? `Sem ${stu.semester}` : '–'}
                    </td>
                    <td style={tdStyle}>
                      <span
                        className={`badge ${stu.is_verified ? 'badge-primary' : 'badge-danger'}`}
                        style={{ fontSize: '0.725rem' }}
                      >
                        {stu.is_verified ? 'Active' : 'Deactivated'}
                      </span>
                    </td>
                    <td style={{ ...tdStyle, textAlign: 'center' }}>
                      <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.45rem', justifyContent: 'center' }}>
                        {/* Edit */}
                        <div className="admin-action-btn-wrap">
                          <button
                            type="button"
                            className="admin-action-icon-btn edit"
                            onClick={() => handleOpenEdit(stu)}
                            aria-label="Edit student"
                            title="Edit Student"
                          >
                            <Edit3 size={15} />
                          </button>
                          <span className="admin-action-tooltip">Edit Student</span>
                        </div>

                        {/* Reset Password */}
                        <div className="admin-action-btn-wrap">
                          <button
                            type="button"
                            className="admin-action-icon-btn reset"
                            onClick={() => setResetTarget(stu)}
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
                            className={`admin-action-icon-btn ${stu.is_verified ? 'deactivate' : 'activate'}`}
                            onClick={() => { setStatusTarget(stu); setStatusError(''); }}
                            aria-label={stu.is_verified ? 'Deactivate student' : 'Activate student'}
                            title={stu.is_verified ? 'Deactivate Student' : 'Activate Student'}
                          >
                            <Power size={14} />
                          </button>
                          <span className="admin-action-tooltip">{stu.is_verified ? 'Deactivate Student' : 'Activate Student'}</span>
                        </div>

                        {/* Delete */}
                        <div className="admin-action-btn-wrap">
                          <button
                            type="button"
                            className="admin-action-icon-btn delete"
                            onClick={() => setDeleteTarget(stu)}
                            aria-label="Delete student"
                            title="Delete Student"
                          >
                            <Trash2 size={15} />
                          </button>
                          <span className="admin-action-tooltip">Delete Student</span>
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
              <button className="btn btn-outline" disabled={page <= 1} onClick={() => loadStudents(page - 1)} style={{ padding: '0.35rem 0.85rem', fontSize: '0.8rem' }}>Previous</button>
              <button className="btn btn-outline" disabled={page >= totalPages} onClick={() => loadStudents(page + 1)} style={{ padding: '0.35rem 0.85rem', fontSize: '0.8rem' }}>Next</button>
            </div>
          </div>
        )}
      </div>

      {/* ── Create Student Modal ── */}
      {showCreate && (
        <div style={overlayStyle} onClick={() => setShowCreate(false)}>
          <div className="card glass-panel" style={{ maxWidth: '540px', width: '100%', padding: '2rem', maxHeight: '88vh', overflowY: 'auto' }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <div style={{ width: '34px', height: '34px', borderRadius: 'var(--radius-md)', background: 'var(--primary-light)', color: 'var(--primary-color)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <GraduationCap size={18} />
                </div>
                <h3 style={{ fontWeight: 700, margin: 0, fontSize: '1.2rem' }}>Create Student</h3>
              </div>
              <button type="button" onClick={() => setShowCreate(false)} style={{ color: 'var(--text-muted)', cursor: 'pointer', padding: '0.25rem', background: 'none', border: 'none' }}><X size={20} /></button>
            </div>

            {createError && (
              <div className="alert alert-danger" style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <AlertCircle size={16} /> {createError}
              </div>
            )}

            <form onSubmit={handleCreate}>
              <div className="form-group"><label className="form-label">Full Name *</label><input type="text" className="form-input" required placeholder="e.g. Rahul Sharma" value={createForm.name} onChange={e => setCreateForm({ ...createForm, name: e.target.value })} /></div>
              <div className="form-group"><label className="form-label">Email Address *</label><input type="email" className="form-input" required placeholder="rahul@example.com" value={createForm.email} onChange={e => setCreateForm({ ...createForm, email: e.target.value })} /></div>
              <div className="form-group"><label className="form-label">Phone Number</label><input type="tel" className="form-input" placeholder="9876543210" value={createForm.phone} onChange={e => setCreateForm({ ...createForm, phone: e.target.value })} /></div>

              <div style={{ padding: '1rem', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', marginBottom: '1.25rem', background: 'var(--surface-subtle)' }}>
                <h4 style={{ fontSize: '0.875rem', fontWeight: 700, marginBottom: '0.75rem', color: 'var(--primary-color)' }}>Academic Details</h4>
                <div className="form-group"><label className="form-label">Enrollment Number</label><input type="text" className="form-input" placeholder="e.g. 0101IT211045" value={createForm.enrollment_no} onChange={e => setCreateForm({ ...createForm, enrollment_no: e.target.value })} /></div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                  <div className="form-group"><label className="form-label">Branch</label>
                    <select className="form-select" value={createForm.branch} onChange={e => setCreateForm({ ...createForm, branch: e.target.value })}>
                      {BRANCHES.map(b => <option key={b} value={b}>{b}</option>)}
                    </select>
                  </div>
                  <div className="form-group"><label className="form-label">Semester</label>
                    <select className="form-select" value={createForm.semester} onChange={e => setCreateForm({ ...createForm, semester: parseInt(e.target.value) })}>
                      {SEMESTERS.map(s => <option key={s} value={s}>Semester {s}</option>)}
                    </select>
                  </div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                  <div className="form-group" style={{ marginBottom: 0 }}><label className="form-label">Section</label><input type="text" className="form-input" placeholder="e.g. IT-4I1" value={createForm.section} onChange={e => setCreateForm({ ...createForm, section: e.target.value })} /></div>
                  <div className="form-group" style={{ marginBottom: 0 }}><label className="form-label">Session</label><input type="text" className="form-input" placeholder="e.g. 2024-2028" value={createForm.session} onChange={e => setCreateForm({ ...createForm, session: e.target.value })} /></div>
                </div>
              </div>

              <div style={{ padding: '0.75rem', borderRadius: 'var(--radius-md)', background: 'var(--primary-light)', marginBottom: '1.25rem', fontSize: '0.825rem', color: 'var(--primary-color)' }}>
                <strong>Note:</strong> Default password will be assigned. The student must change it on their first login.
              </div>

              <button type="submit" className="btn btn-primary w-full" disabled={createLoading} style={{ padding: '0.75rem', fontWeight: 600 }}>
                {createLoading ? (<><div className="spinner spinner-white" style={{ width: '16px', height: '16px' }} /> Creating...</>) : (<><UserPlus size={16} /> Create Student</>)}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* ── Edit Student Modal ── */}
      {editTarget && (
        <div style={overlayStyle} onClick={() => setEditTarget(null)}>
          <div className="card glass-panel" style={{ maxWidth: '540px', width: '100%', padding: '2rem', maxHeight: '88vh', overflowY: 'auto' }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <div style={{ width: '34px', height: '34px', borderRadius: 'var(--radius-md)', background: 'var(--primary-light)', color: 'var(--primary-color)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Edit3 size={17} />
                </div>
                <h3 style={{ fontWeight: 700, margin: 0, fontSize: '1.2rem' }}>Edit Student</h3>
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
              <div className="form-group"><label className="form-label">Phone</label><input type="tel" className="form-input" value={editForm.phone} onChange={e => setEditForm({ ...editForm, phone: e.target.value })} /></div>

              <div style={{ padding: '1rem', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', marginBottom: '1.25rem', background: 'var(--surface-subtle)' }}>
                <h4 style={{ fontSize: '0.875rem', fontWeight: 700, marginBottom: '0.75rem', color: 'var(--primary-color)' }}>Academic Details</h4>
                <div className="form-group"><label className="form-label">Enrollment Number</label><input type="text" className="form-input" value={editForm.enrollment_no} onChange={e => setEditForm({ ...editForm, enrollment_no: e.target.value })} /></div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                  <div className="form-group"><label className="form-label">Branch</label>
                    <select className="form-select" value={editForm.branch} onChange={e => setEditForm({ ...editForm, branch: e.target.value })}>
                      {BRANCHES.map(b => <option key={b} value={b}>{b}</option>)}
                    </select>
                  </div>
                  <div className="form-group"><label className="form-label">Semester</label>
                    <select className="form-select" value={editForm.semester} onChange={e => setEditForm({ ...editForm, semester: e.target.value })}>
                      {SEMESTERS.map(s => <option key={s} value={s}>Semester {s}</option>)}
                    </select>
                  </div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                  <div className="form-group" style={{ marginBottom: 0 }}><label className="form-label">Section</label><input type="text" className="form-input" value={editForm.section} onChange={e => setEditForm({ ...editForm, section: e.target.value })} /></div>
                  <div className="form-group" style={{ marginBottom: 0 }}><label className="form-label">Session</label><input type="text" className="form-input" value={editForm.session} onChange={e => setEditForm({ ...editForm, session: e.target.value })} /></div>
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
                Are you sure you want to reset the password for student <strong style={{ color: 'var(--text-main)' }}>{resetTarget.name}</strong> ({resetTarget.email})?
              </p>
              <p className="text-muted" style={{ fontSize: '0.825rem' }}>
                The password will be reset to default. They will be forced to change it upon next login.
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
                {statusTarget.is_verified ? 'Deactivate Student Account' : 'Activate Student Account'}
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
              <h3 style={{ fontWeight: 700, marginBottom: '0.5rem' }}>Delete Student Account</h3>
              <p className="text-muted" style={{ fontSize: '0.9rem' }}>
                Are you sure you want to permanently delete <strong style={{ color: 'var(--text-main)' }}>{deleteTarget.name}</strong> ({deleteTarget.email})?
              </p>
              <p style={{ fontSize: '0.8rem', color: 'var(--danger-color)', marginTop: '0.5rem', fontWeight: 500 }}>
                All student records and active sessions will be permanently purged. This action cannot be undone.
              </p>
            </div>
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button className="btn btn-outline" style={{ flex: 1, padding: '0.65rem' }} onClick={() => setDeleteTarget(null)}>Cancel</button>
              <button className="btn btn-danger" style={{ flex: 1, padding: '0.65rem' }} onClick={handleDelete} disabled={deleteLoading}>
                {deleteLoading ? (<><div className="spinner spinner-white" style={{ width: '14px', height: '14px' }} /> Deleting...</>) : (<><Trash2 size={14} /> Delete Student</>)}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
