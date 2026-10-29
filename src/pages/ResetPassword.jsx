import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { Lock, Eye, EyeOff, CheckCircle2, AlertCircle, ArrowRight, ShieldCheck, ArrowLeft, KeyRound } from 'lucide-react';
import { api } from '../utils/api';

export default function ResetPassword() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const tokenFromUrl = searchParams.get('token') || '';

  const [token, setToken] = useState(tokenFromUrl);
  const [validatingToken, setValidatingToken] = useState(Boolean(tokenFromUrl));
  const [tokenValid, setTokenValid] = useState(!tokenFromUrl ? true : null);
  const [tokenErrorMsg, setTokenErrorMsg] = useState('');
  const [requiresOtp, setRequiresOtp] = useState(false);
  const [otpCode, setOtpCode] = useState('');

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  // ── Sanitize browser URL & Validate Token on Mount ────────────
  useEffect(() => {
    if (!tokenFromUrl) return;

    // Immediately remove sensitive raw token from the address bar to prevent history/referer leakage
    window.history.replaceState({}, document.title, window.location.pathname);

    const validateToken = async () => {
      setValidatingToken(true);
      try {
        const res = await api.get(`/api/auth/validate-reset-token?token=${encodeURIComponent(tokenFromUrl)}`);
        const data = await res.json();
        if (res.ok && data.is_valid) {
          setTokenValid(true);
          setRequiresOtp(Boolean(data.requires_otp));
        } else {
          setTokenValid(false);
          setTokenErrorMsg(data.message || 'This password reset link is invalid or has expired.');
        }
      } catch {
        setTokenValid(false);
        setTokenErrorMsg('Unable to validate reset link. Please check your connection and try again.');
      } finally {
        setValidatingToken(false);
      }
    };

    validateToken();
  }, [tokenFromUrl]);

  const handleReset = async (e) => {
    e.preventDefault();
    setError('');

    if (!token.trim()) {
      setError('Invalid or missing password reset token.');
      return;
    }

    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters long and contain both letters and numbers.');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    if (requiresOtp && !otpCode.trim()) {
      setError('Please enter the 6-digit verification code sent to your email.');
      return;
    }

    setLoading(true);

    try {
      const response = await api.post('/api/auth/reset-password', {
        token: token.trim(),
        new_password: newPassword,
        otp_code: requiresOtp ? otpCode.trim() : null,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Password reset failed.');
      }

      setSuccess(true);
    } catch (err) {
      setError(err.message || 'An error occurred during password reset.');
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
            <ShieldCheck size={28} />
          </div>
          <h2 style={{ marginBottom: '0.5rem', fontWeight: 800 }}>Set New Password</h2>
          <p className="text-muted" style={{ fontSize: '0.925rem' }}>
            Enter and confirm your new secure password to access your account.
          </p>
        </div>

        {error && (
          <div className="alert alert-danger">
            <AlertCircle size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
            <span>{error}</span>
          </div>
        )}

        {validatingToken ? (
          <div style={{ textAlign: 'center', padding: '2.5rem 1rem' }}>
            <div className="spinner" style={{ width: '38px', height: '38px', margin: '0 auto 1.25rem' }}></div>
            <h4 style={{ fontWeight: 700, marginBottom: '0.35rem' }}>Verifying Security Link...</h4>
            <p className="text-muted" style={{ fontSize: '0.85rem' }}>
              Validating token integrity and expiration.
            </p>
          </div>
        ) : tokenValid === false ? (
          <div style={{ textAlign: 'center', padding: '1rem 0' }}>
            <div style={{
              width: '64px',
              height: '64px',
              borderRadius: '50%',
              backgroundColor: 'var(--danger-light)',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--danger-color)',
              marginBottom: '1.25rem',
              boxShadow: '0 0 0 6px rgba(239, 68, 68, 0.08)'
            }}>
              <AlertCircle size={32} />
            </div>
            <h3 style={{ marginBottom: '0.5rem', fontWeight: 700 }}>Invalid or Expired Link</h3>
            <p className="text-muted" style={{ marginBottom: '1.75rem', fontSize: '0.875rem', lineHeight: 1.5 }}>
              {tokenErrorMsg || 'This password reset link is invalid or has expired. For your security, reset links are single-use and expire after 20 minutes.'}
            </p>
            <Link
              to="/forgot-password"
              className="btn btn-primary w-full inline-flex items-center justify-center gap-2"
              style={{ padding: '0.85rem' }}
            >
              <span>Request a New Reset Link</span>
              <ArrowRight size={18} />
            </Link>
            <div className="text-center" style={{ marginTop: '1.5rem' }}>
              <Link
                to="/login"
                className="inline-flex items-center gap-2"
                style={{ color: 'var(--text-muted)', fontSize: '0.875rem', fontWeight: 600 }}
              >
                <ArrowLeft size={16} /> Back to Login
              </Link>
            </div>
          </div>
        ) : success ? (
          <div style={{ textAlign: 'center', padding: '1rem 0' }}>
            <div style={{
              width: '68px',
              height: '68px',
              borderRadius: '50%',
              backgroundColor: 'var(--success-light)',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--success-color)',
              marginBottom: '1.25rem',
              boxShadow: '0 0 0 6px rgba(16, 185, 129, 0.08)'
            }}>
              <CheckCircle2 size={36} />
            </div>
            <h3 style={{ marginBottom: '0.5rem', fontWeight: 700 }}>Password Updated!</h3>
            <p className="text-muted" style={{ marginBottom: '1.75rem', fontSize: '0.9rem', lineHeight: 1.5 }}>
              Your password has been successfully updated. All prior active sessions across all devices have been signed out. You can now log in with your new credentials.
            </p>
            <button
              onClick={() => navigate('/login')}
              className="btn btn-primary w-full"
              style={{ padding: '0.85rem' }}
            >
              <span>Proceed to Login</span>
              <ArrowRight size={18} />
            </button>
          </div>
        ) : (
          <form onSubmit={handleReset}>
            {!tokenFromUrl && (
              <div className="form-group">
                <label className="form-label">Reset Token</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="Paste your reset token here"
                  required
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                />
              </div>
            )}

            {requiresOtp && (
              <div className="form-group" style={{ marginBottom: '1.25rem' }}>
                <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <KeyRound size={15} style={{ color: 'var(--primary-color)' }} />
                  <span>Security Verification Code (OTP)</span>
                </label>
                <div style={{ position: 'relative' }}>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Enter 6-digit code"
                    required
                    maxLength={6}
                    value={otpCode}
                    onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
                    style={{ paddingLeft: '2.5rem', letterSpacing: '4px', fontWeight: 700, fontSize: '1.1rem' }}
                  />
                  <KeyRound
                    size={18}
                    style={{
                      position: 'absolute',
                      left: '0.85rem',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      color: 'var(--primary-color)',
                      pointerEvents: 'none'
                    }}
                  />
                </div>
                <p className="text-muted" style={{ fontSize: '0.78rem', marginTop: '0.35rem' }}>
                  An additional verification code was dispatched to your email because a new network or device was detected.
                </p>
              </div>
            )}

            <div className="form-group">
              <label className="form-label">New Password</label>
              <div style={{ position: 'relative' }}>
                <input
                  type={showPassword ? 'text' : 'password'}
                  className="form-input"
                  placeholder="Enter new password (min. 8 characters)"
                  required
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  style={{ paddingLeft: '2.5rem', paddingRight: '2.5rem' }}
                />
                <Lock
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
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={{
                    position: 'absolute',
                    right: '0.85rem',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    color: 'var(--text-muted)',
                    display: 'inline-flex',
                    alignItems: 'center',
                    padding: '0.2rem'
                  }}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Confirm New Password</label>
              <div style={{ position: 'relative' }}>
                <input
                  type={showPassword ? 'text' : 'password'}
                  className="form-input"
                  placeholder="Re-enter new password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  style={{ paddingLeft: '2.5rem' }}
                />
                <Lock
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
                  <span>Updating Password...</span>
                </>
              ) : (
                <div className="flex items-center gap-2">
                  <span>Update Password</span>
                  <ArrowRight size={18} />
                </div>
              )}
            </button>

            <div className="text-center" style={{ marginTop: '1.5rem' }}>
              <Link
                to="/login"
                className="inline-flex items-center gap-2"
                style={{ color: 'var(--text-muted)', fontSize: '0.875rem', fontWeight: 600 }}
              >
                <ArrowLeft size={16} /> Back to Login
              </Link>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

