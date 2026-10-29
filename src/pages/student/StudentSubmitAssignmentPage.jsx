import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { api, getCookie } from '../../utils/api';
import {
  UploadCloud, CheckCircle2, FileText, AlertCircle, Sparkles,
  ShieldCheck, Lock, Download, Check, FileCheck, Cpu,
  ChevronDown, ChevronUp, FastForward, X
} from 'lucide-react';

const PREDEFINED_SUBJECTS = [
  'Database Management Systems',
  'Theory of Computation',
  'Probability, Statistics and Linear Programming',
  'Circuits and Systems',
  'Programming in Java',
  'Compiler Design',
  'Operating Systems',
  'Computer Networks',
  'Software Engineering',
  'Design and Analysis of Algorithm',
  'Other',
];

const ASSIGNMENT_OPTIONS = [
  'Assignment 1',
  'Assignment 2',
  'Assignment 3',
  'Assignment 4',
];

export default function StudentSubmitAssignmentPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();

  // ── Step management (1: Upload, 2: Processing, 3: OCR Review, 4: Locked Receipt) ──
  const [currentStep, setCurrentStep] = useState(1);

  // ── Form State ──
  const [subject, setSubject] = useState('Database Management Systems');
  const [customSubject, setCustomSubject] = useState('');
  const [assignmentTitle, setAssignmentTitle] = useState('Assignment 1');
  const [file, setFile] = useState(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState(null);
  const [isDragging, setIsDragging] = useState(false);

  // ── Upload & Two-Phase State ──
  const [_isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [_uploadedBytes, setUploadedBytes] = useState(0);
  const [_totalBytes, setTotalBytes] = useState(0);
  const [submissionPhase, setSubmissionPhase] = useState('submitting'); // 'submitting' | 'calculating'

  // ── Processing Result & Lock State ──
  const [submissionId, setSubmissionId] = useState(null);
  const [statusData, setStatusData] = useState(null);
  const [isLocking, setIsLocking] = useState(false);
  const [lockedReceipt, setLockedReceipt] = useState(null);
  const [error, setError] = useState('');
  const [showExtractedText, setShowExtractedText] = useState(false);

  const pollingIntervalRef = useRef(null);
  const API_URL = import.meta.env.VITE_API_URL || '';

  // Check if navigating from My Submissions to review an unlocked submission
  useEffect(() => {
    if (location.state?.reviewSubmissionId) {
      const loadForReview = async () => {
        try {
          const res = await api.get(`/api/status/${location.state.reviewSubmissionId}`);
          if (res.ok) {
            const data = await res.json();
            setSubmissionId(location.state.reviewSubmissionId);
            setStatusData(data);
            setCurrentStep(3);
          }
        } catch (err) {
          console.error('Failed to load submission for review:', err);
        }
      };
      loadForReview();
    }
  }, [location.state]);

  const handleFileSelected = (selectedFile) => {
    if (!selectedFile) return;
    setFile(selectedFile);
    setError('');

    if (selectedFile.type.startsWith('image/')) {
      const previewUrl = URL.createObjectURL(selectedFile);
      setImagePreviewUrl(previewUrl);
    } else {
      setImagePreviewUrl(null);
    }
  };

  const pollStatus = (subId) => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }
    pollingIntervalRef.current = setInterval(async () => {
      try {
        const res = await api.get(`/api/status/${subId}`);
        if (!res.ok) throw new Error('Status poll failed');
        const data = await res.json();
        setStatusData(data);

        if (data.status === 'completed') {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
          setIsUploading(false);
          setCurrentStep(3);
        } else if (data.status === 'failed') {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
          setIsUploading(false);
          setError(data.progress || 'Processing failed. Please check document quality and try again.');
          setCurrentStep(1);
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 1500);
  };

  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  const uploadWithProgress = (url, formData, token, onProgress) => {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', url);
      xhr.withCredentials = true;
      const csrfToken = getCookie('csrf_token');
      if (csrfToken) {
        xhr.setRequestHeader('X-CSRF-Token', csrfToken);
      }
      if (token) {
        xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      }

      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const percent = Math.round((event.loaded / event.total) * 100);
          onProgress(percent, event.loaded, event.total);
        }
      };

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            resolve(JSON.parse(xhr.responseText));
          } catch {
            resolve(xhr.responseText);
          }
        } else {
          let errMessage = 'Failed to upload assignment';
          try {
            const errData = JSON.parse(xhr.responseText);
            errMessage = errData.detail || errMessage;
          } catch {
            // ignore
          }
          reject(new Error(errMessage));
        }
      };

      xhr.onerror = () => reject(new Error('Network connection error. Verify backend server is running.'));
      xhr.send(formData);
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const finalSubject = subject === 'Other' ? customSubject.trim() : subject;
    const finalAssignment = assignmentTitle;

    if (!file || !finalSubject || !finalAssignment) {
      setError('Please select a subject, assignment option, and an assignment file.');
      return;
    }

    setCurrentStep(2);
    setIsUploading(true);
    setSubmissionPhase('submitting');
    setUploadProgress(0);
    setUploadedBytes(0);
    setTotalBytes(file.size || 0);
    setError('');

    const token = localStorage.getItem('token');
    const formData = new FormData();
    formData.append('file', file);
    formData.append('subject', finalSubject);
    formData.append('assignment_title', finalAssignment);

    try {
      const data = await uploadWithProgress(
        `${API_URL}/api/submit`,
        formData,
        token,
        (percent, loaded, total) => {
          setUploadProgress(percent);
          setUploadedBytes(loaded);
          setTotalBytes(total);
          if (percent === 100) {
            setSubmissionPhase('calculating');
          }
        }
      );

      setSubmissionId(data.submission_id);
      setSubmissionPhase('calculating');

      const statusRes = await api.get(`/api/status/${data.submission_id}`);
      const statusDataRes = await statusRes.json();
      setStatusData(statusDataRes);

      if (statusDataRes.status === 'completed') {
        setIsUploading(false);
        setTimeout(() => setCurrentStep(3), 600);
      } else {
        pollStatus(data.submission_id);
      }
    } catch (err) {
      setError(err.message);
      setIsUploading(false);
      setCurrentStep(1);
    }
  };

  const handleLockSubmission = async () => {
    if (!submissionId) return;
    setIsLocking(true);
    setError('');

    try {
      const res = await api.post(`/api/submissions/${submissionId}/lock`, {});
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to lock submission');
      }

      const receiptData = await res.json();
      setLockedReceipt(receiptData);
      setCurrentStep(4);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLocking(false);
    }
  };

  const handleDiscard = async () => {
    if (submissionId && !statusData?.is_locked) {
      try {
        await api.delete(`/api/submissions/${submissionId}`);
      } catch (err) {
        console.warn('Discard cleanup warning:', err);
      }
    }
    resetUploadFlow();
  };

  const resetUploadFlow = () => {
    setFile(null);
    setImagePreviewUrl(null);
    setSubmissionId(null);
    setStatusData(null);
    setLockedReceipt(null);
    setError('');
    setUploadProgress(0);
    setUploadedBytes(0);
    setTotalBytes(0);
    setSubmissionPhase('submitting');
    setIsUploading(false);
    setCurrentStep(1);
  };

  const handleSkipEvaluation = () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    setIsUploading(false);

    const subTitle = assignmentTitle || 'Assignment';
    const subSubject = subject === 'Other' ? customSubject.trim() : subject;
    const msg = `Assignment "${subTitle}" (${subSubject}) submitted successfully! Background evaluation is in progress. Your scores and report will update automatically in the table below.`;

    resetUploadFlow();
    navigate('/student/submissions', { state: { skipNotification: msg } });
  };

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

