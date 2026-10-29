import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { api } from '../../utils/api';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip,
  Legend, ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts';
import {
  ArrowLeft, Users, AlertCircle, FileCheck, ShieldCheck,
  ChevronRight
} from 'lucide-react';

const SummaryCard = ({ title, value, icon, color }) => (
  <div className="card glass-panel flex items-center gap-4" style={{ padding: '1.25rem 1.5rem' }}>
    <div style={{
      width: '52px',
      height: '52px',
      borderRadius: 'var(--radius-lg)',
      backgroundColor: `${color}18`,
      color: color,
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexShrink: 0,
    }}>
      {icon}
    </div>
    <div>
      <h4 className="text-muted" style={{ fontSize: '0.825rem', fontWeight: 600, marginBottom: '0.2rem', textTransform: 'uppercase', letterSpacing: '0.03em' }}>
        {title}
      </h4>
      <p style={{ fontSize: '1.65rem', fontWeight: 800, color: 'var(--text-main)', margin: 0, lineHeight: 1.1 }}>
        {value}
      </p>
    </div>
  </div>
);

export default function HODOverviewPage() {
  const [view, setView] = useState('batch'); // 'batch' or 'section'
  const [selectedSection, setSelectedSection] = useState(null);
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchBatchReports = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/reports/batch');
      if (!response.ok) throw new Error('Failed to fetch batch reports');
      const data = await response.json();
      setReports(data);
    } catch (err) {
      console.error('Batch reports fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBatchReports();
  }, [fetchBatchReports]);

  // Derive sections
  const sections = useMemo(() => {
    const s = [...new Set(reports.map((r) => r.section))].filter(Boolean);
    return s.length > 0 ? s : ['4I1', '4I2'];
  }, [reports]);

  const batchData = useMemo(() => {
    return sections.map((secName) => {
      const secReports = reports.filter((r) => r.section === secName || (!r.section && secName === 'CSE-A'));
      const clean = secReports.filter((r) => r.plagiarism_score < 20).length;
      const flagged = secReports.filter((r) => r.plagiarism_score >= 20).length;
      return { section: secName, original: clean, plagiarized: flagged };
    });
  }, [sections, reports]);

  const sectionReports = useMemo(() => {
    if (!selectedSection) return [];
    return reports.filter((r) => r.section === selectedSection || (!r.section && selectedSection === 'CSE-A'));
  }, [reports, selectedSection]);

  const sectionPieData = useMemo(() => {
    return [
      { name: 'Original', value: sectionReports.filter((r) => r.plagiarism_score < 15).length || 1, color: '#10b981' },
      { name: 'Moderate Match', value: sectionReports.filter((r) => r.plagiarism_score >= 15 && r.plagiarism_score <= 30).length || 0, color: '#f59e0b' },
      { name: 'High Plagiarism', value: sectionReports.filter((r) => r.plagiarism_score > 30).length || 0, color: '#ef4444' },
    ];
  }, [sectionReports]);

  const handleDrillDown = (sectionName) => {
    setSelectedSection(sectionName);
    setView('section');
  };

  return (
    <>
      {/* Content Header */}
      <div className="teacher-content-header" style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1.75rem' }}>
        <div className="flex flex-col-mob md:flex-row md:items-center justify-between gap-4-mob">
          <div>
            <h2>HOD Dashboard</h2>
            <p>Institutional Evaluation Portal: Monitor academic integrity, stylometric anomalies, and cheating networks.</p>
          </div>
          {view === 'section' && (
            <button className="btn btn-outline w-full-mob" onClick={() => setView('batch')}>
              <ArrowLeft size={16} />
              <span>Back to Overview</span>
            </button>
          )}
        </div>
      </div>

      {loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '380px' }}>
          <div className="spinner" style={{ width: '40px', height: '40px' }}></div>
          <p className="text-muted" style={{ marginTop: '1rem', fontSize: '0.9rem' }}>Aggregating batch data across sections...</p>
        </div>
      ) : view === 'batch' ? (
        <>
          {/* Summary Cards */}
          <div className="grid md:grid-cols-3 gap-6" style={{ marginBottom: '2rem' }}>
            <SummaryCard title="Total Students Evaluated" value={reports.length} icon={<Users size={22} />} color="#4f46e5" />
            <SummaryCard title="Clean Submissions (<20%)" value={reports.filter((r) => r.plagiarism_score < 20).length} icon={<FileCheck size={22} />} color="#10b981" />
            <SummaryCard title="Flagged Plagiarism (≥20%)" value={reports.filter((r) => r.plagiarism_score >= 20).length} icon={<AlertCircle size={22} />} color="#ef4444" />
          </div>

          {/* Cross-Section Comparison Chart */}
          <div className="card glass-panel" style={{ padding: '1.75rem' }}>
            <div style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, margin: 0 }}>Cross-Section Similarity Comparison</h3>
              <p className="text-muted" style={{ fontSize: '0.85rem', margin: '0.2rem 0 0 0' }}>
                Distribution of original vs. flagged assignments stacked by section cohort.
              </p>
            </div>

            <div style={{ height: '360px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={batchData} margin={{ top: 20, right: 30, left: 10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-color)" />
                  <XAxis dataKey="section" axisLine={false} tickLine={false} tick={{ fill: 'var(--text-muted)', fontSize: 12 }} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fill: 'var(--text-muted)', fontSize: 12 }} />
                  <RechartsTooltip
                    contentStyle={{
                      backgroundColor: 'rgba(255, 255, 255, 0.95)',
                      border: '1px solid var(--border-color)',
                      borderRadius: 'var(--radius-md)',
                      boxShadow: 'var(--shadow-md)',
                      fontSize: '0.85rem',
                    }}
                    cursor={{ fill: 'rgba(79, 70, 229, 0.04)' }}
                  />
                  <Legend wrapperStyle={{ paddingTop: '10px' }} />
                  <Bar dataKey="original" name="Original Content" stackId="a" fill="#10b981" radius={[0, 0, 4, 4]} />
                  <Bar dataKey="plagiarized" name="Plagiarized (≥20%)" stackId="a" fill="#ef4444" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Section Cohort Breakdown */}
          <div style={{ marginTop: '2rem' }}>
            <div style={{ marginBottom: '1.25rem' }}>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, margin: 0 }}>Section Cohort Breakdown</h3>
              <p className="text-muted" style={{ fontSize: '0.85rem', margin: '0.2rem 0 0 0' }}>
                Click on any section card below to drill down into student records.
              </p>
            </div>

            <div className="grid md:grid-cols-4 gap-4">
              {batchData.map((data) => {
                const total = data.original + data.plagiarized;
                const plagPercent = total > 0 ? Math.round((data.plagiarized / total) * 100) : 0;
                return (
                  <div
                    key={data.section}
                    className="card glass-panel"
                    style={{
                      padding: '1.25rem',
                      cursor: 'pointer',
                      transition: 'var(--transition)',
                    }}
                    onClick={() => handleDrillDown(data.section)}
                  >
                    <div className="flex items-center justify-between" style={{ marginBottom: '0.75rem' }}>
                      <span style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-main)' }}>Section {data.section}</span>
                      <ChevronRight size={18} className="text-muted" />
                    </div>

                    <div className="flex items-center justify-between text-muted" style={{ fontSize: '0.85rem', marginBottom: '0.5rem' }}>
                      <span>Submissions:</span>
                      <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>{total}</span>
                    </div>

                    <div className="flex items-center justify-between" style={{ fontSize: '0.85rem' }}>
                      <span className="text-muted">Flag Rate:</span>
                      <span className={`badge ${plagPercent > 25 ? 'badge-danger' : 'badge-success'}`}>
                        {plagPercent}%
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </>
      ) : (
        /* Section Drilldown View */
        <div className="grid md:grid-cols-2 gap-6">
          <div className="card glass-panel" style={{ padding: '1.75rem' }}>
            <h3 style={{ marginBottom: '0.25rem', fontSize: '1.15rem', fontWeight: 700 }}>
              Section {selectedSection} Distribution
            </h3>
            <p className="text-muted" style={{ fontSize: '0.85rem', marginBottom: '1.5rem' }}>
              Similarity breakdown for students in section {selectedSection}.
            </p>

            <div style={{ height: '280px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={sectionPieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={70}
                    outerRadius={95}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {sectionPieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <RechartsTooltip
                    contentStyle={{
                      backgroundColor: 'rgba(255, 255, 255, 0.95)',
                      border: '1px solid var(--border-color)',
                      borderRadius: 'var(--radius-md)',
                      fontSize: '0.85rem',
                    }}
                  />
                  <Legend verticalAlign="bottom" height={36} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="card glass-panel" style={{ padding: '1.75rem' }}>
            <h3 style={{ marginBottom: '0.25rem', fontSize: '1.15rem', fontWeight: 700 }}>Top Critical Cases</h3>
            <p className="text-muted" style={{ fontSize: '0.85rem', marginBottom: '1.25rem' }}>
              Submissions exceeding the maximum threshold (&gt;30% overlap).
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {sectionReports.filter((r) => r.plagiarism_score > 30).slice(0, 5).map((report) => (
                <div
                  key={report.submission_id}
                  className="flex items-center justify-between"
                  style={{
                    padding: '0.9rem 1.15rem',
                    border: '1px solid rgba(239, 68, 68, 0.25)',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'var(--danger-light)',
                  }}
                >
                  <div>
                    <h5 style={{ margin: 0, fontWeight: 700, fontSize: '0.95rem' }}>{report.student_name}</h5>
                    <span className="text-muted" style={{ fontSize: '0.8rem' }}>Course: {report.subject}</span>
                  </div>
                  <div className="flex flex-col items-end">
                    <span className="badge badge-danger" style={{ fontSize: '0.85rem' }}>
                      {report.plagiarism_score}% Plagiarism
                    </span>
                  </div>
                </div>
              ))}
              {sectionReports.filter((r) => r.plagiarism_score > 30).length === 0 && (
                <div className="text-center text-muted" style={{ padding: '3rem 1rem' }}>
                  <ShieldCheck size={32} style={{ color: 'var(--success-color)', margin: '0 auto 0.5rem auto' }} />
                  <p style={{ margin: 0, fontSize: '0.9rem' }}>No high-risk plagiarism cases detected in this section.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
