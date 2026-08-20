import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, ArrowRight, ArrowLeft, CheckCircle2, AlertCircle, KeyRound } from 'lucide-react';

export default function ForgotPassword() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [statusMsg, setStatusMsg] = useState('');
  const [resetLink, setResetLink] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setStatusMsg('');
    setResetLink('');
    setLoading(true);

    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
      const response = await fetch(`${API_URL}/api/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to process password reset request.');
      }

      setStatusMsg(data.message || 'Password reset link sent to your email.');
      if (data.reset_link) {
        setResetLink(data.reset_link);
      }
    } catch (err) {
      if (err.name === 'TypeError' || err.message?.toLowerCase().includes('fetch')) {
        setError('Unable to connect to backend server. Please verify backend is running.');
      } else {
        setError(err.message || 'An error occurred. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center" style={{ minHeight: 'calc(100vh - 160px)', padding: '1rem 0' }}>
      <div className="card glass-panel w-full-mob" style={{ maxWidth: '460px', width: '100%', padding: '2.5rem 2rem' }}>
        <div className="text-center" style={{ marginBottom: '2rem' }}>
          <div style={{
            width: '60px',
            height: '60px',
            borderRadius: '50%',
            backgroundColor: 'var(--primary-light)',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--primary-color)',
            marginBottom: '1.25rem',
            boxShadow: '0 0 0 6px rgba(79, 70, 229, 0.06)'
          }}>
            <KeyRound size={28} />
          </div>
          <h2 style={{ marginBottom: '0.5rem', fontWeight: 800 }}>Forgot Password?</h2>
          <p className="text-muted" style={{ fontSize: '0.925rem' }}>
            Enter your registered email address and we'll generate a password reset link for you.
          </p>
        </div>

        {error && (
          <div className="alert alert-danger">
            <AlertCircle size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
            <span>{error}</span>
          </div>
        )}

        {statusMsg && (
          <div className="alert alert-success" style={{ flexDirection: 'column', gap: '0.5rem' }}>
            <div className="flex items-center gap-2" style={{ fontWeight: 700 }}>
              <CheckCircle2 size={18} />
              <span>Reset Link Generated</span>
            </div>
            <p style={{ margin: 0, fontSize: '0.875rem' }}>{statusMsg}</p>
            {resetLink && (
              <div style={{
                marginTop: '0.5rem',
                paddingTop: '0.75rem',
                borderTop: '1px dashed rgba(16, 185, 129, 0.35)',
                width: '100%'
              }}>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-main)', marginBottom: '0.5rem' }}>
                  <strong>Development Shortcut:</strong> Click below to navigate directly:
                </p>
                <button
                  type="button"
                  onClick={() => navigate(resetLink)}
                  className="btn btn-primary w-full"
                  style={{ fontSize: '0.875rem', padding: '0.55rem 0.9rem' }}
                >
                  <span>Open Reset Password Page</span>
                  <ArrowRight size={15} />
                </button>
              </div>
            )}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Email Address</label>
            <div style={{ position: 'relative' }}>
              <input
                type="email"
                className="form-input"
                placeholder="name@institute.edu"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                style={{ paddingLeft: '2.5rem' }}
              />
              <Mail
                size={18}
                style={{
                  position: 'absolute',
                  left: '0.85rem',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'var(--text-subtle)',
                  pointerEvents: 'none'
                }}
              />
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary w-full"
            disabled={loading}
            style={{ marginTop: '1.25rem', padding: '0.8rem 1rem', fontSize: '0.975rem' }}
          >
            {loading ? (
              <>
                <div className="spinner spinner-white" style={{ width: '18px', height: '18px' }}></div>
                <span>Sending Link...</span>
              </>
            ) : (
              <div className="flex items-center gap-2">
                <span>Send Reset Link</span>
                <ArrowRight size={18} />
              </div>
            )}
          </button>
        </form>

        <div className="text-center" style={{ marginTop: '1.75rem' }}>
          <Link
            to="/login"
            className="inline-flex items-center gap-2"
            style={{ color: 'var(--text-muted)', fontSize: '0.875rem', fontWeight: 600 }}
          >
            <ArrowLeft size={16} /> Back to Login
          </Link>
        </div>
      </div>
    </div>
  );
}

