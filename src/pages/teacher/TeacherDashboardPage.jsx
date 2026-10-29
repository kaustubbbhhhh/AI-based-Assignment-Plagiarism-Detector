import React, { useState, useMemo, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../utils/api';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { Search, AlertCircle, BookOpen } from 'lucide-react';
import TeacherReportModal from '../../components/teacher/TeacherReportModal';

export default function TeacherDashboardPage() {
  const { user: authUser } = useAuth();
  const [currentUser, setCurrentUser] = useState(() => authUser || {});

  useEffect(() => {
    if (authUser) setCurrentUser(authUser);
  }, [authUser]);

  const teacherSubjectsSections = useMemo(
    () => currentUser.subjects_sections || [],
    [currentUser.subjects_sections]
  );

  // Derive unique sections from teacher's managed assignments
  const uniqueSections = useMemo(() => {
    const secs = [...new Set(teacherSubjectsSections.map((ss) => ss.section).filter(Boolean))];
    return secs.length > 0 ? secs : ['No sections assigned'];
  }, [teacherSubjectsSections]);

  // Dashboard section selection
  const [section, setSection] = useState(() => uniqueSections[0]);

  // Keep section valid if teacher updates assignments
  useEffect(() => {
    if (!uniqueSections.includes(section)) {
      setSection(uniqueSections[0]);
    }
  }, [uniqueSections, section]);

  // Dynamic non-editable subject automatically loaded for the selected section
  const subject = useMemo(() => {
    const found = teacherSubjectsSections.find((ss) => ss.section === section);
    return found ? found.subject : 'No subjects assigned';
  }, [teacherSubjectsSections, section]);

  const [searchQuery, setSearchQuery] = useState('');
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedReportDetail, setSelectedReportDetail] = useState(null);
  const [modalLoading, setModalLoading] = useState(false);
  const [modalError, setModalError] = useState('');

  // Download Function
  const handleDownload = async (submissionId, studentName) => {
    try {
      const response = await api.get(`/api/download/${submissionId}`);
      if (!response.ok) throw new Error('Download failed');

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

  // Fetch Detailed Report for Modal
  const handleViewReport = async (reportSummary) => {
    setIsModalOpen(true);
    setModalLoading(true);
    setModalError('');
    setSelectedReportDetail(null);

    try {
      const response = await api.get(`/api/report/${reportSummary.submission_id}`);
      if (!response.ok) throw new Error('Failed to fetch detailed report');

      const data = await response.json();
      setSelectedReportDetail({ ...reportSummary, ...data });
    } catch (err) {
      setModalError(err.message);
    } finally {
      setModalLoading(false);
    }
  };

  // Fetch reports filtered by BOTH section and subject
  const fetchReports = async (selectedSection, selectedSubject) => {
    setLoading(true);
    setError('');
    try {
      const url = `/api/reports/section/${encodeURIComponent(selectedSection)}?subject=${encodeURIComponent(selectedSubject)}`;
      const response = await api.get(url);
      if (!response.ok) throw new Error('Failed to fetch section reports');
      const data = await response.json();
      setReports(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (section && subject && !section.startsWith('No ') && !subject.startsWith('No ')) {
      fetchReports(section, subject);
    }
  }, [section, subject]);

  // Derive stats from reports
  const stats = useMemo(() => {
    return {
      original: reports.filter((r) => r.plagiarism_score < 15).length,
      moderate: reports.filter((r) => r.plagiarism_score >= 15 && r.plagiarism_score <= 30).length,
      high: reports.filter((r) => r.plagiarism_score > 30).length,
    };
  }, [reports]);

  const pieData = useMemo(() => {
    return [
      { name: 'Original Content', value: stats.original || (reports.length === 0 ? 1 : 0), color: '#10b981' },
      { name: 'Moderate Match', value: stats.moderate || 0, color: '#f59e0b' },
      { name: 'High Plagiarism', value: stats.high || 0, color: '#ef4444' },
    ];
  }, [stats, reports.length]);

  const filteredStudents = useMemo(() => {
    return reports.filter(
      (report) =>
        report.student_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        report.subject.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [reports, searchQuery]);

  const hasNoResults = !loading && filteredStudents.length === 0;
  const noAssignments = teacherSubjectsSections.length === 0;

  return (
    <>
      {/* Content Header */}
      <div className="teacher-content-header">
        <h2>Dashboard & Roster</h2>
        <p>Review section-wise student assignments, similarity metrics, and AI forensics.</p>
      </div>

      {/* Section/Subject filters */}
      <div className="teacher-filter-row flex flex-col-mob sm:flex-row sm:items-end gap-3" style={{ flexWrap: 'wrap', marginBottom: '1.5rem' }}>
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
              textAlign: 'left',
            }}
          >
            Section
          </label>
          <select
            id="teacher-section-select"
            className="form-select"
            value={section}
            onChange={(e) => setSection(e.target.value)}
            style={{
              minWidth: '110px',
              maxWidth: '160px',
              padding: '0.5rem 0.85rem',
              fontSize: '0.875rem',
              fontWeight: 600,
            }}
          >
            {uniqueSections.map((sec) => (
              <option key={sec} value={sec}>{sec}</option>
            ))}
          </select>
        </div>

        {/* Subject Control - Dynamic Non-Editable Field */}
        <div style={{ display: 'flex', flexDirection: 'column', textAlign: 'left' }}>
          <label
            className="form-label"
            style={{
              marginBottom: '0.35rem',
              fontSize: '0.8rem',
              fontWeight: 700,
              color: 'var(--text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
              textAlign: 'left',
            }}
          >
            Subject
          </label>
          <div
            style={{
              minWidth: '220px',
              maxWidth: '340px',
              padding: '0.5rem 0.85rem',
              fontSize: '0.875rem',
              fontWeight: 600,
              backgroundColor: 'var(--surface-subtle)',
              border: '1.5px solid var(--border-color)',
              borderRadius: 'var(--radius-md)',
              color: subject.startsWith('No ') ? 'var(--text-muted)' : 'var(--text-main)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.6rem',
              height: '38px',
              cursor: 'default',
              userSelect: 'none',
            }}
            title="Subject is automatically loaded from the selected section"
          >
            <BookOpen size={16} style={{ color: 'var(--primary-color)', flexShrink: 0 }} />
            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {subject}
            </span>
          </div>
        </div>
      </div>

      {noAssignments && (
        <div className="alert alert-warning">
          <AlertCircle size={18} style={{ flexShrink: 0 }} />
          <span>No subjects or sections have been assigned to your profile. Please visit the "Manage Subjects" panel to add your teaching assignments.</span>
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
                    fontSize: '0.85rem',
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
                onChange={(e) => setSearchQuery(e.target.value)}
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
                  pointerEvents: 'none',
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
                              color: report.ai_score > 50 ? 'var(--danger-color)' : 'var(--text-main)',
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
                      );
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

      {/* Detailed Report Modal */}
      <TeacherReportModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        report={selectedReportDetail}
        loading={modalLoading}
        error={modalError}
        onDownload={handleDownload}
      />
    </>
  );
}
