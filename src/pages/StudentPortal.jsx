import React, { useState } from 'react';
import { UploadCloud, CheckCircle2, FileText, X } from 'lucide-react';

export default function StudentPortal() {
  const [subject, setSubject] = useState('');
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState('');
  const [user, setUser] = useState(null);

  const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

  React.useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
  }, []);

  const subjects = [
    'Database Management Systems',
    'Theory of Computation',
    'Probability, Statistics and Linear Programming',
    'Circuits and Systems',
    'Programming in Java'
  ];

  const pollStatus = async (submissionId) => {
    const token = localStorage.getItem('token');
    if (!token) return;

    const interval = setInterval(async () => {
      try {
        const response = await fetch(`${API_URL}/api/status/${submissionId}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await response.json();
        setStatus(data);

        if (data.status === 'completed' || data.status === 'failed') {
          clearInterval(interval);
          if (data.status === 'completed') setUploadSuccess(true);
        }
      } catch (err) {
        console.error("Polling error:", err);
        clearInterval(interval);
      }
    }, 2500);
  };


  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
      setUploadSuccess(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file || !subject) return;

    setIsUploading(true);
    setError('');
    const token = localStorage.getItem('token');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('subject', subject);

    try {
      const response = await fetch(`${API_URL}/api/submit`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData,
      });

      if (!response.ok) {
        let errMessage = 'Failed to upload assignment';
        try {
          const errData = await response.json();
          errMessage = errData.detail || errMessage;
        } catch {
          // ignore parsing error
        }
        throw new Error(errMessage);
      }

      const data = await response.json();

      // In sync mode, the backend already processed the file.
      // Fetch the completed status immediately.
      const statusRes = await fetch(`${API_URL}/api/status/${data.submission_id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const statusData = await statusRes.json();
      setStatus(statusData);

      if (statusData.status === 'completed') {
        setUploadSuccess(true);
      } else {
        // Fallback to polling if not yet completed
        pollStatus(data.submission_id);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsUploading(false);
    }
  };

  const resetUpload = () => {
    setFile(null);
    setSubject('');
    setUploadSuccess(false);
    setStatus(null);
    setError('');
  };


  return (
    <div className="portal-shell student-portal-shell" style={{ maxWidth: '800px', margin: '0 auto', padding: '0 1rem' }}>
      <div style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2>Student Dashboard</h2>
          <p className="text-muted">Select your subject and upload your assignment securely.</p>
        </div>
        {user && (
          <div style={{ textAlign: 'right', backgroundColor: 'var(--bg-color)', padding: '0.75rem 1.25rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
            <div style={{ fontWeight: 600, color: 'var(--text-main)', marginBottom: '0.25rem' }}>{user.name}</div>
            <div className="text-muted" style={{ fontSize: '0.875rem', display: 'flex', gap: '1rem' }}>
              <span><strong style={{ fontWeight: 500 }}>Roll No:</strong> {user.enrollment_no || 'N/A'}</span>
              <span><strong style={{ fontWeight: 500 }}>Section:</strong> {user.section || 'N/A'}</span>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger-color)', padding: '1rem', borderRadius: 'var(--radius-md)', marginBottom: '1.5rem', fontWeight: 500 }}>
          {error}
        </div>
      )}

      <div className="card student-upload-card">
        {uploadSuccess ? (
          <div className="flex flex-col items-center justify-center text-center" style={{ padding: '3rem 1rem' }}>
            <CheckCircle2 size={64} style={{ color: 'var(--success-color)', marginBottom: '1rem' }} />
            <h3 style={{ marginBottom: '1.5rem' }}>Analysis Report Ready</h3>

            <div className="grid grid-cols-2 gap-8 w-full max-w-md mx-auto mb-12">
              <div className="flex flex-col items-center">
                <div style={{
                  width: '100px', height: '100px', borderRadius: '50%', border: '8px solid rgba(16, 185, 129, 0.1)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative', marginBottom: '0.75rem'
                }}>
                  <span style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-main)' }}>{status?.plagiarism_score}%</span>
                </div>
                <span className="text-muted" style={{ fontSize: '0.875rem' }}>Plagiarism</span>
              </div>
              <div className="flex flex-col items-center">
                <div style={{
                  width: '100px', height: '100px', borderRadius: '50%', border: '8px solid rgba(79, 70, 229, 0.1)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '0.75rem'
                }}>
                  <span style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-main)' }}>{status?.ai_score}%</span>
                </div>
                <span className="text-muted" style={{ fontSize: '0.875rem' }}>AI Logic</span>
              </div>
            </div>

            <div style={{ backgroundColor: 'var(--bg-color)', padding: '1rem 2rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', marginBottom: '2rem' }}>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Status: </span>
              <span style={{ fontWeight: 600, color: status?.label === 'Original' ? 'var(--success-color)' : 'var(--warning-color)' }}>
                {status?.label || 'Processed'}
              </span>
            </div>

            <button type="button" className="btn btn-outline" onClick={resetUpload}>
              Submit Another Assignment
            </button>
          </div>
        ) : status && status.status !== 'failed' ? (
          <div className="flex flex-col items-center justify-center text-center" style={{ padding: '4rem 1rem' }}>
            <div className="spinner" style={{ width: '48px', height: '48px', borderWidth: '4px', marginBottom: '1.5rem' }}></div>
            <h3 style={{ marginBottom: '0.5rem' }}>Analyzing Content...</h3>
            <p className="text-muted" style={{ fontWeight: 500 }}>{status.progress || 'Waiting for processing'}</p>
            <p style={{ fontSize: '0.875rem', marginTop: '2rem', color: 'var(--text-muted)' }}>
              This usually takes less than a minute. You don't need to refresh.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Subject</label>
              <select
                className="form-select"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                required
              >
                <option value="" disabled>Select a subject...</option>
                {subjects.map((sub) => (
                  <option key={sub} value={sub}>{sub}</option>
                ))}
              </select>
            </div>

            <div className="form-group" style={{ marginTop: '2rem' }}>
              <label className="form-label">Upload Assignment File</label>
              <div
                className="student-upload-dropzone"
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                style={{
                  border: '2px dashed var(--border-color)',
                  borderRadius: 'var(--radius-lg)',
                  padding: '3rem 1.5rem',
                  textAlign: 'center',
                  backgroundColor: file ? 'rgba(79, 70, 229, 0.05)' : 'var(--bg-color)',
                  borderColor: file ? 'var(--primary-color)' : 'var(--border-color)',
                  transition: 'var(--transition)',
                  cursor: 'pointer'
                }}
                onClick={() => document.getElementById('fileUpload').click()}
              >
                {file ? (
                  <div className="flex flex-col items-center">
                    <FileText size={48} color="var(--primary-color)" style={{ marginBottom: '1rem' }} />
                    <p className="student-file-name" style={{ fontWeight: 600, color: 'var(--text-main)', marginBottom: '0.25rem' }}>{file.name}</p>
                    <p className="text-muted" style={{ fontSize: '0.875rem', marginBottom: '1rem' }}>
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                    <button
                      type="button"
                      onClick={(e) => { e.stopPropagation(); setFile(null); }}
                      style={{ background: 'none', display: 'flex', alignItems: 'center', gap: '0.25rem', color: 'var(--danger-color)', fontSize: '0.875rem' }}
                    >
                      <X size={16} /> Remove File
                    </button>
                  </div>
                ) : (
                  <div className="flex flex-col items-center">
                    <div style={{ width: '64px', height: '64px', borderRadius: '50%', backgroundColor: 'rgba(79, 70, 229, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem' }}>
                      <UploadCloud size={32} color="var(--primary-color)" />
                    </div>
                    <p style={{ fontWeight: 500, color: 'var(--text-main)', marginBottom: '0.25rem' }}>
                      Click to upload or drag and drop
                    </p>
                    <p className="text-muted" style={{ fontSize: '0.875rem' }}>
                      Word Docs, PDF, Text, or Images (.jpg, .png)
                    </p>
                  </div>
                )}
                <input
                  id="fileUpload"
                  type="file"
                  accept=".doc,.docx,.pdf,.txt,.png,.jpg,.jpeg"
                  style={{ display: 'none' }}
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      setFile(e.target.files[0]);
                    }
                  }}
                />
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '2rem' }}>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={!file || !subject || isUploading}
                style={{ minWidth: '150px' }}
              >
                {isUploading ? (
                  <><div className="spinner" style={{ width: '16px', height: '16px', borderWidth: '2px' }}></div> Uploading...</>
                ) : (
                  'Submit Assignment'
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
