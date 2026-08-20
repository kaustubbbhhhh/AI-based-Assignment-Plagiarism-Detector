import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { ArrowLeft, Users, AlertCircle, FileCheck, ExternalLink, ShieldCheck, Clock, AlertTriangle, Cpu, TrendingUp, BarChart3, ChevronRight } from 'lucide-react';

export default function HODPortal() {
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' or 'forensics'
  const [view, setView] = useState('batch'); // 'batch' or 'section'
  const [selectedSection, setSelectedSection] = useState(null);
  
  // Overview data states
  const [reports, setReports] = useState([]);
  const [overviewLoading, setOverviewLoading] = useState(false);

  // Forensic data states
  const [forensicSummary, setForensicSummary] = useState(null);
  const [cheatingRings, setCheatingRings] = useState([]);
  const [styleAnomalies, setStyleAnomalies] = useState([]);
  const [riskFactors, setRiskFactors] = useState([]);
  const [insights, setInsights] = useState(null);
  const [forensicsLoading, setForensicsLoading] = useState(false);

  const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

  const fetchBatchReports = useCallback(async () => {
    setOverviewLoading(true);
    const token = localStorage.getItem('token');
    try {
      const response = await fetch(`${API_URL}/api/reports/batch`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error('Failed to fetch batch reports');
      const data = await response.json();
      setReports(data);
    } catch (err) {
      console.error(err);
    } finally {
      setOverviewLoading(false);
    }
  }, [API_URL]);

  const fetchForensicData = useCallback(async () => {
    setForensicsLoading(true);
    const token = localStorage.getItem('token');
    const headers = { 'Authorization': `Bearer ${token}` };
    try {
      // Fetch summary
      const sumRes = await fetch(`${API_URL}/api/analytics/summary`, { headers });
      if (sumRes.ok) setForensicSummary(await sumRes.json());

      // Fetch cheating rings
      const ringsRes = await fetch(`${API_URL}/api/analytics/cheating-rings`, { headers });
      if (ringsRes.ok) setCheatingRings(await ringsRes.json());

      // Fetch stylometric anomalies
      const styleRes = await fetch(`${API_URL}/api/analytics/stylometric-anomalies`, { headers });
      if (styleRes.ok) setStyleAnomalies(await styleRes.json());

      // Fetch risk factors
      const riskRes = await fetch(`${API_URL}/api/analytics/risk-factors`, { headers });
      if (riskRes.ok) setRiskFactors(await riskRes.json());

      // Fetch comprehensive insights
      const insRes = await fetch(`${API_URL}/api/analytics/insights`, { headers });
      if (insRes.ok) setInsights(await insRes.json());
      
    } catch (err) {
      console.error('Forensic data fetch failed:', err);
    } finally {
      setForensicsLoading(false);
    }
  }, [API_URL]);

  useEffect(() => {
    fetchBatchReports();
  }, [fetchBatchReports]);

  useEffect(() => {
    if (activeTab === 'forensics') {
      fetchForensicData();
    }
  }, [activeTab, fetchForensicData]);

  // Dynamically derive sections from reports
  const sections = useMemo(() => {
    const s = [...new Set(reports.map(r => r.section))].filter(Boolean);
    return s.length > 0 ? s : ['4I1', '4I2']; // Fallback for initial load
  }, [reports]);

  const batchData = sections.map(secName => {
    const secReports = reports.filter(r => r.section === secName || (!r.section && secName === 'CSE-A'));
    const clean = secReports.filter(r => r.plagiarism_score < 20).length;
    const flagged = secReports.filter(r => r.plagiarism_score >= 20).length;
    return { section: secName, original: clean, plagiarized: flagged };
  });

  const sectionReports = selectedSection ? reports.filter(r => r.section === selectedSection || (!r.section && selectedSection === 'CSE-A')) : [];

  const sectionPieData = [
    { name: 'Original', value: sectionReports.filter(r => r.plagiarism_score < 15).length || 1, color: '#10b981' },
    { name: 'Moderate Match', value: sectionReports.filter(r => r.plagiarism_score >= 15 && r.plagiarism_score <= 30).length || 0, color: '#f59e0b' },
    { name: 'High Plagiarism', value: sectionReports.filter(r => r.plagiarism_score > 30).length || 0, color: '#ef4444' }
  ];

  const handleDrillDown = (sectionName) => {
    setSelectedSection(sectionName);
    setView('section');
  };

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
        flexShrink: 0
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

  return (
    <div className="portal-shell" style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 0.5rem' }}>
      
      {/* ── Page Header ── */}
      <div className="flex flex-col-mob md:flex-row md:items-center justify-between gap-4-mob" style={{ marginBottom: '1.75rem' }}>
        <div>
          <h2 style={{ fontWeight: 800, marginBottom: '0.25rem' }}>HOD Dashboard</h2>
          <p className="text-muted" style={{ fontSize: '0.925rem' }}>
            Institutional Evaluation Portal: Monitor academic integrity, stylometric anomalies, and cheating networks.
          </p>
        </div>
        {activeTab === 'overview' && view === 'section' && (
          <button className="btn btn-outline w-full-mob" onClick={() => setView('batch')}>
            <ArrowLeft size={16} />
            <span>Back to Overview</span>
          </button>
        )}
      </div>

      {/* ── Modern Tab Selector ── */}
      <div style={{
        display: 'flex',
        gap: '0.5rem',
        borderBottom: '1px solid var(--border-color)',
        marginBottom: '2rem',
        paddingBottom: '0.5rem'
      }}>
        <button
          onClick={() => { setActiveTab('overview'); setView('batch'); }}
          className="btn"
          style={{
            backgroundColor: activeTab === 'overview' ? 'var(--primary-color)' : 'transparent',
            color: activeTab === 'overview' ? '#ffffff' : 'var(--text-muted)',
            boxShadow: activeTab === 'overview' ? 'var(--shadow-sm)' : 'none',
            fontSize: '0.9rem',
            padding: '0.55rem 1.15rem'
          }}
        >
          <BarChart3 size={16} />
          <span>Institutional Overview</span>
        </button>

        <button
          onClick={() => setActiveTab('forensics')}
          className="btn"
          style={{
            backgroundColor: activeTab === 'forensics' ? 'var(--primary-color)' : 'transparent',
            color: activeTab === 'forensics' ? '#ffffff' : 'var(--text-muted)',
            boxShadow: activeTab === 'forensics' ? 'var(--shadow-sm)' : 'none',
            fontSize: '0.9rem',
            padding: '0.55rem 1.15rem'
          }}
        >
          <Cpu size={16} />
          <span>Forensic AI Analytics</span>
        </button>
      </div>

      {/* ======================================================== */}
      {/*                 TAB 1: INSTITUTIONAL OVERVIEW            */}
      {/* ======================================================== */}
      {activeTab === 'overview' && (
        overviewLoading ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '380px' }}>
            <div className="spinner" style={{ width: '40px', height: '40px' }}></div>
            <p className="text-muted" style={{ marginTop: '1rem', fontSize: '0.9rem' }}>Aggregating batch data across sections...</p>
          </div>
        ) : view === 'batch' ? (
          <>
            <div className="grid md:grid-cols-3 gap-6" style={{ marginBottom: '2rem' }}>
              <SummaryCard title="Total Students Evaluated" value={reports.length} icon={<Users size={22} />} color="#4f46e5" />
              <SummaryCard title="Clean Submissions (<20%)" value={reports.filter(r => r.plagiarism_score < 20).length} icon={<FileCheck size={22} />} color="#10b981" />
              <SummaryCard title="Flagged Plagiarism (≥20%)" value={reports.filter(r => r.plagiarism_score >= 20).length} icon={<AlertCircle size={22} />} color="#ef4444" />
            </div>

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
                        fontSize: '0.85rem'
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
                        transition: 'var(--transition)'
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
                        fontSize: '0.85rem'
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
                {sectionReports.filter(r => r.plagiarism_score > 30).slice(0, 5).map((report) => (
                  <div
                    key={report.submission_id}
                    className="flex items-center justify-between"
                    style={{
                      padding: '0.9rem 1.15rem',
                      border: '1px solid rgba(239, 68, 68, 0.25)',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: 'var(--danger-light)'
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
                {sectionReports.filter(r => r.plagiarism_score > 30).length === 0 && (
                  <div className="text-center text-muted" style={{ padding: '3rem 1rem' }}>
                    <ShieldCheck size={32} style={{ color: 'var(--success-color)', margin: '0 auto 0.5rem auto' }} />
                    <p style={{ margin: 0, fontSize: '0.9rem' }}>No high-risk plagiarism cases detected in this section.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )
      )}

      {/* ======================================================== */}
      {/*                 TAB 2: FORENSIC AI ANALYTICS             */}
      {/* ======================================================== */}
      {activeTab === 'forensics' && (
        forensicsLoading ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '380px' }}>
            <div className="spinner" style={{ width: '40px', height: '40px' }}></div>
            <p className="text-muted" style={{ marginTop: '1rem', fontSize: '0.9rem' }}>Running graph clustering and stylometric analysis...</p>
          </div>
        ) : (
          <>
            {/* Forensic overview stats cards */}
            <div className="grid md:grid-cols-4 gap-6" style={{ marginBottom: '2rem' }}>
              <SummaryCard 
                title="Evaluated Papers" 
                value={forensicSummary?.total_evaluated || 0} 
                icon={<ShieldCheck size={22} />} 
                color="#10b981" 
              />
              <SummaryCard 
                title="Active Cheating Rings" 
                value={forensicSummary?.active_cheating_rings || 0} 
                icon={<AlertTriangle size={22} />} 
                color="#ef4444" 
              />
              <SummaryCard 
                title="Stylometric Anomalies" 
                value={forensicSummary?.stylometric_anomalies || 0} 
                icon={<Clock size={22} />} 
                color="#f59e0b" 
              />
              <SummaryCard 
                title="Teacher Hours Saved" 
                value={`${forensicSummary?.hours_saved || 0} Hrs`} 
                icon={<TrendingUp size={22} />} 
                color="#4f46e5" 
              />
            </div>

            {/* Grid for Cheating Rings and Stylometrics */}
            <div className="grid md:grid-cols-2 gap-6" style={{ marginBottom: '2rem' }}>
              
              {/* Cheating Rings Network Panel */}
              <div className="card glass-panel" style={{ maxHeight: '520px', overflowY: 'auto', padding: '1.75rem' }}>
                <div style={{ marginBottom: '1.25rem' }}>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem', margin: 0 }}>
                    <AlertTriangle style={{ color: 'var(--danger-color)' }} size={18} />
                    <span>Social Plagiarism Networks (Cheating Rings)</span>
                  </h3>
                  <p className="text-muted" style={{ fontSize: '0.825rem', margin: '0.35rem 0 0 0' }}>
                    Connected clusters of students sharing identical content or mutual similarity (&gt;30%).
                  </p>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                  {cheatingRings.map((ring) => (
                    <div 
                      key={ring.ring_id} 
                      style={{
                        padding: '1.1rem',
                        border: '1px solid rgba(239, 68, 68, 0.2)',
                        borderRadius: 'var(--radius-md)',
                        backgroundColor: 'rgba(239, 68, 68, 0.03)'
                      }}
                    >
                      <div className="flex justify-between items-center" style={{ marginBottom: '0.6rem' }}>
                        <span style={{ fontWeight: 700, color: 'var(--danger-color)', fontSize: '0.95rem' }}>
                          {ring.ring_id} ({ring.size} Students)
                        </span>
                        <span className="badge badge-danger">
                          Max similarity: {ring.max_similarity}%
                        </span>
                      </div>

                      <div style={{ marginBottom: '0.65rem' }}>
                        <strong style={{ fontSize: '0.825rem', color: 'var(--text-main)' }}>Members:</strong>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginTop: '0.3rem' }}>
                          {ring.members.map(member => (
                            <span 
                              key={member.id} 
                              className="badge badge-neutral"
                              style={{ fontSize: '0.75rem' }}
                            >
                              {member.name} ({member.section})
                            </span>
                          ))}
                        </div>
                      </div>

                      <div>
                        <strong style={{ fontSize: '0.825rem', color: 'var(--text-main)' }}>Shared Courses:</strong>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
                          {ring.subjects.join(', ')}
                        </div>
                      </div>
                    </div>
                  ))}

                  {cheatingRings.length === 0 && (
                    <div className="text-center text-muted" style={{ padding: '3rem 1rem' }}>
                      <p style={{ margin: 0, fontSize: '0.9rem' }}>No multi-student collusion clusters identified in the database.</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Stylometric Anomalies Panel */}
              <div className="card glass-panel" style={{ maxHeight: '520px', overflowY: 'auto', padding: '1.75rem' }}>
                <div style={{ marginBottom: '1.25rem' }}>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem', margin: 0 }}>
                    <Clock style={{ color: 'var(--warning-color)' }} size={18} />
                    <span>Authorship Fingerprints (Stylometric Shifts)</span>
                  </h3>
                  <p className="text-muted" style={{ fontSize: '0.825rem', margin: '0.35rem 0 0 0' }}>
                    Significant divergence (&gt;2.0σ Z-score) from a student's established writing profile.
                  </p>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                  {styleAnomalies.map((anom) => (
                    <div 
                      key={anom.submission_id} 
                      style={{
                        padding: '1.1rem',
                        border: '1px solid rgba(245, 158, 11, 0.25)',
                        borderRadius: 'var(--radius-md)',
                        backgroundColor: 'rgba(245, 158, 11, 0.03)'
                      }}
                    >
                      <div className="flex justify-between items-center" style={{ marginBottom: '0.5rem' }}>
                        <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>{anom.student_name} ({anom.section})</span>
                        <span className="badge badge-warning">
                          Shift: {anom.style_deviation}σ
                        </span>
                      </div>

                      <div style={{ fontSize: '0.825rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                        <strong>Course:</strong> {anom.subject} | <strong>File:</strong> {anom.filename}
                      </div>

                      <div style={{ 
                        fontSize: '0.8rem', 
                        backgroundColor: 'var(--bg-color)', 
                        padding: '0.6rem 0.75rem', 
                        borderRadius: 'var(--radius-sm)',
                        borderLeft: '3px solid var(--warning-color)',
                        lineHeight: '1.5',
                        color: 'var(--text-main)'
                      }}>
                        {anom.reasoning}
                      </div>
                    </div>
                  ))}

                  {styleAnomalies.length === 0 && (
                    <div className="text-center text-muted" style={{ padding: '3rem 1rem' }}>
                      <p style={{ margin: 0, fontSize: '0.9rem' }}>No significant stylometric anomalies detected across student profiles.</p>
                    </div>
                  )}
                </div>
              </div>

            </div>

            {/* Grid for Temporal Risk Analysis and Subject Vulnerability */}
            <div className="grid md:grid-cols-3 gap-6">
              
              {/* Hourly Plagiarism Risk Chart */}
              <div className="card glass-panel md:col-span-2" style={{ padding: '1.75rem' }}>
                <h3 style={{ marginBottom: '0.25rem', fontSize: '1.15rem', fontWeight: 700 }}>
                  Submission Timing & Plagiarism Correlation
                </h3>
                <p className="text-muted" style={{ fontSize: '0.825rem', marginBottom: '1.5rem' }}>
                  Average plagiarism overlap and AI-generated probability indexed by time of submission.
                </p>
                <div style={{ height: '280px' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={riskFactors} margin={{ top: 10, right: 10, left: -15, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-color)" />
                      <XAxis dataKey="hour" axisLine={false} tickLine={false} tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                      <YAxis axisLine={false} tickLine={false} tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                      <RechartsTooltip
                        contentStyle={{
                          backgroundColor: 'rgba(255, 255, 255, 0.95)',
                          border: '1px solid var(--border-color)',
                          borderRadius: 'var(--radius-md)',
                          fontSize: '0.85rem'
                        }}
                      />
                      <Legend wrapperStyle={{ paddingTop: '8px' }} />
                      <Bar dataKey="avg_plagiarism" name="Avg Plagiarism %" fill="#ef4444" radius={[3, 3, 0, 0]} />
                      <Bar dataKey="avg_ai" name="Avg AI Score %" fill="#4f46e5" radius={[3, 3, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Subject Vulnerability Ranks */}
              <div className="card glass-panel md:col-span-1" style={{ maxHeight: '420px', overflowY: 'auto', padding: '1.75rem' }}>
                <h3 style={{ marginBottom: '0.25rem', fontSize: '1.15rem', fontWeight: 700 }}>
                  Course Risk Ranking
                </h3>
                <p className="text-muted" style={{ fontSize: '0.825rem', marginBottom: '1.25rem' }}>
                  Academic subjects ordered by aggregate vulnerability and overlap rate.
                </p>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
                  {insights?.subject_vulnerabilities?.map((sub, idx) => (
                    <div 
                      key={sub.subject} 
                      className="flex items-center justify-between"
                      style={{ 
                        padding: '0.8rem 1rem', 
                        border: '1px solid var(--border-color)', 
                        borderRadius: 'var(--radius-md)',
                        backgroundColor: idx === 0 ? 'var(--danger-light)' : 'var(--surface-color)'
                      }}
                    >
                      <div>
                        <div style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--text-main)' }}>{sub.subject}</div>
                        <span className="text-muted" style={{ fontSize: '0.75rem' }}>
                          {sub.submissions_count} papers • Plag: {sub.avg_plagiarism}%
                        </span>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <div style={{ 
                          fontWeight: 800, 
                          color: sub.vulnerability_score > 30 ? 'var(--danger-color)' : 'var(--success-color)',
                          fontSize: '1.05rem',
                          lineHeight: 1
                        }}>
                          {sub.vulnerability_score}
                        </div>
                        <span className="text-muted" style={{ fontSize: '0.7rem' }}>Risk Score</span>
                      </div>
                    </div>
                  ))}

                  {(!insights?.subject_vulnerabilities || insights.subject_vulnerabilities.length === 0) && (
                    <div className="text-center text-muted" style={{ padding: '2rem 1rem' }}>
                      <p style={{ margin: 0, fontSize: '0.85rem' }}>No course statistics computed yet.</p>
                    </div>
                  )}
                </div>
              </div>

            </div>
          </>
        )
      )}

    </div>
  );
}

