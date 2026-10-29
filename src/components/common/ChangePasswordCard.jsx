import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Lock, Eye, EyeOff, CheckCircle2, AlertCircle, LogOut } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../utils/api';

export default function ChangePasswordCard() {
  const navigate = useNavigate();
  const { user, logoutAll } = useAuth();

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showCurrentPwd, setShowCurrentPwd] = useState(false);
  const [showNewPwd, setShowNewPwd] = useState(false);
  const [showConfirmPwd, setShowConfirmPwd] = useState(false);

  const [pwdLoading, setPwdLoading] = useState(false);
  const [pwdSuccess, setPwdSuccess] = useState('');
  const [pwdError, setPwdError] = useState('');

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setPwdSuccess('');
    setPwdError('');

    if (!currentPassword || !newPassword || !confirmPassword) {
      setPwdError('Please fill in all fields.');
      return;
    }
    if (newPassword.length < 4) {
      setPwdError('New password must be at least 4 characters long.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setPwdError('New password and confirmation do not match.');
      return;
    }
    if (currentPassword === newPassword) {
      setPwdError('New password cannot be the same as the current password.');
      return;
    }

    setPwdLoading(true);
    try {
      const response = await api.post('/api/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to change password.');
      }

      setPwdSuccess('Password changed successfully! Active session rotated securely.');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      setPwdError(err.message || 'Failed to connect to backend.');
    } finally {
      setPwdLoading(false);
    }
  };

  const handleLogoutAll = async () => {
    if (window.confirm('Are you sure you want to log out from all devices?')) {
      await logoutAll();
      navigate('/login');
    }
  };

  return (
    <div style={{ maxWidth: '520px' }}>
      <div className="card">
        <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '0.5rem' }}>
          <Lock size={18} style={{ marginRight: '0.5rem', verticalAlign: 'text-bottom' }} />
          Update Password
        </h3>
        <p className="text-muted" style={{ fontSize: '0.85rem', marginBottom: '1.5rem' }}>
          Enter your current password and choose a new one. Password must be at least 4 characters.
        </p>

        <form onSubmit={handleChangePassword}>
          {/* Current Password */}
          <div className="form-group" style={{ marginBottom: '1.15rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
              <label className="form-label" style={{ marginBottom: 0 }}>Current Password</label>
              <Link
                to="/forgot-password"
                state={{ email: user?.email, fromPortal: true }}
                style={{ fontSize: '0.8rem', color: 'var(--primary-color)', textDecoration: 'none', fontWeight: 600 }}
              >
                Forgot Password?
              </Link>
            </div>
            <div style={{ position: 'relative' }}>
              <input
                type={showCurrentPwd ? 'text' : 'password'}
                className="form-input"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                placeholder="Enter current password"
                required
                style={{ paddingRight: '2.75rem' }}
              />
              <button
                type="button"
                onClick={() => setShowCurrentPwd(!showCurrentPwd)}
                style={{
                  position: 'absolute',
                  right: '0.75rem',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: 'var(--text-muted)',
                  padding: '0.2rem',
                }}
                aria-label="Toggle password visibility"
              >
                {showCurrentPwd ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {/* New Password */}
          <div className="form-group" style={{ marginBottom: '1.15rem' }}>
            <label className="form-label">New Password</label>
            <div style={{ position: 'relative' }}>
              <input
                type={showNewPwd ? 'text' : 'password'}
                className="form-input"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Enter new password"
                minLength={4}
                required
                style={{ paddingRight: '2.75rem' }}
              />
              <button
                type="button"
                onClick={() => setShowNewPwd(!showNewPwd)}
                style={{
                  position: 'absolute',
                  right: '0.75rem',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: 'var(--text-muted)',
                  padding: '0.2rem',
                }}
                aria-label="Toggle password visibility"
              >
                {showNewPwd ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {/* Confirm New Password */}
          <div className="form-group" style={{ marginBottom: '1.5rem' }}>
            <label className="form-label">Confirm New Password</label>
            <div style={{ position: 'relative' }}>
              <input
                type={showConfirmPwd ? 'text' : 'password'}
                className="form-input"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm new password"
                required
                minLength={4}
                style={{ paddingRight: '2.75rem' }}
              />
              <button
                type="button"
                onClick={() => setShowConfirmPwd(!showConfirmPwd)}
                style={{
                  position: 'absolute',
                  right: '0.75rem',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: 'var(--text-muted)',
                  padding: '0.2rem',
                }}
                aria-label="Toggle password visibility"
              >
                {showConfirmPwd ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {pwdSuccess && (
            <div className="alert alert-success" style={{ marginBottom: '1rem' }}>
              <CheckCircle2 size={18} style={{ flexShrink: 0 }} />
              <span>{pwdSuccess}</span>
            </div>
          )}
          {pwdError && (
            <div className="alert alert-danger" style={{ marginBottom: '1rem' }}>
              <AlertCircle size={18} style={{ flexShrink: 0 }} />
              <span>{pwdError}</span>
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary"
            disabled={pwdLoading}
            style={{ width: '100%' }}
          >
            {pwdLoading ? (
              <>
                <div className="spinner spinner-white" style={{ width: '16px', height: '16px' }}></div>
                <span>Changing Password...</span>
              </>
            ) : (
              <>
                <Lock size={16} />
                <span>Change Password</span>
              </>
            )}
          </button>
        </form>

        {/* Reset via Email Callout */}
        <div
          style={{
            marginTop: '1.5rem',
            padding: '0.85rem 1.15rem',
            backgroundColor: 'var(--surface-color)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-color)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '1rem',
          }}
        >
          <div>
            <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-main)' }}>
              Forgot your current password?
            </div>
            <div className="text-muted" style={{ fontSize: '0.78rem' }}>
              Send a password reset link to your registered email address.
            </div>
          </div>
          <Link
            to="/forgot-password"
            state={{ email: user?.email, fromPortal: true }}
            className="btn btn-outline"
            style={{ padding: '0.35rem 0.85rem', fontSize: '0.8rem', whiteSpace: 'nowrap', textDecoration: 'none' }}
          >
            Reset via Email
          </Link>
        </div>

        {/* Device & Session Management */}
        <div style={{ marginTop: '2rem', paddingTop: '1.5rem', borderTop: '1px solid var(--border-color)' }}>
          <h4 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '0.5rem', color: 'var(--danger-color)' }}>
            Device & Session Management
          </h4>
          <p className="text-muted" style={{ fontSize: '0.825rem', marginBottom: '1rem' }}>
            Lost a device or want to force logout everywhere? Invalidate all active sessions across all browsers and devices.
          </p>
          <button
            type="button"
            className="btn btn-outline"
            style={{ borderColor: 'var(--danger-color)', color: 'var(--danger-color)', width: '100%' }}
            onClick={handleLogoutAll}
          >
            <LogOut size={16} style={{ marginRight: '0.5rem' }} />
            Log Out From All Devices
          </button>
        </div>
      </div>
    </div>
  );
}
