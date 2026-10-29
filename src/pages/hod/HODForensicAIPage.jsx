import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../../utils/api';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip,
  Legend, ResponsiveContainer
} from 'recharts';
import {
  ShieldCheck, AlertTriangle, Clock, TrendingUp
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

export default function HODForensicAIPage() {
  const [forensicSummary, setForensicSummary] = useState(null);
  const [cheatingRings, setCheatingRings] = useState([]);
  const [styleAnomalies, setStyleAnomalies] = useState([]);
  const [riskFactors, setRiskFactors] = useState([]);
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchForensicData = useCallback(async () => {
    setLoading(true);
    try {
      const [sumRes, ringsRes, styleRes, riskRes, insRes] = await Promise.all([
        api.get('/api/analytics/summary'),
        api.get('/api/analytics/cheating-rings'),
        api.get('/api/analytics/stylometric-anomalies'),
        api.get('/api/analytics/risk-factors'),
        api.get('/api/analytics/insights'),
      ]);

      if (sumRes.ok) setForensicSummary(await sumRes.json());
      if (ringsRes.ok) setCheatingRings(await ringsRes.json());
      if (styleRes.ok) setStyleAnomalies(await styleRes.json());
      if (riskRes.ok) setRiskFactors(await riskRes.json());
      if (insRes.ok) setInsights(await insRes.json());
    } catch (err) {
      console.error('Forensic data fetch failed:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchForensicData();
  }, [fetchForensicData]);

  return (
    <>
      {/* Content Header */}
      <div className="teacher-content-header" style={{ marginBottom: '1.75rem' }}>
        <h2>Forensic AI Analytics</h2>
        <p>Deep dive into graph clustering, stylometrics, and plagiarism networks.</p>
      </div>

      {loading ? (
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
                      backgroundColor: 'rgba(239, 68, 68, 0.03)',
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
                        {ring.members.map((member) => (
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
                      backgroundColor: 'rgba(245, 158, 11, 0.03)',
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
                      color: 'var(--text-main)',
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
                        fontSize: '0.85rem',
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
                      backgroundColor: idx === 0 ? 'var(--danger-light)' : 'var(--surface-color)',
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
                        lineHeight: 1,
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
      )}
    </>
  );
}
