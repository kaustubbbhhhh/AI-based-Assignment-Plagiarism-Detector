import React, { useState, useMemo } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { Search, X, Download, FileText, Settings, Plus, Trash2, Save, AlertCircle, CheckCircle2, User, LayoutDashboard } from 'lucide-react';

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
    { name: 'Original Content', value: stats.original || (reports.length === 0 ? 1 : 0), color: '#10b981' },
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
    <div className="portal-shell" style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 0.5rem' }}>
      
      {/* ── Page Header & Filters ── */}
      <div className="teacher-header-row flex flex-col-mob md:flex-row md:items-end justify-between gap-4-mob" style={{ marginBottom: '1.75rem' }}>
        <div>
          <h2 style={{ fontWeight: 800, marginBottom: '0.25rem' }}>Teacher Portal</h2>
          <p className="text-muted" style={{ fontSize: '0.925rem', margin: 0 }}>
            {activeTab === 'dashboard'
              ? 'Review section-wise student assignments, similarity metrics, and AI forensics.'
              : 'Configure your course assignments and assigned class sections.'}
          </p>
        </div>

        {activeTab === 'dashboard' && (
          <div className="teacher-filter-row flex flex-col-mob sm:flex-row sm:items-end gap-3" style={{ flexWrap: 'wrap' }}>
            {/* Section Control */}
            <div style={{ display: 'flex', flexDirection: 'column', textAlign: 'left' }}>
              <label
                htmlFor="teacher-section-select"
                className="form-label"
                style={{
                  marginBottom: '0.35rem',
                  fontSize: '0.8rem',
                  fontWeight: 700,
                  color: 'var(--text-muted)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                  textAlign: 'left'
                }}
              >
                Section
              </label>
              <select
                id="teacher-section-select"
                className="form-select"
                value={section}
                onChange={e => setSection(e.target.value)}
                style={{
                  minWidth: '110px',
                  maxWidth: '160px',
                  padding: '0.5rem 0.85rem',
                  fontSize: '0.875rem',
                  fontWeight: 600
                }}
              >
                {uniqueSections.map(sec => (
                  <option key={sec} value={sec}>{sec}</option>
                ))}
              </select>
            </div>

            {/* Subject Control */}
            <div style={{ display: 'flex', flexDirection: 'column', textAlign: 'left' }}>
              <label
                htmlFor="teacher-subject-select"
                className="form-label"
                style={{
                  marginBottom: '0.35rem',
                  fontSize: '0.8rem',
                  fontWeight: 700,
                  color: 'var(--text-muted)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                  textAlign: 'left'
                }}
              >
                Subject
              </label>
              <select
                id="teacher-subject-select"
                className="form-select"
                value={subject}
                onChange={e => setSubject(e.target.value)}
                style={{
                  minWidth: '220px',
                  maxWidth: '320px',
                  padding: '0.5rem 0.85rem',
                  fontSize: '0.875rem',
                  fontWeight: 600
                }}
              >
                {uniqueSubjects.map(sub => (
                  <option key={sub} value={sub}>{sub}</option>
                ))}
              </select>
            </div>
          </div>
        )}
      </div>

      {/* ── Modern Tab Navigation ── */}
      <div style={{
        display: 'flex',
        gap: '0.5rem',
        borderBottom: '1px solid var(--border-color)',
        marginBottom: '2rem',
        paddingBottom: '0.5rem'
      }}>
        <button
          onClick={() => setActiveTab('dashboard')}
          className="btn"
          style={{
            backgroundColor: activeTab === 'dashboard' ? 'var(--primary-color)' : 'transparent',
            color: activeTab === 'dashboard' ? '#ffffff' : 'var(--text-muted)',
            boxShadow: activeTab === 'dashboard' ? 'var(--shadow-sm)' : 'none',
            fontSize: '0.9rem',
            padding: '0.55rem 1.15rem'
          }}
        >
          <LayoutDashboard size={16} />
          <span>Dashboard & Roster</span>
        </button>

        <button
          onClick={() => setActiveTab('subjects')}
          className="btn"
          style={{
            backgroundColor: activeTab === 'subjects' ? 'var(--primary-color)' : 'transparent',
            color: activeTab === 'subjects' ? '#ffffff' : 'var(--text-muted)',
            boxShadow: activeTab === 'subjects' ? 'var(--shadow-sm)' : 'none',
            fontSize: '0.9rem',
            padding: '0.55rem 1.15rem'
          }}
        >
          <Settings size={16} />
          <span>Manage Courses ({teacherSubjectsSections.length})</span>
        </button>
      </div>

      {activeTab === 'dashboard' ? (
        <>
          {noAssignments && (
            <div className="alert alert-warning">
              <AlertCircle size={18} style={{ flexShrink: 0 }} />
              <span>No subjects or sections have been assigned to your profile. Please visit the "Manage Courses" tab to add your teaching assignments.</span>
            </div>
          )}

          {error && (
            <div className="alert alert-danger">
              <AlertCircle size={18} style={{ flexShrink: 0 }} />
              <span>{error}</span>
            </div>
          )}

          <div className="teacher-main-grid grid md:grid-cols-3 gap-6">

            {/* Statistics Overview Card */}
            <div className="card md:col-span-1">
              <h3 style={{ marginBottom: '1.25rem', fontSize: '1.15rem', fontWeight: 700 }}>Section Statistics</h3>
              <div className="teacher-chart-shell">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={82}
                      paddingAngle={4}
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        border: '1px solid var(--border-color)',
                        borderRadius: 'var(--radius-md)',
                        boxShadow: 'var(--shadow-md)',
                        fontSize: '0.85rem'
                      }}
                    />
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
              <div style={{ marginTop: '1.25rem', borderTop: '1px solid var(--border-color)', paddingTop: '0.85rem' }}>
                <p style={{ fontSize: '0.825rem' }} className="text-muted text-center">
                  Overview for <strong>{section}</strong> • <strong>{subject}</strong>
                </p>
              </div>
            </div>

            {/* Roster & Report List */}
            <div className="card md:col-span-2">
              <div className="teacher-roster-toolbar flex flex-col-mob md:flex-row md:items-center justify-between gap-4-mob" style={{ marginBottom: '1.5rem' }}>
                <div>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 700, margin: 0 }}>Student Submissions</h3>
                  <p className="text-muted" style={{ fontSize: '0.825rem', margin: '0.2rem 0 0 0' }}>
                    Showing {filteredStudents.length} submission{filteredStudents.length !== 1 ? 's' : ''}
                  </p>
                </div>

                <div className="teacher-search-wrap w-full-mob" style={{ position: 'relative', width: '100%', maxWidth: '280px' }}>
                  <input
                    type="text"
                    className="form-input w-full-mob"
                    placeholder="Search student or topic..."
                    value={searchQuery}
                    onChange={e => setSearchQuery(e.target.value)}
                    style={{ paddingLeft: '2.5rem', paddingRight: '0.75rem', fontSize: '0.875rem' }}
                  />
                  <Search
                    size={16}
                    style={{
                      position: 'absolute',
                      left: '0.85rem',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      color: 'var(--text-subtle)',
                      pointerEvents: 'none'
                    }}
                  />
                </div>
              </div>

              {loading ? (
                <div style={{ padding: '3rem 1rem', textAlign: 'center' }}>
                  <div className="spinner" style={{ margin: '0 auto', width: '36px', height: '36px' }}></div>
                  <p className="text-muted" style={{ marginTop: '1rem', fontSize: '0.9rem' }}>Loading section reports...</p>
                </div>
              ) : (
                <>
                  <div className="table-responsive teacher-table-desktop" style={{ overflowX: 'auto', width: '100%' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', minWidth: '600px' }}>
                      <thead>
                        <tr style={{ borderBottom: '2px solid var(--border-color)', color: 'var(--text-muted)', fontSize: '0.825rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                          <th style={{ padding: '0.75rem 0.5rem' }}>Student & Subject</th>
                          <th style={{ padding: '0.75rem 0.5rem' }}>Plagiarism Match</th>
                          <th style={{ padding: '0.75rem 0.5rem' }}>AI Generated</th>
                          <th style={{ padding: '0.75rem 0.5rem', textAlign: 'right' }}>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredStudents.map((report) => {
                          const isHighRisk = report.plagiarism_score > 30;
                          return (
                            <tr key={report.submission_id} style={{ borderBottom: '1px solid var(--border-color)', transition: 'background-color 0.15s' }}>
                              <td style={{ padding: '0.9rem 0.5rem' }}>
                                <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>{report.student_name}</div>
                                <div className="text-muted" style={{ fontSize: '0.8rem' }}>Course: {report.subject}</div>
                              </td>
                              <td style={{ padding: '0.9rem 0.5rem' }}>
                                <span className={`badge ${isHighRisk ? 'badge-danger' : 'badge-success'}`}>
                                  {report.plagiarism_score}% Match
                                </span>
                              </td>
                              <td style={{ padding: '0.9rem 0.5rem' }}>
                                <div style={{
                                  fontSize: '0.9rem',
                                  fontWeight: 600,
                                  color: report.ai_score > 50 ? 'var(--danger-color)' : 'var(--text-main)'
                                }}>
                                  {report.ai_score}%
                                </div>
                                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{report.label}</div>
                              </td>
                              <td style={{ padding: '0.9rem 0.5rem', textAlign: 'right' }}>
                                <button 
                                  className="btn btn-outline" 
                                  style={{ padding: '0.35rem 0.75rem', fontSize: '0.825rem' }}
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

                  {/* Mobile Roster Card List */}
                  <div className="teacher-mobile-list">
                    {filteredStudents.map((report) => {
                      const isHighRisk = report.plagiarism_score > 30;
                      return (
                        <div key={report.submission_id} className="teacher-student-card">
                          <div className="teacher-student-head">
                            <div>
                              <div style={{ fontWeight: 700 }}>{report.student_name}</div>
                              <div className="teacher-subject-text">Course: {report.subject}</div>
                            </div>
                            <span className={`badge ${isHighRisk ? 'badge-danger' : 'badge-success'}`}>
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
                                {isHighRisk ? 'High Risk' : 'Normal'}
                              </div>
                              <div className="teacher-score-note">{isHighRisk ? 'Needs manual check' : 'Passed automated filter'}</div>
                            </div>
                          </div>

                          <button 
                            className="btn btn-outline w-full-mob" 
                            style={{ padding: '0.45rem 0.75rem', fontSize: '0.84rem' }}
                            onClick={() => handleViewReport(report)}
                          >
                            View Detailed Report
                          </button>
                        </div>
                      );
                    })}
                  </div>

                  {hasNoResults && (
                    <div className="text-center text-muted" style={{ padding: '3rem 1rem' }}>
                      <p style={{ margin: 0, fontSize: '0.9rem' }}>No student submissions found matching your query.</p>
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
                <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '0.25rem' }}>Assigned Courses & Sections</h3>
                <p className="text-muted" style={{ fontSize: '0.875rem' }}>
                  These mappings determine which classes appear in your portal for plagiarism monitoring.
                </p>
              </div>
            </div>

            {editingSubjects.length === 0 ? (
              <div style={{
                textAlign: 'center',
                padding: '3rem 1.5rem',
                border: '1.5px dashed var(--border-color)',
                borderRadius: 'var(--radius-lg)',
                backgroundColor: 'var(--surface-subtle)'
              }}>
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
                      transition: 'var(--transition)'
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>{ss.subject}</div>
                      <div style={{ fontSize: '0.825rem', color: 'var(--primary-color)', fontWeight: 600, marginTop: '0.15rem' }}>
                        Section: {ss.section}
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
                        transition: 'var(--transition)'
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
            <div style={{
              marginTop: '2rem',
              paddingTop: '1.5rem',
              borderTop: '1px solid var(--border-color)',
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem'
            }}>
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

          {/* Form Card for Adding New Mappings */}
          <div className="card md:col-span-1">
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '1.25rem' }}>Add Course Assignment</h3>
            
            <div className="form-group">
              <label className="form-label">Subject / Course</label>
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
                  placeholder="Enter course name"
                  value={customSubjectText}
                  onChange={e => setCustomSubjectText(e.target.value)}
                />
              </div>
            )}

            <div className="form-group">
              <label className="form-label">Section Code</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. 4I1, CSE-A, A, B"
                value={newSectionText}
                onChange={e => setNewSectionText(e.target.value)}
              />
            </div>

            <button
              type="button"
              className="btn btn-outline w-full"
              onClick={handleAddSubjectSection}
              style={{ marginTop: '1.5rem', width: '100%' }}
            >
              <Plus size={16} /> Add to List
            </button>
          </div>
        </div>
      )}

      {/* ── Detailed Report Modal ───────────────────────────────── */}
      {isModalOpen && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(15, 23, 42, 0.65)', backdropFilter: 'blur(8px)',
          WebkitBackdropFilter: 'blur(8px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 1000, padding: '1rem'
        }}>
          <div className="card glass-panel" style={{
            width: '100%', maxWidth: '780px', maxHeight: '90vh', overflowY: 'auto',
            position: 'relative', padding: '2rem', borderRadius: 'var(--radius-xl)'
          }}>
            <button 
              onClick={() => setIsModalOpen(false)}
              style={{
                position: 'absolute',
                top: '1.25rem',
                right: '1.25rem',
                background: 'var(--surface-hover)',
                color: 'var(--text-muted)',
                borderRadius: '50%',
                padding: '0.4rem',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer'
              }}
              aria-label="Close dialog"
            >
              <X size={20} />
            </button>

            {modalLoading ? (
              <div style={{ padding: '4rem 1rem', textAlign: 'center' }}>
                <div className="spinner" style={{ margin: '0 auto', width: '40px', height: '40px' }}></div>
                <p className="text-muted" style={{ marginTop: '1rem', fontSize: '0.9rem' }}>Loading report details...</p>
              </div>
            ) : modalError ? (
              <div className="alert alert-danger" style={{ margin: '2rem 0' }}>
                <AlertCircle size={18} />
                <span>{modalError}</span>
              </div>
            ) : selectedReportDetail ? (
              <div>
                <h2 style={{ marginBottom: '0.35rem', fontWeight: 800 }}>Assignment Report</h2>
                <div className="text-muted" style={{ marginBottom: '1.75rem', display: 'flex', gap: '1.25rem', flexWrap: 'wrap', fontSize: '0.9rem' }}>
                  <span><strong style={{ color: 'var(--text-main)' }}>Student:</strong> {selectedReportDetail.student_name}</span>
                  <span>•</span>
                  <span><strong style={{ color: 'var(--text-main)' }}>Course:</strong> {selectedReportDetail.subject}</span>
                </div>

                <div className="grid md:grid-cols-2 gap-4" style={{ marginBottom: '1.75rem' }}>
                  <div style={{
                    padding: '1.25rem',
                    backgroundColor: selectedReportDetail.plagiarism_score > 30 ? 'var(--danger-light)' : 'var(--success-light)',
                    borderRadius: 'var(--radius-lg)',
                    border: `1px solid ${selectedReportDetail.plagiarism_score > 30 ? 'rgba(239, 68, 68, 0.25)' : 'rgba(16, 185, 129, 0.25)'}`
                  }}>
                    <div style={{ fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                      Plagiarism Overlap
                    </div>
                    <div style={{
                      fontSize: '2.25rem',
                      fontWeight: 800,
                      color: selectedReportDetail.plagiarism_score > 30 ? 'var(--danger-color)' : 'var(--success-color)',
                      lineHeight: 1
                    }}>
                      {selectedReportDetail.plagiarism_score}%
                    </div>
                  </div>
                  
                  <div style={{
                    padding: '1.25rem',
                    backgroundColor: selectedReportDetail.ai_score > 50 ? 'var(--danger-light)' : 'var(--primary-light)',
                    borderRadius: 'var(--radius-lg)',
                    border: `1px solid ${selectedReportDetail.ai_score > 50 ? 'rgba(239, 68, 68, 0.25)' : 'rgba(79, 70, 229, 0.25)'}`
                  }}>
                    <div style={{ fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                      AI Logic Confidence
                    </div>
                    <div style={{
                      fontSize: '2.25rem',
                      fontWeight: 800,
                      color: selectedReportDetail.ai_score > 50 ? 'var(--danger-color)' : 'var(--primary-color)',
                      lineHeight: 1
                    }}>
                      {selectedReportDetail.ai_score}%
                    </div>
                    <div style={{ fontSize: '0.825rem', fontWeight: 600, marginTop: '0.35rem', color: 'var(--text-main)' }}>
                      Classification: {selectedReportDetail.label}
                    </div>
                  </div>
                </div>

                <div style={{ marginBottom: '1.75rem' }}>
                  <h4 style={{ marginBottom: '0.75rem', fontSize: '1rem', fontWeight: 700 }}>Extracted Text Content</h4>
                  <div style={{ 
                    padding: '1.25rem',
                    backgroundColor: 'var(--bg-color)',
                    borderRadius: 'var(--radius-md)', 
                    border: '1px solid var(--border-color)',
                    maxHeight: '220px',
                    overflowY: 'auto',
                    fontSize: '0.875rem',
                    lineHeight: '1.6',
                    whiteSpace: 'pre-wrap',
                    color: 'var(--text-main)',
                    fontFamily: 'inherit'
                  }}>
                    {selectedReportDetail.processed_text || "No extracted text preview available."}
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', borderTop: '1px solid var(--border-color)', paddingTop: '1.25rem' }}>
                  <button 
                    className="btn btn-primary"
                    onClick={() => handleDownload(selectedReportDetail.submission_id, selectedReportDetail.student_name)}
                  >
                    <Download size={16} />
                    <span>Download Original File</span>
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

