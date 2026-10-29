import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { api } from '../../utils/api';
import { Search, ShieldCheck, Download, RefreshCw, FileText, CheckCircle2 } from 'lucide-react';
import ReceiptModal from '../../components/student/ReceiptModal';

export default function StudentSubmissionsPage() {
  const navigate = useNavigate();
  const location = useLocation();

  const [historySubmissions, setHistorySubmissions] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [historySearch, setHistorySearch] = useState('');
  const [selectedReceiptModal, setSelectedReceiptModal] = useState(null);
  const [skipNotification, setSkipNotification] = useState(location.state?.skipNotification || '');

  const fetchHistory = async () => {
    setLoadingHistory(true);
    try {
      const res = await api.get('/api/submissions/my');
      if (res.ok) {
        const data = await res.json();
        setHistorySubmissions(data);
      }
    } catch (err) {
      console.error('Failed to load history:', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  // Auto-refresh history while any submission is pending or processing
  useEffect(() => {
    const hasPending = historySubmissions.some(
      (s) => s.status === 'pending' || s.status === 'processing'
    );
    if (!hasPending) return;

    const timer = setInterval(() => {
      fetchHistory();
    }, 3500);

    return () => clearInterval(timer);
  }, [historySubmissions]);

  const filteredHistory = useMemo(() => {
    if (!historySearch.trim()) return historySubmissions;
    const q = historySearch.toLowerCase();
    return historySubmissions.filter(
      (s) =>
        s.subject.toLowerCase().includes(q) ||
        s.assignment_title.toLowerCase().includes(q) ||
        s.filename.toLowerCase().includes(q) ||
        (s.verification_token && s.verification_token.toLowerCase().includes(q))
    );
  }, [historySubmissions, historySearch]);

  const handleDownloadFile = async (subId, filename) => {
    try {
      const response = await api.get(`/api/download/${subId}`);
      if (!response.ok) throw new Error('Download failed');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || `submission_${subId}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      alert(`Could not download file: ${err.message}`);
    }
  };

  const handleDownloadReceiptText = (receipt) => {
    if (!receipt) return;
    const content = `=====================================================
PLAGIARISM AI — OFFICIAL SUBMISSION RECEIPT
=====================================================
Verification Token: ${receipt.verification_token || 'N/A'}
Status:             LOCKED & VERIFIED IN INSTITUTIONAL REGISTRY
Timestamp (UTC):    ${receipt.locked_at ? new Date(receipt.locked_at).toUTCString() : new Date().toUTCString()}

ASSIGNMENT DETAILS:
Subject:            ${receipt.subject}
Assignment Title:   ${receipt.assignment_title}
Uploaded File:      ${receipt.filename}

FORENSIC AUDIT & QUALITY METRICS:
OCR Legibility Score: ${receipt.ocr_score != null ? `${receipt.ocr_score}%` : '100% (Digital Text)'}
Plagiarism Match:     ${receipt.plagiarism_score != null ? `${receipt.plagiarism_score}%` : '0%'}
AI Forensics Score:   ${receipt.ai_score != null ? `${receipt.ai_score}%` : '0%'}
Integrity Status:     ACCEPTED & SEALED
=====================================================
Verified by PlagiarismAI Deep Forensics Engine.
`;

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Submission_Receipt_${receipt.submission_id || receipt.id}.txt`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    a.remove();
  };

  const getFileBadge = (filename) => {
    const ext = filename?.split('.').pop()?.toUpperCase() || 'FILE';
    const isImage = ['JPG', 'JPEG', 'PNG'].includes(ext);
    const isPdf = ext === 'PDF';
    const isDoc = ['DOC', 'DOCX'].includes(ext);

    let badgeClass = 'badge-neutral';
    if (isImage) badgeClass = 'badge-accent';
    else if (isPdf) badgeClass = 'badge-danger';
    else if (isDoc) badgeClass = 'badge-primary';

    return <span className={`badge ${badgeClass}`} style={{ fontSize: '0.7rem', fontWeight: 700 }}>.{ext}</span>;
  };

  const handleReviewSubmission = (sub) => {
    navigate('/student/submit', { state: { reviewSubmissionId: sub.id } });
  };

  return (
    <>
      {/* Content Header */}
      <div className="teacher-content-header">
        <h2>My Submissions</h2>
        <p>Review past assignments, similarity scores, verification certificates, and integrity logs.</p>
      </div>

      {/* Skip Notification Banner */}
      {skipNotification && (
        <div className="alert alert-success" style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem' }}>
          <div className="flex items-center gap-2">
            <CheckCircle2 size={20} style={{ flexShrink: 0 }} />
            <span>{skipNotification}</span>
          </div>
          <button
            type="button"
            onClick={() => setSkipNotification('')}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit', fontWeight: 700 }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Submissions Table / Card */}
      <div className="card glass-panel" style={{ padding: '1.75rem' }}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3" style={{ marginBottom: '1.5rem' }}>
          <div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, margin: 0 }}>Submission Records</h3>
            <p className="text-muted" style={{ fontSize: '0.825rem', margin: '0.2rem 0 0 0' }}>
              Showing {filteredHistory.length} assignment record{filteredHistory.length !== 1 ? 's' : ''}
            </p>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem', width: '100%', maxWidth: '320px' }}>
            <div style={{ position: 'relative', width: '100%' }}>
              <input
                type="text"
                className="form-input"
                placeholder="Search subject, title, token..."
                value={historySearch}
                onChange={(e) => setHistorySearch(e.target.value)}
                style={{ paddingLeft: '2.5rem', paddingRight: '0.75rem', fontSize: '0.85rem' }}
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
            <button
              type="button"
              className="btn btn-outline"
              onClick={fetchHistory}
              title="Refresh submissions"
              style={{ padding: '0.4rem 0.65rem' }}
            >
              <RefreshCw size={15} className={loadingHistory ? 'spin' : ''} />
            </button>
          </div>
        </div>

        {loadingHistory && historySubmissions.length === 0 ? (
          <div style={{ padding: '3.5rem 1rem', textAlign: 'center' }}>
            <div className="spinner" style={{ margin: '0 auto', width: '36px', height: '36px' }}></div>
            <p className="text-muted" style={{ marginTop: '1rem', fontSize: '0.9rem' }}>Loading submission records...</p>
          </div>
        ) : filteredHistory.length === 0 ? (
          <div style={{ padding: '3.5rem 1rem', textAlign: 'center' }}>
            <FileText size={40} style={{ color: 'var(--text-subtle)', margin: '0 auto 0.75rem' }} />
            <h4 style={{ fontWeight: 700, color: 'var(--text-main)', marginBottom: '0.25rem' }}>No Submissions Found</h4>
            <p className="text-muted" style={{ fontSize: '0.85rem' }}>
              {historySearch ? 'No assignments match your search filter.' : 'You have not submitted any assignments yet.'}
            </p>
          </div>
        ) : (
          <>
            {/* Desktop Table */}
            <div className="table-responsive teacher-table-desktop" style={{ overflowX: 'auto', width: '100%' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', minWidth: '700px' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid var(--border-color)', color: 'var(--text-muted)', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    <th style={{ padding: '0.75rem 0.5rem' }}>Document</th>
                    <th style={{ padding: '0.75rem 0.5rem' }}>Course & Title</th>
                    <th style={{ padding: '0.75rem 0.5rem' }}>Submitted At</th>
                    <th style={{ padding: '0.75rem 0.5rem' }}>OCR Clarity</th>
                    <th style={{ padding: '0.75rem 0.5rem' }}>Plagiarism</th>
                    <th style={{ padding: '0.75rem 0.5rem' }}>AI Forensics</th>
                    <th style={{ padding: '0.75rem 0.5rem', textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredHistory.map((sub) => {
                    const isProcessing = sub.status === 'processing' || sub.status === 'pending';
                    const isHighPlag = sub.plagiarism_score > 30;
                    return (
                      <tr key={sub.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                        <td style={{ padding: '0.85rem 0.5rem' }}>
                          <div className="flex items-center gap-2">
                            {getFileBadge(sub.filename)}
                            <span style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--text-main)', maxWidth: '160px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={sub.filename}>
                              {sub.filename}
                            </span>
                          </div>
                        </td>
                        <td style={{ padding: '0.85rem 0.5rem' }}>
                          <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{sub.subject}</div>
                          <div className="text-muted" style={{ fontSize: '0.78rem' }}>{sub.assignment_title}</div>
                        </td>
                        <td style={{ padding: '0.85rem 0.5rem', fontSize: '0.825rem', color: 'var(--text-muted)' }}>
                          {new Date(sub.created_at).toLocaleDateString()} {new Date(sub.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </td>
                        <td style={{ padding: '0.85rem 0.5rem' }}>
                          {isProcessing ? (
                            <span className="text-muted" style={{ fontSize: '0.78rem' }}>Analyzing...</span>
                          ) : (
                            <span style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--success-color)' }}>
                              {sub.ocr_score != null ? `${sub.ocr_score}%` : '100%'}
                            </span>
                          )}
                        </td>
                        <td style={{ padding: '0.85rem 0.5rem' }}>
                          {isProcessing ? (
                            <span className="text-muted" style={{ fontSize: '0.78rem' }}>Computing...</span>
                          ) : (
                            <span className={`badge ${isHighPlag ? 'badge-danger' : 'badge-success'}`} style={{ fontSize: '0.78rem' }}>
                              {sub.plagiarism_score != null ? `${sub.plagiarism_score}%` : '0%'}
                            </span>
                          )}
                        </td>
                        <td style={{ padding: '0.85rem 0.5rem' }}>
                          {isProcessing ? (
                            <span className="text-muted" style={{ fontSize: '0.78rem' }}>Scanning...</span>
                          ) : (
                            <div>
                              <div style={{ fontWeight: 700, fontSize: '0.85rem', color: sub.ai_score > 50 ? 'var(--danger-color)' : 'var(--text-main)' }}>
                                {sub.ai_score != null ? `${sub.ai_score}%` : '0%'}
                              </div>
                              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{sub.label}</div>
                            </div>
                          )}
                        </td>
                        <td style={{ padding: '0.85rem 0.5rem', textAlign: 'right' }}>
                          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}>
                            {isProcessing ? (
                              <div className="flex items-center gap-1 text-muted" style={{ fontSize: '0.78rem' }}>
                                <div className="spinner" style={{ width: '12px', height: '12px', borderWidth: '1.5px' }}></div>
                                <span>Processing</span>
                              </div>
                            ) : sub.is_locked ? (
                              <button
                                type="button"
                                className="btn btn-outline"
                                style={{ padding: '0.3rem 0.65rem', fontSize: '0.78rem', gap: '0.3rem' }}
                                onClick={() => setSelectedReceiptModal(sub)}
                              >
                                <ShieldCheck size={14} style={{ color: 'var(--success-color)' }} />
                                <span>Certificate</span>
                              </button>
                            ) : (
                              <button
                                type="button"
                                className="btn btn-primary"
                                style={{ padding: '0.3rem 0.65rem', fontSize: '0.78rem' }}
                                onClick={() => handleReviewSubmission(sub)}
                              >
                                Review & Lock
                              </button>
                            )}

                            <button
                              type="button"
                              className="btn btn-outline"
                              style={{ padding: '0.3rem 0.5rem' }}
                              onClick={() => handleDownloadFile(sub.id, sub.filename)}
                              title="Download File"
                            >
                              <Download size={13} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Mobile Card List */}
            <div className="teacher-mobile-list">
              {filteredHistory.map((sub) => {
                const isProcessing = sub.status === 'processing' || sub.status === 'pending';
                const isHighPlag = sub.plagiarism_score > 30;
                return (
                  <div key={sub.id} className="teacher-student-card">
                    <div className="teacher-student-head">
                      <div>
                        <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>{sub.subject}</div>
                        <div className="teacher-subject-text">{sub.assignment_title} • {sub.filename}</div>
                      </div>
                      <div>
                        {isProcessing ? (
                          <span className="badge badge-neutral">Processing</span>
                        ) : (
                          <span className={`badge ${isHighPlag ? 'badge-danger' : 'badge-success'}`}>
                            {sub.plagiarism_score}% Match
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="teacher-score-grid">
                      <div className="teacher-score-cell">
                        <div className="teacher-score-label">OCR Quality</div>
                        <div className="teacher-score-value" style={{ color: 'var(--success-color)' }}>
                          {isProcessing ? '...' : `${sub.ocr_score || 100}%`}
                        </div>
                      </div>
                      <div className="teacher-score-cell">
                        <div className="teacher-score-label">AI Forensics</div>
                        <div className="teacher-score-value" style={{ color: sub.ai_score > 50 ? 'var(--danger-color)' : 'var(--text-main)' }}>
                          {isProcessing ? '...' : `${sub.ai_score || 0}%`}
                        </div>
                      </div>
                    </div>

                    <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem' }}>
                      {sub.is_locked ? (
                        <button
                          type="button"
                          className="btn btn-outline"
                          style={{ flex: 1, padding: '0.45rem', fontSize: '0.82rem' }}
                          onClick={() => setSelectedReceiptModal(sub)}
                        >
                          <ShieldCheck size={14} style={{ color: 'var(--success-color)' }} />
                          <span>View Certificate</span>
                        </button>
                      ) : !isProcessing ? (
                        <button
                          type="button"
                          className="btn btn-primary"
                          style={{ flex: 1, padding: '0.45rem', fontSize: '0.82rem' }}
                          onClick={() => handleReviewSubmission(sub)}
                        >
                          Review & Lock
                        </button>
                      ) : null}

                      <button
                        type="button"
                        className="btn btn-outline"
                        style={{ padding: '0.45rem 0.75rem' }}
                        onClick={() => handleDownloadFile(sub.id, sub.filename)}
                      >
                        <Download size={15} />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </div>

      {/* Receipt Viewer Modal */}
      <ReceiptModal
        receipt={selectedReceiptModal}
        onClose={() => setSelectedReceiptModal(null)}
        onDownloadReceiptText={handleDownloadReceiptText}
      />
    </>
  );
}
