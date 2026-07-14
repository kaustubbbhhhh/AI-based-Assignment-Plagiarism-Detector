import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { User, BookOpen, GraduationCap, ArrowRight, Plus, X, CheckCircle2 } from 'lucide-react';

// ── Branch → Subjects mapping ────────────────────────────────
const BRANCH_SUBJECTS = {
  'IT': ['Database Management Systems', 'Theory of Computation', 'Probability, Statistics and Linear Programming', 'Circuits and Systems', 'Programming in Java'],
  'CSE': ['Operating Systems', 'Computer Networks', 'Software Engineering', 'Data Structures', 'AI & ML'],
  'ECE': ['Digital Electronics', 'Signals & Systems', 'Microprocessors', 'VLSI Design', 'Embedded Systems'],
  'EE': ['Power Systems', 'Control Systems', 'Electrical Machines', 'Power Electronics', 'Circuit Theory'],
  'ME': ['Thermodynamics', 'Fluid Mechanics', 'Manufacturing', 'Machine Design', 'Heat Transfer'],
};

// ── Branch → Sections mapping ────────────────────────────────
const BRANCH_SECTIONS = {
  'IT': ['4I1', '4I2', '4I3', '4I4', '4I5', '4I6', '4I7', '4I8', '4I9'],
  'CSE': ['A', 'B', 'C', 'D'],
  'ECE': ['A', 'B', 'C', 'D'],
  'EE': ['A', 'B', 'C', 'D'],
  'ME': ['A', 'B', 'C', 'D'],
};

const SECTIONS_FALLBACK = ['A', 'B', 'C', 'D'];
const SESSIONS = ['2022-2026', '2023-2027', '2024-2028', '2025-2029'];

