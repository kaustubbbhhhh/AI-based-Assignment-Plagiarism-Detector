import React from 'react';
import { X, Download, AlertCircle } from 'lucide-react';

export default function TeacherReportModal({
  isOpen,
  onClose,
  report,
  loading,
  error,
  onDownload,
}) {
  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.65)',
        backdropFilter: 'blur(8px)',
        WebkitBackdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '1rem',
      }}
    >
      <div
        className="card glass-panel"
        style={{
          width: '100%',
          maxWidth: '780px',
          maxHeight: '90vh',
          overflowY: 'auto',
          position: 'relative',
          padding: '2rem',
          borderRadius: 'var(--radius-xl)',
        }}
      >
        <button
          onClick={onClose}
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
            cursor: 'pointer',
            border: 'none',
          }}
          aria-label="Close dialog"
        >
          <X size={20} />
        </button>

        {loading ? (
          <div style={{ padding: '4rem 1rem', textAlign: 'center' }}>
            <div className="spinner" style={{ margin: '0 auto', width: '40px', height: '40px' }}></div>
            <p className="text-muted" style={{ marginTop: '1rem', fontSize: '0.9rem' }}>Loading report details...</p>
          </div>
        ) : error ? (
          <div className="alert alert-danger" style={{ margin: '2rem 0' }}>
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        ) : report ? (
          <div>
            <h2 style={{ marginBottom: '0.35rem', fontWeight: 800 }}>Assignment Report</h2>
            <div className="text-muted" style={{ marginBottom: '1.75rem', display: 'flex', gap: '1.25rem', flexWrap: 'wrap', fontSize: '0.9rem' }}>
              <span><strong style={{ color: 'var(--text-main)' }}>Student:</strong> {report.student_name}</span>
              <span>•</span>
              <span><strong style={{ color: 'var(--text-main)' }}>Course:</strong> {report.subject}</span>
            </div>

            <div className="grid md:grid-cols-2 gap-4" style={{ marginBottom: '1.75rem' }}>
              <div
                style={{
                  padding: '1.25rem',
                  backgroundColor: report.plagiarism_score > 30 ? 'var(--danger-light)' : 'var(--success-light)',
                  borderRadius: 'var(--radius-lg)',
                  border: `1px solid ${report.plagiarism_score > 30 ? 'rgba(239, 68, 68, 0.25)' : 'rgba(16, 185, 129, 0.25)'}`,
                }}
              >
                <div style={{ fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                  Plagiarism Overlap
                </div>
                <div
                  style={{
                    fontSize: '2.25rem',
                    fontWeight: 800,
                    color: report.plagiarism_score > 30 ? 'var(--danger-color)' : 'var(--success-color)',
                    lineHeight: 1,
                  }}
                >
                  {report.plagiarism_score}%
                </div>
              </div>

              <div
                style={{
                  padding: '1.25rem',
                  backgroundColor: report.ai_score > 50 ? 'var(--danger-light)' : 'var(--primary-light)',
                  borderRadius: 'var(--radius-lg)',
                  border: `1px solid ${report.ai_score > 50 ? 'rgba(239, 68, 68, 0.25)' : 'rgba(79, 70, 229, 0.25)'}`,
                }}
              >
                <div style={{ fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                  AI Logic Confidence
                </div>
                <div
                  style={{
                    fontSize: '2.25rem',
                    fontWeight: 800,
                    color: report.ai_score > 50 ? 'var(--danger-color)' : 'var(--primary-color)',
                    lineHeight: 1,
                  }}
                >
                  {report.ai_score}%
                </div>
                <div style={{ fontSize: '0.825rem', fontWeight: 600, marginTop: '0.35rem', color: 'var(--text-main)' }}>
                  Classification: {report.label}
                </div>
              </div>
            </div>

            <div style={{ marginBottom: '1.75rem' }}>
              <h4 style={{ marginBottom: '0.75rem', fontSize: '1rem', fontWeight: 700 }}>Extracted Text Content</h4>
              <div
                style={{
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
                  fontFamily: 'inherit',
                }}
              >
                {report.processed_text || 'No extracted text preview available.'}
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', borderTop: '1px solid var(--border-color)', paddingTop: '1.25rem' }}>
              <button
                className="btn btn-primary"
                onClick={() => onDownload(report.submission_id, report.student_name)}
              >
                <Download size={16} />
                <span>Download Original File</span>
              </button>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
