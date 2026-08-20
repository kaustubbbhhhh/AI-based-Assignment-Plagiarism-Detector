import React, { useState, useEffect, useMemo, useRef } from 'react';
import {
  UploadCloud,
  CheckCircle2,
  FileText,
  X,
  AlertCircle,
  Sparkles,
  ShieldCheck,
  User,
  Lock,
  Clock,
  Eye,
  RefreshCw,
  Download,
  Check,
  FileCheck,
  Layers,
  Terminal,
  ArrowRight,
  Search,
  Image as ImageIcon,
  Cpu,
  Zap,
  CheckCheck,
  ChevronDown,
  ChevronUp,
  FileSpreadsheet
} from 'lucide-react';

export default function StudentPortal() {
  // ── User state ──
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState('new-submission'); // 'new-submission' | 'history'

  // ── Step management (1: Setup & Upload, 2: Behind-the-Scenes Pipeline, 3: OCR Review, 4: Locked Receipt) ──
  const [currentStep, setCurrentStep] = useState(1);

  // ── Form State ──
  const [subject, setSubject] = useState('Database Management Systems');
  const [customSubject, setCustomSubject] = useState('');
  const [assignmentTitle, setAssignmentTitle] = useState('Assignment 1');
  const [customAssignment, setCustomAssignment] = useState('');
  const [file, setFile] = useState(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState(null);
  const [isDragging, setIsDragging] = useState(false);

  // ── Upload & Progress State ──
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadedBytes, setUploadedBytes] = useState(0);
  const [totalBytes, setTotalBytes] = useState(0);
  const [activeEngineStage, setActiveEngineStage] = useState('ingest'); // ingest | preprocessing | ocr | quality | subject | ai | plagiarism | completed
  const [engineLogs, setEngineLogs] = useState([]);
  const [pipelineStepIndex, setPipelineStepIndex] = useState(0);

  // ── Processing Result & Lock State ──
  const [submissionId, setSubmissionId] = useState(null);
  const [statusData, setStatusData] = useState(null);
  const [isLocking, setIsLocking] = useState(false);
  const [lockedReceipt, setLockedReceipt] = useState(null);
  const [error, setError] = useState('');
  const [showExtractedText, setShowExtractedText] = useState(false);

  // ── History Tab State ──
  const [historySubmissions, setHistorySubmissions] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [historySearch, setHistorySearch] = useState('');
  const [selectedReceiptModal, setSelectedReceiptModal] = useState(null);

  const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
  const logsContainerRef = useRef(null);

  // ── Predefined Subjects & Quick Assignment Presets ──
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
    'Other'
  ];

  const ASSIGNMENT_PRESETS = [
    'Assignment 1',
    'Assignment 2',
    'Assignment 3',
    'Assignment 4',
    'Lab Experiment Report',
    'Midterm Project',
    'Custom'
  ];

  // Pipeline step definition
  const PIPELINE_STAGES = [
    { key: 'ingest', name: 'Payload Ingestion', desc: 'Secure transfer & file structure audit', icon: UploadCloud },
    { key: 'preprocessing', name: 'Image & Stream Preprocessing', desc: 'Deskew, shadow removal & contrast normalization', icon: Layers },
    { key: 'ocr', name: 'OCR Neural Recognition', desc: 'TrOCR & Neural Vision text extraction', icon: Cpu },
    { key: 'quality', name: 'OCR Quality & Acceptance Gate', desc: 'Evaluating confidence threshold (≥ 65%)', icon: Zap },
    { key: 'subject', name: 'Semantic Subject Validation', desc: 'Curriculum relevance & topic match', icon: CheckCheck },
    { key: 'ai', name: 'Forensic AI Detection', desc: 'Deep-learning perplexity & burstiness scan', icon: Sparkles },
    { key: 'plagiarism', name: 'Plagiarism & Visual Hash', desc: 'Cross-sectional peer corpus indexing', icon: ShieldCheck }
  ];

  // ── Fetch user from localStorage ──
  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
  }, []);

  // ── Auto-scroll telemetry log ──
  useEffect(() => {
    if (logsContainerRef.current) {
      logsContainerRef.current.scrollTop = logsContainerRef.current.scrollHeight;
    }
  }, [engineLogs]);

  // ── Handle file selection and instant image thumbnail preview ──
  const handleFileSelected = (selectedFile) => {
    if (!selectedFile) return;
    setFile(selectedFile);
    setError('');

    // Generate preview thumbnail if image (JPG, PNG, JPEG)
    if (selectedFile.type.startsWith('image/')) {
      const previewUrl = URL.createObjectURL(selectedFile);
      setImagePreviewUrl(previewUrl);
    } else {
      setImagePreviewUrl(null);
    }
  };

  // ── Add formatted log entry ──
  const addLog = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 3 });
    setEngineLogs((prev) => [...prev, { timestamp, message, type }]);
  };

  // ── Polling logic for status ──
  const pollStatus = async (subId) => {
    const token = localStorage.getItem('token');
    if (!token) return;

    let pollCount = 0;
    const interval = setInterval(async () => {
      pollCount++;
      try {
        const res = await fetch(`${API_URL}/api/status/${subId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Status poll failed');
        const data = await res.json();
        setStatusData(data);

        // Update pipeline visually based on status
        if (data.status === 'processing') {
          const stepIndex = Math.min(Math.floor(pollCount / 2) + 2, 6);
          setPipelineStepIndex(stepIndex);
          setActiveEngineStage(PIPELINE_STAGES[stepIndex]?.key || 'ai');
          addLog(`[PIPELINE] ${data.progress || 'Analyzing document layers...'}`, 'info');
        } else if (data.status === 'completed') {
          clearInterval(interval);
          setPipelineStepIndex(7);
          setActiveEngineStage('completed');
          addLog(`[SUCCESS] OCR score calculated: ${data.ocr_score || 100}% (${data.ocr_status || 'Accepted'}).`, 'success');
          addLog(`[SUCCESS] Forensic analysis finished. AI Score: ${data.ai_score}%, Plag Match: ${data.plagiarism_score}%.`, 'success');
          addLog(`[SUCCESS] Document accepted and ready for student review & lock.`, 'success');
          setIsUploading(false);
          setCurrentStep(3); // Move to Step 3: OCR & Document Review
        } else if (data.status === 'failed') {
          clearInterval(interval);
          setIsUploading(false);
          setError(data.progress || 'Processing failed. Please check document quality and try again.');
          addLog(`[ERROR] Document processing rejected: ${data.progress}`, 'error');
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 1800);
  };

  // ── XHR Upload with Real-Time Byte Monitoring ──
  const uploadWithProgress = (url, formData, token, onProgress) => {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', url);
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

  // ── Submit & Run Behind-the-Scenes Pipeline ──
  const handleSubmit = async (e) => {
    e.preventDefault();
    const finalSubject = subject === 'Other' ? customSubject.trim() : subject;
    const finalAssignment = assignmentTitle === 'Custom' ? customAssignment.trim() : assignmentTitle;

    if (!file || !finalSubject || !finalAssignment) {
      setError('Please select a subject, assignment title, and an assignment file.');
      return;
    }

    // Switch to Step 2 (Live Pipeline Monitor)
    setCurrentStep(2);
    setIsUploading(true);
    setUploadProgress(0);
    setUploadedBytes(0);
    setTotalBytes(file.size || 0);
    setError('');
    setEngineLogs([]);
    setPipelineStepIndex(0);
    setActiveEngineStage('ingest');

    addLog(`Initiating upload session for file: "${file.name}" (${(file.size / 1024 / 1024).toFixed(2)} MB)...`, 'info');
    addLog(`Target subject: "${finalSubject}" | Assignment: "${finalAssignment}"`, 'info');

    const token = localStorage.getItem('token');
    const formData = new FormData();
    formData.append('file', file);
    formData.append('subject', finalSubject);
    formData.append('assignment_title', finalAssignment);

    try {
      addLog(`Connecting to ingest server: POST /api/submit`, 'info');

      const data = await uploadWithProgress(
        `${API_URL}/api/submit`,
        formData,
        token,
        (percent, loaded, total) => {
          setUploadProgress(percent);
          setUploadedBytes(loaded);
          setTotalBytes(total);
          if (percent === 100) {
            addLog(`Payload 100% transmitted to backend buffer (${(total / 1024 / 1024).toFixed(2)} MB).`, 'success');
            addLog(`Initializing behind-the-scenes forensic OCR & plagiarism engines...`, 'info');
            setPipelineStepIndex(1);
            setActiveEngineStage('preprocessing');
          }
        }
      );

      setSubmissionId(data.submission_id);
      addLog(`Submission registered in database with ID #${data.submission_id}.`, 'success');

      // Fetch immediately or start polling
      const statusRes = await fetch(`${API_URL}/api/status/${data.submission_id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const statusData = await statusRes.json();
      setStatusData(statusData);

      if (statusData.status === 'completed') {
        setPipelineStepIndex(7);
        setActiveEngineStage('completed');
        addLog(`[SUCCESS] OCR score calculated: ${statusData.ocr_score || 100}% (${statusData.ocr_status || 'Accepted'}).`, 'success');
        addLog(`[SUCCESS] Forensic analysis finished. AI Score: ${statusData.ai_score}%, Plag Match: ${statusData.plagiarism_score}%.`, 'success');
        addLog(`[SUCCESS] Document accepted and ready for student review & lock.`, 'success');
        setIsUploading(false);
        setTimeout(() => setCurrentStep(3), 800);
      } else {
        // Poll for background worker completion
        pollStatus(data.submission_id);
      }
    } catch (err) {
      setError(err.message);
      addLog(`Upload / Processing failed: ${err.message}`, 'error');
      setIsUploading(false);
    }
  };

  // ── Save & Lock Submission ──
  const handleLockSubmission = async () => {
    if (!submissionId) return;
    setIsLocking(true);
    setError('');

    const token = localStorage.getItem('token');
    try {
      const res = await fetch(`${API_URL}/api/submissions/${submissionId}/lock`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to lock submission');
      }

      const receiptData = await res.json();
      setLockedReceipt(receiptData);
      setCurrentStep(4); // Move to Step 4: Finalized & Locked
      fetchHistory(); // refresh history list
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLocking(false);
    }
  };

  // ── Discard and Re-upload ──
  const handleDiscard = async () => {
    if (submissionId && !statusData?.is_locked) {
      const token = localStorage.getItem('token');
      try {
        await fetch(`${API_URL}/api/submissions/${submissionId}`, {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${token}` }
        });
      } catch (err) {
        console.warn('Discard cleanup warning:', err);
      }
    }
    resetUploadFlow();
  };

  // ── Reset entire flow for another submission ──
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
    setEngineLogs([]);
    setCurrentStep(1);
  };

  // ── Fetch Student's Past Submissions History ──
  const fetchHistory = async () => {
    const token = localStorage.getItem('token');
    if (!token) return;
    setLoadingHistory(true);
    try {
      const res = await fetch(`${API_URL}/api/submissions/my`, {
        headers: { Authorization: `Bearer ${token}` }
      });
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
    if (activeTab === 'history') {
      fetchHistory();
    }
  }, [activeTab]);

  // ── Filtered History ──
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

  // ── Download File Helper ──
  const handleDownloadFile = async (subId, filename) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/download/${subId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!response.ok) throw new Error('Download failed');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || 'Assignment_File';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
    } catch (err) {
      alert('Error downloading file: ' + err.message);
    }
  };

  // ── Download Official Receipt as Text File ──
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

  // ── Helper to format file format badge ──
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

  return (
    <div className="portal-shell student-portal-shell" style={{ maxWidth: '960px', margin: '0 auto', padding: '0 0.5rem 3rem' }}>
      
      {/* ── Top Header & Student Badge ── */}
      <div className="flex flex-col-mob md:flex-row md:items-center justify-between gap-4-mob" style={{ marginBottom: '1.75rem' }}>
        <div>
          <div className="flex items-center gap-2">
            <h2 style={{ fontWeight: 800, marginBottom: '0.25rem' }}>Student Submission Portal</h2>
            <span className="badge badge-primary" style={{ fontSize: '0.75rem' }}>v2.0 AI & OCR</span>
          </div>
          <p className="text-muted" style={{ fontSize: '0.925rem' }}>
            Multi-stage assignment upload, real-time OCR quality scoring, and forensic locking.
          </p>
        </div>

        {user && (
          <div style={{
            backgroundColor: 'var(--surface-color)',
            padding: '0.75rem 1.25rem',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--border-color)',
            boxShadow: 'var(--shadow-xs)'
          }}>
            <div className="flex items-center gap-2" style={{ fontWeight: 700, color: 'var(--text-main)', marginBottom: '0.25rem' }}>
              <User size={15} style={{ color: 'var(--primary-color)' }} />
              <span>{user.name}</span>
            </div>
            <div className="flex items-center gap-3 text-muted" style={{ fontSize: '0.825rem' }}>
              <span><strong>Roll:</strong> {user.enrollment_no || 'N/A'}</span>
              <span>•</span>
              <span><strong>Sec:</strong> {user.section || 'N/A'}</span>
            </div>
          </div>
        )}
      </div>

      {/* ── Tab Switcher (New Submission vs My Submissions) ── */}
      <div style={{
        display: 'flex',
        gap: '0.5rem',
        borderBottom: '1px solid var(--border-color)',
        marginBottom: '2rem',
        paddingBottom: '0.25rem'
      }}>
        <button
          type="button"
          onClick={() => setActiveTab('new-submission')}
          style={{
            padding: '0.65rem 1.25rem',
            borderRadius: 'var(--radius-md) var(--radius-md) 0 0',
            fontWeight: 700,
            fontSize: '0.925rem',
            color: activeTab === 'new-submission' ? 'var(--primary-color)' : 'var(--text-muted)',
            borderBottom: activeTab === 'new-submission' ? '2.5px solid var(--primary-color)' : '2.5px solid transparent',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            transition: 'var(--transition)'
          }}
        >
          <UploadCloud size={17} />
          <span>Upload & Submit Assignment</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('history')}
          style={{
            padding: '0.65rem 1.25rem',
            borderRadius: 'var(--radius-md) var(--radius-md) 0 0',
            fontWeight: 700,
            fontSize: '0.925rem',
            color: activeTab === 'history' ? 'var(--primary-color)' : 'var(--text-muted)',
            borderBottom: activeTab === 'history' ? '2.5px solid var(--primary-color)' : '2.5px solid transparent',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            transition: 'var(--transition)'
          }}
        >
          <Clock size={17} />
          <span>My Submissions History</span>
        </button>
      </div>

      {/* ── Error Banner ── */}
      {error && (
        <div className="alert alert-danger" style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
          <AlertCircle size={20} style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <div style={{ fontWeight: 700, marginBottom: '0.15rem' }}>Submission Alert</div>
            <div>{error}</div>
          </div>
        </div>
      )}

      {/* ────────────────────────────────────────────────────────────
          TAB 1: NEW SUBMISSION (4-STEP INTERACTIVE WORKFLOW)
      ──────────────────────────────────────────────────────────── */}
      {activeTab === 'new-submission' && (
        <div>
          {/* ── 4-Stage Progress Stepper ── */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '0.75rem',
            marginBottom: '2rem'
          }}>
            {[
              { num: 1, title: 'Subject & Upload', subtitle: 'Select & ingest' },
              { num: 2, title: 'Engine Pipeline', subtitle: 'Real-time telemetry' },
              { num: 3, title: 'OCR & Review', subtitle: 'Quality acceptance' },
              { num: 4, title: 'Save & Lock', subtitle: 'Institutional seal' }
            ].map((step) => {
              const isActive = currentStep === step.num;
              const isCompleted = currentStep > step.num;
              return (
                <div
                  key={step.num}
                  style={{
                    backgroundColor: isActive ? 'var(--primary-light)' : 'var(--surface-color)',
                    border: `1px solid ${isActive ? 'var(--primary-color)' : isCompleted ? 'var(--success-color)' : 'var(--border-color)'}`,
                    borderRadius: 'var(--radius-lg)',
                    padding: '0.75rem 1rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    boxShadow: isActive ? 'var(--shadow-sm)' : 'none',
                    transition: 'var(--transition)'
                  }}
                >
                  <div
                    style={{
                      width: '28px',
                      height: '28px',
                      borderRadius: '50%',
                      backgroundColor: isCompleted ? 'var(--success-color)' : isActive ? 'var(--primary-color)' : 'var(--border-color)',
                      color: '#ffffff',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 800,
                      fontSize: '0.8rem',
                      flexShrink: 0
                    }}
                  >
                    {isCompleted ? <Check size={14} /> : step.num}
                  </div>
                  <div style={{ overflow: 'hidden' }}>
                    <div style={{ fontWeight: 700, fontSize: '0.85rem', color: isActive ? 'var(--primary-color)' : 'var(--text-main)', whiteSpace: 'nowrap' }}>
                      {step.title}
                    </div>
                    <div className="text-muted" style={{ fontSize: '0.725rem', whiteSpace: 'nowrap' }}>
                      {step.subtitle}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* ══════════════════════════════════════════════════════════
              STAGE 1: SELECTION & FILE UPLOAD (JPG, PNG, PDF, DOCX, TXT)
          ══════════════════════════════════════════════════════════ */}
          {currentStep === 1 && (
            <div className="card glass-panel student-upload-card" style={{ padding: '2rem' }}>
              <form onSubmit={handleSubmit}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6" style={{ marginBottom: '1.75rem' }}>
                  
                  {/* Subject Selector */}
                  <div className="form-group">
                    <label className="form-label" style={{ fontWeight: 700 }}>
                      1. Select Course / Subject *
                    </label>
                    <select
                      className="form-select"
                      value={subject}
                      onChange={(e) => setSubject(e.target.value)}
                      required
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
                        style={{ marginTop: '0.5rem' }}
                        value={customSubject}
                        onChange={(e) => setCustomSubject(e.target.value)}
                        required
                      />
                    )}
                  </div>

                  {/* Assignment Title Selector */}
                  <div className="form-group">
                    <label className="form-label" style={{ fontWeight: 700 }}>
                      2. Assignment / Submission Title *
                    </label>
                    <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', marginBottom: '0.5rem' }}>
                      {ASSIGNMENT_PRESETS.map((preset) => (
                        <button
                          key={preset}
                          type="button"
                          onClick={() => {
                            setAssignmentTitle(preset);
                            if (preset !== 'Custom') setCustomAssignment('');
                          }}
                          style={{
                            padding: '0.3rem 0.65rem',
                            borderRadius: 'var(--radius-full)',
                            fontSize: '0.78rem',
                            fontWeight: 600,
                            backgroundColor: assignmentTitle === preset ? 'var(--primary-color)' : 'var(--surface-color)',
                            color: assignmentTitle === preset ? '#ffffff' : 'var(--text-muted)',
                            border: `1px solid ${assignmentTitle === preset ? 'var(--primary-color)' : 'var(--border-color)'}`,
                            transition: 'var(--transition)'
                          }}
                        >
                          {preset}
                        </button>
                      ))}
                    </div>

                    {assignmentTitle === 'Custom' ? (
                      <input
                        type="text"
                        className="form-input"
                        placeholder="e.g. Assignment 1: Relational Algebra & SQL"
                        value={customAssignment}
                        onChange={(e) => setCustomAssignment(e.target.value)}
                        required
                      />
                    ) : (
                      <input
                        type="text"
                        className="form-input"
                        value={assignmentTitle}
                        onChange={(e) => setAssignmentTitle(e.target.value)}
                        required
                      />
                    )}
                  </div>
                </div>

                {/* Drag and Drop Zone supporting JPG, PNG, PDF, DOCX, TXT */}
                <div className="form-group" style={{ marginTop: '1rem' }}>
                  <label className="form-label" style={{ fontWeight: 700 }}>
                    3. Upload Assignment Document or Handwritten Photo *
                  </label>
                  
                  <div
                    className="student-upload-dropzone"
                    onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                    onDragLeave={() => setIsDragging(false)}
                    onDrop={(e) => {
                      e.preventDefault();
                      setIsDragging(false);
                      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                        handleFileSelected(e.dataTransfer.files[0]);
                      }
                    }}
                    style={{
                      border: `2px dashed ${file ? 'var(--primary-color)' : isDragging ? 'var(--accent-color)' : 'var(--border-color)'}`,
                      borderRadius: 'var(--radius-xl)',
                      padding: '2.5rem 1.5rem',
                      textAlign: 'center',
                      backgroundColor: file ? 'var(--primary-light)' : isDragging ? 'var(--accent-light)' : 'var(--surface-subtle)',
                      transition: 'var(--transition)',
                      cursor: 'pointer',
                      position: 'relative'
                    }}
                    onClick={() => document.getElementById('fileUploadInput').click()}
                  >
                    {file ? (
                      <div className="flex flex-col items-center">
                        {/* Instant Image Preview for JPG/PNG */}
                        {imagePreviewUrl ? (
                          <div style={{ position: 'relative', marginBottom: '1rem' }}>
                            <img
                              src={imagePreviewUrl}
                              alt="Assignment Preview"
                              style={{
                                maxHeight: '180px',
                                maxWidth: '280px',
                                objectFit: 'contain',
                                borderRadius: 'var(--radius-md)',
                                border: '2px solid var(--border-color)',
                                boxShadow: 'var(--shadow-md)'
                              }}
                            />
                            <span
                              className="badge badge-accent"
                              style={{
                                position: 'absolute',
                                bottom: '6px',
                                right: '6px',
                                fontSize: '0.7rem',
                                boxShadow: 'var(--shadow-sm)'
                              }}
                            >
                              Photo Detected
                            </span>
                          </div>
                        ) : (
                          <div style={{
                            width: '60px',
                            height: '60px',
                            borderRadius: 'var(--radius-lg)',
                            backgroundColor: 'var(--surface-color)',
                            display: 'inline-flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: 'var(--primary-color)',
                            marginBottom: '0.75rem',
                            boxShadow: 'var(--shadow-sm)'
                          }}>
                            <FileText size={34} />
                          </div>
                        )}

                        <div className="flex items-center gap-2" style={{ marginBottom: '0.2rem' }}>
                          <p style={{ fontWeight: 700, color: 'var(--text-main)', fontSize: '1.05rem' }}>
                            {file.name}
                          </p>
                          {getFileBadge(file.name)}
                        </div>

                        <p className="text-muted" style={{ fontSize: '0.85rem', marginBottom: '1.25rem' }}>
                          {(file.size / 1024 / 1024).toFixed(2)} MB • Ready for OCR & forensic ingestion
                        </p>

                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            setFile(null);
                            setImagePreviewUrl(null);
                          }}
                          className="btn btn-outline"
                          style={{
                            padding: '0.35rem 0.85rem',
                            fontSize: '0.8rem',
                            color: 'var(--danger-color)',
                            borderColor: 'rgba(239, 68, 68, 0.3)'
                          }}
                        >
                          <X size={14} /> Remove File & Choose Another
                        </button>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center">
                        <div style={{
                          width: '64px',
                          height: '64px',
                          borderRadius: '50%',
                          backgroundColor: 'var(--primary-light)',
                          display: 'inline-flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          marginBottom: '1rem',
                          color: 'var(--primary-color)'
                        }}>
                          <UploadCloud size={32} />
                        </div>
                        <p style={{ fontWeight: 700, color: 'var(--text-main)', marginBottom: '0.35rem', fontSize: '1.05rem' }}>
                          Click to select or drag and drop your assignment
                        </p>
                        <p className="text-muted" style={{ fontSize: '0.875rem', marginBottom: '1.25rem', maxWidth: '480px' }}>
                          Accepts <strong>JPG, JPEG, PNG</strong> photos of handwritten notebooks, or digital <strong>PDF, DOCX, DOC, TXT</strong> documents.
                        </p>

                        {/* Format badges */}
                        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', justifyContent: 'center' }}>
                          {[
                            { name: 'JPG / JPEG', type: 'Handwritten / Scan' },
                            { name: 'PNG', type: 'Image' },
                            { name: 'PDF', type: 'Document' },
                            { name: 'DOCX', type: 'Word' },
                            { name: 'TXT', type: 'Plain text' }
                          ].map((fmt) => (
                            <span
                              key={fmt.name}
                              className="badge badge-neutral"
                              style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem' }}
                            >
                              .{fmt.name}
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

                {/* Submit Action */}
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '2rem' }}>
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={!file || !subject}
                    style={{ minWidth: '200px', padding: '0.85rem 1.75rem', fontSize: '0.95rem' }}
                  >
                    <div className="flex items-center gap-2">
                      <Sparkles size={18} />
                      <span>Start Forensic Ingestion</span>
                    </div>
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* ══════════════════════════════════════════════════════════
              STAGE 2: BEHIND-THE-SCENES LIVE PIPELINE & TELEMETRY MONITOR
          ══════════════════════════════════════════════════════════ */}
          {currentStep === 2 && (
            <div className="card glass-panel" style={{ padding: '2rem' }}>
              <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                <div style={{
                  width: '64px',
                  height: '64px',
                  borderRadius: '50%',
                  backgroundColor: 'var(--primary-light)',
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--primary-color)',
                  marginBottom: '1rem',
                  boxShadow: '0 0 0 8px rgba(79, 70, 229, 0.1)'
                }}>
                  <Cpu size={32} className="pulse-icon" />
                </div>
                <h3 style={{ fontWeight: 800, marginBottom: '0.25rem' }}>
                  Processing Assignment & Live Telemetry
                </h3>
                <p className="text-muted" style={{ fontSize: '0.9rem' }}>
                  Watch real-time background stages as your document is parsed, scanned by OCR, and verified.
                </p>
              </div>

              {/* Byte Upload Progress Bar */}
              <div style={{
                backgroundColor: 'var(--surface-color)',
                padding: '1.25rem',
                borderRadius: 'var(--radius-lg)',
                border: '1px solid var(--border-color)',
                marginBottom: '1.75rem'
              }}>
                <div className="flex justify-between items-center" style={{ marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: 600 }}>
                  <span className="flex items-center gap-2" style={{ color: 'var(--text-main)' }}>
                    <UploadCloud size={16} style={{ color: 'var(--primary-color)' }} />
                    <span>Payload Stream Ingestion</span>
                  </span>
                  <span style={{ color: 'var(--primary-color)', fontWeight: 800 }}>{uploadProgress}%</span>
                </div>

                <div style={{
                  width: '100%',
                  height: '8px',
                  backgroundColor: 'var(--border-color)',
                  borderRadius: 'var(--radius-full)',
                  overflow: 'hidden',
                  position: 'relative'
                }}>
                  <div style={{
                    width: `${uploadProgress}%`,
                    height: '100%',
                    background: 'linear-gradient(90deg, var(--primary-color) 0%, var(--accent-color) 100%)',
                    borderRadius: 'var(--radius-full)',
                    transition: 'width 0.2s ease-out'
                  }}></div>
                </div>

                <div className="flex justify-between items-center" style={{ marginTop: '0.5rem', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  <span>
                    Transferred: {uploadedBytes ? `${(uploadedBytes / 1024 / 1024).toFixed(2)} MB` : '0 MB'} / {totalBytes ? `${(totalBytes / 1024 / 1024).toFixed(2)} MB` : '0 MB'}
                  </span>
                  <span>{uploadProgress < 100 ? 'Streaming file payload...' : 'Payload received by backend buffer'}</span>
                </div>
              </div>

              {/* Visual Pipeline Stages */}
              <div style={{ marginBottom: '1.75rem' }}>
                <h4 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '1rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Behind-The-Scenes Forensic Stages
                </h4>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
                  {PIPELINE_STAGES.map((stage, idx) => {
                    const isStageCompleted = pipelineStepIndex > idx;
                    const isStageCurrent = pipelineStepIndex === idx;
                    const IconComp = stage.icon;

                    return (
                      <div
                        key={stage.key}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          padding: '0.75rem 1rem',
                          borderRadius: 'var(--radius-md)',
                          backgroundColor: isStageCurrent
                            ? 'var(--primary-light)'
                            : isStageCompleted
                            ? 'rgba(16, 185, 129, 0.05)'
                            : 'var(--surface-color)',
                          border: `1px solid ${
                            isStageCurrent
                              ? 'var(--primary-color)'
                              : isStageCompleted
                              ? 'rgba(16, 185, 129, 0.25)'
                              : 'var(--border-color)'
                          }`,
                          transition: 'var(--transition)'
                        }}
                      >
                        <div className="flex items-center gap-3">
                          <div
                            style={{
                              width: '32px',
                              height: '32px',
                              borderRadius: 'var(--radius-sm)',
                              backgroundColor: isStageCurrent
                                ? 'var(--primary-color)'
                                : isStageCompleted
                                ? 'var(--success-color)'
                                : 'var(--surface-subtle)',
                              color: isStageCurrent || isStageCompleted ? '#ffffff' : 'var(--text-subtle)',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center'
                            }}
                          >
                            <IconComp size={16} />
                          </div>
                          <div>
                            <div style={{
                              fontWeight: 700,
                              fontSize: '0.875rem',
                              color: isStageCurrent ? 'var(--primary-color)' : 'var(--text-main)'
                            }}>
                              {idx + 1}. {stage.name}
                            </div>
                            <div className="text-muted" style={{ fontSize: '0.75rem' }}>
                              {stage.desc}
                            </div>
                          </div>
                        </div>

                        <div>
                          {isStageCompleted ? (
                            <span className="badge badge-success" style={{ fontSize: '0.72rem' }}>
                              <Check size={12} /> Done
                            </span>
                          ) : isStageCurrent ? (
                            <div className="flex items-center gap-2" style={{ color: 'var(--primary-color)', fontSize: '0.78rem', fontWeight: 700 }}>
                              <div className="spinner" style={{ width: '14px', height: '14px', borderWidth: '2px' }}></div>
                              <span>Running...</span>
                            </div>
                          ) : (
                            <span className="text-muted" style={{ fontSize: '0.75rem' }}>Waiting</span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Terminal / Telemetry Event Console */}
              <div style={{
                backgroundColor: '#090d16',
                borderRadius: 'var(--radius-lg)',
                padding: '1rem',
                color: '#e2e8f0',
                fontFamily: 'monospace',
                fontSize: '0.78rem',
                border: '1px solid #1e293b',
                boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.5)'
              }}>
                <div className="flex items-center justify-between" style={{ borderBottom: '1px solid #1e293b', paddingBottom: '0.5rem', marginBottom: '0.75rem' }}>
                  <div className="flex items-center gap-2" style={{ color: '#38bdf8', fontWeight: 700 }}>
                    <Terminal size={14} />
                    <span>Live Engine Telemetry & Backend Events</span>
                  </div>
                  <span style={{ fontSize: '0.7rem', color: '#64748b' }}>WebSocket/Polling Synced</span>
                </div>

                <div
                  ref={logsContainerRef}
                  style={{
                    maxHeight: '140px',
                    overflowY: 'auto',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.35rem'
                  }}
                >
                  {engineLogs.length === 0 ? (
                    <div style={{ color: '#64748b' }}>Waiting for engine initialization...</div>
                  ) : (
                    engineLogs.map((log, i) => (
                      <div key={i} style={{ display: 'flex', gap: '0.5rem', lineHeight: 1.4 }}>
                        <span style={{ color: '#64748b' }}>[{log.timestamp}]</span>
                        <span
                          style={{
                            color:
                              log.type === 'error'
                                ? '#f87171'
                                : log.type === 'success'
                                ? '#4ade80'
                                : '#93c5fd'
                          }}
                        >
                          {log.message}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}

          {/* ══════════════════════════════════════════════════════════
              STAGE 3: DOCUMENT REVIEW & OCR SCORE ACCEPTANCE
          ══════════════════════════════════════════════════════════ */}
          {currentStep === 3 && statusData && (
            <div className="card glass-panel" style={{ padding: '2rem' }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                borderBottom: '1px solid var(--border-color)',
                paddingBottom: '1.25rem',
                marginBottom: '1.75rem'
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
                gap: '1rem'
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
                        border: '1px solid var(--border-color)'
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
                      justifyContent: 'center'
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
                  textAlign: 'center'
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
                  textAlign: 'center'
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
                  textAlign: 'center'
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
                  marginBottom: '1.75rem'
                }}>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      cursor: 'pointer'
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
                      whiteSpace: 'pre-wrap'
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
                gap: '0.85rem'
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

          {/* ══════════════════════════════════════════════════════════
              STAGE 4: FINALIZED & LOCKED SUBMISSION RECEIPT
          ══════════════════════════════════════════════════════════ */}
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
                boxShadow: '0 0 0 10px rgba(16, 185, 129, 0.1)'
              }}>
                <ShieldCheck size={44} />
              </div>

              <h2 style={{ fontWeight: 900, marginBottom: '0.35rem', color: 'var(--text-main)' }}>
                Submission Locked & Finalized!
              </h2>
              <p className="text-muted" style={{ fontSize: '0.925rem', marginBottom: '2rem', maxWidth: '520px', margin: '0 auto 2rem' }}>
                Your assignment has been recorded with an immutable institutional verification seal.
              </p>

              {/* Official Certificate Box */}
              <div style={{
                backgroundColor: 'var(--surface-color)',
                borderRadius: 'var(--radius-xl)',
                border: '1.5px solid var(--border-color)',
                padding: '1.75rem',
                maxWidth: '620px',
                margin: '0 auto 2rem',
                textAlign: 'left',
                boxShadow: 'var(--shadow-md)'
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
                  marginBottom: '1.5rem'
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
                    <span className="text-muted">Course / Subject:</span>
                    <div style={{ fontWeight: 700 }}>{lockedReceipt.subject}</div>
                  </div>
                  <div>
                    <span className="text-muted">Assignment Title:</span>
                    <div style={{ fontWeight: 700 }}>{lockedReceipt.assignment_title}</div>
                  </div>
                  <div>
                    <span className="text-muted">Uploaded File:</span>
                    <div style={{ fontWeight: 700 }}>{lockedReceipt.filename}</div>
                  </div>
                  <div>
                    <span className="text-muted">Locked Timestamp:</span>
                    <div style={{ fontWeight: 700 }}>
                      {new Date(lockedReceipt.locked_at).toLocaleString()}
                    </div>
                  </div>
                </div>

                {/* Scores Snapshot */}
                <div className="grid grid-cols-3 gap-3 text-center">
                  <div style={{ padding: '0.75rem', backgroundColor: 'var(--bg-color)', borderRadius: 'var(--radius-md)' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>OCR Score</div>
                    <div style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--success-color)' }}>
                      {lockedReceipt.ocr_score != null ? `${lockedReceipt.ocr_score}%` : '100%'}
                    </div>
                  </div>
                  <div style={{ padding: '0.75rem', backgroundColor: 'var(--bg-color)', borderRadius: 'var(--radius-md)' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Plagiarism</div>
                    <div style={{ fontSize: '1.2rem', fontWeight: 800, color: lockedReceipt.plagiarism_score > 30 ? 'var(--danger-color)' : 'var(--success-color)' }}>
                      {lockedReceipt.plagiarism_score != null ? `${lockedReceipt.plagiarism_score}%` : '0%'}
                    </div>
                  </div>
                  <div style={{ padding: '0.75rem', backgroundColor: 'var(--bg-color)', borderRadius: 'var(--radius-md)' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>AI Score</div>
                    <div style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--primary-color)' }}>
                      {lockedReceipt.ai_score != null ? `${lockedReceipt.ai_score}%` : '0%'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Receipt Actions */}
              <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => handleDownloadReceiptText(lockedReceipt)}
                  style={{ padding: '0.75rem 1.5rem' }}
                >
                  <Download size={16} /> Download Official Receipt
                </button>

                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={() => {
                    setActiveTab('history');
                    resetUploadFlow();
                  }}
                  style={{ padding: '0.75rem 1.5rem' }}
                >
                  <Clock size={16} /> View in My Submissions
                </button>

                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={resetUploadFlow}
                  style={{ padding: '0.75rem 1.5rem' }}
                >
                  <Sparkles size={16} /> Submit Another Assignment
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ────────────────────────────────────────────────────────────
          TAB 2: MY SUBMISSIONS HISTORY
      ──────────────────────────────────────────────────────────── */}
      {activeTab === 'history' && (
        <div className="card glass-panel" style={{ padding: '2rem' }}>
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4" style={{ marginBottom: '1.5rem' }}>
            <div>
              <h3 style={{ fontWeight: 800 }}>My Submission Records</h3>
              <p className="text-muted" style={{ fontSize: '0.875rem' }}>
                All assignments submitted and locked under your student ID.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <div className="search-box" style={{ maxWidth: '280px' }}>
                <Search size={16} className="search-icon" />
                <input
                  type="text"
                  placeholder="Search subject, assignment..."
                  value={historySearch}
                  onChange={(e) => setHistorySearch(e.target.value)}
                  className="form-input"
                  style={{ paddingLeft: '2.25rem', fontSize: '0.85rem' }}
                />
              </div>

              <button
                type="button"
                className="btn btn-outline"
                onClick={fetchHistory}
                style={{ padding: '0.5rem 0.75rem' }}
                title="Refresh Submissions"
              >
                <RefreshCw size={15} className={loadingHistory ? 'spin' : ''} />
              </button>
            </div>
          </div>

          {loadingHistory ? (
            <div style={{ padding: '3rem 1rem', textAlign: 'center' }}>
              <div className="spinner" style={{ width: '36px', height: '36px', margin: '0 auto 1rem' }}></div>
              <p className="text-muted">Loading submission history...</p>
            </div>
          ) : filteredHistory.length === 0 ? (
            <div style={{ padding: '3rem 1rem', textAlign: 'center', backgroundColor: 'var(--surface-color)', borderRadius: 'var(--radius-lg)', border: '1px dashed var(--border-color)' }}>
              <FileSpreadsheet size={40} style={{ color: 'var(--text-subtle)', marginBottom: '0.75rem' }} />
              <h4 style={{ fontWeight: 700, marginBottom: '0.25rem' }}>No Submissions Found</h4>
              <p className="text-muted" style={{ fontSize: '0.875rem', marginBottom: '1.25rem' }}>
                {historySearch ? 'No assignments matched your search query.' : 'You haven’t submitted any assignments yet.'}
              </p>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => setActiveTab('new-submission')}
              >
                Submit Your First Assignment
              </button>
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table" style={{ width: '100%', fontSize: '0.875rem' }}>
                <thead>
                  <tr>
                    <th>Assignment & Subject</th>
                    <th>File</th>
                    <th>Submitted On</th>
                    <th>OCR Score</th>
                    <th>Plagiarism</th>
                    <th>AI Score</th>
                    <th>Status</th>
                    <th style={{ textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredHistory.map((sub) => (
                    <tr key={sub.id}>
                      <td>
                        <div style={{ fontWeight: 700, color: 'var(--text-main)' }}>
                          {sub.assignment_title || 'Assignment 1'}
                        </div>
                        <div className="text-muted" style={{ fontSize: '0.775rem' }}>
                          {sub.subject}
                        </div>
                      </td>
                      <td>
                        <div className="flex items-center gap-1.5">
                          <span style={{ maxWidth: '140px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={sub.filename}>
                            {sub.filename}
                          </span>
                          {getFileBadge(sub.filename)}
                        </div>
                      </td>
                      <td className="text-muted" style={{ fontSize: '0.8rem' }}>
                        {new Date(sub.created_at).toLocaleDateString()}{' '}
                        <span style={{ fontSize: '0.72rem' }}>{new Date(sub.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      </td>
                      <td>
                        <span className="badge badge-success" style={{ fontSize: '0.75rem', fontWeight: 700 }}>
                          {sub.ocr_score != null ? `${sub.ocr_score}%` : '100%'}
                        </span>
                      </td>
                      <td>
                        <span
                          className={`badge ${sub.plagiarism_score > 30 ? 'badge-danger' : 'badge-success'}`}
                          style={{ fontSize: '0.75rem', fontWeight: 700 }}
                        >
                          {sub.plagiarism_score != null ? `${sub.plagiarism_score}%` : '0%'}
                        </span>
                      </td>
                      <td>
                        <span
                          className={`badge ${sub.ai_score > 50 ? 'badge-danger' : 'badge-primary'}`}
                          style={{ fontSize: '0.75rem', fontWeight: 700 }}
                        >
                          {sub.ai_score != null ? `${sub.ai_score}%` : '0%'}
                        </span>
                      </td>
                      <td>
                        {sub.is_locked ? (
                          <span className="badge badge-success" style={{ fontSize: '0.72rem', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                            <Lock size={11} /> Locked
                          </span>
                        ) : (
                          <span className="badge badge-warning" style={{ fontSize: '0.72rem' }}>
                            Draft / Review
                          </span>
                        )}
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <div style={{ display: 'inline-flex', gap: '0.35rem' }}>
                          <button
                            type="button"
                            className="btn btn-outline"
                            onClick={() => setSelectedReceiptModal(sub)}
                            style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                            title="View Official Receipt"
                          >
                            <ShieldCheck size={13} /> Receipt
                          </button>
                          <button
                            type="button"
                            className="btn btn-outline"
                            onClick={() => handleDownloadFile(sub.id, sub.filename)}
                            style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                            title="Download File"
                          >
                            <Download size={13} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ── Receipt Viewer Modal ── */}
      {selectedReceiptModal && (
        <div className="modal-backdrop" onClick={() => setSelectedReceiptModal(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '560px', padding: '2rem' }}>
            <div className="flex justify-between items-center" style={{ marginBottom: '1.25rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
              <div className="flex items-center gap-2">
                <ShieldCheck size={22} style={{ color: 'var(--success-color)' }} />
                <h4 style={{ fontWeight: 800 }}>Institutional Submission Receipt</h4>
              </div>
              <button
                type="button"
                onClick={() => setSelectedReceiptModal(null)}
                style={{ color: 'var(--text-muted)', padding: '0.25rem' }}
              >
                <X size={20} />
              </button>
            </div>

            <div style={{
              backgroundColor: 'var(--primary-light)',
              border: '1px dashed var(--primary-color)',
              borderRadius: 'var(--radius-md)',
              padding: '0.75rem 1rem',
              marginBottom: '1.25rem'
            }}>
              <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--primary-color)', textTransform: 'uppercase' }}>
                Verification Token
              </div>
              <div style={{ fontFamily: 'monospace', fontWeight: 800, fontSize: '0.95rem', color: 'var(--text-main)' }}>
                {selectedReceiptModal.verification_token || `PLAG-SEC-${String(selectedReceiptModal.id).padStart(4, '0')}-REG`}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3" style={{ fontSize: '0.85rem', marginBottom: '1.5rem' }}>
              <div>
                <span className="text-muted">Subject:</span>
                <div style={{ fontWeight: 700 }}>{selectedReceiptModal.subject}</div>
              </div>
              <div>
                <span className="text-muted">Assignment:</span>
                <div style={{ fontWeight: 700 }}>{selectedReceiptModal.assignment_title}</div>
              </div>
              <div>
                <span className="text-muted">File:</span>
                <div style={{ fontWeight: 700 }}>{selectedReceiptModal.filename}</div>
              </div>
              <div>
                <span className="text-muted">Submitted At:</span>
                <div style={{ fontWeight: 700 }}>{new Date(selectedReceiptModal.created_at).toLocaleString()}</div>
              </div>
              <div>
                <span className="text-muted">OCR Legibility:</span>
                <div style={{ fontWeight: 700, color: 'var(--success-color)' }}>
                  {selectedReceiptModal.ocr_score != null ? `${selectedReceiptModal.ocr_score}%` : '100%'}
                </div>
              </div>
              <div>
                <span className="text-muted">Forensic Classification:</span>
                <div style={{ fontWeight: 700 }}>{selectedReceiptModal.label || 'Original'}</div>
              </div>
            </div>

            <div className="flex justify-between items-center">
              <button
                type="button"
                className="btn btn-outline"
                onClick={() => setSelectedReceiptModal(null)}
              >
                Close
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => handleDownloadReceiptText(selectedReceiptModal)}
              >
                <Download size={15} /> Download Receipt (.txt)
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