export default function Register() {
  const navigate = useNavigate();
  const [role, setRole] = useState('student');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  // ── Shared fields ─────────────────────────────────────────
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [phone, setPhone] = useState('');

  // ── Student fields ────────────────────────────────────────
  const [enrollmentNo, setEnrollmentNo] = useState('');
  const [fatherPhone, setFatherPhone] = useState('');
  const [motherPhone, setMotherPhone] = useState('');
  const [branch, setBranch] = useState('');
  const [section, setSection] = useState('');
  const [session, setSession] = useState('');

  // ── Teacher fields ────────────────────────────────────────
  const [teacherId, setTeacherId] = useState('');
  const [teacherBranch, setTeacherBranch] = useState('');
  const [subjectsSections, setSubjectsSections] = useState([]);

  // ── HOD fields ────────────────────────────────────────────
  const [hodId, setHodId] = useState('');
  const [department, setDepartment] = useState('');

  // ── Teacher: Add subject-section pair ──────────────────────
  const addSubjectSection = () => {
    setSubjectsSections([...subjectsSections, { subject: '', section: '' }]);
  };

  const updateSubjectSection = (index, field, value) => {
    const updated = [...subjectsSections];
    updated[index][field] = value;
    setSubjectsSections(updated);
  };

  const removeSubjectSection = (index) => {
    setSubjectsSections(subjectsSections.filter((_, i) => i !== index));
  };

  // ── Submit ─────────────────────────────────────────────────
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const payload = { name, email, password, role, phone };

    if (role === 'student') {
      payload.enrollment_no = enrollmentNo;
      payload.father_phone = fatherPhone;
      payload.mother_phone = motherPhone;
      payload.branch = branch;
      payload.section = `${branch}-${section}`;
      payload.session = session;
    } else if (role === 'teacher') {
      payload.teacher_id = teacherId;
      payload.branch = teacherBranch;
      payload.subjects_sections = subjectsSections.filter(s => s.subject && s.section);
    } else if (role === 'hod') {
      payload.hod_id = hodId;
      payload.department = department;
      payload.branch = department;
    }

    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
      const response = await fetch(`${API_URL}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Registration failed');
      }

      setSuccess(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // ── Success Screen ─────────────────────────────────────────
  if (success) {
    return (
      <div className="flex items-center justify-center" style={{ minHeight: 'calc(100vh - 150px)' }}>
        <div className="card glass-panel" style={{ maxWidth: '480px', width: '100%', padding: '3rem', textAlign: 'center' }}>
          <CheckCircle2 size={64} style={{ color: 'var(--success-color)', marginBottom: '1.5rem', margin: '0 auto 1.5rem' }} />
          <h2 style={{ marginBottom: '0.5rem' }}>Registration Successful!</h2>
          <p className="text-muted" style={{ marginBottom: '2rem' }}>
            Your {role === 'student' ? 'Student' : role === 'teacher' ? 'Teacher' : 'HOD'} account has been created.
          </p>
          <button className="btn btn-primary w-full" onClick={() => navigate('/login')}>
            Go to Login <ArrowRight size={18} />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center p-4" style={{ minHeight: 'calc(100vh - 150px)', padding: '0 1rem' }}>
      <div className="card glass-panel w-full-mob" style={{ maxWidth: '650px', width: '100%', padding: '2.5rem' }}>
        <div className="text-center" style={{ marginBottom: '2rem' }}>
          <h2 style={{ marginBottom: '0.5rem' }}>Create Account</h2>
          <p className="text-muted">Register to start using the Plagiarism Detection System.</p>
        </div>

        <form onSubmit={handleSubmit}>

          {/* ── Role Selector ─────────────────────────────── */}
          <div className="form-group">
            <label className="form-label">I am a</label>
            <div className="grid grid-cols-3 gap-2" style={{ marginBottom: '1.5rem' }}>
              <RoleOption icon={<User size={20} />} label="Student" selected={role === 'student'} onClick={() => setRole('student')} />
              <RoleOption icon={<BookOpen size={20} />} label="Teacher" selected={role === 'teacher'} onClick={() => setRole('teacher')} />
              <RoleOption icon={<GraduationCap size={20} />} label="HOD" selected={role === 'hod'} onClick={() => setRole('hod')} />
            </div>
          </div>

          {error && (
            <div style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger-color)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', marginBottom: '1rem', fontSize: '0.875rem', textAlign: 'center' }}>
              {error}
            </div>
          )}

          {/* ── Common Fields ─────────────────────────────── */}
          <div className="form-group">
            <label className="form-label">Full Name *</label>
            <input type="text" className="form-input" placeholder="Enter your full name" required value={name} onChange={(e) => setName(e.target.value)} />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="form-group">
              <label className="form-label">
                {role === 'student' ? 'Enrollment No. *' : role === 'teacher' ? 'Teacher ID *' : 'HOD ID *'}
              </label>
              <input
                type="text"
                className="form-input"
                placeholder={role === 'student' ? 'e.g. 0901IT241001' : role === 'teacher' ? 'e.g. FAC-2024-01' : 'e.g. HOD-CSE-01'}
                required
                value={role === 'student' ? enrollmentNo : role === 'teacher' ? teacherId : hodId}
                onChange={(e) => {
                  if (role === 'student') setEnrollmentNo(e.target.value);
                  else if (role === 'teacher') setTeacherId(e.target.value);
                  else setHodId(e.target.value);
                }}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Phone Number *</label>
              <input type="tel" className="form-input" placeholder="+91 9876543210" required value={phone} onChange={(e) => setPhone(e.target.value)} />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="form-group">
              <label className="form-label">Email *</label>
              <input type="email" className="form-input" placeholder="name@institute.edu" required value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Password *</label>
              <input type="password" className="form-input" placeholder="Min 6 characters" required value={password} onChange={(e) => setPassword(e.target.value)} />
            </div>
          </div>

          {/* ══════════════════════════════════════════════════
                          STUDENT FIELDS
             ══════════════════════════════════════════════════ */}
          {role === 'student' && (
            <>
              <div style={{ borderTop: '1px solid var(--border-color)', margin: '1.5rem 0', paddingTop: '1.5rem' }}>
                <h4 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem', color: 'var(--primary-color)' }}>Academic Details</h4>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="form-group">
                  <label className="form-label">Father's Phone</label>
                  <input type="tel" className="form-input" placeholder="+91 ..." value={fatherPhone} onChange={(e) => setFatherPhone(e.target.value)} />
                </div>
                <div className="form-group">
                  <label className="form-label">Mother's Phone</label>
                  <input type="tel" className="form-input" placeholder="+91 ..." value={motherPhone} onChange={(e) => setMotherPhone(e.target.value)} />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="form-group">
                  <label className="form-label">Branch *</label>
                  <select className="form-select" required value={branch} onChange={(e) => setBranch(e.target.value)}>
                    <option value="" disabled>Select</option>
                    {Object.keys(BRANCH_SUBJECTS).map(b => <option key={b} value={b}>{b}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Section *</label>
                  <select className="form-select" required value={section} onChange={(e) => setSection(e.target.value)}>
                    <option value="" disabled>Select</option>
                    {(BRANCH_SECTIONS[branch] || SECTIONS_FALLBACK).map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Session *</label>
                  <select className="form-select" required value={session} onChange={(e) => setSession(e.target.value)}>
                    <option value="" disabled>Select</option>
                    {SESSIONS.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
              </div>
            </>
          )}

          {/* ══════════════════════════════════════════════════
                          TEACHER FIELDS
             ══════════════════════════════════════════════════ */}
          {role === 'teacher' && (
            <>
              <div style={{ borderTop: '1px solid var(--border-color)', margin: '1.5rem 0', paddingTop: '1.5rem' }}>
                <h4 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem', color: 'var(--primary-color)' }}>Teaching Details</h4>
              </div>

              <div className="form-group">
                <label className="form-label">Branch You Teach *</label>
                <select className="form-select" required value={teacherBranch} onChange={(e) => { setTeacherBranch(e.target.value); setSubjectsSections([]); }}>
                  <option value="" disabled>Select branch first...</option>
                  {Object.keys(BRANCH_SUBJECTS).map(b => <option key={b} value={b}>{b}</option>)}
                </select>
              </div>

              {teacherBranch && (
                <div className="form-group">
                  <div className="flex items-center justify-between" style={{ marginBottom: '0.75rem' }}>
                    <label className="form-label" style={{ margin: 0 }}>Subjects & Sections</label>
                    <button type="button" onClick={addSubjectSection} className="btn btn-outline" style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem' }}>
                      <Plus size={14} /> Add Subject
                    </button>
                  </div>

                  {subjectsSections.length === 0 && (
                    <div style={{ padding: '2rem', textAlign: 'center', border: '2px dashed var(--border-color)', borderRadius: 'var(--radius-md)', color: 'var(--text-muted)' }}>
                      <p style={{ fontSize: '0.875rem', margin: 0 }}>Click "Add Subject" to assign subjects and sections</p>
                    </div>
                  )}

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {subjectsSections.map((item, idx) => (
                      <div key={idx} style={{
                        display: 'flex', flexWrap: 'wrap', gap: '0.75rem', alignItems: 'center',
                        padding: '0.75rem', border: '1px solid var(--border-color)',
                        borderRadius: 'var(--radius-md)', backgroundColor: 'var(--bg-color)'
                      }}>
                        <select
                          className="form-select"
                          value={item.subject}
                          onChange={(e) => updateSubjectSection(idx, 'subject', e.target.value)}
                          style={{ flex: '1 1 220px', minWidth: 0 }}
                          required
                        >
                          <option value="" disabled>Subject</option>
                          {BRANCH_SUBJECTS[teacherBranch]?.map(sub => (
                            <option key={sub} value={sub}>{sub}</option>
                          ))}
                        </select>

                        <select
                          className="form-select"
                          value={item.section}
                          onChange={(e) => updateSubjectSection(idx, 'section', e.target.value)}
                          style={{ flex: '1 1 220px', minWidth: 0 }}
                          required
                        >
                          <option value="" disabled>Section</option>
                          {(BRANCH_SECTIONS[teacherBranch] || SECTIONS_FALLBACK).map(s => (
                            <option key={s} value={s}>{teacherBranch}-{s}</option>
                          ))}
                        </select>

                        <button
                          type="button"
                          onClick={() => removeSubjectSection(idx)}
                          style={{ background: 'none', color: 'var(--danger-color)', padding: '0.25rem', cursor: 'pointer', flexShrink: 0 }}
                        >
                          <X size={18} />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {/* ══════════════════════════════════════════════════
                          HOD FIELDS
             ══════════════════════════════════════════════════ */}
          {role === 'hod' && (
            <>
              <div style={{ borderTop: '1px solid var(--border-color)', margin: '1.5rem 0', paddingTop: '1.5rem' }}>
                <h4 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem', color: 'var(--primary-color)' }}>Department Details</h4>
              </div>

              <div className="form-group">
                <label className="form-label">Department *</label>
                <select className="form-select" required value={department} onChange={(e) => setDepartment(e.target.value)}>
                  <option value="" disabled>Select department</option>
                  {Object.keys(BRANCH_SUBJECTS).map(b => <option key={b} value={b}>{b}</option>)}
                </select>
              </div>
            </>
          )}

          {/* ── Submit Button ─────────────────────────────── */}
          <button type="submit" className="btn btn-primary w-full" disabled={loading} style={{ marginTop: '1.5rem', padding: '0.875rem' }}>
            {loading ? (
              <div className="spinner" style={{ width: '20px', height: '20px' }}></div>
            ) : (
              <div className="flex items-center gap-2">Create Account <ArrowRight size={18} /></div>
            )}
          </button>

          <p className="text-center text-muted" style={{ marginTop: '1.5rem', fontSize: '0.875rem' }}>
            Already have an account? <Link to="/login" style={{ color: 'var(--primary-color)', fontWeight: 600 }}>Login here</Link>
          </p>
        </form>
      </div>
    </div>
  );
}


function RoleOption({ icon, label, selected, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      style={{
        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem', padding: '1rem 0.5rem',
        border: `2px solid ${selected ? 'var(--primary-color)' : 'var(--border-color)'}`,
        backgroundColor: selected ? 'rgba(79, 70, 229, 0.05)' : 'var(--bg-color)',
        borderRadius: 'var(--radius-md)', color: selected ? 'var(--primary-color)' : 'var(--text-muted)',
        transition: 'all 0.2s', cursor: 'pointer'
      }}
    >
      {icon}
      <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>{label}</span>
    </button>
  );
}