STUDENT DETAILS:
Name:               ${user?.name || 'Student'}
Enrollment/Roll:    ${user?.enrollment_no || 'N/A'}
Section:            ${user?.section || 'N/A'}
Branch:             ${user?.branch || 'Computer Science & Engineering'}

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

  const getFileIconType = (filename) => {
    const ext = filename?.split('.').pop()?.toUpperCase() || '';
    if (['JPG', 'JPEG', 'PNG'].includes(ext)) return 'img-type';
    if (ext === 'PDF') return 'pdf-type';
    if (['DOC', 'DOCX'].includes(ext)) return 'doc-type';
    return 'txt-type';
  };

  const getFileTypeName = (filename) => {
    const ext = filename?.split('.').pop()?.toUpperCase() || 'FILE';
    if (['JPG', 'JPEG', 'PNG'].includes(ext)) return 'Image';
    if (ext === 'PDF') return 'PDF';
    if (['DOC', 'DOCX'].includes(ext)) return 'Word Document';
    return 'Text File';
  };

  return (
    <>
      {/* Content Header */}
      <div className="teacher-content-header">
        <h2>Submit Assignment</h2>
        <p>Upload handwritten or digital assignments for real-time OCR extraction and forensic analysis.</p>
      </div>

      {error && (
        <div className="alert alert-danger" style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
          <AlertCircle size={20} style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <div style={{ fontWeight: 700, marginBottom: '0.15rem' }}>Submission Alert</div>
            <div>{error}</div>
          </div>
        </div>
      )}

      {/* ── STAGE 1: SELECTION & FILE UPLOAD ── */}
      {currentStep === 1 && (
        <div className="card glass-panel" style={{ padding: '1.5rem 1.75rem' }}>
          <form onSubmit={handleSubmit}>
            {/* Row 1: Course + Assignment */}
            <div className="sp-form-cols" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.25rem' }}>
              <div>
                <label className="sp-step-label">
                  <span className="sp-step-number">01</span>
                  Select Course / Subject *
                </label>
                <select
                  className="form-select"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  required
                  style={{ fontSize: '0.88rem' }}
                >
                  {PREDEFINED_SUBJECTS.map((sub) => (
                    <option key={sub} value={sub}>{sub}</option>
                  ))}
                </select>
                {subject === 'Other' && (
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Enter course name..."
                    style={{ marginTop: '0.5rem', fontSize: '0.88rem' }}
                    value={customSubject}
                    onChange={(e) => setCustomSubject(e.target.value)}
                    required
                  />
                )}
              </div>

              <div>
                <label className="sp-step-label">
                  <span className="sp-step-number">02</span>
                  Select Assignment *
                </label>
                <div className="sp-assignment-grid">
                  {ASSIGNMENT_OPTIONS.map((opt) => (
                    <button
                      key={opt}
                      type="button"
                      className={`sp-assignment-btn ${assignmentTitle === opt ? 'selected' : ''}`}
                      onClick={() => setAssignmentTitle(opt)}
                    >
                      <span>{opt}</span>
                      {assignmentTitle === opt && (
                        <CheckCircle2 size={15} style={{ color: 'var(--primary-color)' }} />
                      )}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Row 2: Upload Zone */}
            <div style={{ marginBottom: '1.25rem' }}>
              <label className="sp-step-label">
                <span className="sp-step-number">03</span>
                Upload Assignment Document *
              </label>

              <div
                className={`sp-upload-zone ${file ? 'has-file' : ''} ${isDragging ? 'dragging' : ''}`}
                onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setIsDragging(false);
                  if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                    handleFileSelected(e.dataTransfer.files[0]);
                  }
                }}
                onClick={() => !file && document.getElementById('fileUploadInput').click()}
                style={file ? { cursor: 'default' } : {}}
              >
                {file ? (
                  <div className="sp-file-preview">
                    {imagePreviewUrl ? (
                      <img src={imagePreviewUrl} alt="Preview" className="sp-file-preview-thumb" />
                    ) : (
                      <div className={`sp-file-preview-icon ${getFileIconType(file.name)}`}>
                        <FileText size={22} />
                      </div>
                    )}

                    <div className="sp-file-preview-info">
                      <div className="sp-file-preview-name">{file.name}</div>
                      <div className="sp-file-preview-meta">
                        {getFileTypeName(file.name)} • {(file.size / 1024 / 1024).toFixed(2)} MB
                      </div>
                    </div>

                    <div className="sp-file-preview-actions">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          document.getElementById('fileUploadInput').click();
                        }}
                      >
                        Replace
                      </button>
                      <button
                        type="button"
                        className="remove-btn"
                        onClick={(e) => {
                          e.stopPropagation();
                          setFile(null);
                          setImagePreviewUrl(null);
                        }}
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center">
                    <div style={{
                      width: '52px',
                      height: '52px',
                      borderRadius: '50%',
                      backgroundColor: 'var(--primary-light)',
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      marginBottom: '0.75rem',
                      color: 'var(--primary-color)',
                    }}>
                      <UploadCloud size={26} />
                    </div>
                    <p style={{ fontWeight: 700, color: 'var(--text-main)', marginBottom: '0.25rem', fontSize: '0.95rem' }}>
                      Click to select or drag and drop your assignment
                    </p>
                    <p className="text-muted" style={{ fontSize: '0.82rem', marginBottom: '0.75rem', maxWidth: '440px' }}>
                      Accepts <strong>JPG, JPEG, PNG</strong> photos of handwritten notebooks, or digital <strong>PDF, DOCX, DOC, TXT</strong> documents.
                    </p>
                    <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap', justifyContent: 'center' }}>
                      {['.JPG / JPEG', '.PNG', '.PDF', '.DOCX', '.TXT'].map((fmt) => (
                        <span
                          key={fmt}
                          className="badge badge-neutral"
                          style={{ fontSize: '0.72rem', padding: '0.25rem 0.5rem' }}
                        >
                          {fmt}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <input
                  id="fileUploadInput"
                  type="file"
                  accept=".jpg,.jpeg,.png,.pdf,.docx,.doc,.txt"
                  style={{ display: 'none' }}
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      handleFileSelected(e.target.files[0]);
                    }
                  }}
                />
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={!file || !subject}
                style={{ width: '210px', padding: '0.65rem 1.25rem', fontSize: '0.9rem' }}
              >
                <div className="flex items-center justify-center gap-2">
                  <Sparkles size={16} />
                  <span>Submit Assignment</span>
                </div>
              </button>
            </div>
          </form>
        </div>
      )}

      {/* ── STAGE 2: TWO-PHASE PULSING LOADER ── */}
      {currentStep === 2 && (
        <div className="card glass-panel" style={{ padding: '3.5rem 2rem', textAlign: 'center' }}>
          <div className="pulsing-loader-container">
            <div className="pulsing-loader-ring ring-1"></div>
            <div className="pulsing-loader-ring ring-2"></div>
            <div className="pulsing-loader-core">
              <Cpu size={36} className="pulse-icon" />
            </div>
          </div>

          <h3 style={{ fontWeight: 800, fontSize: '1.4rem', marginBottom: '0.5rem', color: 'var(--text-main)' }}>
            {submissionPhase === 'submitting' ? 'Submitting Assignment...' : 'Calculating Plagiarism & OCR Scores...'}
          </h3>
          <p className="text-muted" style={{ fontSize: '0.925rem', marginBottom: '2.5rem', maxWidth: '480px', margin: '0 auto 2.5rem' }}>
            {submissionPhase === 'submitting'
              ? 'Transmitting document payload to the secure institutional repository.'
              : 'Analyzing document structure, handwriting clarity, and checking peer corpus for originality.'}
          </p>

          <div style={{
            maxWidth: '520px',
            margin: '0 auto 2rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem',
            textAlign: 'left',
          }}>
            {/* Phase 1: Submitting */}
            <div className={`phase-step-card ${submissionPhase === 'submitting' ? 'active' : 'completed'}`}>
              <div className="flex items-center gap-3">
                <div style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '50%',
                  backgroundColor: submissionPhase === 'submitting' ? 'var(--primary-color)' : 'var(--success-color)',
                  color: '#ffffff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 800,
                  fontSize: '0.9rem',
                  flexShrink: 0,
                }}>
                  {submissionPhase === 'submitting' ? (
                    <UploadCloud size={18} />
                  ) : (
                    <Check size={18} />
                  )}
                </div>
                <div>
                  <div style={{
                    fontWeight: 700,
                    fontSize: '0.95rem',
                    color: submissionPhase === 'submitting' ? 'var(--primary-color)' : 'var(--text-main)',
                  }}>
                    Phase 1: Submitting
                  </div>
                  <div className="text-muted" style={{ fontSize: '0.8rem' }}>
                    {submissionPhase === 'submitting'
                      ? `Uploading file payload (${uploadProgress}%)`
                      : 'Assignment uploaded & registered successfully'}
                  </div>
                </div>
              </div>

              <div>
                {submissionPhase === 'submitting' ? (
                  <div className="flex items-center gap-2" style={{ color: 'var(--primary-color)', fontWeight: 700, fontSize: '0.825rem' }}>
                    <div className="spinner" style={{ width: '15px', height: '15px', borderWidth: '2px' }}></div>
                    <span>Uploading...</span>
                  </div>
                ) : (
                  <span className="badge badge-success" style={{ fontSize: '0.75rem', fontWeight: 700 }}>
                    <Check size={12} /> Done
                  </span>
                )}
              </div>
            </div>

            {/* Phase 2: Calculating Score */}
            <div className={`phase-step-card ${submissionPhase === 'calculating' ? 'active' : ''}`}>
              <div className="flex items-center gap-3">
                <div style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '50%',
                  backgroundColor: submissionPhase === 'calculating' ? 'var(--primary-color)' : 'var(--surface-subtle)',
                  color: submissionPhase === 'calculating' ? '#ffffff' : 'var(--text-subtle)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 800,
                  fontSize: '0.9rem',
                  flexShrink: 0,
                }}>
                  <Sparkles size={18} />
                </div>
                <div>
                  <div style={{
                    fontWeight: 700,
                    fontSize: '0.95rem',
                    color: submissionPhase === 'calculating' ? 'var(--primary-color)' : 'var(--text-main)',
                  }}>
                    Phase 2: Calculating Score
                  </div>
                  <div className="text-muted" style={{ fontSize: '0.8rem' }}>
                    {submissionPhase === 'calculating'
                      ? 'Evaluating OCR confidence, AI detection & similarity metrics...'
                      : 'Awaiting upload completion...'}
                  </div>
                </div>
              </div>

              <div>
                {submissionPhase === 'calculating' ? (
                  <div className="flex items-center gap-2" style={{ color: 'var(--primary-color)', fontWeight: 700, fontSize: '0.825rem' }}>
                    <div className="spinner" style={{ width: '15px', height: '15px', borderWidth: '2px' }}></div>
                    <span>Calculating...</span>
                  </div>
                ) : (
                  <span className="text-muted" style={{ fontSize: '0.78rem' }}>Waiting</span>
                )}
              </div>
            </div>
          </div>

          {/* Progress bar during file transfer */}
          {submissionPhase === 'submitting' && (
            <div style={{ maxWidth: '520px', margin: '0 auto' }}>
              <div style={{
                width: '100%',
                height: '6px',
                backgroundColor: 'var(--border-color)',
                borderRadius: 'var(--radius-full)',
                overflow: 'hidden',
              }}>
                <div style={{
                  width: `${uploadProgress}%`,
                  height: '100%',
                  background: 'linear-gradient(90deg, var(--primary-color) 0%, var(--accent-color) 100%)',
                  borderRadius: 'var(--radius-full)',
                  transition: 'width 0.2s ease-out',
                }}></div>
              </div>
            </div>
          )}

          {/* Skip Evaluation Option */}
          {submissionPhase === 'calculating' && (
            <div style={{
              maxWidth: '520px',
              margin: '2rem auto 0',
              padding: '1.25rem 1.5rem',
              backgroundColor: 'var(--surface-color)',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--border-color)',
              textAlign: 'center',
            }}>
              <div className="flex items-center justify-center gap-2" style={{ color: 'var(--text-main)', fontWeight: 700, fontSize: '0.925rem', marginBottom: '0.35rem' }}>
                <FastForward size={16} style={{ color: 'var(--primary-color)' }} />
                <span>Evaluation taking time?</span>
              </div>
              <p className="text-muted" style={{ fontSize: '0.825rem', marginBottom: '1rem', lineHeight: 1.45 }}>
                Your document is safely stored and queued. Analysis will finish in the background. You can skip waiting and check your report anytime in <strong>My Submissions</strong>.
              </p>
              <button
                type="button"
                className="btn btn-outline"
                onClick={handleSkipEvaluation}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.65rem 1.25rem',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  borderColor: 'var(--primary-color)',
                  color: 'var(--primary-color)',
                  width: '100%',
                  justifyContent: 'center',
                }}
              >
                <FastForward size={16} />
                <span>Skip Waiting & View in My Submissions</span>
              </button>
            </div>
          )}
        </div>
      )}

      {/* ── STAGE 3: DOCUMENT REVIEW & OCR SCORE ACCEPTANCE ── */}
      {currentStep === 3 && statusData && (
        <div className="card glass-panel" style={{ padding: '2rem' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid var(--border-color)',
            paddingBottom: '1.25rem',
            marginBottom: '1.75rem',
          }}>
            <div>
              <div className="flex items-center gap-2">
                <CheckCircle2 size={22} style={{ color: 'var(--success-color)' }} />
                <h3 style={{ fontWeight: 800 }}>Document Analysis & OCR Verification Ready</h3>
              </div>
              <p className="text-muted" style={{ fontSize: '0.9rem', marginTop: '0.2rem' }}>
                Review your uploaded document, calculated OCR legibility score, and forensic integrity before locking.
              </p>
            </div>

            <span className="badge badge-success" style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem' }}>
              Accepted & Validated
            </span>
          </div>

          {/* Uploaded Document Card */}
          <div style={{
            backgroundColor: 'var(--surface-color)',
            borderRadius: 'var(--radius-lg)',
            padding: '1.25rem',
            border: '1px solid var(--border-color)',
            marginBottom: '1.5rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '1rem',
          }}>
            <div className="flex items-center gap-4">
              {imagePreviewUrl ? (
                <img
                  src={imagePreviewUrl}
                  alt="Uploaded File"
                  style={{
                    width: '64px',
                    height: '64px',
                    objectFit: 'cover',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-color)',
                  }}
                />
              ) : (
                <div style={{
                  width: '56px',
                  height: '56px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'var(--primary-light)',
                  color: 'var(--primary-color)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}>
                  <FileText size={28} />
                </div>
              )}

              <div>
                <div className="flex items-center gap-2" style={{ marginBottom: '0.2rem' }}>
                  <span style={{ fontWeight: 800, fontSize: '1rem', color: 'var(--text-main)' }}>
                    {statusData.filename || file?.name}
                  </span>
                  {getFileBadge(statusData.filename || file?.name)}
                </div>
                <div className="text-muted" style={{ fontSize: '0.825rem' }}>
                  <strong>Subject:</strong> {statusData.subject || subject} • <strong>Assignment:</strong> {statusData.assignment_title || assignmentTitle}
                </div>
              </div>
            </div>

            <div>
              <button
                type="button"
                className="btn btn-outline"
                onClick={() => handleDownloadFile(submissionId, statusData.filename || file?.name)}
                style={{ fontSize: '0.8rem', padding: '0.4rem 0.85rem' }}
              >
                <Download size={14} /> Download File
              </button>
            </div>
          </div>

          {/* OCR Score & Forensic Score Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4" style={{ marginBottom: '1.75rem' }}>
            {/* 1. OCR Confidence Score Card */}
            <div style={{
              padding: '1.5rem 1.25rem',
              backgroundColor: 'rgba(16, 185, 129, 0.06)',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid rgba(16, 185, 129, 0.25)',
              textAlign: 'center',
            }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--success-color)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.4rem' }}>
                OCR Legibility Score
              </div>
              <div style={{ fontSize: '2.5rem', fontWeight: 900, color: 'var(--success-color)', lineHeight: 1 }}>
                {statusData.ocr_score != null ? `${statusData.ocr_score}%` : '100%'}
              </div>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-main)', marginTop: '0.5rem' }}>
                {statusData.ocr_status || 'Accepted (≥ 65% Threshold)'}
              </div>
              <div className="text-muted" style={{ fontSize: '0.72rem', marginTop: '0.2rem' }}>
                {statusData.ocr_score >= 65 ? 'High Neural Clarity' : 'Passes Quality Criteria'}
              </div>
            </div>

            {/* 2. Plagiarism Match Score */}
            <div style={{
              padding: '1.5rem 1.25rem',
              backgroundColor: statusData.plagiarism_score > 30 ? 'var(--danger-light)' : 'rgba(16, 185, 129, 0.06)',
              borderRadius: 'var(--radius-lg)',
              border: `1px solid ${statusData.plagiarism_score > 30 ? 'rgba(239, 68, 68, 0.25)' : 'rgba(16, 185, 129, 0.25)'}`,
              textAlign: 'center',
            }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: statusData.plagiarism_score > 30 ? 'var(--danger-color)' : 'var(--success-color)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.4rem' }}>
                Plagiarism Match
              </div>
              <div style={{ fontSize: '2.5rem', fontWeight: 900, color: statusData.plagiarism_score > 30 ? 'var(--danger-color)' : 'var(--success-color)', lineHeight: 1 }}>
                {statusData.plagiarism_score != null ? `${statusData.plagiarism_score}%` : '0%'}
              </div>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-main)', marginTop: '0.5rem' }}>
                {statusData.plagiarism_score > 30 ? 'High Similarity Flagged' : 'Original Content'}
              </div>
              <div className="text-muted" style={{ fontSize: '0.72rem', marginTop: '0.2rem' }}>
                Cross-section peer corpus match
              </div>
            </div>

            {/* 3. AI Generated Content Score */}
            <div style={{
              padding: '1.5rem 1.25rem',
              backgroundColor: statusData.ai_score > 50 ? 'var(--danger-light)' : 'var(--primary-light)',
              borderRadius: 'var(--radius-lg)',
              border: `1px solid ${statusData.ai_score > 50 ? 'rgba(239, 68, 68, 0.25)' : 'rgba(79, 70, 229, 0.25)'}`,
              textAlign: 'center',
            }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: statusData.ai_score > 50 ? 'var(--danger-color)' : 'var(--primary-color)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.4rem' }}>
                AI Forensics Score
              </div>
              <div style={{ fontSize: '2.5rem', fontWeight: 900, color: statusData.ai_score > 50 ? 'var(--danger-color)' : 'var(--primary-color)', lineHeight: 1 }}>
                {statusData.ai_score != null ? `${statusData.ai_score}%` : '0%'}
              </div>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-main)', marginTop: '0.5rem' }}>
                Label: {statusData.label || 'Original'}
              </div>
              <div className="text-muted" style={{ fontSize: '0.72rem', marginTop: '0.2rem' }}>
                Perplexity & Burstiness Scan
              </div>
            </div>
          </div>

          {/* Extracted Text Snippet Viewer */}
          {statusData.processed_text_preview && (
            <div style={{
              backgroundColor: 'var(--surface-color)',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--border-color)',
              padding: '1rem',
              marginBottom: '1.75rem',
            }}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  cursor: 'pointer',
                }}
                onClick={() => setShowExtractedText(!showExtractedText)}
              >
                <div className="flex items-center gap-2" style={{ fontWeight: 700, fontSize: '0.875rem' }}>
                  <FileCheck size={16} style={{ color: 'var(--primary-color)' }} />
                  <span>Extracted Document Text ({statusData.word_count || 0} words, {statusData.sentence_count || 0} sentences)</span>
                </div>
                <button type="button" className="btn btn-outline" style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}>
                  {showExtractedText ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  <span>{showExtractedText ? 'Collapse' : 'Inspect Extracted Text'}</span>
                </button>
              </div>

              {showExtractedText && (
                <div style={{
                  marginTop: '0.75rem',
                  padding: '0.75rem',
                  backgroundColor: 'var(--bg-color)',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.825rem',
                  lineHeight: 1.6,
                  color: 'var(--text-main)',
                  maxHeight: '160px',
                  overflowY: 'auto',
                  whiteSpace: 'pre-wrap',
                }}>
                  {statusData.processed_text_preview}
                </div>
              )}
            </div>
          )}

          {/* Final Lock Confirmation Callout */}
          <div style={{
            backgroundColor: 'rgba(79, 70, 229, 0.04)',
            border: '1px solid rgba(79, 70, 229, 0.2)',
            borderRadius: 'var(--radius-lg)',
            padding: '1rem 1.25rem',
            marginBottom: '2rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.85rem',
          }}>
            <ShieldCheck size={28} style={{ color: 'var(--primary-color)', flexShrink: 0 }} />
            <div style={{ fontSize: '0.85rem' }}>
              <div style={{ fontWeight: 700, color: 'var(--text-main)' }}>
                Ready to Save & Lock Submission
              </div>
              <div className="text-muted">
                Locking will officially register your submission in the institutional ledger and generate an immutable verification token.
              </div>
            </div>
          </div>

          {/* Action Buttons: Save & Lock vs Discard */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <button
              type="button"
              onClick={handleDiscard}
              className="btn btn-outline"
              style={{ color: 'var(--danger-color)', borderColor: 'rgba(239, 68, 68, 0.3)' }}
            >
              <X size={16} /> Discard & Upload Different File
            </button>

            <button
              type="button"
              onClick={handleLockSubmission}
              disabled={isLocking}
              className="btn btn-primary"
              style={{ minWidth: '220px', padding: '0.85rem 1.75rem', fontSize: '0.95rem' }}
            >
              {isLocking ? (
                <>
                  <div className="spinner spinner-white" style={{ width: '16px', height: '16px' }}></div>
                  <span>Locking Submission...</span>
                </>
              ) : (
                <div className="flex items-center gap-2">
                  <Lock size={16} />
                  <span>Save and Lock Submission</span>
                </div>
              )}
            </button>
          </div>
        </div>
      )}

      {/* ── STAGE 4: FINALIZED & LOCKED SUBMISSION RECEIPT ── */}
      {currentStep === 4 && lockedReceipt && (
        <div className="card glass-panel" style={{ padding: '2.5rem 2rem', textAlign: 'center' }}>
          <div style={{
            width: '76px',
            height: '76px',
            borderRadius: '50%',
            backgroundColor: 'var(--success-light)',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--success-color)',
            marginBottom: '1.25rem',
            boxShadow: '0 0 0 10px rgba(16, 185, 129, 0.1)',
          }}>
            <ShieldCheck size={44} />
          </div>

          <h2 style={{ fontWeight: 900, marginBottom: '0.35rem', color: 'var(--text-main)' }}>
            Submission Locked & Finalized!
          </h2>
          <p className="text-muted" style={{ fontSize: '0.925rem', marginBottom: '2rem', maxWidth: '520px', margin: '0 auto 2rem' }}>
            Your assignment has been recorded with an immutable institutional verification seal.
          </p>

          <div style={{
            backgroundColor: 'var(--surface-color)',
            borderRadius: 'var(--radius-xl)',
            border: '1.5px solid var(--border-color)',
            padding: '1.75rem',
            maxWidth: '620px',
            margin: '0 auto 2rem',
            textAlign: 'left',
            boxShadow: 'var(--shadow-md)',
          }}>
            {/* Verification Token Banner */}
            <div style={{
              backgroundColor: 'var(--primary-light)',
              border: '1px dashed var(--primary-color)',
              borderRadius: 'var(--radius-md)',
              padding: '0.75rem 1rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '1.5rem',
            }}>
              <div>
                <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--primary-color)', textTransform: 'uppercase' }}>
                  Official Verification Token
                </div>
                <div style={{ fontFamily: 'monospace', fontWeight: 800, fontSize: '1rem', color: 'var(--text-main)' }}>
                  {lockedReceipt.verification_token}
                </div>
              </div>
              <span className="badge badge-success" style={{ fontSize: '0.72rem' }}>
                <Lock size={12} /> LOCKED
              </span>
            </div>

            {/* Metadata Grid */}
            <div className="grid grid-cols-2 gap-4" style={{ fontSize: '0.85rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '1.25rem', marginBottom: '1.25rem' }}>
              <div>
                <span className="text-muted">Student Name:</span>
                <div style={{ fontWeight: 700 }}>{user?.name || 'Student'}</div>
              </div>
              <div>
                <span className="text-muted">Enrollment / Roll:</span>
                <div style={{ fontWeight: 700 }}>{user?.enrollment_no || 'N/A'}</div>
              </div>
              <div>
                <span className="text-muted">Subject:</span>
                <div style={{ fontWeight: 700 }}>{lockedReceipt.subject}</div>
              </div>
              <div>
                <span className="text-muted">Assignment Title:</span>
                <div style={{ fontWeight: 700 }}>{lockedReceipt.assignment_title}</div>
              </div>
              <div>
                <span className="text-muted">Submitted File:</span>
                <div style={{ fontWeight: 700 }}>{lockedReceipt.filename}</div>
              </div>
              <div>
                <span className="text-muted">Timestamp:</span>
                <div style={{ fontWeight: 700 }}>{new Date().toLocaleString()}</div>
              </div>
            </div>

            {/* Forensic Scores */}
            <div className="grid grid-cols-3 gap-2" style={{ textAlign: 'center', fontSize: '0.8rem' }}>
              <div style={{ padding: '0.75rem 0.5rem', backgroundColor: 'var(--surface-subtle)', borderRadius: 'var(--radius-md)' }}>
                <div className="text-muted" style={{ fontSize: '0.72rem' }}>OCR Legibility</div>
                <div style={{ fontWeight: 800, color: 'var(--success-color)', fontSize: '1.15rem' }}>
                  {lockedReceipt.ocr_score != null ? `${lockedReceipt.ocr_score}%` : '100%'}
                </div>
              </div>
              <div style={{ padding: '0.75rem 0.5rem', backgroundColor: 'var(--surface-subtle)', borderRadius: 'var(--radius-md)' }}>
                <div className="text-muted" style={{ fontSize: '0.72rem' }}>Plagiarism</div>
                <div style={{ fontWeight: 800, color: lockedReceipt.plagiarism_score > 30 ? 'var(--danger-color)' : 'var(--success-color)', fontSize: '1.15rem' }}>
                  {lockedReceipt.plagiarism_score != null ? `${lockedReceipt.plagiarism_score}%` : '0%'}
                </div>
              </div>
              <div style={{ padding: '0.75rem 0.5rem', backgroundColor: 'var(--surface-subtle)', borderRadius: 'var(--radius-md)' }}>
                <div className="text-muted" style={{ fontSize: '0.72rem' }}>AI Confidence</div>
                <div style={{ fontWeight: 800, color: lockedReceipt.ai_score > 50 ? 'var(--danger-color)' : 'var(--primary-color)', fontSize: '1.15rem' }}>
                  {lockedReceipt.ai_score != null ? `${lockedReceipt.ai_score}%` : '0%'}
                </div>
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <button
              type="button"
              className="btn btn-outline"
              onClick={resetUploadFlow}
            >
              Submit Another Assignment
            </button>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => handleDownloadReceiptText(lockedReceipt)}
            >
              <Download size={16} /> Download Verification Receipt (.txt)
            </button>
          </div>
        </div>
      )}
    </>
  );
}
