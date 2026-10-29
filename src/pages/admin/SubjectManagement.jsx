import React, { useState, useEffect, useCallback } from 'react';
import {
  BookOpen,
  Plus,
  Edit3,
  Trash2,
  X,
  AlertCircle,
  CheckCircle2,
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

export default function SubjectManagement() {
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [branch, setBranch] = useState('IT');
  const [semester, setSemester] = useState(4);

  // Alerts
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Add Subject Form
  const [newCode, setNewCode] = useState('');
  const [newName, setNewName] = useState('');
  const [addLoading, setAddLoading] = useState(false);

  // Edit Subject Modal
  const [editingSubject, setEditingSubject] = useState(null);
  const [editForm, setEditForm] = useState({ subject_code: '', subject_name: '' });
  const [editLoading, setEditLoading] = useState(false);

  const loadSubjects = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get(`/api/admin/subjects?branch=${branch}&semester=${semester}`);
      if (res.ok) {
        const data = await res.json();
        setSubjects(data.items);
      } else {
        const err = await res.json();
        setError(err.detail || 'Failed to load subjects.');
      }
    } catch {
      setError('Failed to connect to server.');
    }
    setLoading(false);
  }, [branch, semester]);

  useEffect(() => {
    let ignore = false;
    const fetchInitial = async () => {
      try {
        const res = await api.get(`/api/admin/subjects?branch=${branch}&semester=${semester}`);
        if (!ignore) {
          if (res.ok) {
            const data = await res.json();
            setSubjects(data.items);
          } else {
            const err = await res.json();
            setError(err.detail || 'Failed to load subjects.');
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
  }, [branch, semester]);

  const handleAddSubject = async (e) => {
    e.preventDefault();
    setAddLoading(true);
    setError('');
    try {
      const res = await api.post('/api/admin/subjects', {
        subject_code: newCode.trim(),
        subject_name: newName.trim(),
        branch,
        semester,
      });
      if (res.ok) {
        setNewCode('');
        setNewName('');
        setSuccess(`Subject '${newCode.trim()}' added successfully.`);
        loadSubjects();
        setTimeout(() => setSuccess(''), 4000);
      } else {
        const err = await res.json();
        setError(err.detail || 'Failed to add subject.');
      }
    } catch {
      setError('Failed to connect to server.');
    }
    setAddLoading(false);
  };

  const handleOpenEdit = (sub) => {
    setEditingSubject(sub);
    setEditForm({
      subject_code: sub.subject_code,
      subject_name: sub.subject_name,
    });
  };

  const handleSaveEdit = async (e) => {
    e.preventDefault();
    if (!editingSubject) return;
    setEditLoading(true);
    try {
      const res = await api.put(`/api/admin/subjects/${editingSubject.id}`, {
        subject_code: editForm.subject_code.trim(),
        subject_name: editForm.subject_name.trim(),
      });
      if (res.ok) {
        setEditingSubject(null);
        setSuccess('Subject updated successfully.');
        loadSubjects();
        setTimeout(() => setSuccess(''), 4000);
      } else {
        const err = await res.json();
        setError(err.detail || 'Failed to update subject.');
      }
    } catch {
      setError('Failed to connect to server.');
    }
    setEditLoading(false);
  };

  const handleDeactivate = async (sub) => {
    if (!window.confirm(`Deactivate '${sub.subject_code} - ${sub.subject_name}'? It will no longer appear in teacher selection.`)) return;
    try {
      const res = await api.delete(`/api/admin/subjects/${sub.id}`);
      if (res.ok) {
        setSuccess(`Subject '${sub.subject_code}' deactivated.`);
        loadSubjects();
        setTimeout(() => setSuccess(''), 4000);
      } else {
        const err = await res.json();
        setError(err.detail || 'Failed to deactivate subject.');
      }
    } catch {
      setError('Failed to connect to server.');
    }
  };

  return (
    <div style={{ width: '100%' }}>
      {/* Header */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.65rem', fontWeight: 800, margin: '0 0 0.25rem 0' }}>Subject Management</h2>
        <p className="text-muted" style={{ margin: 0, fontSize: '0.9rem' }}>
          Configure curriculum subjects for each branch and semester. These appear in teacher class assignment dropdowns.
        </p>
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

      {/* Main Grid: Subjects Table + Add Subject Card */}
      <div className="grid" style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '1.5rem', alignItems: 'start' }}>
        {/* Left Column: Selector & Table */}
        <div>
          {/* Branch & Semester Selection Bar */}
          <div className="card" style={{ padding: '1rem 1.25rem', marginBottom: '1.25rem', display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <div className="form-group" style={{ marginBottom: 0, flex: '0 0 auto' }}>
              <label className="form-label" style={{ fontSize: '0.8rem', marginBottom: '0.25rem' }}>Branch</label>
              <select className="form-select" value={branch} onChange={e => setBranch(e.target.value)} style={{ minWidth: '130px' }}>
                {BRANCHES.map(b => <option key={b} value={b}>{b}</option>)}
              </select>
            </div>
            <div className="form-group" style={{ marginBottom: 0, flex: '0 0 auto' }}>
              <label className="form-label" style={{ fontSize: '0.8rem', marginBottom: '0.25rem' }}>Semester</label>
              <select className="form-select" value={semester} onChange={e => setSemester(parseInt(e.target.value))} style={{ minWidth: '130px' }}>
                {SEMESTERS.map(s => <option key={s} value={s}>Semester {s}</option>)}
              </select>
            </div>
          </div>

          {/* Subjects Table Card */}
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            {loading ? (
              <div style={{ padding: '3.5rem', textAlign: 'center' }}>
                <div className="spinner" style={{ width: '28px', height: '28px', margin: '0 auto 0.75rem' }} />
                <p className="text-muted" style={{ margin: 0 }}>Loading subjects...</p>
              </div>
            ) : subjects.length === 0 ? (
              <div style={{ padding: '3.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                <BookOpen size={36} style={{ margin: '0 auto 0.75rem', opacity: 0.4, display: 'block' }} />
                <p style={{ margin: 0 }}>No subjects configured for {branch} Semester {semester}.</p>
              </div>
            ) : (
              <div style={{ overflowX: 'auto', width: '100%' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border-color)', backgroundColor: 'var(--surface-subtle)' }}>
                      <th style={{ ...thStyle, width: '25%' }}>Subject Code</th>
                      <th style={{ ...thStyle, width: '45%' }}>Subject Name</th>
                      <th style={{ ...thStyle, width: '15%' }}>Status</th>
                      <th style={{ ...thStyle, width: '15%', textAlign: 'center' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {subjects.map(s => (
                      <tr key={s.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                        <td style={tdStyle}>
                          <span style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: '0.85rem' }}>{s.subject_code}</span>
                        </td>
                        <td style={tdStyle}>{s.subject_name}</td>
                        <td style={tdStyle}>
                          <span className={`badge ${s.status === 'active' ? 'badge-primary' : 'badge-danger'}`} style={{ textTransform: 'capitalize', fontSize: '0.75rem' }}>
                            {s.status}
                          </span>
                        </td>
                        <td style={{ ...tdStyle, textAlign: 'center' }}>
                          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.45rem', justifyContent: 'center' }}>
                            <div className="admin-action-btn-wrap">
                              <button
                                type="button"
                                className="admin-action-icon-btn edit"
                                onClick={() => handleOpenEdit(s)}
                                aria-label="Edit subject"
                                title="Edit Subject"
                              >
                                <Edit3 size={15} />
                              </button>
                              <span className="admin-action-tooltip">Edit Subject</span>
                            </div>

                            {s.status === 'active' && (
                              <div className="admin-action-btn-wrap">
                                <button
                                  type="button"
                                  className="admin-action-icon-btn delete"
                                  onClick={() => handleDeactivate(s)}
                                  aria-label="Deactivate subject"
                                  title="Deactivate Subject"
                                >
                                  <Trash2 size={15} />
                                </button>
                                <span className="admin-action-tooltip">Deactivate Subject</span>
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Add Subject Sticky Card */}
        <div className="card" style={{ padding: '1.5rem', position: 'sticky', top: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '1.25rem' }}>
            <div style={{ width: '32px', height: '32px', borderRadius: 'var(--radius-md)', background: 'rgba(139, 92, 246, 0.1)', color: '#8b5cf6', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Plus size={18} />
            </div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, margin: 0 }}>Add Subject</h3>
          </div>
          <p className="text-muted" style={{ fontSize: '0.8rem', marginBottom: '1.25rem' }}>
            Adding to <strong>{branch}</strong> &mdash; <strong>Semester {semester}</strong>
          </p>
          <form onSubmit={handleAddSubject}>
            <div className="form-group">
              <label className="form-label" style={{ fontSize: '0.825rem' }}>Subject Code *</label>
              <input
                type="text"
                className="form-input"
                required
                placeholder="e.g. CIC-201"
                value={newCode}
                onChange={e => setNewCode(e.target.value)}
                style={{ fontSize: '0.875rem' }}
              />
            </div>
            <div className="form-group">
              <label className="form-label" style={{ fontSize: '0.825rem' }}>Subject Name *</label>
              <input
                type="text"
                className="form-input"
                required
                placeholder="e.g. Database Management Systems"
                value={newName}
                onChange={e => setNewName(e.target.value)}
                style={{ fontSize: '0.875rem' }}
              />
            </div>
            <button
              type="submit"
              className="btn btn-primary w-full"
              disabled={addLoading}
              style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', padding: '0.65rem' }}
            >
              {addLoading ? <div className="spinner spinner-white" style={{ width: '16px', height: '16px' }} /> : <><Plus size={16} /> Add Subject</>}
            </button>
          </form>
        </div>
      </div>

      {/* ── Edit Subject Modal ── */}
      {editingSubject && (
        <div style={overlayStyle} onClick={() => setEditingSubject(null)}>
          <div className="card glass-panel" style={{ maxWidth: '440px', width: '100%', padding: '2rem' }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
              <h3 style={{ fontWeight: 700, margin: 0, fontSize: '1.15rem' }}>Edit Subject</h3>
              <button type="button" onClick={() => setEditingSubject(null)} style={{ color: 'var(--text-muted)', cursor: 'pointer', padding: '0.25rem', background: 'none', border: 'none' }}><X size={20} /></button>
            </div>
            <form onSubmit={handleSaveEdit}>
              <div className="form-group">
                <label className="form-label">Subject Code *</label>
                <input
                  type="text"
                  className="form-input"
                  required
                  value={editForm.subject_code}
                  onChange={e => setEditForm({ ...editForm, subject_code: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Subject Name *</label>
                <input
                  type="text"
                  className="form-input"
                  required
                  value={editForm.subject_name}
                  onChange={e => setEditForm({ ...editForm, subject_name: e.target.value })}
                />
              </div>
              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.25rem' }}>
                <button type="button" className="btn btn-outline" style={{ flex: 1, padding: '0.65rem' }} onClick={() => setEditingSubject(null)}>Cancel</button>
                <button type="submit" className="btn btn-primary" style={{ flex: 1, padding: '0.65rem' }} disabled={editLoading}>
                  {editLoading ? <div className="spinner spinner-white" style={{ width: '16px', height: '16px' }} /> : <><Save size={15} /> Save Changes</>}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
