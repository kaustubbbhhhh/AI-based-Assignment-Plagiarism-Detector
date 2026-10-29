import React, { useState, useMemo, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../utils/api';
import { Plus, Trash2, Save, CheckCircle2, AlertCircle } from 'lucide-react';

const BRANCH_DATA = {
  IT: {
    name: 'Information Technology',
    sections: ['IT-4I1', 'IT-4I2', 'IT-4I3', 'IT-4I4', 'IT-4I5', 'IT-4I6', 'IT-4I7', 'IT-4I8', 'IT-4I9'],
    subjects: [
      'Database Management Systems',
      'Theory of Computation',
      'Probability, Statistics and Linear Programming',
      'Circuits and Systems',
      'Programming in Java',
    ],
  },
  CSE: {
    name: 'Computer Science & Engineering',
    sections: ['CSE-A', 'CSE-B', 'CSE-C', 'CSE-D'],
    subjects: [
      'Operating Systems',
      'Computer Networks',
      'Software Engineering',
      'Design and Analysis of Algorithm',
      'Compiler Design',
      'Data Structures',
      'AI & ML',
    ],
  },
  ECE: {
    name: 'Electronics & Communication',
    sections: ['ECE-A', 'ECE-B', 'ECE-C', 'ECE-D'],
    subjects: [
      'Digital Electronics',
      'Signals & Systems',
      'Microprocessors',
      'VLSI Design',
      'Embedded Systems',
    ],
  },
  EE: {
    name: 'Electrical Engineering',
    sections: ['EE-A', 'EE-B', 'EE-C', 'EE-D'],
    subjects: [
      'Power Systems',
      'Control Systems',
      'Electrical Machines',
      'Power Electronics',
      'Circuit Theory',
    ],
  },
  ME: {
    name: 'Mechanical Engineering',
    sections: ['ME-A', 'ME-B', 'ME-C', 'ME-D'],
    subjects: [
      'Thermodynamics',
      'Fluid Mechanics',
      'Manufacturing',
      'Machine Design',
      'Heat Transfer',
    ],
  },
};

export default function TeacherSubjectsPage() {
  const { user: authUser, refreshUser } = useAuth();
  const [currentUser, setCurrentUser] = useState(() => authUser || {});

  useEffect(() => {
    if (authUser) setCurrentUser(authUser);
  }, [authUser]);

  const [editingSubjects, setEditingSubjects] = useState(() => currentUser.subjects_sections || []);

  const [manageBranch, setManageBranch] = useState(() => {
    const userBranch = currentUser.branch || currentUser.department;
    return userBranch && BRANCH_DATA[userBranch] ? userBranch : 'IT';
  });

  const [manageSemester, setManageSemester] = useState(4);
  const [dbSubjects, setDbSubjects] = useState([]);
  const [loadingSubjects, setLoadingSubjects] = useState(false);

  // Dynamic fetch of subjects from database
  useEffect(() => {
    let isMounted = true;
    const fetchDbSubjects = async () => {
      setLoadingSubjects(true);
      try {
        const res = await api.get(`/api/subjects?branch=${manageBranch}&semester=${manageSemester}`);
        if (res.ok && isMounted) {
          const data = await res.json();
          setDbSubjects(data.items || []);
        }
      } catch {
        // Fallback to static data on error
      } finally {
        if (isMounted) setLoadingSubjects(false);
      }
    };
    fetchDbSubjects();
    return () => {
      isMounted = false;
    };
  }, [manageBranch, manageSemester]);

  const availableSections = useMemo(() => {
    return BRANCH_DATA[manageBranch]?.sections || [];
  }, [manageBranch]);

  const availableSubjects = useMemo(() => {
    if (dbSubjects.length > 0) {
      return [...dbSubjects.map((s) => s.subject_name), 'Other'];
    }
    return [...(BRANCH_DATA[manageBranch]?.subjects || []), 'Other'];
  }, [dbSubjects, manageBranch]);

  const [manageSection, setManageSection] = useState(() => availableSections[0] || '');
  const [manageSubject, setManageSubject] = useState(() => availableSubjects[0] || '');
  const [customSubjectText, setCustomSubjectText] = useState('');
  const [savingSubjects, setSavingSubjects] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState('');
  const [saveError, setSaveError] = useState('');

  useEffect(() => {
    if (availableSubjects.length > 0 && !availableSubjects.includes(manageSubject)) {
      setManageSubject(availableSubjects[0]);
    }
  }, [availableSubjects, manageSubject]);

  const handleBranchChange = (newBranch) => {
    setManageBranch(newBranch);
    const secs = BRANCH_DATA[newBranch]?.sections || [];
    setManageSection(secs[0] || '');
    setCustomSubjectText('');
  };

  useEffect(() => {
    if (currentUser && currentUser.subjects_sections) {
      setEditingSubjects(currentUser.subjects_sections);
    }
  }, [currentUser]);

  const handleAddSubjectSection = () => {
    const finalSubject = manageSubject === 'Other' ? customSubjectText.trim() : manageSubject;

    if (!manageBranch || !manageSection || !finalSubject) {
      setSaveError('Please select a branch, section, and subject.');
      return;
    }

    const exists = editingSubjects.some(
      (ss) =>
        ss.subject.toLowerCase() === finalSubject.toLowerCase() &&
        ss.section.toLowerCase() === manageSection.toLowerCase()
    );

    if (exists) {
      setSaveError('This Subject and Section combination is already in your list.');
      return;
    }

    setEditingSubjects([
      ...editingSubjects,
      { subject: finalSubject, section: manageSection, branch: manageBranch },
    ]);

    if (manageSubject === 'Other') {
      setCustomSubjectText('');
    }
    setSaveError('');
    setSaveSuccess('');
  };

  const handleDeleteSubjectSection = (index) => {
    const updated = editingSubjects.filter((_, i) => i !== index);
    setEditingSubjects(updated);
    setSaveError('');
    setSaveSuccess('');
  };

  const handleSaveSubjects = async () => {
    setSavingSubjects(true);
    setSaveSuccess('');
    setSaveError('');
    try {
      const response = await api.put(
        '/api/auth/teacher/subjects',
        editingSubjects.map((s) => ({
          subject: s.subject,
          section: s.section,
          ...(s.branch ? { branch: s.branch } : {}),
        }))
      );

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to save subject assignments.');
      }

      const updatedUser = await response.json();
      setCurrentUser(updatedUser);
      if (refreshUser) refreshUser();
      setSaveSuccess('Subject and section assignments updated successfully!');
    } catch (err) {
      setSaveError(err.message || 'Failed to connect to backend.');
    } finally {
      setSavingSubjects(false);
    }
  };

  return (
    <>
      {/* Content Header */}
      <div className="teacher-content-header">
        <h2>Manage Subjects & Sections</h2>
        <p>Configure your course assignments and assigned class sections.</p>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        {/* Current Assignments List */}
        <div className="card md:col-span-2">
          <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '0.25rem' }}>Assigned Courses & Sections</h3>
              <p className="text-muted" style={{ fontSize: '0.875rem' }}>
                These mappings determine which classes appear in your portal for plagiarism monitoring.
              </p>
            </div>
          </div>

          {editingSubjects.length === 0 ? (
            <div
              style={{
                textAlign: 'center',
                padding: '3rem 1.5rem',
                border: '1.5px dashed var(--border-color)',
                borderRadius: 'var(--radius-lg)',
                backgroundColor: 'var(--surface-subtle)',
              }}
            >
              <p className="text-muted" style={{ marginBottom: '0.5rem', fontWeight: 600 }}>No courses assigned yet</p>
              <p style={{ fontSize: '0.85rem' }} className="text-muted">Use the form on the right to assign your first course and section.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
              {editingSubjects.map((ss, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.9rem 1.15rem',
                    backgroundColor: 'var(--surface-color)',
                    border: '1px solid var(--border-color)',
                    borderRadius: 'var(--radius-md)',
                    transition: 'var(--transition)',
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>{ss.subject}</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginTop: '0.15rem' }}>
                      <span style={{ fontSize: '0.825rem', color: 'var(--primary-color)', fontWeight: 600 }}>
                        Section: {ss.section}
                      </span>
                      {ss.branch && (
                        <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                          • Branch: {ss.branch}
                        </span>
                      )}
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleDeleteSubjectSection(idx)}
                    style={{
                      padding: '0.45rem',
                      color: 'var(--danger-color)',
                      backgroundColor: 'var(--danger-light)',
                      borderRadius: 'var(--radius-sm)',
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      cursor: 'pointer',
                      border: 'none',
                      transition: 'var(--transition)',
                    }}
                    title="Remove Mapping"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Save Button & Messages Bar */}
          <div
            style={{
              marginTop: '2rem',
              paddingTop: '1.5rem',
              borderTop: '1px solid var(--border-color)',
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem',
            }}
          >
            {saveSuccess && (
              <div className="alert alert-success">
                <CheckCircle2 size={18} style={{ flexShrink: 0 }} />
                <span>{saveSuccess}</span>
              </div>
            )}
            {saveError && (
              <div className="alert alert-danger">
                <AlertCircle size={18} style={{ flexShrink: 0 }} />
                <span>{saveError}</span>
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleSaveSubjects}
                disabled={savingSubjects}
              >
                {savingSubjects ? (
                  <>
                    <div className="spinner spinner-white" style={{ width: '16px', height: '16px' }}></div>
                    <span>Saving Assignments...</span>
                  </>
                ) : (
                  <div className="flex items-center gap-2">
                    <Save size={16} />
                    <span>Save Changes</span>
                  </div>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Form Card for Adding New Mappings: Branch -> Section -> Subject */}
        <div className="card md:col-span-1">
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '1.25rem' }}>Add Course Assignment</h3>

          {/* 1. Branch Dropdown */}
          <div className="form-group" style={{ marginBottom: '1rem' }}>
            <label className="form-label" style={{ fontWeight: 600, fontSize: '0.875rem' }}>
              1. Branch
            </label>
            <select
              className="form-select"
              value={manageBranch}
              onChange={(e) => handleBranchChange(e.target.value)}
            >
              {Object.keys(BRANCH_DATA).map((b) => (
                <option key={b} value={b}>
                  {b} — {BRANCH_DATA[b].name}
                </option>
              ))}
            </select>
          </div>

          {/* 2. Semester Dropdown */}
          <div className="form-group" style={{ marginBottom: '1rem' }}>
            <label className="form-label" style={{ fontWeight: 600, fontSize: '0.875rem' }}>
              2. Semester
            </label>
            <select
              className="form-select"
              value={manageSemester}
              onChange={(e) => setManageSemester(parseInt(e.target.value))}
            >
              {[1, 2, 3, 4, 5, 6, 7, 8].map((sem) => (
                <option key={sem} value={sem}>Semester {sem}</option>
              ))}
            </select>
          </div>

          {/* 3. Section Dropdown */}
          <div className="form-group" style={{ marginBottom: '1rem' }}>
            <label className="form-label" style={{ fontWeight: 600, fontSize: '0.875rem' }}>
              3. Section
            </label>
            <select
              className="form-select"
              value={manageSection}
              onChange={(e) => setManageSection(e.target.value)}
            >
              {availableSections.map((sec) => (
                <option key={sec} value={sec}>{sec}</option>
              ))}
            </select>
          </div>

          {/* 4. Subject Dropdown */}
          <div className="form-group" style={{ marginBottom: '1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
              <label className="form-label" style={{ fontWeight: 600, fontSize: '0.875rem', marginBottom: 0 }}>
                4. Subject
              </label>
              {loadingSubjects && (
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Loading...</span>
              )}
            </div>
            <select
              className="form-select"
              value={manageSubject}
              onChange={(e) => setManageSubject(e.target.value)}
            >
              {availableSubjects.map((sub) => (
                <option key={sub} value={sub}>{sub}</option>
              ))}
            </select>
          </div>

          {manageSubject === 'Other' && (
            <div className="form-group" style={{ marginBottom: '1.25rem' }}>
              <label className="form-label" style={{ fontWeight: 600, fontSize: '0.875rem' }}>
                Custom Subject Name *
              </label>
              <input
                type="text"
                className="form-input"
                placeholder="Enter subject name..."
                value={customSubjectText}
                onChange={(e) => setCustomSubjectText(e.target.value)}
                required
              />
            </div>
          )}

          <button
            type="button"
            className="btn btn-outline w-full"
            onClick={handleAddSubjectSection}
            style={{ marginTop: '0.5rem', width: '100%' }}
          >
            <Plus size={16} /> Add to List
          </button>
        </div>
      </div>
    </>
  );
}
