import React, { useState, useMemo } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { Search, X, Download, FileText, Settings, Plus, Trash2, Save } from 'lucide-react';

export default function TeacherPortal() {
  // ── Stateful User profile for immediate dynamic updates ──────
  const [currentUser, setCurrentUser] = useState(() => JSON.parse(localStorage.getItem('user') || '{}'));
  const teacherSubjectsSections = useMemo(() => currentUser.subjects_sections || [], [currentUser.subjects_sections]);

  // ── State for active tab ─────────────────────────────────────
  const [activeTab, setActiveTab] = useState('dashboard'); // 'dashboard' | 'subjects'

  const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

  // ── Derive unique sections and subjects from teacher's registered data ──
  const uniqueSections = useMemo(() => {
    const secs = [...new Set(teacherSubjectsSections.map(ss => ss.section))];
    return secs.length > 0 ? secs : ['No sections assigned'];
  }, [teacherSubjectsSections]);

  const uniqueSubjects = useMemo(() => {
    const subs = [...new Set(teacherSubjectsSections.map(ss => ss.subject))];
    return subs.length > 0 ? subs : ['No subjects assigned'];
  }, [teacherSubjectsSections]);

  // ── State ────────────────────────────────────────────────────
  const [section, setSection] = useState(uniqueSections[0]);
  const [subject, setSubject] = useState(uniqueSubjects[0]);

  // ── Reset filter selections if they are no longer in the assigned list ──
  React.useEffect(() => {
    if (!uniqueSections.includes(section)) {
      setSection(uniqueSections[0]);
    }
  }, [uniqueSections, section]);

  React.useEffect(() => {
    if (!uniqueSubjects.includes(subject)) {
      setSubject(uniqueSubjects[0]);
    }
  }, [uniqueSubjects, subject]);

  // ── State for Subject Management ──────────────────────────────
  const [editingSubjects, setEditingSubjects] = useState(() => currentUser.subjects_sections || []);
  const [newSubjectText, setNewSubjectText] = useState('Compiler Design');
  const [customSubjectText, setCustomSubjectText] = useState('');
  const [newSectionText, setNewSectionText] = useState('');
  const [savingSubjects, setSavingSubjects] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState('');
  const [saveError, setSaveError] = useState('');

  // Sync editingSubjects if currentUser changes
  React.useEffect(() => {
    if (currentUser && currentUser.subjects_sections) {
      setEditingSubjects(currentUser.subjects_sections);
    }
  }, [currentUser]);

  // Predefined list of subjects mapped in the backend validator
  const PREDEFINED_SUBJECTS = [
    "Compiler Design",
    "Operating Systems",
    "Computer Networks",
    "Design and Analysis of Algorithm",
    "Software Engineering",
    "Economics for Engineers",
    "Database Management Systems",
    "Theory of Computation",
    "Programming in Java",
    "Probability, Statistics and Linear Programming",
    "Circuits and Systems",
    "Other"
  ];
  const [searchQuery, setSearchQuery] = useState('');
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // ── Modal State ──────────────────────────────────────────────
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedReportDetail, setSelectedReportDetail] = useState(null);
  const [modalLoading, setModalLoading] = useState(false);
  const [modalError, setModalError] = useState('');

  // ── Download Function ────────────────────────────────────────
  const handleDownload = async (submissionId, studentName) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/download/${submissionId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) throw new Error('Download failed');
      
      // Get filename from header or fallback
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `${studentName}_Assignment.docx`;
      if (contentDisposition && contentDisposition.includes('filename=')) {
        filename = contentDisposition.split('filename=')[1].replace(/"/g, '');
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
    } catch (err) {
      alert('Error downloading file: ' + err.message);
    }
  };

  // ── Fetch Detailed Report for Modal ──────────────────────────
  const handleViewReport = async (reportSummary) => {
    setIsModalOpen(true);
    setModalLoading(true);
    setModalError('');
    setSelectedReportDetail(null);
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/report/${reportSummary.submission_id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error('Failed to fetch detailed report');
      
      const data = await response.json();
      // Combine summary metadata with detailed report
      setSelectedReportDetail({ ...reportSummary, ...data });
    } catch (err) {
      setModalError(err.message);
    } finally {
      setModalLoading(false);
    }
  };

  // ── Fetch reports filtered by BOTH section and subject ──────
  const fetchReports = async (selectedSection, selectedSubject) => {
    setLoading(true);
    setError('');
    const token = localStorage.getItem('token');
    try {
      const url = `${API_URL}/api/reports/section/${encodeURIComponent(selectedSection)}?subject=${encodeURIComponent(selectedSubject)}`;
      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error('Failed to fetch section reports');
      const data = await response.json();
      setReports(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    if (section && subject && !section.startsWith('No ') && !subject.startsWith('No ')) {
      fetchReports(section, subject);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [section, subject, API_URL]);

  // ── Subject Management Handlers ──────────────────────────────
  const handleAddSubjectSection = () => {
    const finalSubject = newSubjectText === 'Other' ? customSubjectText.trim() : newSubjectText;
    
    if (!finalSubject || !newSectionText.trim()) {
      setSaveError('Please enter both a Subject name and a Section code.');
      return;
    }
    
    // Check if duplicate already exists
    const exists = editingSubjects.some(
      (ss) =>
        ss.subject.toLowerCase() === finalSubject.toLowerCase() &&
        ss.section.toLowerCase() === newSectionText.trim().toLowerCase()
    );
    
    if (exists) {
      setSaveError('This Subject and Section combination is already in your list.');
      return;
    }
    
    setEditingSubjects([
      ...editingSubjects,
      { subject: finalSubject, section: newSectionText.trim() }
    ]);
    
    if (newSubjectText === 'Other') {
      setCustomSubjectText('');
    }
    setNewSectionText('');
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
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/auth/teacher/subjects`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(editingSubjects)
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to save subject assignments.');
      }
      
      const updatedUser = await response.json();
      localStorage.setItem('user', JSON.stringify(updatedUser));
      setCurrentUser(updatedUser);
      setSaveSuccess('Subject and section assignments updated successfully!');
    } catch (err) {
      setSaveError(err.message || 'Failed to connect to backend.');
    } finally {
      setSavingSubjects(false);
    }
  };

  // Derive stats from real reports
  const stats = {
    original: reports.filter(r => r.plagiarism_score < 15).length,
    moderate: reports.filter(r => r.plagiarism_score >= 15 && r.plagiarism_score <= 30).length,
    high: reports.filter(r => r.plagiarism_score > 30).length
  };

  const pieData = [
    { name: 'Original Content', value: stats.original || 1, color: '#10b981' },
    { name: 'Moderate Match', value: stats.moderate || 0, color: '#f59e0b' },
    { name: 'High Plagiarism', value: stats.high || 0, color: '#ef4444' },
  ];

  const filteredStudents = reports.filter(report =>
    report.student_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    report.subject.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const hasNoResults = !loading && filteredStudents.length === 0;
  const noAssignments = teacherSubjectsSections.length === 0;

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 1rem' }}>
      <div className="teacher-header-row flex flex-col-mob md:flex-row md:items-center justify-between gap-4-mob" style={{ marginBottom: '2rem' }}>
        <div>
          <h2>Teacher Portal</h2>
          <p className="text-muted">
            {activeTab === 'dashboard'
              ? 'Review section-wise student assignments and plagiarism reports.'
              : 'Add, edit, or delete your subject-section mappings.'}
          </p>
        </div>
        {activeTab === 'dashboard' && (
          <div className="teacher-filter-row flex flex-col-mob md:flex-row md:items-center gap-2 w-full" style={{ flexWrap: 'wrap' }}>
            {/* ── Section Dropdown ──────────────────────────── */}
            <label className="form-label mb-0" style={{ margin: 0, marginRight: '0.5rem' }}>Section:</label>
            <select
              className="form-select w-full-mob"
              value={section}
              onChange={e => setSection(e.target.value)}
              style={{ minWidth: '150px', maxWidth: '220px' }}
            >
              {uniqueSections.map(sec => (
                <option key={sec} value={sec}>{sec}</option>
              ))}
            </select>

            {/* ── Subject Dropdown ──────────────────────────── */}
            <label className="form-label mb-0" style={{ margin: 0, marginLeft: '1rem', marginRight: '0.5rem' }}>Subject:</label>
            <select
              className="form-select w-full-mob"
              value={subject}
              onChange={e => setSubject(e.target.value)}
              style={{ minWidth: '180px', maxWidth: '320px' }}
            >
              {uniqueSubjects.map(sub => (
                <option key={sub} value={sub}>{sub}</option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* ── Tab Switcher ────────────────────────────────────────── */}
      <div style={{
        display: 'flex',
        gap: '0.75rem',
        borderBottom: '1px solid var(--border-color)',
        marginBottom: '2rem',
        paddingBottom: '0.75rem'
      }}>
        <button
          onClick={() => setActiveTab('dashboard')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.6rem 1.2rem',
            borderRadius: 'var(--radius-md)',
            fontWeight: 600,
            fontSize: '0.9rem',
            backgroundColor: activeTab === 'dashboard' ? 'var(--primary-color)' : 'transparent',
            color: activeTab === 'dashboard' ? '#ffffff' : 'var(--text-muted)',
            transition: 'var(--transition)'
          }}
          onMouseEnter={(e) => {
            if (activeTab !== 'dashboard') {
              e.currentTarget.style.backgroundColor = 'rgba(79, 70, 229, 0.05)';
              e.currentTarget.style.color = 'var(--primary-color)';
            }
          }}
          onMouseLeave={(e) => {
            if (activeTab !== 'dashboard') {
              e.currentTarget.style.backgroundColor = 'transparent';
              e.currentTarget.style.color = 'var(--text-muted)';
            }
          }}
        >
          Dashboard
        </button>
        <button
          onClick={() => setActiveTab('subjects')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.6rem 1.2rem',
            borderRadius: 'var(--radius-md)',
            fontWeight: 600,
            fontSize: '0.9rem',
            backgroundColor: activeTab === 'subjects' ? 'var(--primary-color)' : 'transparent',
            color: activeTab === 'subjects' ? '#ffffff' : 'var(--text-muted)',
            transition: 'var(--transition)'
          }}
          onMouseEnter={(e) => {
            if (activeTab !== 'subjects') {
              e.currentTarget.style.backgroundColor = 'rgba(79, 70, 229, 0.05)';
              e.currentTarget.style.color = 'var(--primary-color)';
            }
          }}
          onMouseLeave={(e) => {
            if (activeTab !== 'subjects') {
              e.currentTarget.style.backgroundColor = 'transparent';
              e.currentTarget.style.color = 'var(--text-muted)';
            }
          }}
        >
          <Settings size={16} />
          Manage Subjects
        </button>
      </div>

      {activeTab === 'dashboard' ? (
        <>
          {noAssignments && (
            <div
              style={{
                marginBottom: '1.25rem',
                backgroundColor: 'rgba(245, 158, 11, 0.08)',
                color: 'var(--warning-color, #f59e0b)',
                border: '1px solid rgba(245, 158, 11, 0.25)',
                borderRadius: 'var(--radius-md)',
                padding: '0.75rem 1rem',
                fontSize: '0.9rem',
                fontWeight: 500
              }}
            >
              No subjects or sections have been assigned to your profile. Please contact the administrator or update your registration.
            </div>
          )}

          {error && (
            <div
              style={{
                marginBottom: '1.25rem',
                backgroundColor: 'rgba(239, 68, 68, 0.08)',
                color: 'var(--danger-color)',
                border: '1px solid rgba(239, 68, 68, 0.25)',
                borderRadius: 'var(--radius-md)',
                padding: '0.75rem 1rem',
                fontSize: '0.9rem',
                fontWeight: 500
              }}
            >
              {error}
            </div>
          )}

          <div className="teacher-main-grid grid md:grid-cols-3 gap-6">

            {/* Statistics Overview Card */}
            <div className="card md:col-span-1">
              <h3 style={{ marginBottom: '1.5rem', fontSize: '1.25rem' }}>Section Statistics</h3>
              <div className="teacher-chart-shell">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="teacher-legend">
                {pieData.map((item) => (
                  <div key={item.name} className="teacher-legend-item">
                    <span className="teacher-legend-dot" style={{ backgroundColor: item.color }}></span>
                    <span>{item.name}</span>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: '1rem', borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
                <p style={{ fontSize: '0.875rem' }} className="text-muted text-center">
                  Showing AI + Copied Content ratio for <strong>{section}</strong> — <strong>{subject}</strong>.
                </p>
              </div>
            </div>

            {/* Roster & Report List */}
            <div className="card md:col-span-2">
              <div className="teacher-roster-toolbar flex flex-col-mob md:flex-row md:items-center justify-between gap-4-mob" style={{ marginBottom: '1.5rem' }}>
                <h3 style={{ fontSize: '1.25rem' }}>Student Roster</h3>
                <div className="teacher-search-wrap w-full-mob" style={{ position: 'relative', width: '100%', maxWidth: '300px' }}>
                  <input
                    type="text"
                    className="form-input w-full-mob"
                    placeholder="Search students..."
                    value={searchQuery}
                    onChange={e => setSearchQuery(e.target.value)}
                    style={{ paddingLeft: '2.5rem' }}
                  />
                  <Search size={18} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                </div>
              </div>

              {loading ? (
                <div style={{ padding: '2rem', textAlign: 'center' }}>
                  <div className="spinner" style={{ margin: '0 auto' }}></div>
                  <p className="text-muted" style={{ marginTop: '1rem' }}>Loading section reports...</p>
                </div>
              ) : (
                <>
                  <div className="table-responsive teacher-table-desktop" style={{ overflowX: 'auto', width: '100%' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', minWidth: '600px' }}>
                      <thead>
                        <tr style={{ borderBottom: '2px solid var(--border-color)', color: 'var(--text-muted)' }}>
                          <th style={{ padding: '0.75rem' }}>Student ID & Name</th>
                          <th style={{ padding: '0.75rem' }}>Overall Plagiarism</th>
                          <th style={{ padding: '0.75rem' }}>AI Generated</th>
                          <th style={{ padding: '0.75rem', textAlign: 'right' }}>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredStudents.map((report) => {
                          const isHighRisk = report.plagiarism_score > 30;
                          return (
                            <tr key={report.submission_id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                              <td style={{ padding: '1rem 0.75rem' }}>
                                <div style={{ fontWeight: 500 }}>{report.student_name}</div>
                                <div className="text-muted" style={{ fontSize: '0.875rem' }}>Sub: {report.subject}</div>
                              </td>
                              <td style={{ padding: '1rem 0.75rem' }}>
                                <span style={{
                                  display: 'inline-flex', padding: '0.25rem 0.75rem', borderRadius: '1rem', fontSize: '0.85rem', fontWeight: 600,
                                  backgroundColor: isHighRisk ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)',
                                  color: isHighRisk ? 'var(--danger-color)' : 'var(--success-color)'
                                }}>
                                  {report.plagiarism_score}% Match
                                </span>
                              </td>
                              <td style={{ padding: '1rem 0.75rem' }}>
                                <div style={{
                                  fontSize: '0.9rem',
                                  fontWeight: 500,
                                  color: report.ai_score > 50 ? 'var(--danger-color)' : 'var(--text-main)'
                                }}>
                                  {report.ai_score}%
                                </div>
                                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{report.label}</div>
                              </td>
                              <td style={{ padding: '1rem 0.75rem', textAlign: 'right' }}>
                                <button 
                                  className="btn btn-outline" 
                                  style={{ padding: '0.4rem 0.75rem', fontSize: '0.85rem' }}
                                  onClick={() => handleViewReport(report)}
                                >
                                  View Report
                                </button>
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>

                  <div className="teacher-mobile-list">
                    {filteredStudents.map((report) => {
                      const isHighRisk = report.plagiarism_score > 30;
                      return (
                        <div key={report.submission_id} className="teacher-student-card">
                          <div className="teacher-student-head">
                            <div>
                              <div style={{ fontWeight: 600 }}>{report.student_name}</div>
                              <div className="teacher-subject-text">Sub: {report.subject}</div>
                            </div>
                            <span style={{
                              display: 'inline-flex',
                              padding: '0.2rem 0.65rem',
                              borderRadius: '999px',
                              fontSize: '0.78rem',
                              fontWeight: 600,
                              backgroundColor: isHighRisk ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)',
                              color: isHighRisk ? 'var(--danger-color)' : 'var(--success-color)'
                            }}>
                              {report.plagiarism_score}% Match
                            </span>
                          </div>

                          <div className="teacher-score-grid">
                            <div className="teacher-score-cell">
                              <div className="teacher-score-label">AI Generated</div>
                              <div className="teacher-score-value" style={{ color: report.ai_score > 50 ? 'var(--danger-color)' : 'var(--text-main)' }}>
                                {report.ai_score}%
                              </div>
                              <div className="teacher-score-note">{report.label}</div>
                            </div>

                            <div className="teacher-score-cell">
                              <div className="teacher-score-label">Risk Status</div>
                              <div className="teacher-score-value" style={{ color: isHighRisk ? 'var(--danger-color)' : 'var(--success-color)' }}>
                                {isHighRisk ? 'High' : 'Normal'}
                              </div>
                              <div className="teacher-score-note">{isHighRisk ? 'Needs review' : 'Within threshold'}</div>
                            </div>
                          </div>

                          <button 
                            className="btn btn-outline w-full-mob" 
                            style={{ padding: '0.45rem 0.75rem', fontSize: '0.84rem' }}
                            onClick={() => handleViewReport(report)}
                          >
                            View Report
                          </button>
                        </div>
                      );
                    })}
                  </div>

                  {hasNoResults && (
                    <div className="text-center text-muted" style={{ padding: '2rem' }}>
                      No students found matching your query.
                    </div>
                  )}
                </>
              )}
            </div>

          </div>
        </>
      ) : (
        <div className="grid md:grid-cols-3 gap-6">
          {/* Current Assignments List */}
          <div className="card md:col-span-2">
            <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ fontSize: '1.25rem', marginBottom: '0.25rem' }}>Your Assigned Subjects & Sections</h3>
                <p className="text-muted" style={{ fontSize: '0.875rem' }}>
                  These mappings determine which classes you can view and monitor on the dashboard.
                </p>
              </div>
            </div>

            {editingSubjects.length === 0 ? (
              <div style={{
                textAlign: 'center',
                padding: '3rem 1.5rem',
                border: '2px dashed var(--border-color)',
                borderRadius: 'var(--radius-lg)',
                backgroundColor: 'rgba(0, 0, 0, 0.01)'
              }}>
                <p className="text-muted" style={{ marginBottom: '1rem' }}>No subjects or sections assigned yet.</p>
                <p style={{ fontSize: '0.85rem' }} className="text-muted">Use the form on the right to add your first subject mapping.</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {editingSubjects.map((ss, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '1rem',
                      backgroundColor: 'var(--bg-color)',
                      border: '1px solid var(--border-color)',
                      borderRadius: 'var(--radius-md)',
                      transition: 'var(--transition)'
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>{ss.subject}</div>
                      <div style={{ fontSize: '0.85rem', color: 'var(--primary-color)', fontWeight: 500 }}>Section: {ss.section}</div>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleDeleteSubjectSection(idx)}
                      style={{
                        padding: '0.5rem',
                        color: 'var(--danger-color)',
                        backgroundColor: 'rgba(239, 68, 68, 0.05)',
                        borderRadius: 'var(--radius-sm)',
                        transition: 'var(--transition)'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.15)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.05)';
                      }}
                      title="Remove Mapping"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                ))}
              </div>
            )}
            
            {/* Save Button & Messages Bar */}
            <div style={{
              marginTop: '2rem',
              paddingTop: '1.5rem',
              borderTop: '1px solid var(--border-color)',
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem'
            }}>
              {saveSuccess && (
                <div style={{
                  backgroundColor: 'rgba(16, 185, 129, 0.08)',
                  color: 'var(--success-color)',
                  border: '1px solid rgba(16, 185, 129, 0.25)',
                  borderRadius: 'var(--radius-md)',
                  padding: '0.75rem 1rem',
                  fontSize: '0.9rem',
                  fontWeight: 500
                }}>
                  {saveSuccess}
                </div>
              )}
              {saveError && (
                <div style={{
                  backgroundColor: 'rgba(239, 68, 68, 0.08)',
                  color: 'var(--danger-color)',
                  border: '1px solid rgba(239, 68, 68, 0.25)',
                  borderRadius: 'var(--radius-md)',
                  padding: '0.75rem 1rem',
                  fontSize: '0.9rem',
                  fontWeight: 500
                }}>
                  {saveError}
                </div>
              )}
              
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={handleSaveSubjects}
                  disabled={savingSubjects}
                  style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                >
                  {savingSubjects ? (
                    <>
                      <span className="spinner" style={{ width: '16px', height: '16px', border: '2px solid #fff', borderTop: '2px solid transparent', display: 'inline-block' }}></span>
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save size={18} />
                      Save Assignments
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Form Card for Adding New Mappings */}
          <div className="card md:col-span-1">
            <h3 style={{ fontSize: '1.25rem', marginBottom: '1.5rem' }}>Add New Mapping</h3>
            
            <div className="form-group">
              <label className="form-label">Subject</label>
              <select
                className="form-select"
                value={newSubjectText}
                onChange={e => setNewSubjectText(e.target.value)}
              >
                {PREDEFINED_SUBJECTS.map(sub => (
                  <option key={sub} value={sub}>{sub}</option>
                ))}
              </select>
            </div>

            {newSubjectText === 'Other' && (
              <div className="form-group">
                <label className="form-label">Custom Subject Name</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="Enter custom subject name"
                  value={customSubjectText}
                  onChange={e => setCustomSubjectText(e.target.value)}
                />
              </div>
            )}

            <div className="form-group" style={{ marginTop: '1.25rem' }}>
              <label className="form-label">Section Code</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. 5A, 5B, A, B"
                value={newSectionText}
                onChange={e => setNewSectionText(e.target.value)}
              />
            </div>

            <button
              type="button"
              className="btn btn-outline w-full"
              onClick={handleAddSubjectSection}
              style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', marginTop: '2rem', width: '100%' }}
            >
              <Plus size={18} /> Add Mapping
            </button>
          </div>
        </div>
      )}

      {/* ── Detailed Report Modal ───────────────────────────────── */}
      {isModalOpen && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(4px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 1000, padding: '1rem'
        }}>
          <div className="card glass-panel" style={{
            width: '100%', maxWidth: '800px', maxHeight: '90vh', overflowY: 'auto',
            position: 'relative', padding: '2rem'
          }}>
            <button 
              onClick={() => setIsModalOpen(false)}
              style={{ position: 'absolute', top: '1.5rem', right: '1.5rem', background: 'none', color: 'var(--text-muted)' }}
            >
              <X size={24} />
            </button>

            {modalLoading ? (
              <div style={{ padding: '4rem', textAlign: 'center' }}>
                <div className="spinner" style={{ margin: '0 auto' }}></div>
                <p className="text-muted mt-4">Loading report details...</p>
              </div>
            ) : modalError ? (
              <div style={{ color: 'var(--danger-color)', padding: '2rem', textAlign: 'center' }}>
                {modalError}
              </div>
            ) : selectedReportDetail ? (
              <div>
                <h2 style={{ marginBottom: '0.5rem' }}>Assignment Report</h2>
                <div className="text-muted" style={{ marginBottom: '2rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                  <span><strong style={{ color: 'var(--text-main)' }}>Student:</strong> {selectedReportDetail.student_name}</span>
                  <span><strong style={{ color: 'var(--text-main)' }}>Subject:</strong> {selectedReportDetail.subject}</span>
                </div>

                <div className="grid md:grid-cols-2 gap-4" style={{ marginBottom: '2rem' }}>
                  <div style={{ padding: '1.5rem', backgroundColor: 'rgba(239, 68, 68, 0.05)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
                    <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>Plagiarism Score</div>
                    <div style={{ fontSize: '2rem', fontWeight: 700, color: selectedReportDetail.plagiarism_score > 30 ? 'var(--danger-color)' : 'var(--success-color)' }}>
                      {selectedReportDetail.plagiarism_score}%
                    </div>
                  </div>
                  
                  <div style={{ padding: '1.5rem', backgroundColor: 'rgba(79, 70, 229, 0.05)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(79, 70, 229, 0.2)' }}>
                    <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>AI Logic Confidence</div>
                    <div style={{ fontSize: '2rem', fontWeight: 700, color: selectedReportDetail.ai_score > 50 ? 'var(--danger-color)' : 'var(--primary-color)' }}>
                      {selectedReportDetail.ai_score}%
                    </div>
                    <div style={{ fontSize: '0.875rem', fontWeight: 600, marginTop: '0.25rem' }}>{selectedReportDetail.label}</div>
                  </div>
                </div>

                <div style={{ marginBottom: '2rem' }}>
                  <h3 style={{ marginBottom: '1rem', fontSize: '1.1rem' }}>Extracted Text Preview</h3>
                  <div style={{ 
                    padding: '1.5rem', backgroundColor: 'var(--bg-color)', borderRadius: 'var(--radius-md)', 
                    border: '1px solid var(--border-color)', maxHeight: '200px', overflowY: 'auto',
                    fontSize: '0.9rem', lineHeight: '1.6', whiteSpace: 'pre-wrap', color: 'var(--text-muted)'
                  }}>
                    {selectedReportDetail.processed_text || "No text could be extracted."}
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', borderTop: '1px solid var(--border-color)', paddingTop: '1.5rem' }}>
                  <button 
                    className="btn btn-primary"
                    onClick={() => handleDownload(selectedReportDetail.submission_id, selectedReportDetail.student_name)}
                    style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                  >
                    <Download size={18} /> Download Original File
                  </button>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}

    </div>
  );
}
