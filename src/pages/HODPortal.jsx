import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { ArrowLeft, Users, AlertCircle, FileCheck, ExternalLink, ShieldCheck, Clock, AlertTriangle, Cpu, TrendingUp } from 'lucide-react';

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
    <div className="card flex items-center gap-4">
      <div style={{ padding: '1rem', borderRadius: '50%', backgroundColor: `${color}15`, color: color }}>
        {icon}
      </div>
      <div>
        <h4 className="text-muted" style={{ fontSize: '0.875rem', fontWeight: 500, marginBottom: '0.25rem' }}>{title}</h4>
        <p style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>{value}</p>
      </div>
    </div>
  );

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 1rem' }}>
      
      {/* --- Page Header --- */}
      <div className="flex flex-col-mob md:items-center justify-between gap-4-mob" style={{ marginBottom: '1.5rem' }}>
        <div>
          <h2>HOD Dashboard</h2>
          <p className="text-muted">
            Institutional Evaluation Portal: Monitor academic integrity, style anomalies and cheating networks.
          </p>
        </div>
        {activeTab === 'overview' && view === 'section' && (
          <button className="btn btn-outline w-full-mob" onClick={() => setView('batch')}>
            <ArrowLeft size={16} /> Back to Overview
          </button>
        )}
      </div>

      {/* --- Premium Tab Selector --- */}
      <div style={{
        display: 'flex',
        borderBottom: '1px solid var(--border-color)',
        marginBottom: '2rem',
        gap: '2rem'
      }}>
        <button
          onClick={() => { setActiveTab('overview'); setView('batch'); }}
          style={{
            background: 'none',
            border: 'none',
            padding: '0.75rem 0',
            fontWeight: 600,
            fontSize: '1rem',
            color: activeTab === 'overview' ? 'var(--primary-color)' : 'var(--text-muted)',
            borderBottom: activeTab === 'overview' ? '3px solid var(--primary-color)' : '3px solid transparent',
            cursor: 'pointer',
            transition: 'all 0.2s'
          }}
        >
          Institutional Overview
        </button>
        <button
          onClick={() => setActiveTab('forensics')}
          style={{
            background: 'none',
            border: 'none',
            padding: '0.75rem 0',
            fontWeight: 600,
            fontSize: '1rem',
            color: activeTab === 'forensics' ? 'var(--primary-color)' : 'var(--text-muted)',
            borderBottom: activeTab === 'forensics' ? '3px solid var(--primary-color)' : '3px solid transparent',
            cursor: 'pointer',
            transition: 'all 0.2s',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}
        >
          <Cpu size={16} /> Forensic AI Analytics
        </button>
      </div>

      {/* ======================================================== */}
      {/*                 TAB 1: INSTITUTIONAL OVERVIEW            */}
      {/* ======================================================== */}
      {activeTab === 'overview' && (
        overviewLoading ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '400px' }}>
            <div className="spinner" style={{ width: '40px', height: '40px' }}></div>
            <p className="text-muted" style={{ marginTop: '1rem' }}>Aggregating batch data...</p>
          </div>
        ) : view === 'batch' ? (
          <>
            <div className="grid md:grid-cols-3 gap-6" style={{ marginBottom: '2rem' }}>
              <SummaryCard title="Total Students Evaluated" value={reports.length} icon={<Users size={24} />} color="#4f46e5" />
              <SummaryCard title="Overall Clean Submissions" value={reports.filter(r => r.plagiarism_score < 20).length} icon={<FileCheck size={24} />} color="#10b981" />
              <SummaryCard title="Flagged for Plagiarism" value={reports.filter(r => r.plagiarism_score >= 20).length} icon={<AlertCircle size={24} />} color="#ef4444" />
            </div>

            <div className="card">
              <h3 style={{ marginBottom: '1.5rem', fontSize: '1.25rem' }}>Plagiarism Comparison Across Sections</h3>
              <div style={{ height: '400px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={batchData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-color)" />
                    <XAxis dataKey="section" axisLine={false} tickLine={false} />
                    <YAxis axisLine={false} tickLine={false} />
                    <RechartsTooltip cursor={{ fill: 'rgba(79, 70, 229, 0.05)' }} />
                    <Legend />
                    <Bar dataKey="original" name="Original Content" stackId="a" fill="#10b981" radius={[0, 0, 4, 4]} />
                    <Bar dataKey="plagiarized" name="Plagiarized" stackId="a" fill="#ef4444" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div style={{ marginTop: '2rem' }}>
              <h3 style={{ marginBottom: '1rem', fontSize: '1.25rem' }}>Section Breakdown</h3>
              <div className="grid md:grid-cols-4 gap-4">
                {batchData.map((data) => (
                  <div key={data.section} className="card" style={{ padding: '1rem', cursor: 'pointer' }} onClick={() => handleDrillDown(data.section)}>
                    <div className="flex items-center justify-between mb-2">
                      <span style={{ fontWeight: 600 }}>{data.section}</span>
                      <ExternalLink size={16} className="text-muted" />
                    </div>
                    <div className="flex justify-between text-muted" style={{ fontSize: '0.875rem' }}>
                      <span>Plagiarized:</span>
                      <span style={{ color: 'var(--danger-color)', fontWeight: 600 }}>
                        {data.original + data.plagiarized > 0 
                          ? `${Math.round((data.plagiarized / (data.original + data.plagiarized)) * 100)}%` 
                          : '0%'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        ) : (
          <div className="grid md:grid-cols-2 gap-6">
            <div className="card">
              <h3 style={{ marginBottom: '1.5rem', fontSize: '1.25rem' }}>{selectedSection} Plagiarism Distribution</h3>
              <div style={{ height: '300px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={sectionPieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={80}
                      outerRadius={110}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {sectionPieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <RechartsTooltip />
                    <Legend verticalAlign="bottom" height={36} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="card">
              <h3 style={{ marginBottom: '1.5rem', fontSize: '1.25rem' }}>Top Critical Cases</h3>
              <p className="text-muted" style={{ marginBottom: '1rem' }}>Students exceeding maximum acceptable threshold (30%).</p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {sectionReports.filter(r => r.plagiarism_score > 30).slice(0, 5).map((report) => (
                  <div key={report.submission_id} className="flex items-center justify-between" style={{ padding: '1rem', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)' }}>
                    <div>
                      <h5 style={{ margin: 0 }}>{report.student_name}</h5>
                      <span className="text-muted" style={{ fontSize: '0.85rem' }}>Subject: {report.subject}</span>
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      <span style={{ color: 'var(--danger-color)', fontWeight: 600, fontSize: '1.1rem' }}>{report.plagiarism_score}%</span>
                    </div>
                  </div>
                ))}
                {sectionReports.filter(r => r.plagiarism_score > 30).length === 0 && (
                  <div className="text-center text-muted" style={{ padding: '2rem' }}>No critical cases in this section.</div>
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
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '400px' }}>
            <div className="spinner" style={{ width: '40px', height: '40px' }}></div>
            <p className="text-muted" style={{ marginTop: '1rem' }}>Running forensic data mining algorithms...</p>
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
                title="Authorship anomalies" 
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
              <div className="card" style={{ maxHeight: '500px', overflowY: 'auto' }}>
                <div style={{ marginBottom: '1.25rem' }}>
                  <h3 style={{ fontSize: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <AlertTriangle style={{ color: 'var(--danger-color)' }} size={20} />
                    Social Plagiarism Networks (Cheating Rings)
                  </h3>
                  <p className="text-muted" style={{ fontSize: '0.85rem' }}>
                    Connected groups of students uploading work of high mutual similarity (&gt;30%) or identical visual hashes.
                  </p>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {cheatingRings.map((ring) => (
                    <div 
                      key={ring.ring_id} 
                      style={{
                        padding: '1rem',
                        border: '1px solid var(--border-color)',
                        borderRadius: 'var(--radius-md)',
                        backgroundColor: 'rgba(239, 68, 68, 0.02)'
                      }}
                    >
                      <div className="flex justify-between items-center" style={{ marginBottom: '0.5rem' }}>
                        <span style={{ fontWeight: 700, color: 'var(--danger-color)' }}>{ring.ring_id} ({ring.size} Students)</span>
                        <span className="badge" style={{ backgroundColor: 'var(--danger-color)', color: '#fff', fontSize: '0.8rem', padding: '0.2rem 0.5rem' }}>
                          Max similarity: {ring.max_similarity}%
                        </span>
                      </div>

                      <div style={{ marginBottom: '0.75rem' }}>
                        <strong style={{ fontSize: '0.85rem' }}>Members:</strong>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.25rem' }}>
                          {ring.members.map(member => (
                            <span 
                              key={member.id} 
                              className="text-muted" 
                              style={{ 
                                fontSize: '0.8rem', 
                                backgroundColor: 'var(--border-color)', 
                                padding: '0.15rem 0.4rem', 
                                borderRadius: '4px' 
                              }}
                            >
                              {member.name} ({member.section})
                            </span>
                          ))}
                        </div>
                      </div>

                      <div>
                        <strong style={{ fontSize: '0.85rem' }}>Shared Subjects:</strong>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.1rem' }}>
                          {ring.subjects.join(', ')}
                        </div>
                      </div>
                    </div>
                  ))}

                  {cheatingRings.length === 0 && (
                    <div className="text-center text-muted" style={{ padding: '2rem' }}>
                      No multi-student cheating rings identified in the database yet.
                    </div>
                  )}
                </div>
              </div>

              {/* Stylometric Anomalies Panel */}
              <div className="card" style={{ maxHeight: '500px', overflowY: 'auto' }}>
                <div style={{ marginBottom: '1.25rem' }}>
                  <h3 style={{ fontSize: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Clock style={{ color: 'var(--warning-color)' }} size={20} />
                    Authorship Verification (Stylometric Deviations)
                  </h3>
                  <p className="text-muted" style={{ fontSize: '0.85rem' }}>
                    Students showing severe style shifts (&gt;2.0σ average Z-score deviation) compared to their own historical fingerprints.
                  </p>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {styleAnomalies.map((anom) => (
                    <div 
                      key={anom.submission_id} 
                      style={{
                        padding: '1rem',
                        border: '1px solid var(--border-color)',
                        borderRadius: 'var(--radius-md)',
                        backgroundColor: 'rgba(245, 158, 11, 0.02)'
                      }}
                    >
                      <div className="flex justify-between items-center" style={{ marginBottom: '0.5rem' }}>
                        <span style={{ fontWeight: 600 }}>{anom.student_name} ({anom.section})</span>
                        <span style={{ 
                          fontSize: '0.8rem', 
                          fontWeight: 700, 
                          color: 'var(--warning-color)',
                          backgroundColor: 'rgba(245, 158, 11, 0.1)',
                          padding: '0.2rem 0.5rem',
                          borderRadius: '4px'
                        }}>
                          Shift: {anom.style_deviation}σ
                        </span>
                      </div>

                      <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                        <strong>Sub:</strong> {anom.subject} | <strong>File:</strong> {anom.filename}
                      </div>

                      <div style={{ 
                        fontSize: '0.8rem', 
                        backgroundColor: 'rgba(0,0,0,0.02)', 
                        padding: '0.5rem', 
                        borderRadius: '4px',
                        borderLeft: '3px solid var(--warning-color)',
                        lineHeight: '1.4'
                      }}>
                        {anom.reasoning}
                      </div>
                    </div>
                  ))}

                  {styleAnomalies.length === 0 && (
                    <div className="text-center text-muted" style={{ padding: '2rem' }}>
                      No severe stylometric anomalies detected. Student writing profiles remain consistent.
                    </div>
                  )}
                </div>
              </div>

            </div>

            {/* Grid for Temporal Risk Analysis and Subject Vulnerability */}
            <div className="grid md:grid-cols-3 gap-6">
              
              {/* Hourly Plagiarism Risk Chart */}
              <div className="card md:col-span-2">
                <h3 style={{ marginBottom: '0.5rem', fontSize: '1.25rem' }}>Hourly Plagiarism & AI Generation Risk</h3>
                <p className="text-muted" style={{ fontSize: '0.85rem', marginBottom: '1.5rem' }}>
                  A breakdown of average plagiarized content ratio (TF-IDF) and AI-generated probability based on the hour of submission.
                </p>
                <div style={{ height: '300px' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={riskFactors} margin={{ top: 10, right: 10, left: -10, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-color)" />
                      <XAxis dataKey="hour" axisLine={false} tickLine={false} />
                      <YAxis axisLine={false} tickLine={false} />
                      <RechartsTooltip />
                      <Legend />
                      <Bar dataKey="avg_plagiarism" name="Avg Plagiarism %" fill="#ef4444" radius={[3, 3, 0, 0]} />
                      <Bar dataKey="avg_ai" name="Avg AI Score %" fill="#4f46e5" radius={[3, 3, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Subject Vulnerability Ranks */}
              <div className="card md:col-span-1" style={{ maxHeight: '420px', overflowY: 'auto' }}>
                <h3 style={{ marginBottom: '0.5rem', fontSize: '1.25rem' }}>Subject Vulnerability Ranking</h3>
                <p className="text-muted" style={{ fontSize: '0.85rem', marginBottom: '1rem' }}>
                  Ranked list of academic courses based on their aggregate plagiarism risk score.
                </p>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {insights?.subject_vulnerabilities?.map((sub, idx) => (
                    <div 
                      key={sub.subject} 
                      className="flex items-center justify-between"
                      style={{ 
                        padding: '0.75rem', 
                        border: '1px solid var(--border-color)', 
                        borderRadius: 'var(--radius-md)',
                        backgroundColor: idx === 0 ? 'rgba(239, 68, 68, 0.02)' : 'transparent'
                      }}
                    >
                      <div>
                        <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{sub.subject}</div>
                        <span className="text-muted" style={{ fontSize: '0.75rem' }}>
                          {sub.submissions_count} papers | Plag: {sub.avg_plagiarism}%
                        </span>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <div style={{ 
                          fontWeight: 700, 
                          color: sub.vulnerability_score > 30 ? 'var(--danger-color)' : 'var(--success-color)',
                          fontSize: '1rem'
                        }}>
                          {sub.vulnerability_score}
                        </div>
                        <span className="text-muted" style={{ fontSize: '0.75rem' }}>Risk Score</span>
                      </div>
                    </div>
                  ))}

                  {(!insights?.subject_vulnerabilities || insights.subject_vulnerabilities.length === 0) && (
                    <div className="text-center text-muted" style={{ padding: '2rem' }}>
                      No subject statistics computed.
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
