import React from 'react';
import { ShieldCheck, X, Download } from 'lucide-react';

export default function ReceiptModal({ receipt, onClose, onDownloadReceiptText }) {
  if (!receipt) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '560px', padding: '2rem' }}>
        <div className="flex justify-between items-center" style={{ marginBottom: '1.25rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
          <div className="flex items-center gap-2">
            <ShieldCheck size={22} style={{ color: 'var(--success-color)' }} />
            <h4 style={{ fontWeight: 800 }}>Institutional Submission Receipt</h4>
          </div>
          <button
            type="button"
            onClick={onClose}
            style={{ color: 'var(--text-muted)', padding: '0.25rem', background: 'none', border: 'none', cursor: 'pointer' }}
            aria-label="Close"
          >
            <X size={20} />
          </button>
        </div>

        <div style={{
          backgroundColor: 'var(--primary-light)',
          border: '1px dashed var(--primary-color)',
          borderRadius: 'var(--radius-md)',
          padding: '0.75rem 1rem',
          marginBottom: '1.25rem',
        }}>
          <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--primary-color)', textTransform: 'uppercase' }}>
            Verification Token
          </div>
          <div style={{ fontFamily: 'monospace', fontWeight: 800, fontSize: '0.95rem', color: 'var(--text-main)' }}>
            {receipt.verification_token || `PLAG-SEC-${String(receipt.id).padStart(4, '0')}-REG`}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3" style={{ fontSize: '0.85rem', marginBottom: '1.5rem' }}>
          <div>
            <span className="text-muted">Subject:</span>
            <div style={{ fontWeight: 700 }}>{receipt.subject}</div>
          </div>
          <div>
            <span className="text-muted">Assignment:</span>
            <div style={{ fontWeight: 700 }}>{receipt.assignment_title}</div>
          </div>
          <div>
            <span className="text-muted">File:</span>
            <div style={{ fontWeight: 700 }}>{receipt.filename}</div>
          </div>
          <div>
            <span className="text-muted">Submitted At:</span>
            <div style={{ fontWeight: 700 }}>{new Date(receipt.created_at || receipt.locked_at).toLocaleString()}</div>
          </div>
          <div>
            <span className="text-muted">OCR Legibility:</span>
            <div style={{ fontWeight: 700, color: 'var(--success-color)' }}>
              {receipt.ocr_score != null ? `${receipt.ocr_score}%` : '100%'}
            </div>
          </div>
          <div>
            <span className="text-muted">Forensic Classification:</span>
            <div style={{ fontWeight: 700 }}>{receipt.label || 'Original'}</div>
          </div>
        </div>

        <div className="flex justify-between items-center">
          <button
            type="button"
            className="btn btn-outline"
            onClick={onClose}
          >
            Close
          </button>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => onDownloadReceiptText(receipt)}
          >
            <Download size={15} /> Download Receipt (.txt)
          </button>
        </div>
      </div>
    </div>
  );
}
